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

# =================== Variáveis Globais para Potência da CPU (NOVAS) =====================
# Variáveis para cálculo de potência de forma não-bloqueante (eliminando time.sleep)
LAST_ENERGY_READING = 0
LAST_READING_TIME = 0.0

# =================== Funções do Script =====================
def ler_script():
    # Verifica se o arquivo existe antes de tentar ler
    if not os.path.exists(SCRIPT_PATH):
         # Cria o arquivo com um conteúdo básico se não existir (para evitar erro)
        conteudo_base = """
def is_steam_game_running():
    return False

def determine_governor(is_game_running, is_on_ac):
    return 'powersave'

def apply_pcie_policy(is_game_running, is_on_ac):
    pass

def read_file(path):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except:
        return ""

from Padrao import determine_governor, apply_pcie_policy

def is_any_steam_game_running():
    return is_steam_game_running()

if __name__ == '__main__':
    pass
"""
        with open(SCRIPT_PATH, "w", encoding="utf-8") as file:
             file.write(conteudo_base.strip())
        return conteudo_base

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


# Função para capturar o P-State da GPU -> P0, P3, P5, P8 ...
def get_gpu_pstate():
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=pstate', '--format=csv,noheader'],
            capture_output=True, text=True, check=True
        )
        pstate = result.stdout.strip()

        # Mapeamento do P-State para a descrição
        if pstate in ["P0"]:
            return f"🔥 Máximo desempenho {pstate}"
        elif pstate in ["P1", "P2"]:
            return f"⚡ Desempenho intermediário {pstate}"
        elif pstate in ["P3", "P4", "P5", "P6", "P7"]:
            return f"✨ Desempenho Baixo {pstate}"
        elif pstate in ["P8", "P12"]:
            return f"🌙 Ocioso / Economia {pstate}"
        elif pstate in ["P15", "P20"]:
            # P15 é o estado de menor potência em algumas GPUs (Deep Idle)
            return f"💤 Economia Extrema {pstate}"
        else:
            # Retorna o P-State lido se não estiver mapeado
            return f"P-State: {pstate}"

    except:
        return "N/A (P-State)"


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

# FUNÇÃO REVISADA PARA CAPTURAR AS TEMPERATURAS DOS DOIS NVMe
def get_nvme_temps():
    nvme_temps = {}
    try:
        result = subprocess.run(['sensors'], capture_output=True, text=True, check=True)
        output = result.stdout

        # Expressão regular que captura ID (e100 ou e200), a temperatura Composite e a crítica
        matches = re.findall(r'(nvme-pci-e\d+).*?Composite:\s*\+(\d+\.\d)°C.*?\(crit = \+(\d+\.\d)°C\)', output, re.DOTALL)

        for name, temp_val, crit_val in matches:
            # Simplifica o nome para a GUI
            simple_name = "NVMe 1" if "e100" in name else ("NVMe 2" if "e200" in name else name)
            nvme_temps[simple_name] = {
                'temp': float(temp_val),
                'temp_str': f"+{temp_val}°C",
                'crit': float(crit_val)
            }
        return nvme_temps
    except:
        return {} # Retorna dicionário vazio em caso de erro

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
# **Mantenha APENAS Frequência e Temperatura aqui.**
cpu_frame = ttk.Frame(monitor_frame, style="Monitor.TFrame")
cpu_frame.pack(anchor="center", pady=(0, 5)) # Reduzi o pady para aproximar da potência

# Label APENAS para a Frequência
avg_freq_label = ttk.Label(cpu_frame, text="-- MHz", style="Value.Monitor.TLabel")
avg_freq_label.pack(side="left", padx=5)
avg_freq_label.pack(anchor="center", pady=(5, 0)) # Adicionei título

# Label APENAS para a Temperatura da CPU (será colorida)
cpu_temp_label = ttk.Label(cpu_frame, text="(-- °C)", style="Value.Monitor.TLabel")
cpu_temp_label.pack(side="left", padx=5)


