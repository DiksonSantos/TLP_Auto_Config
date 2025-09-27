import tkinter as tk
from tkinter import messagebox, PhotoImage, ttk
import subprocess
import os
import re
import glob
import time

# =================== Configurações =====================
SCRIPT_PATH = "/home/dikson/Linux_Helper/TLP_Power_Management/SUDO_CPU_2key.sh"
ICON_PERFIL = "/home/dikson/Features/Icones/Perfil_Energia.png"
ICON_MONITOR = "/home/dikson/Features/Icones/Power_Monitor_config.png"

# Cores para o tema escuro
BG_DARK = "#282c34"  # Cor de fundo principal
FG_LIGHT = "#abb2bf"  # Cor do texto principal
ACCENT_COLOR = "#61afef"  # Cor de destaque
FRAME_BG = "#3e4452"  # Cor de fundo para frames

# =================== Funções do Script =====================
def ler_script():
    with open(SCRIPT_PATH, "r", encoding="utf-8") as file:
        return file.read()

def salvar_script(conteudo):
    with open(SCRIPT_PATH, "w", encoding="utf-8") as file:
        file.write(conteudo)

def ler_estado_wine():
    conteudo = ler_script()
    return "is_proton_game_running" in conteudo

def aplicar_perfil(perfil):
    conteudo = ler_script()
    conteudo = re.sub(
        r'from\s+\w+\s+import\s+determine_governor,\s*apply_pcie_policy',
        f'from {perfil} import determine_governor, apply_pcie_policy',
        conteudo
    )
    salvar_script(conteudo)
    status_var.set(f"Perfil aplicado: {perfil}")
    messagebox.showinfo("✅ Sucesso", f"O perfil '{perfil}' foi aplicado.\n\nNão é preciso reiniciar o serviço systemd para aplicar estas alterações.")

def toggle_wine():
    conteudo = ler_script()
    bloco_ativado = '''
def is_any_steam_game_running():
    try:
        from WinePuro import is_proton_game_running
        return is_steam_game_running() or is_proton_game_running()
    except ImportError:
        return is_steam_game_running()
'''.strip()
    bloco_desativado = '''
def is_any_steam_game_running():
    return is_steam_game_running()
'''.strip()
    conteudo = re.sub(
        r'def is_any_steam_game_running\(\):.*?((?=\n\ndef)|(?=\n\nif __name__)|(?=\Z))',
        bloco_ativado if wine_var.get() else bloco_desativado,
        conteudo,
        flags=re.DOTALL
    )
    salvar_script(conteudo)
    status_var.set("Configuração Wine atualizada.")
    messagebox.showinfo("✅ Sucesso", "Configuração Wine atualizada.\n\nReinicie o serviço systemd para aplicar.")

# Função para capturar uso e temperatura da GPU
def get_gpu_usage():
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, check=True)
        output = result.stdout
        # Procura a temperatura (ex: 50C) e o uso (ex: 10%)
        match = re.search(r'\|\s*N/A\s*(\d+C)\s*P\d\s*.*?(\d+%)\s*Default\s*\|', output)
        if match:
            temp, usage = match.groups()
            return usage, temp
        return "N/A", "N/A"
    except:
        return "Erro", "Erro"

# Função para capturar a temperatura da CPU via lm-sensors
def get_cpu_temp():
    try:
        result = subprocess.run(['sensors'], capture_output=True, text=True, check=True)
        output = result.stdout
        # Procura a temperatura principal (Tctl ou Package id 0)
        match = re.search(r'(Tctl|Package id 0):\s*\+(\d+\.\d)°C', output)
        if match:
            return f"{match.group(2)}°C"
        return "N/A"
    except:
        return "Erro"

# Função para capturar o consumo de energia da GPU
def get_gpu_power_draw():
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=power.draw', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, check=True
        )
        power = result.stdout.strip()
        return f"{float(power):.2f}"
    except:
        return "Erro"

# =================== GUI =====================
app = tk.Tk()
app.title("Gerenciador de Energia e Monitoramento")
app.geometry("600x600")
app.resizable(False, False)
app.configure(bg=BG_DARK)

# Ícone
try:
    icon = PhotoImage(file=ICON_PERFIL)
    app.iconphoto(True, icon)
except:
    pass

# Variáveis
wine_var = tk.BooleanVar()
wine_var.set(ler_estado_wine())
status_var = tk.StringVar()
status_var.set("Perfil atual: Desconhecido")

