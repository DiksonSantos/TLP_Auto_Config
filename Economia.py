import subprocess

def determine_governor(power_state, steam_running):
    """Retorna o governor adequado conforme a situação para o perfil Padrão."""
    if power_state == "on_battery":
        return "powersave"
    # Caso não esteja na bateria, e rode um jogo Steam;
    if steam_running:
        return "schedutil"
    return "powersave"

def apply_pcie_policy(power_state, steam_running):
    """Aplica a política ASPM para o perfil Economia."""
    if power_state == "on_battery":
        policy = "powersupersave"
    elif steam_running:
        policy = "powersave"
    else:
        policy = "powersupersave"

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

def dry_run(power_state, steam_running):
    """Retorna o que seria aplicado, sem aplicar nada."""
    governor = determine_governor(power_state, steam_running)

    if power_state == "on_battery":
        aspm = "powersupersave"
    elif steam_running:
        aspm = "powersave"
    else:
        aspm = "powersupersave"

    return governor, aspm


# OLD
# import subprocess
#
# def determine_governor(power_state, steam_running):
#     """Retorna o governor adequado conforme a situação para o perfil Economia."""
#     return "powersave"
#
# def apply_pcie_policy(password, power_state, steam_running):
#     """Aplica a política ASPM para o perfil Economia."""
#     policy = "powersupersave" #if power_state == "on_battery" else "powersave"
#
#     cmd = f"echo {policy} > /sys/module/pcie_aspm/parameters/policy"
#     result = subprocess.run(
#         ["sudo", "-S", "bash", "-c", cmd],
#         input=f"{password}\n",
#         text=True,
#         stdout=subprocess.PIPE,
#         stderr=subprocess.PIPE,
#     )
#
#     if result.returncode == 0:
#         return f"✅ ASPM policy aplicada: {policy}"
#     else:
#         return f"❌ Erro ao aplicar policy ASPM: {result.stderr}"
