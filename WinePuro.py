import subprocess

# def is_proton_game_running():
#     """Pega programas que usam Wine Puro."""
#     result = subprocess.run(["pgrep", "-f", "wine"], stdout=subprocess.DEVNULL)
#     return result.returncode == 0

def is_proton_game_running():
    """Detecta se há algum jogo rodando via Proton (inclusive GE)."""
    result = subprocess.run(["pgrep", "-fa", "wine"], capture_output=True, text=True)
    if result.returncode != 0:
        return False

    for line in result.stdout.splitlines():
        if "steamapps/compatdata" in line or "proton" in line.lower():
            return True
    return False
