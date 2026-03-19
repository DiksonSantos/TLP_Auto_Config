#!/usr/bin/env python3
# coding: utf-8
import subprocess
import time
import os
from Padrao import determine_governor, apply_pcie_policy


def is_steam_game_running():
    """
    Verifica se um jogo de 64 bits da Steam está rodando,
    filtrando jogos de 32 bits.
    """
    try:
        # Comando para listar todos os processos e seus caminhos
        result = subprocess.run(["ps", "-eo", "pid,cmd"], stdout=subprocess.PIPE, text=True)
        if result.returncode != 0:
            return False

        # Itera sobre cada processo
        for line in result.stdout.splitlines():
            line_parts = line.strip().split()
            if len(line_parts) < 2:
                continue

            # O primeiro elemento é o PID, o resto é o comando
            pid = line_parts[0]
            cmd = " ".join(line_parts[1:])

            # Verifica se o processo é de um jogo Steam, Ou jogos fora da Steam que use o GE-Proton
            if "steamapps/common" in cmd or "steamapps/compatdata" in cmd or "compatibilitytools.d" in cmd:
                # Tenta encontrar o caminho do executável.
                # Geralmente é a primeira parte do comando.
                exe_path = cmd.split()[0]
                if not os.path.exists(exe_path):
                    continue

                # Usa o comando 'file' para verificar a arquitetura
                try:
                    file_result = subprocess.run(["file", exe_path], stdout=subprocess.PIPE, text=True)
                    if "ELF 64-bit" in file_result.stdout:
                        print(f"Jogo 64-bit detectado: {exe_path}")
                        return True
                    else:
                        #print(f"Processo detectado, mas não é 64-bit: {exe_path}")
                        pass
                except FileNotFoundError:
                    # 'file' não está instalado. Não é possível verificar a arquitetura, então retorna False
                    # ou decide retornar True para não interromper a funcionalidade base.
                    print("Atenção: Comando 'file' não encontrado. Não é possível verificar a arquitetura dos jogos.")
                    # Como não podemos confirmar, vamos ser conservadores e retornar False para não ligar o modo de performance
                    # para jogos 32-bit por engano.
                    return False

    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        return False

    return False





def fix_log_permissions():
    """Altera as permissões do arquivo de log para 666 (leitura e escrita para todos)."""
    cmd = "chmod 666 /tmp/pos_Blue_Brilho.log"
    result = subprocess.run(
        ["sudo", "bash", "-c", cmd],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode == 0:
        print("✅ Permissões do log corrigidas (666).")
    else:
        print(f"❌ Erro ao corrigir permissões do log: {result.stderr}")

def is_any_steam_game_running():
    return is_steam_game_running()

def get_power_state():
    """Retorna 'on_ac' se conectado na tomada, ou 'on_battery'."""
    command = "cat /sys/class/power_supply/ACAD/online"
    result = subprocess.run(
        ["sudo", "bash", "-c", command],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        print(f"Erro ao verificar energia: {result.stderr}")
        return None
    return "on_ac" if result.stdout.strip() == "1" else "on_battery"

def apply_governor(governor):
    """Aplica o governor a todos os núcleos da CPU."""
    command = (
        f"for CPU in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do "
        f"echo {governor} > $CPU; done"
    )
    result = subprocess.run(
        ["sudo", "bash", "-c", command],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.returncode == 0, result.stderr


def fix_rapl_permission():
    """Muda o dono do arquivo de energia da CPU para o usuário atual."""
    cmd = "chown dikson:dikson /sys/class/powercap/intel-rapl:0/energy_uj"
    result = subprocess.run(
        ["sudo", "bash", "-c", cmd],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode == 0:
        print("✅ Permissão do energy_uj corrigida (dono alterado).")
    else:
        print(f"❌ Erro ao corrigir permissões: {result.stderr}")


def fix_brightness_permission():
    """Corrige a propriedade do arquivo de brilho da tela (opcional)."""
    cmd = "chown dikson:dikson /sys/class/backlight/intel_backlight/brightness"
    result = subprocess.run(
        ["sudo", "bash", "-c", cmd],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.returncode == 0, result.stderr

def set_cpu_governor():
    try:
        for i in range(1):
            print(f"\n[{i+1}/1] Verificando estado...")

            power_state = get_power_state()
            if power_state is None:
                return

            steam_running = is_any_steam_game_running()
            governor = determine_governor(power_state, steam_running)
            msg = apply_pcie_policy(power_state, steam_running)

            print(f"Fonte de energia: {'Tomada' if power_state == 'on_ac' else 'Bateria'}")
            print(f"Jogo Rodando: {'Sim' if steam_running else 'Não'}")
            print(f"Governor selecionado: {governor}")
            print(f"{msg}")

            success, error = apply_governor(governor)
            if success:
                print(f"✅ Governor: {governor} aplicado com sucesso.")
            else:
                print(f"❌ Erro ao aplicar governor: {error}")

            ok, err = fix_brightness_permission()
            if ok:
                print("✅ Permissão do brilho corrigida.")
            else:
                print(f"❌ Erro ao corrigir brilho: {err}")

            if i < 4:
                time.sleep(5)

    except Exception as e:
        print(f"Erro inesperado: {e}")

from set_gpu_power import set_gpu_power_mode

if __name__ == "__main__":
    set_cpu_governor()
    fix_rapl_permission()

    # --- Lê o governor atual ---
    try:
        result = subprocess.run(
            ["cat", "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"],
            stdout=subprocess.PIPE,
            text=True
        )
        current_governor = result.stdout.strip()
        #print(f"Governor atual: {current_governor}")
        pass

        # --- Define o modo da GPU conforme o governor ---
        if current_governor == "performance":
            gpu_mode = "max"
        elif current_governor == "schedutil":
            gpu_mode = "balanced"
        elif current_governor == "powersave":
            gpu_mode = "eco"
        else:
            gpu_mode = "balanced"  # modo padrão de segurança

        print(f"Aplicando modo de GPU: {gpu_mode}")
        set_gpu_power_mode(gpu_mode)

    except Exception as e:
        print(f"Erro ao aplicar perfil de GPU: {e}")

gpu_mode_aplicado = set_gpu_power_mode(gpu_mode)

with open("/tmp/gpu_mode_atual.txt", "w") as f:
    f.write(gpu_mode_aplicado)