# Label APENAS para a Potência/Voltagem da CPU
# **MOVIMENTO: Agora ele é empacotado diretamente no monitor_frame**
cpu_power_label = ttk.Label(monitor_frame, text="-- W", style="Value.Monitor.TLabel")
cpu_power_label.pack(anchor="center", pady=(0, 10)) # Com pady=(0, 10) para espaçar da GPU

# --- Monitoramento da GPU ---
gpu_title = ttk.Label(monitor_frame, text="Uso da GPU", style="Title.Monitor.TLabel")
gpu_title.pack(anchor="center")

# Label para o P-State Nvidia -> P2, P8 ...
gpu_pstate_label = ttk.Label(monitor_frame, text="-- P-State", style="Value.Monitor.TLabel", foreground="#ffb703") # Use uma cor de destaque
gpu_pstate_label.pack(anchor="center", pady=(0, 5)) # Adicionado após o título da GPU
# --------------------

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

# --- Monitoramento PCIe e NVMe ---
pcie_title = ttk.Label(monitor_frame, text="PCIe Policy (NVMe)", style="Title.Monitor.TLabel")
pcie_title.pack(anchor="center")

# Label APENAS para a política (ASPM)
pcie_policy_label = ttk.Label(monitor_frame, text="--", style="Value.Monitor.TLabel")
pcie_policy_label.pack(anchor="center", pady=(0, 5))

# Frame para agrupar as Temperaturas NVMe
nvme_temp_frame = ttk.Frame(monitor_frame, style="Monitor.TFrame")
nvme_temp_frame.pack(anchor="center", pady=(0, 5))

# --- NVMe 1 ---
nvme1_name_label = ttk.Label(nvme_temp_frame, text="NVMe 1:", style="Value.Monitor.TLabel", foreground=ACCENT_COLOR)
nvme1_name_label.pack(side="left", padx=(10, 0))
nvme1_temp_label = ttk.Label(nvme_temp_frame, text="-- °C", style="Value.Monitor.TLabel")
nvme1_temp_label.pack(side="left", padx=(0, 10))

# --- NVMe 2 ---
nvme2_name_label = ttk.Label(nvme_temp_frame, text="NVMe 2:", style="Value.Monitor.TLabel", foreground=ACCENT_COLOR)
nvme2_name_label.pack(side="left", padx=(10, 0))
nvme2_temp_label = ttk.Label(nvme_temp_frame, text="-- °C", style="Value.Monitor.TLabel")
nvme2_temp_label.pack(side="left", padx=(0, 10))

# Label para a velocidade (mantida separada para clareza)
pcie_speed_label = ttk.Label(monitor_frame, text="Velocidade: --", style="Value.Monitor.TLabel")
pcie_speed_label.pack(anchor="center", pady=(0, 10))


# =================== Funções de atualização =====================
def read_file(path):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except:
        return "Erro"

def get_cpu_power():
    """
    Calcula a potência instantânea da CPU em Watts a partir de energy_uj de forma
    NÃO-BLOQUEANTE (sem time.sleep).
    """
    global LAST_ENERGY_READING, LAST_READING_TIME

    # 1. Obter o valor atual e o tempo.
    try:
        # Tenta ler o valor de energia atual
        current_energy_uj_str = read_file("/sys/class/powercap/intel-rapl:0/energy_uj")
        if current_energy_uj_str == "Erro":
             return "N/A"

        current_energy_uj = int(current_energy_uj_str)
        current_time = time.time()
    except Exception:
        return "N/A (RAPL)"

    # 2. Calcular a potência se houver um valor anterior.
    if LAST_READING_TIME != 0.0:
        delta_energy = current_energy_uj - LAST_ENERGY_READING
        delta_time = current_time - LAST_READING_TIME

        # Evita divisão por zero e garante que o tempo decorrido seja suficiente
        if delta_time > 0.05:
            # Potência (W) = (Energia em Joules) / (Tempo em Segundos)
            # 1 Joule = 1,000,000 microjoules (uj)
            power_watts = (delta_energy / 1_000_000.0) / delta_time
            result = f"Consumo: {power_watts:.2f} Watts"
        else:
            # Caso o update_monitor() tenha sido chamado muito rapidamente
            result = cpu_power_label.cget("text")

    else:
        # Primeira execução, não é possível calcular a potência.
        result = "Aguardando"

    # 3. Armazenar os valores atuais para o próximo cálculo.
    LAST_ENERGY_READING = current_energy_uj
    LAST_READING_TIME = current_time

    return result