# Estilo ttk
style = ttk.Style()
style.theme_use("clam")
style.configure(".", background=BG_DARK, foreground=FG_LIGHT, font=("Segoe UI", 10))
style.configure("TLabel", background=BG_DARK, foreground=FG_LIGHT)
style.configure("TButton", background=ACCENT_COLOR, foreground="black", font=("Segoe UI", 10, "bold"), borderwidth=0)
style.map("TButton", background=[("active", "#4d90fe")])
style.configure("TCheckbutton", background=BG_DARK, foreground=FG_LIGHT)
style.configure("TLabelframe", background=FRAME_BG, foreground=FG_LIGHT, font=("Segoe UI", 11, "bold"))
style.configure("TLabelframe.Label", background=FRAME_BG, foreground=FG_LIGHT, font=("Segoe UI", 11, "bold"))
style.configure("Monitor.TFrame", background=FRAME_BG)
style.configure("Monitor.TLabel", background=FRAME_BG, foreground=FG_LIGHT, font=("Segoe UI", 11))
style.configure("Title.Monitor.TLabel", font=("Segoe UI", 12, "bold"), foreground="#1abc9c")
style.configure("Value.Monitor.TLabel", font=("Consolas", 11, "bold"), foreground=ACCENT_COLOR)

# =================== Layout =====================
frame_perfil = ttk.LabelFrame(app, text="Perfis de Energia")
frame_perfil.pack(pady=10, padx=10, fill="x")

buttons_frame = ttk.Frame(frame_perfil)
buttons_frame.pack(pady=5)

ttk.Button(buttons_frame, text="🚀 Turbo", width=12, command=lambda: aplicar_perfil("Turbo")).pack(side="left", padx=5, pady=5)
ttk.Button(buttons_frame, text="⚙️ Padrão", width=12, command=lambda: aplicar_perfil("Padrao")).pack(side="left", padx=5, pady=5)
ttk.Button(buttons_frame, text="🔋 Economia", width=12, command=lambda: aplicar_perfil("Economia")).pack(side="left", padx=5, pady=5)
ttk.Button(buttons_frame, text="🤖 Auto", width=12, command=lambda: aplicar_perfil("Auto")).pack(side="left", padx=5, pady=5)

ttk.Checkbutton(app, text="Habilitar Wine Puro", variable=wine_var, command=toggle_wine).pack(pady=5)
ttk.Label(app, text="Se ativado, jogos via Wine puro serão detectados.").pack()
ttk.Label(app, textvariable=status_var, foreground=ACCENT_COLOR).pack(pady=5)
ttk.Label(app, text="⚙️ Mudança de perfil imediata.").pack()

# Frame monitoramento
frame_monitor = ttk.LabelFrame(app, text="Monitor de Estado Atual")
frame_monitor.pack(pady=10, padx=10, fill="x")

monitor_frame = ttk.Frame(frame_monitor, style="Monitor.TFrame")
monitor_frame.pack(fill="both", expand=False)

cpu_governor_path = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
pcie_policy_path = "/sys/module/pcie_aspm/parameters/policy"
# Ajuste o path da PCIe se for diferente no seu sistema
pcie_speed_path = "/sys/bus/pci/devices/0000:01:00.0/current_link_speed"
cpu_freq_paths = sorted(glob.glob("/sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_cur_freq"))

# --- Monitoramento da CPU ---
governor_title = ttk.Label(monitor_frame, text="CPU Scaling Governor", style="Title.Monitor.TLabel")
governor_title.pack(anchor="center")
governor_label = ttk.Label(monitor_frame, text="--", style="Value.Monitor.TLabel")
governor_label.pack(anchor="center", pady=(0, 10))

freq_title = ttk.Label(monitor_frame, text="Frequência Média da CPU", style="Title.Monitor.TLabel")
freq_title.pack(anchor="center")

# Frame para agrupar Frequência e Temperatura da CPU
cpu_frame = ttk.Frame(monitor_frame, style="Monitor.TFrame")
cpu_frame.pack(anchor="center", pady=(0, 10))

# Label APENAS para a Frequência
avg_freq_label = ttk.Label(cpu_frame, text="-- MHz", style="Value.Monitor.TLabel")
avg_freq_label.pack(side="left", padx=5)

# Label APENAS para a Temperatura da CPU (será colorida)
cpu_temp_label = ttk.Label(cpu_frame, text="-- °C", style="Value.Monitor.TLabel")
cpu_temp_label.pack(side="left", padx=5)

