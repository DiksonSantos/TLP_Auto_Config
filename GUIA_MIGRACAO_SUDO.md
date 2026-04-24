# Guia de Migração: Removendo `sudo` do Gerenciamento de CPU/GPU

Este guia explica como eliminar chamadas `sudo` desnecessárias em scripts Python de gerenciamento de energia, substituindo-as por permissões permanentes via **udev** e **systemd**. O resultado é um sistema mais rápido, mais limpo e mais seguro.

---

## Por que fazer isso?

Cada chamada `subprocess.run(["sudo", ...])` tem um custo real:

- **Fork de processo**: o kernel cria um novo PID a cada chamada
- **Autenticação PAM**: o sudo consulta `/etc/shadow` e as regras de sudoers
- **Latência**: em loops que rodam a cada 5 segundos, esse overhead é perceptível

Ao conceder permissões permanentes via udev/systemd, o Python lê e escreve diretamente no `sysfs` — que reside na memória do kernel — sem disparar nenhum processo externo.

---

## Pré-requisitos

- Linux com systemd
- Acesso a `sudo` para aplicar as configurações uma única vez
- Substituir `seu_usuario` pelo seu nome de usuário real nos comandos abaixo

---

## Passo 1 — Regras udev para permissões permanentes

O udev aplica permissões automaticamente quando o kernel registra um dispositivo. Crie o arquivo de regras:

```bash
sudo nano /etc/udev/rules.d/99-power-management.rules
```

Cole o seguinte conteúdo, substituindo `seu_usuario` pelo seu usuário:

```
# Permissão para o Brilho da tela (Intel Backlight)
ACTION=="add", SUBSYSTEM=="backlight", KERNEL=="intel_backlight", \
    RUN+="/usr/bin/chown seu_usuario:seu_usuario /sys/class/backlight/intel_backlight/brightness"

# Permissão para o Intel RAPL (Energia da CPU)
ACTION=="add", SUBSYSTEM=="powercap", KERNEL=="intel-rapl:0", \
    RUN+="/usr/bin/chown -R seu_usuario:seu_usuario /sys/class/powercap/intel-rapl:0/"

# Permissão de leitura para o estado da fonte de energia (AC)
ACTION=="add", SUBSYSTEM=="power_supply", KERNEL=="ACAD", \
    RUN+="/usr/bin/chmod 644 /sys/class/power_supply/ACAD/online"
```

Aplique as regras sem reiniciar:

```bash
sudo udevadm control --reload-rules && sudo udevadm trigger
```

> **Nota:** O `scaling_governor` da CPU **não** pode ser tratado pelo udev com `ACTION=="add"`, pois o cpufreq já existe antes das regras serem processadas. Ele é tratado no Passo 2.

---

## Passo 2 — Serviço systemd para o `scaling_governor`

O `scaling_governor` precisa de permissão de escrita em todos os núcleos. Como o udev não consegue capturar esse dispositivo de forma confiável no boot, usamos um serviço `oneshot` do systemd:

```bash
sudo nano /etc/systemd/system/fix-cpufreq-perms.service
```

Cole o conteúdo:

```ini
[Unit]
Description=Corrige permissões do scaling_governor da CPU
After=systemd-modules-load.service
Before=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'chmod 666 /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

Ative e aplique imediatamente:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now fix-cpufreq-perms.service
```

Verifique se funcionou:

```bash
ls -la /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
# Esperado: -rw-rw-rw-
```

---

## Passo 3 — Substituir `subprocess sudo` por leitura direta em Python

Com as permissões no lugar, substitua as chamadas lentas por acesso direto ao `sysfs`:

```python
# ANTES — lento, gera processo extra, requer sudo
result = subprocess.run(["sudo", "bash", "-c", "cat /sys/class/power_supply/ACAD/online"], ...)

# DEPOIS — instantâneo, sem processo extra, sem sudo
def get_power_state():
    try:
        with open("/sys/class/power_supply/ACAD/online", "r") as f:
            return "on_ac" if f.read().strip() == "1" else "on_battery"
    except Exception as e:
        print(f"Erro ao ler energia: {e}")
        return None
```

```python
# ANTES — lento, requer sudo
subprocess.run(["sudo", "bash", "-c", f"echo {governor} > /sys/.../scaling_governor"], ...)

# DEPOIS — instantâneo, sem sudo
import glob

def apply_governor(governor):
    try:
        files = glob.glob("/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor")
        for cpu_file in files:
            with open(cpu_file, "w") as f:
                f.write(governor)
        return True, ""
    except Exception as e:
        return False, str(e)
```

```python
# ANTES — lento, requer sudo
subprocess.run(["sudo", "bash", "-c", "cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"], ...)

# DEPOIS — instantâneo, sem sudo
def get_estado_atual():
    with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor", "r") as f:
        governor = f.read().strip()

    with open("/sys/module/pcie_aspm/parameters/policy", "r") as f:
        aspm_raw = f.read().strip()
        aspm = re.search(r'\[(\w+)\]', aspm_raw)
        aspm = aspm.group(1) if aspm else aspm_raw

    return governor, aspm
```

---

## Passo 4 — Limpar o sudoers

Com udev e systemd no lugar, várias entradas do sudoers se tornam redundantes. Edite com segurança usando:

```bash
sudo visudo -f /etc/sudoers.d/99-seu-arquivo
```

**Remova** as linhas que tratavam de:
- `scaling_governor` → coberto pelo systemd
- `chown intel_backlight` → coberto pelo udev
- `chown intel-rapl` → coberto pelo udev
- `cat ACAD/online` → coberto pelo udev
- `/usr/bin/bash` irrestrito → **risco de segurança**, remova sempre

**Mantenha** apenas o que ainda precisa de privilégio real, como:
- Escrita no `pcie_aspm` (ASPM policy)
- `nvidia-smi` (gerenciamento de GPU)
- `systemctl suspend`

Valide a sintaxe antes de fechar o terminal:

```bash
sudo visudo -c
# Esperado: parsed OK para todos os arquivos
```

---

## Resultado esperado

Após seguir este guia, seus scripts de gerenciamento de energia rodam **sem nenhuma senha, sem nenhum processo extra**, lendo e escrevendo diretamente no kernel via `sysfs`. O `sudo` fica reservado apenas para operações que genuinamente exigem privilégio de root.