def update_monitor():
    governor_label.config(text=read_file(cpu_governor_path))

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
        if temp_val >= 93.1: # Limite de 90°C para alerta da CPU
            cpu_temp_label.config(foreground="red")
        else:
            cpu_temp_label.config(foreground=ACCENT_COLOR)
    else:
        avg_freq_label.config(text="Erro")
        cpu_temp_label.config(text="(-- °C)", foreground=ACCENT_COLOR)


    # --- Potência da CPU (CHAMADA INCLUÍDA) ---
    cpu_power_val = get_cpu_power()
    cpu_power_label.config(text=cpu_power_val)


    # --- Uso, Temperatura e Consumo da GPU ---
    gpu_usage_percent, gpu_temp_with_c = get_gpu_usage()
    gpu_power = get_gpu_power_draw()

    # Capturar e exibir o P-State da GPU
    gpu_pstate_status = get_gpu_pstate()
    gpu_pstate_label.config(text=gpu_pstate_status)

    # Extrai o valor numérico da temperatura da GPU para comparação.
    gpu_temp_val = float(re.sub(r'[^\d.]', '', gpu_temp_with_c)) if gpu_temp_with_c not in ("N/A", "Erro") else 0

    # 1. Atualiza APENAS o uso da GPU. Garante que fique na cor normal.
    gpu_usage_label.config(text=gpu_usage_percent, foreground=ACCENT_COLOR)

    # 2. Atualiza APENAS a temperatura da GPU (com parênteses para estética).
    gpu_temp_label.config(text=f"({gpu_temp_with_c})")

    # 3. Lógica de cor APENAS para a temperatura da GPU.
    if gpu_temp_val >= 84.0:
        gpu_temp_label.config(foreground="red")
    else:
        gpu_temp_label.config(foreground=ACCENT_COLOR)

    gpu_power_label.config(text=f"Consumo: {gpu_power} Watts")

    # --- Monitoramento PCIe e NVMe ---
    policy = read_file(pcie_policy_path)
    speed = read_file(pcie_speed_path)
    nvme_temps_data = get_nvme_temps()

    pcie_policy_label.config(text=policy) # Apenas a política
    pcie_speed_label.config(text=f"Velocidade: {speed}") # Apenas a velocidade

    # Função interna para atualizar a label de cada NVMe
    def update_nvme_temperature(name, temp_label):
        if name in nvme_temps_data:
            data = nvme_temps_data[name]
            temp = data['temp']
            temp_str = data['temp_str']
            crit = data['crit']

            temp_label.config(text=temp_str)

            # Alerta se a temperatura estiver 5°C abaixo do limite crítico do próprio disco.
            if temp >= (crit - 9.8):
                temp_label.config(foreground="red")
            else:
                temp_label.config(foreground=ACCENT_COLOR)
        else:
             temp_label.config(text="N/A", foreground=FG_LIGHT)

    # Atualiza as temperaturas dos dois NVMe, usando as labels de temperatura
    update_nvme_temperature("NVMe 1", nvme1_temp_label)
    update_nvme_temperature("NVMe 2", nvme2_temp_label)

    # Chama a si mesma novamente em 1000ms (1 segundo)
    app.after(1000, update_monitor)


# Inicia monitoramento
update_monitor()
app.mainloop()
