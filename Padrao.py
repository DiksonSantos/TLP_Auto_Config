import subprocess

def determine_governor(power_state, steam_running):
    """Retorna o governor adequado conforme a situação para o perfil Padrão."""
    if power_state == "on_battery":
        return "powersave"
    if steam_running:
        return "schedutil"
    return "schedutil"

def apply_pcie_policy(power_state, steam_running):
    """Aplica a política ASPM para o perfil Padrão."""
    if power_state == "on_battery":
        policy = "powersupersave"
    elif steam_running:
        policy = "default"
    else:
        policy = "powersave"

    cmd = f"echo {policy} > /sys/module/pcie_aspm/parameters/policy"
    result = subprocess.run(
        ["sudo", "bash", "-c", cmd],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if result.returncode == 0:
        return f"✅ ASPM policy aplicada: {policy}"
    else:
        return f"❌ Erro ao aplicar policy ASPM: {result.stderr}"
