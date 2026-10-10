#!/usr/bin/env python3
import subprocess
import time
import re
import sys
import os
import importlib

# Corrigido para .py para evitar a criação de arquivos .sh fantasmas
SUDO_CPU_PATH = '/home/dikson/Linux_Helper/TLP_Power_Management/SUDO_CPU_2key.py'
sys.path.insert(0, '/home/dikson/Linux_Helper/TLP_Power_Management/')

# Gap (em segundos) entre relógio de parede e relógio monotônico que indica
# que o sistema foi suspenso (standby). Ver _detectar_suspensao() mais abaixo.
# Mesma técnica usada no fan_control.py: durante a suspensão, o relógio de
# parede (time.time()) salta pra frente, mas o monotônico (time.monotonic())
# fica pausado no Linux — a diferença entre os dois é o tempo suspenso.
SUSPEND_GAP_SEGUNDOS = 8


def set_fan_profile(perfil):
    """Ventoinha Inteligente -> 1.40V na tomada, e Volta a AUTO em AC """
    try:
        import socket
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(0.5)
            client.connect("/tmp/fan_control.sock")
            client.send(f"PERFIL:{perfil}".encode())
    except:
        pass


def get_perfil_do_script():
    """Lê qual perfil (módulo) está importado na linha 'from X import ...' do SUDO_CPU."""
    try:
        result = subprocess.run(
            ["grep", "^from.*import determine_governor", SUDO_CPU_PATH],
            stdout=subprocess.PIPE, text=True
        )
        match = re.search(r'from (\w+) import', result.stdout)
        return match.group(1) if match else None
    except:
        return None

def get_power_state():
    """Lê se está na tomada ou na bateria."""
    try:
        with open("/sys/class/power_supply/ACAD/online", "r") as f:
            return "on_ac" if f.read().strip() == "1" else "on_battery"
    except:
        return "on_ac"

def get_steam_running():
    """Importa a detecção do script principal."""
    try:
        dir_path = os.path.dirname(SUDO_CPU_PATH)
        if dir_path not in sys.path:
            sys.path.append(dir_path)
        import SUDO_CPU_2key as sc
        importlib.reload(sc)
        return sc.is_steam_game_running()
    except:
        return False

def get_estado_atual():
    """Lê o governor e a política ASPM do hardware."""
    with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor", "r") as f:
        gov = f.read().strip()
    with open("/sys/module/pcie_aspm/parameters/policy", "r") as f:
        aspm_raw = f.read().strip()
        aspm = re.search(r'\[(.*?)\]', aspm_raw).group(1) if "[" in aspm_raw else aspm_raw
    return gov, aspm

