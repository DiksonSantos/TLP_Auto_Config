import subprocess

def is_proton_game_running():
    """Pega programas que usam Wine Puro."""
    result = subprocess.run(["pgrep", "-f", "wine"], stdout=subprocess.DEVNULL)
    return result.returncode == 0
