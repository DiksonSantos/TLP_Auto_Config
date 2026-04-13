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

# ---------------------------------------------------------------------------
# Inicialização
# ---------------------------------------------------------------------------
print("🚀 Looping Dono Ativo (Monitorando GUI e Jogos)")
subprocess.call(f'python3 {SUDO_CPU_PATH}', shell=True)

steam_anterior = False
perfil_atual = get_perfil_do_script()

while True:
    time.sleep(5)

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

    print(f"[{perfil_atual}] Esperado: {gov_esperado}/{aspm_esperado} | Atual: {gov_atual}/{aspm_atual}")

    if gov_atual != gov_esperado or aspm_atual != aspm_esperado:
        print("🔄 Estado divergente. Aplicando perfil...")
        subprocess.call(f'python3 {SUDO_CPU_PATH}', shell=True)
