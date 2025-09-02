import subprocess
import os
import time
from datetime import datetime  # <-- IMPORTANTE

# Variável pública (global) para armazenar o nome do processo detectado
processo_encontrado = None


def gerenciar_slideshow_cinnamon():
    """
    Detecta se jogos estão em execução e ativa/desativa o slideshow de wallpapers no Cinnamon.
    Jogos detectados:
    - Jogos via Steam/Proton/Proton-GE (processos steamapps/wine/Proton)
    - Jogos nativos (usando OpenGL/Vulkan)
    """

    def processo_existe(palavras_chave):
        global processo_encontrado
        try:
            resultado = subprocess.check_output(["ps", "-eo", "cmd"], text=True)
            for linha in resultado.splitlines():
                for chave in palavras_chave:
                    if chave.lower() in linha.lower():
                        processo_encontrado = linha.strip()
                        return True
            return False
        except Exception as e:
            print(f"Erro ao buscar processos: {e}")
            return False

    # Critérios de detecção de jogos
    chaves_proton = ["steamapps", "proton", "Proton", "Proton-GE", "wine", "dxvk", "gamescope"]
    chaves_nativas = ["libGL.so", "libvulkan.so", "vulkan", "OpenGL", "SDL2", "godot", "love", "unity", "unreal", "metro", "Yuzu", "mpv", "mednafen"]



    # Verifica se algum jogo está em execução
    jogo_ativo = processo_existe(chaves_proton + chaves_nativas)



    try:
        status_atual = subprocess.check_output([
            "gsettings", "get", "org.cinnamon.desktop.background.slideshow", "slideshow-enabled"
        ]).decode("utf-8").strip()

        agora = datetime.now().strftime("[%H:%M:%S]")  # <- Hora formatada

        if jogo_ativo and status_atual == "true":
            subprocess.run([
                "gsettings", "set", "org.cinnamon.desktop.background.slideshow", "slideshow-enabled", "false"
            ])

            nome = processo_encontrado[processo_encontrado.rfind('/')+1:]
            print(nome)
            print(f"🔕 API detectada. Slideshow desativado: {agora}.")
            #pass
        elif not jogo_ativo and status_atual == "false":
            subprocess.run([
                "gsettings", "set", "org.cinnamon.desktop.background.slideshow", "slideshow-enabled", "true"
            ])
            print(f"🎞️ Nada ativo. Slideshow ativado: {agora}")
            #pass
        else:
            print("ℹ️ Nenhuma alteração no slideshow foi necessária.")
            #pass
    except Exception as e:
        print(f"Erro ao controlar slideshow: {e}")


# while True:
# 	time.sleep(5)
# 	gerenciar_slideshow_cinnamon()

#print(processo_encontrado)