def kill_wineserver_if_stale():
    """Limpa o wineserver se não houver jogo real rodando."""
    try:
        result = subprocess.run(["ps", "-eo", "pid,cmd"], stdout=subprocess.PIPE, text=True)
        wine_daemons = {"wineserver", "winedevice.exe", "services.exe", "plugplay.exe", "explorer.exe"}
        has_real_process = False
        for line in result.stdout.splitlines():
            parts = line.strip().split(None, 1)
            if len(parts) < 2: continue
            cmd = parts[1].lower()
            exe_name = os.path.basename(cmd.split()[0]) if cmd.split() else ""
            if exe_name in wine_daemons: continue
            if any(x in cmd for x in ("wine", "proton", "steamapps/compatdata")):
                has_real_process = True
                break
        if not has_real_process:
            print("🧹 Limpando processos residuais do Wine...")
            subprocess.run(["wineserver", "-k"], stderr=subprocess.DEVNULL)
            subprocess.run(["pkill", "-9", "-f", "wineserver"], stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Erro na limpeza: {e}")


def detectar_suspensao(last_wall, last_mono):
    """
    Compara relógio de parede com relógio monotônico para detectar se o
    sistema foi suspenso desde a última checagem (ver SUSPEND_GAP_SEGUNDOS).

    Retorna (suspensao_detectada: bool, agora_wall, agora_mono) — os dois
    últimos valores devem ser guardados pelo chamador para a próxima checagem.
    """
    agora_wall = time.time()
    agora_mono = time.monotonic()

    suspensao_detectada = False
    if last_wall is not None:
        gap = (agora_wall - last_wall) - (agora_mono - last_mono)
        if gap > SUSPEND_GAP_SEGUNDOS:
            suspensao_detectada = True

    return suspensao_detectada, agora_wall, agora_mono


# ---------------------------------------------------------------------------
# Inicialização
# ---------------------------------------------------------------------------
print("🚀 Looping Dono Ativo (Monitorando GUI e Jogos)")
subprocess.call(f'python3 {SUDO_CPU_PATH}', shell=True)

steam_anterior = False
perfil_atual = get_perfil_do_script()
estado_energia_anterior = None
_last_wall_clock = None
_last_monotonic = None

while True:
    time.sleep(5)

    # --- Detecção de suspensão do sistema (standby) ---
    # A PCIe Policy e o governor sobrevivem à suspensão (o kernel preserva
    # esses valores em sysfs), mas o registro de HCTM do controlador NVMe
    # NÃO sobrevive (o controlador reseta pro valor de fábrica). Como a
    # checagem de "divergência" mais abaixo só compara governor/ASPM, ela
    # nunca percebe essa perda sozinha — por isso a suspensão precisa ser
    # detectada explicitamente aqui, e forçar a reaplicação completa.
    suspensao_detectada, _last_wall_clock, _last_monotonic = detectar_suspensao(
        _last_wall_clock, _last_monotonic
    )
    if suspensao_detectada:
        print("💤 Suspensão do sistema detectada - reaplicando perfil completo "
              "(governor/PCIe/HCTM do NVMe/GPU)...")
        subprocess.call(f'python3 {SUDO_CPU_PATH}', shell=True)

    power_state = get_power_state()

    # 1. Verifica se você mudou o perfil na GUI (Turbo/Padrão/Eco)
    perfil_novo = get_perfil_do_script()
    if perfil_novo and perfil_novo != perfil_atual:
        print(f"🔄 Perfil alterado via GUI para: {perfil_novo}")
        perfil_atual = perfil_novo
        subprocess.call(f'python3 {SUDO_CPU_PATH}', shell=True)

    # 2. Carrega as regras do perfil ativo
    try:
        modulo = importlib.import_module(perfil_atual)
        importlib.reload(modulo)
    except:
        continue

    # 3. Monitora estado do Jogo e Energia
    power_state = get_power_state()
    steam = get_steam_running()

    # Gatilho de saída do jogo
    if steam_anterior and not steam:
        print("🎮 Jogo encerrado. Verificando limpeza de RAM...")
        kill_wineserver_if_stale()
        time.sleep(1) # Tempo para o kernel atualizar

    steam_anterior = steam

    # 4. Compara o esperado vs atual
    gov_esperado, aspm_esperado = modulo.dry_run(power_state, steam)
    try:
        gov_atual, aspm_atual = get_estado_atual()
    except:
        continue

    # Muda Rotação da Ventoinha apenas na TRANSIÇÃO de energia:
    if power_state != estado_energia_anterior:
        if power_state == "on_battery":
            set_fan_profile("BASICO")
            print("🔋 Ventoinha_Nvme em LENTA (Usando: Bateria)")

        if power_state == "on_ac" and power_state != estado_energia_anterior:
            set_fan_profile("NORMAL")
            print("🔌 Ventoinha_Nvme em AUTO (Usando: Tomada)")

        # ATUALIZA O ESTADO para evitar repetições no próximo loop de 5s
        estado_energia_anterior = power_state


    print(f"[{perfil_atual}] Esperado: {gov_esperado}/{aspm_esperado} | Atual: {gov_atual}/{aspm_atual}")


    if gov_atual != gov_esperado or aspm_atual != aspm_esperado:
        print("🔄 Estado divergente. Aplicando perfil...")
        subprocess.call(f'python3 {SUDO_CPU_PATH}', shell=True)
