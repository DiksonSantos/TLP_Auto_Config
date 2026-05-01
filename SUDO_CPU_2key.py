#!/usr/bin/env python3
# coding: utf-8
import subprocess
import glob
import time
import os
from Padrao import determine_governor, apply_pcie_policy
from set_gpu_power import set_gpu_power_mode


# ---------------------------------------------------------------------------
# Detecção de jogos Steam 64-bit
# ---------------------------------------------------------------------------

def is_steam_game_running():
    """
    Verifica se um jogo de 64 bits da Steam está rodando,
    filtrando jogos de 32 bits.
    Permissões necessárias já garantidas pela regra udev.
    """
    try:
        result = subprocess.run(["ps", "-eo", "pid,cmd"], stdout=subprocess.PIPE, text=True)
        if result.returncode != 0:
            return False

        for line in result.stdout.splitlines():
            line_parts = line.strip().split()
            if len(line_parts) < 2:
                continue

            cmd = " ".join(line_parts[1:])

            if (
                "steamapps/common" in cmd
                or "steamapps/compatdata" in cmd
                or "compatibilitytools.d" in cmd
            ):
                exe_path = cmd.split()[0]
                if not os.path.exists(exe_path):
                    continue

                try:
                    file_result = subprocess.run(
                        ["file", exe_path], stdout=subprocess.PIPE, text=True
                    )
                    if "ELF 64-bit" in file_result.stdout:
                        print(f"Jogo 64-bit detectado: {exe_path}")
                        return True
                except FileNotFoundError:
                    print("Atenção: Comando 'file' não encontrado.")
                    return False

    except Exception as e:
        print(f"Ocorreu um erro ao detectar jogo: {e}")

    return False


def is_any_steam_game_running():
    return is_steam_game_running()


# ---------------------------------------------------------------------------
# Energia / Governor / GPU
# ---------------------------------------------------------------------------

def get_power_state():
    """Lê se está na tomada ou na bateria. Permissão garantida pelo udev."""
    try:
        with open("/sys/class/power_supply/ACAD/online", "r") as f:
            return "on_ac" if f.read().strip() == "1" else "on_battery"
    except Exception as e:
        print(f"Erro ao ler energia: {e}")
        return None


def apply_governor(governor):
    """Escreve o governor em todos os núcleos. Permissão 666 garantida pelo udev."""
    try:
        files = glob.glob("/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor")
        if not files:
            return False, "Nenhum arquivo scaling_governor encontrado."
        for cpu_file in files:
            with open(cpu_file, "w") as f:
                f.write(governor)
        return True, ""
    except Exception as e:
        return False, str(e)


def set_brightness(level):
    """Ajusta o brilho da tela. Dono alterado para dikson pelo udev."""
    try:
        with open("/sys/class/backlight/intel_backlight/brightness", "w") as f:
            f.write(str(level))
    except Exception as e:
        print(f"Erro ao ajustar brilho: {e}")


def set_usb_power_management(mode="auto"):
    path = "/sys/block/sdb/device/power/control"
    if os.path.exists(path):
        try:
            # Usa o sudo tee conforme a permissão que você criou no sudoers
            subprocess.run(
                f'echo "{mode}" | sudo /usr/bin/tee {path}',
                shell=True, check=True, stdout=subprocess.DEVNULL
            )
        except Exception as e:
            print(f"Erro ao ajustar energia do USB: {e}")

"""
Para implementar a função set_usb_power_management:

Crie um novo arquivo:
sudo nano /etc/udev/rules.d/99-usb-power.rules

Com:
ACTION=="add|change", SUBSYSTEM=="usb", ATTR{product}=="Storage Device", RUN+="/bin/chmod 666 /sys/block/sdb/device/power/control"

Adicionei também a linha;
dikson ALL=(ALL) NOPASSWD: /usr/bin/tee /sys/block/sdb/device/power/control

EM:
/etc/sudoers.d/SSD_Speed
"""



