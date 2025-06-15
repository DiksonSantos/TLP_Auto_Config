import tkinter as tk
from tkinter import messagebox
import os
import re

# Caminho para o script principal
SCRIPT_PATH = "/home/dikson/Linux_Helper/TLP_Power_Management/PROJETO/SUDO_CPU_2key.sh"

# Função para ler o conteúdo atual do script
def ler_script():
    with open(SCRIPT_PATH, "r", encoding="utf-8") as file:
        return file.read()

# Função para salvar as modificações no script
def salvar_script(conteudo):
    with open(SCRIPT_PATH, "w", encoding="utf-8") as file:
        file.write(conteudo)

# Função para ler o estado do Wine Puro
def ler_estado_wine():
    conteudo = ler_script()
    return "is_proton_game_running" in conteudo

# Função para alterar o perfil
# def aplicar_perfil(perfil):
#     conteudo = ler_script()
#     # Substituir a linha de importação
#     conteudo = re.sub(
#         r'from (Turbo|Padrão|Economia|Auto) import determine_governor, apply_pcie_policy',
#         f'from {perfil} import determine_governor, apply_pcie_policy',
#         conteudo
#     )
#     salvar_script(conteudo)
#     status_var.set(f"Perfil aplicado: {perfil}")
#     messagebox.showinfo("✅ Sucesso", f"O perfil '{perfil}' foi aplicado.\n\nNão é preciso reiniciar o serviço systemd para aplicar estas alterações.")

# def aplicar_perfil(perfil):
#     conteudo = ler_script()
#     # Substituir a linha de importação
#     conteudo = re.sub(
#         r'from (Turbo|Padrao|Economia|Auto) import determine_governor, apply_pcie_policy',
#         f'from {perfil} import determine_governor, apply_pcie_policy',
#         conteudo
#     )
#     salvar_script(conteudo)
#     status_var.set(f"Perfil aplicado: {perfil}")
#     messagebox.showinfo("✅ Sucesso", f"O perfil '{perfil}' foi aplicado.\n\nNão é preciso reiniciar o serviço systemd para aplicar estas alterações.")

# Função para alterar o perfil
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



# Função para ativar ou desativar Wine Puro
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

    # Substituir o bloco da função is_any_steam_game_running
    conteudo = re.sub(
        r'def is_any_steam_game_running\(\):.*?((?=\n\ndef)|(?=\n\nif __name__)|(?=\Z))',
        bloco_ativado if wine_var.get() else bloco_desativado,
        conteudo,
        flags=re.DOTALL
    )

    salvar_script(conteudo)
    status_var.set("Configuração Wine atualizada.")
    messagebox.showinfo("✅ Sucesso", "Configuração Wine atualizada.\n\nReinicie o serviço systemd para aplicar.")

# ============== GUI =================

janela = tk.Tk()
wine_var = tk.BooleanVar()
wine_var.set(ler_estado_wine())  # Lê o script e define o estado inicial da caixa
janela.title("Gerenciador de Perfis de Energia")
janela.geometry("460x290")
janela.resizable(False, False)

frame = tk.Frame(janela)
frame.pack(pady=15)

# Botões de perfis
tk.Button(frame, text="🚀 Turbo", width=12, command=lambda: aplicar_perfil("Turbo")).grid(row=0, column=0, padx=5, pady=5)
tk.Button(frame, text="⚙️ Padrao", width=12, command=lambda: aplicar_perfil("Padrao")).grid(row=0, column=1, padx=5, pady=5)
tk.Button(frame, text="🔋 Economia", width=12, command=lambda: aplicar_perfil("Economia")).grid(row=1, column=0, padx=5, pady=5)
tk.Button(frame, text="🤖 Auto", width=12, command=lambda: aplicar_perfil("Auto")).grid(row=1, column=1, padx=5, pady=5)

# Check para Wine
tk.Checkbutton(janela, text="Habilitar Wine Puro", variable=wine_var, command=toggle_wine).pack(pady=10)

tk.Label(janela, text="Se ativado, jogos via Wine também serão detectados no perfil Auto.").pack()

# Status
status_var = tk.StringVar()
status_var.set("Perfil atual: Desconhecido")
tk.Label(janela, textvariable=status_var, fg="blue").pack(pady=10)

# Rodapé
tk.Label(janela, text="⚙️ Reinicie o serviço systemd após mudar o perfil.").pack()

janela.mainloop()
