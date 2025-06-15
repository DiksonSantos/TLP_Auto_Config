#!/usr/bin/env python3
# coding: utf-8

import subprocess
import time
import os
from Padrao import determine_governor, apply_pcie_policy

def is_steam_game_running():
    result = subprocess.run(["ps", "-eo", "pid,cmd"], stdout=subprocess.PIPE, text=True)
    for line in result.stdout.splitlines():
        if "steamapps/common" in line:
            return True
    return False

def fix_log_permissions(password):
    """Altera as permissões do arquivo de log para 666 (leitura e escrita para todos)."""
    cmd = "chmod 666 /var/log/pos_Blue_Brilho.log"
    result = subprocess.run(
        ["sudo", "-S", "bash", "-c", cmd],
        input=f"{password}\n",
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

def get_power_state(password):
    """Retorna 'on_ac' se conectado na tomada, ou 'on_battery'."""
    command = "cat /sys/class/power_supply/ACAD/online"
    result = subprocess.run(
        ["sudo", "-S", "bash", "-c", command],
        input=f"{password}\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        print(f"Erro ao verificar energia: {result.stderr}")
        return None
    return "on_ac" if result.stdout.strip() == "1" else "on_battery"

def apply_governor(password, governor):
    """Aplica o governor a todos os núcleos da CPU."""
    command = (
        f"for CPU in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do "
        f"echo {governor} > $CPU; done"
    )
    result = subprocess.run(
        ["sudo", "-S", "bash", "-c", command],
        input=f"{password}\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.returncode == 0, result.stderr

def fix_brightness_permission(password):
    """Corrige a propriedade do arquivo de brilho da tela (opcional)."""
    cmd = "chown dikson:dikson /sys/class/backlight/intel_backlight/brightness"
    result = subprocess.run(
        ["sudo", "-S", "bash", "-c", cmd],
        input=f"{password}\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.returncode == 0, result.stderr

def set_cpu_governor(password):
    try:
        for i in range(2):
            print(f"\n[{i+1}/2] Verificando estado...")

            power_state = get_power_state(password)
            if power_state is None:
                return

            steam_running = is_any_steam_game_running()
            governor = determine_governor(power_state, steam_running)
            msg = apply_pcie_policy(password, power_state, steam_running)

            print(f"Fonte de energia: {'Tomada' if power_state == 'on_ac' else 'Bateria'}")
            print(f"Jogo Rodando: {'Sim' if steam_running else 'Não'}")
            print(f"Governor selecionado: {governor}")
            print(f"{msg}")

            success, error = apply_governor(password, governor)
            if success:
                print(f"✅ Governor: {governor} aplicado com sucesso.")
            else:
                print(f"❌ Erro ao aplicar governor: {error}")

            ok, err = fix_brightness_permission(password)
            if ok:
                print("✅ Permissão do brilho corrigida.")
            else:
                print(f"❌ Erro ao corrigir brilho: {err}")

            if i < 4:
                time.sleep(5)

    except Exception as e:
        print(f"Erro inesperado: {e}")

if __name__ == "__main__":
    user_password = 'Sua_Senha_AQUI'  # substitua por input() se quiser interativo
    set_cpu_governor(user_password)
