import tkinter as tk
from tkinter import messagebox
import subprocess
from tkinter import PhotoImage


def execute_command(command):
    try:
        result = subprocess.check_output(command, shell=True, text=True)
        output_box.delete(1.0, tk.END)
        output_box.insert(tk.END, result)
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Erro", f"Erro ao executar o comando:\n{e}")
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro inesperado:\n{e}")

def get_scaling_governor():
    command = "cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor"
    execute_command(command)

def get_pcie_policy():
    command = "cat /sys/module/pcie_aspm/parameters/policy"
    execute_command(command)

# Configuração da interface gráfica
app = tk.Tk()
app.title("Monitor de Configurações")
app.geometry("500x300")

#ICONE DO APP
icon = PhotoImage(file="/home/dikson/Features/Icones/Power_Monitor_config.png")
app.iconphoto(True, icon)


# Botões
btn_scaling_governor = tk.Button(app, text="CPU Scaling Governor", command=get_scaling_governor, width=25)
btn_scaling_governor.pack(pady=10)

btn_pcie_policy = tk.Button(app, text="PCIe Policy (NVME)", command=get_pcie_policy, width=25)
btn_pcie_policy.pack(pady=10)

# Caixa de texto para saída
output_box = tk.Text(app, wrap=tk.WORD, height=10, width=60)
output_box.pack(pady=10)

# Iniciar o aplicativo
app.mainloop()
