import subprocess

def set_gpu_power_mode(password, mode):
    """
    Ajusta a GPU para um perfil de energia aproximado:
    - 'max'  -> força clocks altos (equivalente a P0/P1)
    - 'balanced' -> clocks médios (P2/P3)
    - 'eco'  -> clocks baixos / limite de potência (P8/P12)
    """
    cmds = []
    if mode == "max":
        cmds = [
            "nvidia-smi -pm 1",
            "nvidia-smi -pl 75",          # Define limite alto (ajuste conforme tua GPU)
            "nvidia-smi -lgc 1200,2100"   # Faixa alta de clock (força P0/P2)
        ]
    elif mode == "balanced":
        cmds = [
            "nvidia-smi -pm 1",
            "nvidia-smi -pl 75",
            "nvidia-smi -rgc"             # Remove limites de clock definidos antes
        ]
    elif mode == "eco":
        cmds = [
            "nvidia-smi -pm 1",           # Garante power management ativado
            "nvidia-smi -pl 30",          # Limite de potência mais baixo (ajuste conforme sua GPU)
            "nvidia-smi -lgc 100,300"     # Faixa de clock mais baixa, próxima do P12-P15
        ]

    for cmd in cmds:
        subprocess.run(
            ["sudo", "-S", "bash", "-c", cmd],
            input=f"{password}\n",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

# Descubra qual a voltagem máxima suportada pela sua gpu com;
# $ nvidia-smi -q | grep -i "Power Limit"

# Maximo Clock da placa;
# $ nvidia-smi -q -d CLOCK
# 
# Minha placa 'GeForce RTX 3050 Mobile' chega á 2100
"""
Max Clocks
    Graphics : 2100 MHz   ← clock máximo do núcleo (core)
    SM       : 2100 MHz   ← mesmo valor, pois SM = core shader clock
    Memory   : 6001 MHz   ← clock máximo da VRAM
    Video    : 1950 MHz   ← clock máximo do motor de vídeo (NVENC/NVDEC)

"""
