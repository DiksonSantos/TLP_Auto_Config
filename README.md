⚙️ Documentação — Gerenciador de Energia TLP Power Management
📜 Descrição
Este script permite alternar entre perfis de energia no Linux, controlando o CPU governor e a política PCIe ASPM, com foco em notebooks gamers que utilizam o TLP como gerenciador de energia.
💻 Hardware de Teste
    • Modelo: Acer Nitro AN517-54
    • Sistema: Debian 12 (Bookworm)
    • Kernel: 6.1.0-37-amd64
    • CPU: Intel 11ª geração
    • GPU: NVIDIA RTX (laptop)
    • TLP: Ativado

🔥 Perfis Disponíveis
🔥 Perfil	🧠 CPU Governor	🔌 PCIe Policy	🚀 Objetivo
Turbo	performance	performance	Máximo desempenho, sem restrições.
Padrão	schedutil	default	Equilíbrio entre performance e economia.
Econômico	powersave	powersupersave	Economia máxima de energia e menor aquecimento.


📊 Resultados de Benchmark (em FPS)
Jogo/Teste: (Especificar qual foi usado)
Perfil	FPS Mínimo	FPS Máximo	FPS Médio
Turbo	76,0	126,0	94,2
Padrão	66,0	128,0	90,5
Econômico	35,1	72,4	57,1


🧠 Análise dos Resultados
    • O perfil Econômico reduz drasticamente o desempenho, sendo recomendado apenas para atividades leves como navegação, vídeos ou trabalho de escritório.
    • O perfil Padrão mantém 96% da performance do modo Turbo, com uma gestão térmica e de energia muito mais eficiente, sendo o melhor custo-benefício para uso no dia a dia, inclusive jogos.
    • O perfil Turbo entrega o melhor FPS mínimo e estabilidade em cenários de alta demanda, à custa de maior consumo energético e aquecimento.
🚩 Recomendações
    • Para uso na tomada:
➕ Perfil Turbo se quiser garantir máximo desempenho em jogos ou renderizações.
➕ Perfil Padrão para uso geral, incluindo games, com temperatura mais controlada.
    • Para uso na bateria:
➕ Perfil Econômico para tarefas leves.
➕ Perfil Padrão se quiser jogar ou trabalhar mantendo equilíbrio.
⚠️ Riscos do Uso Contínuo no Modo Econômico (powersupersave)
    • ✅ Não oferece riscos permanentes de hardware.
    • ⚠️ Pode gerar:
        ◦ Quedas de desempenho significativas.
        ◦ Aumento de latências no barramento PCIe (afeta SSDs NVMe e GPUs).
        ◦ Travamentos ou micro lags em atividades que exigem muito da CPU ou GPU.
✔️ É seguro, mas projetado para economia máxima, não para performance.

📜 Observação Importante
    • Esta documentação reflete os testes realizados no modelo específico Acer Nitro AN517-54.
    • Resultados podem variar em outros hardwares devido às diferenças em gerenciamento térmico, arquitetura e eficiência energética.
🛠️ Desenvolvido por:
[Gow Dikson Santos.]
💻 Engenheiro de Software • Usuário avançado Linux • Entusiasta em otimizações.
✅ Licença
Este projeto está licenciado sob a licença MIT, podendo ser livremente usado, modificado e distribuído.
