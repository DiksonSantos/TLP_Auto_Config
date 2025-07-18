import subprocess
import os

def gerenciar_slideshow_cinnamon():
    """
    Detecta se jogos estão em execução e ativa/desativa o slideshow de wallpapers no Cinnamon.
    Jogos detectados: 
    - Jogos via Steam/Proton/Proton-GE (processos steamapps/wine/Proton)
    - Jogos nativos (usando OpenGL/Vulkan)
    """

    def processo_existe(palavras_chave):
        try:
            resultado = subprocess.check_output(["ps", "-eo", "cmd"], text=True)
            for linha in resultado.splitlines():
                for chave in palavras_chave:
                    if chave.lower() in linha.lower():
                        return True
            return False
        except Exception as e:
            print(f"Erro ao buscar processos: {e}")
            return False

    # Critérios de detecção de jogos
    chaves_proton = ["steamapps", "proton", "Proton", "Proton-GE", "wine", "dxvk", "gamescope"]
    chaves_nativas = ["libGL.so", "libvulkan.so", "vulkan", "OpenGL", "SDL2", "godot", "love", "unity", "unreal"]

    # Verifica se algum jogo está em execução
    jogo_ativo = processo_existe(chaves_proton + chaves_nativas)

    try:
        status_atual = subprocess.check_output([
            "gsettings", "get", "org.cinnamon.desktop.background.slideshow", "slideshow-enabled"
        ]).decode("utf-8").strip()

        if jogo_ativo and status_atual == "true":
            subprocess.run([
                "gsettings", "set", "org.cinnamon.desktop.background.slideshow", "slideshow-enabled", "false"
            ])
            print("🔕 Jogo detectado. Slideshow desativado.")
        elif not jogo_ativo and status_atual == "false":
            subprocess.run([
                "gsettings", "set", "org.cinnamon.desktop.background.slideshow", "slideshow-enabled", "true"
            ])
            print("🎞️ Nenhum jogo ativo. Slideshow ativado.")
        else:
            print("ℹ️ Nenhuma alteração no slideshow foi necessária.")
    except Exception as e:
        print(f"Erro ao controlar slideshow: {e}")


agir = gerenciar_slideshow_cinnamon()

