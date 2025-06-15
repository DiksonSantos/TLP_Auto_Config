import subprocess

def determine_governor(power_state, steam_running):
    """Retorna o governor adequado conforme a situação para o perfil Turbo."""
    if power_state == "on_battery":
        return "schedutil"
    if steam_running:
        return "performance"
    return "schedutil"

def apply_pcie_policy(password, power_state, steam_running):
    """Aplica a política ASPM para o perfil Turbo."""
    if power_state == "on_battery":
        policy = "powersave"
    elif steam_running:
        policy = "performance"
    else:
        policy = "default"

    cmd = f"echo {policy} > /sys/module/pcie_aspm/parameters/policy"
    result = subprocess.run(
        ["sudo", "-S", "bash", "-c", cmd],
        input=f"{password}\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if result.returncode == 0:
        return f"✅ ASPM policy aplicada: {policy}"
    else:
        return f"❌ Erro ao aplicar policy ASPM: {result.stderr}"
