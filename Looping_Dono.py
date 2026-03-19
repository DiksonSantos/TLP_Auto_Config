#!/usr/bin/env python3
import subprocess
import time
import re
import sys
import os
import importlib

SUDO_CPU_PATH = '/home/dikson/Linux_Helper/TLP_Power_Management/SUDO_CPU_2key.sh'
sys.path.insert(0, '/home/dikson/Linux_Helper/TLP_Power_Management/')


def get_perfil_do_script():
    """Lê qual perfil está importado na linha 6 do SUDO_CPU."""
    result = subprocess.run(
        ["grep", "^from.*import determine_governor", SUDO_CPU_PATH],
        stdout=subprocess.PIPE, text=True
    )
    match = re.search(r'from (\w+) import', result.stdout)
    return match.group(1) if match else None


def get_power_state():
    result = subprocess.run(
        ["sudo", "bash", "-c", "cat /sys/class/power_supply/ACAD/online"],
        stdout=subprocess.PIPE, text=True
    )
    return "on_ac" if result.stdout.strip() == "1" else "on_battery"


def get_estado_atual():
    """Lê governor e ASPM policy ativos no sistema agora."""
    governor = subprocess.run(
        ["cat", "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"],
        stdout=subprocess.PIPE, text=True
    ).stdout.strip()

    aspm_raw = subprocess.run(
        ["cat", "/sys/module/pcie_aspm/parameters/policy"],
        stdout=subprocess.PIPE, text=True
    ).stdout.strip()
    aspm = re.search(r'\[(\w+)\]', aspm_raw)
    aspm = aspm.group(1) if aspm else aspm_raw

    return governor, aspm


def get_steam_running():
    """Detecta se um jogo 64-bit da Steam está rodando."""
    try:
        result = subprocess.run(["ps", "-eo", "pid,cmd"], stdout=subprocess.PIPE, text=True)
        if result.returncode != 0:
            return False
        for line in result.stdout.splitlines():
            line_parts = line.strip().split()
            if len(line_parts) < 2:
                continue
            pid = line_parts[0]
            cmd = " ".join(line_parts[1:])
            if "steamapps/common" in cmd or "steamapps/compatdata" in cmd or "compatibilitytools.d" in cmd:
                exe_path = cmd.split()[0]
                if not os.path.exists(exe_path):
                    continue
                try:
                    file_result = subprocess.run(["file", exe_path], stdout=subprocess.PIPE, text=True)
                    if "ELF 64-bit" in file_result.stdout:
                        return True
                except FileNotFoundError:
                    return False
    except Exception as e:
        print(f"Erro ao detectar jogo: {e}")
    return False


# CHAMADA UNICA PARA ALTERAR PERMISSÕES DO INTEL BACKLIGH / BRILHO DA TELA;
# Aplica o perfil imediatamente no início da sessão,
# garantindo permissões de brilho e estado correto antes do loop.
print("🚀 Inicializando — aplicando perfil imediatamente...")
subprocess.call(f'python3 {SUDO_CPU_PATH}', shell=True)


while True:
    time.sleep(5)

    perfil_nome = get_perfil_do_script()  # ex: "Padrao"
    if not perfil_nome:
        print("❌ Não foi possível identificar o perfil no script.")
        continue

    # Importa dinamicamente o perfil ativo e executa o dry_run
    modulo = importlib.import_module(perfil_nome)
    modulo = importlib.reload(modulo)  # garante que relê do disco sempre

    power_state = get_power_state()
    steam       = get_steam_running()
    gov_esperado, aspm_esperado = modulo.dry_run(power_state, steam)

    # Lê o estado atual do sistema
    gov_atual, aspm_atual = get_estado_atual()

    print(f"[{perfil_nome}] Esperado: {gov_esperado}/{aspm_esperado} | Atual: {gov_atual}/{aspm_atual}")

    if gov_atual != gov_esperado or aspm_atual != aspm_esperado:
        print("🔄 Estado divergente. Aplicando perfil...")
        subprocess.call(f'python3 {SUDO_CPU_PATH}', shell=True)
    else:
        print("✅ Perfil já vigente. Nada a fazer.")


# CONFERIR SE ESTA RODANDO;
# ps aux | grep Looping_Dono.py