def get_gpu_mode_for_governor(governor):
    mapping = {
        "performance": "max",
        "schedutil":   "balanced",
        "powersave":   "eco",
    }
    return mapping.get(governor, "balanced")


# ---------------------------------------------------------------------------
# Fluxo principal
# ---------------------------------------------------------------------------

def set_cpu_governor():
    try:
        print("\n[1/1] Verificando estado...")

        power_state = get_power_state()
        if power_state is None:
            print("❌ Não foi possível determinar a fonte de energia. Abortando.")
            return None

        steam_running = is_any_steam_game_running()
        governor      = determine_governor(power_state, steam_running)
        msg           = apply_pcie_policy(power_state, steam_running)

        print(f"Fonte de energia : {'Tomada' if power_state == 'on_ac' else 'Bateria'}")
        print(f"Jogo rodando     : {'Sim' if steam_running else 'Não'}")
        print(f"Governor escolhido: {governor}")
        print(f"{msg}")

        success, error = apply_governor(governor)
        if success:
            print(f"✅ Governor '{governor}' aplicado com sucesso.")
        else:
            print(f"❌ Erro ao aplicar governor: {error}")

        return governor

    except Exception as e:
        print(f"Erro inesperado em set_cpu_governor: {e}")
        return None


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    governor_aplicado = set_cpu_governor()

    # --- NOVO: Gerenciamento de energia do USB/SD ---
    power_state = get_power_state()
    if power_state == "on_battery":
        # Na bateria, forçamos o descanso do USB/LED
        set_usb_power_management("auto")
        print("🔋 Modo Bateria: USB Power Management definido como 'auto'.")
    else:
        # Na tomada, garantimos performance máxima para a cópia
        set_usb_power_management("on")
        print("🔌 Modo AC: USB Power Management definido como 'on' (Máxima estabilidade).")
    # ------------------------------------------------

    if governor_aplicado is None:
        # Fallback seguro: lê o governor atual do sistema
        try:
            with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor", "r") as f:
                governor_aplicado = f.read().strip()
            print(f"Usando governor atual do sistema como fallback: {governor_aplicado}")
        except Exception as e:
            print(f"❌ Não foi possível ler o governor atual: {e}")
            governor_aplicado = "schedutil"  # último recurso

    gpu_mode = get_gpu_mode_for_governor(governor_aplicado)
    print(f"Aplicando modo de GPU: {gpu_mode}")

    try:
        gpu_mode_aplicado = set_gpu_power_mode(gpu_mode)

        with open("/tmp/gpu_mode_atual.txt", "w") as f:
            f.write(gpu_mode_aplicado)

        print(f"✅ Modo de GPU '{gpu_mode_aplicado}' salvo em /tmp/gpu_mode_atual.txt")

    except Exception as e:
        print(f"❌ Erro ao aplicar perfil de GPU: {e}")




# if __name__ == "__main__":
#     governor_aplicado = set_cpu_governor()
#
#     if governor_aplicado is None:
#         # Fallback seguro: lê o governor atual do sistema
#         try:
#             with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor", "r") as f:
#                 governor_aplicado = f.read().strip()
#             print(f"Usando governor atual do sistema como fallback: {governor_aplicado}")
#         except Exception as e:
#             print(f"❌ Não foi possível ler o governor atual: {e}")
#             governor_aplicado = "schedutil"  # último recurso
#
#     gpu_mode = get_gpu_mode_for_governor(governor_aplicado)
#     print(f"Aplicando modo de GPU: {gpu_mode}")
#
#     try:
#         gpu_mode_aplicado = set_gpu_power_mode(gpu_mode)
#
#         with open("/tmp/gpu_mode_atual.txt", "w") as f:
#             f.write(gpu_mode_aplicado)
#
#         print(f"✅ Modo de GPU '{gpu_mode_aplicado}' salvo em /tmp/gpu_mode_atual.txt")
#
#     except Exception as e:
#         print(f"❌ Erro ao aplicar perfil de GPU: {e}")
