import tkinter as tk
from tkinter import messagebox, PhotoImage, ttk
import subprocess
import os
import re
import glob

# =================== Configurações =====================
SCRIPT_PATH = "/home/dikson/Linux_Helper/TLP_Power_Management/SUDO_CPU_2key.sh"
ICON_PERFIL = "/home/dikson/Features/Icones/Perfil_Energia.png"
ICON_MONITOR = "/home/dikson/Features/Icones/Power_Monitor_config.png"

# Cores para o tema escuro
BG_DARK = "#282c34"  # Cor de fundo principal
FG_LIGHT = "#abb2bf"  # Cor do texto principal
ACCENT_COLOR = "#61afef" # Cor de destaque (para botões, por exemplo)
FRAME_BG = "#3e4452" # Cor de fundo para frames

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

# =================== GUI =====================
app = tk.Tk()
app.title("Gerenciador de Energia e Monitoramento")
app.geometry("600x520")
app.resizable(False, False)

# Configurações de tema para a janela principal
app.configure(bg=BG_DARK) # Define o fundo da janela principal

# Ícone
try:
    icon = PhotoImage(file=ICON_PERFIL)
    app.iconphoto(True, icon)
except Exception as e:
    print(f"Erro ao carregar ícone: {e}")
    pass

# Variáveis
wine_var = tk.BooleanVar()
wine_var.set(ler_estado_wine())
status_var = tk.StringVar()
status_var.set("Perfil atual: Desconhecido")

# Estilo para os widgets ttk
style = ttk.Style()
style.theme_use("clam")

# Configurações de estilo para o tema escuro
style.configure(".", background=BG_DARK, foreground=FG_LIGHT, font=("Segoe UI", 10))
style.configure("TLabel", background=BG_DARK, foreground=FG_LIGHT)
style.configure("TButton", background=ACCENT_COLOR, foreground="black", font=("Segoe UI", 10, "bold"), borderwidth=0)
style.map("TButton", background=[("active", "#4d90fe")]) # Cor ao passar o mouse
style.configure("TCheckbutton", background=BG_DARK, foreground=FG_LIGHT)
style.configure("TLabelframe", background=FRAME_BG, foreground=FG_LIGHT)
style.configure("TLabelframe.Label", background=FRAME_BG, foreground=FG_LIGHT, font=("Segoe UI", 11, "bold"))

# Frame perfis
frame_perfil = ttk.LabelFrame(app, text="Perfis de Energia")
frame_perfil.pack(pady=10, padx=10, fill="x")

# --- NOVO CÓDIGO PARA CENTRALIZAR OS BOTÕES ---
# Crie um Frame interno para agrupar e centralizar os botões
buttons_frame = ttk.Frame(frame_perfil)
buttons_frame.pack(pady=5) # Centraliza o frame de botões dentro do frame_perfil

# Adicione os botões dentro do novo frame, usando side="left" para mantê-los lado a lado
ttk.Button(buttons_frame, text="🚀 Turbo", width=12, command=lambda: aplicar_perfil("Turbo")).pack(side="left", padx=5, pady=5)
ttk.Button(buttons_frame, text="⚙️ Padrão", width=12, command=lambda: aplicar_perfil("Padrao")).pack(side="left", padx=5, pady=5)
ttk.Button(buttons_frame, text="🔋 Economia", width=12, command=lambda: aplicar_perfil("Economia")).pack(side="left", padx=5, pady=5)
ttk.Button(buttons_frame, text="🤖 Auto", width=12, command=lambda: aplicar_perfil("Auto")).pack(side="left", padx=5, pady=5)
# --- FIM DO NOVO CÓDIGO ---

# Wine puro
ttk.Checkbutton(app, text="Habilitar Wine Puro", variable=wine_var, command=toggle_wine).pack(pady=5)
ttk.Label(app, text="Se ativado, jogos via Wine puro serão detectados\nquando em TURBO ou PADRÃO.").pack()
ttk.Label(app, textvariable=status_var, foreground=ACCENT_COLOR).pack(pady=5) # Use a cor de destaque para o status
ttk.Label(app, text="⚙️ Mudança de perfil imediata.").pack()

# Frame monitoramento embutido (substitui botões)
frame_monitor = ttk.LabelFrame(app, text="Monitor de Estado Atual")
frame_monitor.pack(pady=10, padx=10, fill="x")

# Inserindo monitor do algoritmo 2
style.configure("Monitor.TFrame", background=FRAME_BG)
style.configure("Monitor.TLabel", background=FRAME_BG, foreground=FG_LIGHT, font=("Segoe UI", 11))
style.configure("Title.Monitor.TLabel", font=("Segoe UI", 12, "bold"), foreground="#1abc9c")
style.configure("Value.Monitor.TLabel", font=("Consolas", 11, "bold"), foreground=ACCENT_COLOR)

monitor_frame = ttk.Frame(frame_monitor, style="Monitor.TFrame")
monitor_frame.pack(fill="both", expand=True)

cpu_governor_path = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
pcie_policy_path = "/sys/module/pcie_aspm/parameters/policy"
cpu_freq_paths = sorted(glob.glob("/sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_cur_freq"))

governor_title = ttk.Label(monitor_frame, text="CPU Scaling Governor", style="Title.Monitor.TLabel")
governor_title.pack(anchor="center")
governor_label = ttk.Label(monitor_frame, text="--", style="Value.Monitor.TLabel")
governor_label.pack(anchor="center", pady=(0, 10))

pcie_title = ttk.Label(monitor_frame, text="PCIe Policy (NVMe)", style="Title.Monitor.TLabel")
pcie_title.pack(anchor="center")
pcie_label = ttk.Label(monitor_frame, text="--", style="Value.Monitor.TLabel")
pcie_label.pack(anchor="center", pady=(0, 10))

freq_title = ttk.Label(monitor_frame, text="Média Frequência CPU", style="Title.Monitor.TLabel")
freq_title.pack(anchor="center")
avg_freq_label = ttk.Label(monitor_frame, text="-- MHz", style="Value.Monitor.TLabel")
avg_freq_label.pack(anchor="center")

def read_file(path):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception as e:
        return "Erro ao ler"

def update_monitor():
    governor_label.config(text=read_file(cpu_governor_path))
    pcie_label.config(text=read_file(pcie_policy_path))
    total_freq = 0
    count = 0
    for path in cpu_freq_paths:
        try:
            with open(path, "r") as f:
                freq_khz = int(f.read().strip())
                freq_mhz = freq_khz / 1000
                total_freq += freq_mhz
                count += 1
        except Exception as e:
            pass
    if count > 0:
        avg_freq = total_freq / count
        avg_freq_label.config(text=f"{avg_freq:.2f} MHz")
    else:
        avg_freq_label.config(text="Erro ao calcular")
    app.after(3000, update_monitor)

update_monitor()

app.mainloop()
