import subprocess

def determine_governor(power_state, steam_running):
    """Retorna o governor adequado conforme a situação para o perfil Economia."""
    return "powersave"

def apply_pcie_policy(password, power_state, steam_running):
    """Aplica a política ASPM para o perfil Economia."""
    policy = "powersupersave" if power_state == "on_battery" else "powersave"

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