# --- Monitoramento da GPU ---
gpu_title = ttk.Label(monitor_frame, text="Uso da GPU", style="Title.Monitor.TLabel")
gpu_title.pack(anchor="center")

# Frame para agrupar Uso e Temperatura da GPU
gpu_usage_frame = ttk.Frame(monitor_frame, style="Monitor.TFrame")
gpu_usage_frame.pack(anchor="center", pady=(0, 0))

# Label APENAS para o Uso da GPU
gpu_usage_label = ttk.Label(gpu_usage_frame, text="-- %", style="Value.Monitor.TLabel")
gpu_usage_label.pack(side="left", padx=5)

# Label APENAS para a Temperatura da GPU (será colorida)
gpu_temp_label = ttk.Label(gpu_usage_frame, text="-- °C", style="Value.Monitor.TLabel")
gpu_temp_label.pack(side="left", padx=5)

gpu_power_label = ttk.Label(monitor_frame, text="-- W", style="Value.Monitor.TLabel")
gpu_power_label.pack(anchor="center", pady=(0, 10))

# --- Monitoramento PCIe ---
pcie_title = ttk.Label(monitor_frame, text="PCIe Policy (NVMe)", style="Title.Monitor.TLabel")
pcie_title.pack(anchor="center")
pcie_label = ttk.Label(monitor_frame, text="--", style="Value.Monitor.TLabel", justify="center")
pcie_label.pack(anchor="center", pady=(0, 0))

# =================== Funções de atualização =====================
def read_file(path):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except:
        return "Erro"

def update_monitor():
    governor_label.config(text=read_file(cpu_governor_path))

    policy = read_file(pcie_policy_path)
    speed = read_file(pcie_speed_path)
    pcie_label.config(text=f"{policy}\nVelocidade: {speed}")

    # --- Frequência média e Temperatura da CPU ---
    total_freq, count = 0, 0
    for path in cpu_freq_paths:
        try:
            with open(path, "r") as f:
                freq_khz = int(f.read().strip())
                total_freq += freq_khz / 1000
                count += 1
        except:
            pass

    temp = get_cpu_temp()
    # Converte para float para comparação. Remove tudo que não for dígito ou ponto.
    temp_val = float(re.sub(r'[^\d.]', '', temp)) if temp not in ("N/A", "Erro") else 0

    if count > 0:
        avg_freq = total_freq / count

        # 1. Atualiza APENAS a frequência. Garante que fique na cor normal.
        avg_freq_label.config(text=f"{avg_freq:.2f} MHz", foreground=ACCENT_COLOR)

        # 2. Atualiza APENAS a temperatura da CPU (com parênteses para estética).
        cpu_temp_label.config(text=f"({temp})")

        # 3. Lógica de cor APENAS para a temperatura da CPU.
        if temp_val >= 90.1: # Limite de 95°C para CPU
            cpu_temp_label.config(foreground="red")
        else:
            cpu_temp_label.config(foreground=ACCENT_COLOR)
    else:
        avg_freq_label.config(text="Erro")
        cpu_temp_label.config(text="(-- °C)", foreground=ACCENT_COLOR)


    # --- Uso, Temperatura e Consumo da GPU ---
    gpu_usage_percent, gpu_temp_with_c = get_gpu_usage()
    gpu_power = get_gpu_power_draw()

    # Extrai o valor numérico da temperatura da GPU para comparação.
    gpu_temp_val = float(re.sub(r'[^\d.]', '', gpu_temp_with_c)) if gpu_temp_with_c not in ("N/A", "Erro") else 0

    # 1. Atualiza APENAS o uso da GPU. Garante que fique na cor normal.
    gpu_usage_label.config(text=gpu_usage_percent, foreground=ACCENT_COLOR)

    # 2. Atualiza APENAS a temperatura da GPU (com parênteses para estética).
    gpu_temp_label.config(text=f"({gpu_temp_with_c})")

    # 3. Lógica de cor APENAS para a temperatura da GPU.
    # Usando 85°C conforme sua solicitação. Se for 85°C, mude para 85.0.
    if gpu_temp_val >= 85.1:
        gpu_temp_label.config(foreground="red")
    else:
        gpu_temp_label.config(foreground=ACCENT_COLOR)

    gpu_power_label.config(text=f"Consumo: {gpu_power} Watts")

    app.after(1000, update_monitor)


# Inicia monitoramento
update_monitor()
app.mainloop()
