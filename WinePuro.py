import subprocess
import os

def is_proton_game_running():
    """
    Detecta jogos de 64-bit (via Steam/Proton/Wine) e emuladores.
    Ignora processos de 32-bit ou o cliente Steam principal.
    """
    result = subprocess.run(["ps", "-eo", "pid,cmd"], capture_output=True, text=True)
    if result.returncode != 0:
        return False

    for line in result.stdout.splitlines():
        if line.strip().startswith("PID"):
            continue

        parts = line.strip().split(None, 1)
        if len(parts) < 2:
            continue

        pid, cmd = parts
        ll = cmd.lower()

        # Verifica processos que podem ser jogos/emuladores.
        if any(substr in ll for substr in (
            "steamapps/compatdata",
            "proton",
            "pcsx2",
            "rpcs3"
        )) or ("wine" in ll and "steamclient" not in ll): # Exclui processos como steamclient.exe que são 32bits

            # Executa a verificação de arquitetura
            try:
                exe_path = f"/proc/{pid}/exe"
                file_output = subprocess.check_output(["file", exe_path], text=True)

                if "64-bit" in file_output or "pcsx2" in ll or "rpcs3" in ll:
                    # Se for um processo 64-bit ou um emulador, consideramos um jogo válido.
                    return True

            except Exception:
                continue

    return False

"""
Se a prioridade for performance a versão ativa (a cima) é preferível.
A versão def a baixo usaria mais ciclos e verificações/processamento.
"""


# def is_proton_game_running():
#     """Detecta Proton (ou wine) e emuladores PCSX2/RPCS3.
#        Ignora processos Wine de 32-bit."""
#     result = subprocess.run(["ps", "-eo", "pid,cmd"], capture_output=True, text=True)
#     if result.returncode != 0:
#         return False
#
#     for line in result.stdout.splitlines():
#         if line.strip().startswith("PID"):  # pular cabeçalho
#             continue
#
#         parts = line.strip().split(None, 1)
#         if len(parts) < 2:
#             continue
#
#         pid, cmd = parts
#         exe_path = f"/proc/{pid}/exe"
#         ll = cmd.lower()
#
#         if any(substr in ll for substr in (
#             "steamapps/compatdata",
#             "wine",
#             "proton",
#             "pcsx2",
#             "rpcs3"
#         )):
#             try:
#                 file_output = subprocess.check_output(["file", exe_path], text=True)
#
#                 # Ignora Wine 32-bit
#                 if "wine" in ll and "32-bit" in file_output:
#                     continue
#
#                 # Aceita se for 64-bit Wine ou se for emulador
#                 if "64-bit" in file_output or "pcsx2" in ll or "rpcs3" in ll:
#                     return True
#
#             except Exception:
#                 # /proc/<pid>/exe pode falhar (permissão, processo fechando, etc.)
#                 continue
#
#     return False

# def is_proton_game_running():
#     """Pega programas que usam Wine Puro."""
#     result = subprocess.run(["pgrep", "-f", "wine"], stdout=subprocess.DEVNULL)
#     return result.returncode == 0

# def is_proton_game_running():
#     """Detecta se há algum jogo rodando via Proton (inclusive GE)."""
#     result = subprocess.run(["pgrep", "-fa", "wine"], capture_output=True, text=True)
#     if result.returncode != 0:
#         return False
#
#     for line in result.stdout.splitlines():
#         if "steamapps/compatdata" in line or "proton" in line.lower():
#             return True
#     return False

# def is_proton_game_running():
#     """Detecta Proton (ou wine) e emuladores PCSX2/RPCS3."""
#     # listar todos os processos com comando completo
#     result = subprocess.run(["ps", "-eo", "pid,cmd"], capture_output=True, text=True)
#     if result.returncode != 0:
#         return False
#
#     for line in result.stdout.splitlines():
#         ll = line.lower()
#         # Aqui está a linha única com os emuladores incluídos
#         if any(substr in ll for substr in (
#             "steamapps/compatdata",
#             "wine",
#             "proton",
#             "pcsx2",
#             "rpcs3"
#         )):
#             return True
#     return False


# if __name__ == "__main__":
#     if is_proton_game_running():
#         print("🎮 Jogo ou emulador detectado (Proton/Wine/PCSX2/RPCS3).")
#     else:
#         print("⚡ Nenhum jogo ou emulador detectado.")
