# =================== nvme_temp.py → VERSÃO ATUALIZADA (DEZEMBRO 2025) ===================
import subprocess
import re

def get_nvme_temps():
    nvme_temps = {}
    try:
        result = subprocess.run(['sensors'], capture_output=True, text=True, check=True)
        output = result.stdout

        blocks = re.split(r'\n(?=[a-zA-Z0-9_-]+-pci-)', output)

        nvme_count = 0
        for block in blocks:
            if '-pci-' not in block or 'nvme' not in block.lower():
                continue

            nvme_count += 1
            simple_name = f"NVMe {nvme_count}"

            temp = None
            crit = None

            # 1. Composite (padrão mais comum)
            composite_match = re.search(r'Composite:\s*\+(\d+\.\d)°C.*?\(crit\s*=\s*\+(\d+\.\d)°C', block)
            if composite_match:
                temp = float(composite_match.group(1))
                crit = float(composite_match.group(2))
            else:
                # 2. Outros sensores (temp1, Sensor 1, etc.)
                lines = block.split('\n')
                for line in lines:
                    m = re.search(r'(?:temp\d|Sensor \d|Composite).*?\+(\d+\.\d)°C.*?\(crit\s*=\s*\+(\d+\.\d)°C', line)
                    if m:
                        temp = float(m.group(1))
                        crit = float(m.group(2))
                        break
                    m2 = re.search(r'(?:temp\d|Sensor \d|Composite).*?\+(\d+\.\d)°C', line)
                    if m2 and temp is None:
                        temp = float(m2.group(1))

            if temp is not None:
                temp_str = f"+{temp:.1f}°C"

                # ========== AQUI ESTÁ A MÁGICA: LIMITE PERSONALIZADO ==========
                # NVMe 1 = Kingston KC3000 → queremos vermelho a partir de 70°C
                # NVMe 2 = GF GEM4 (ou outro) → pode manter o padrão mais alto
                if nvme_count == 1:  # Primeiro NVMe detectado = seu Kingston KC3000
                    alerta_temp = 70.0       # ← LIMITE DESEJADO
                    crit_for_alert = 85.0    # Valor apenas para exibição (não afeta a cor)
                else:
                    alerta_temp = crit - 7 if crit else 78.0
                    crit_for_alert = crit if crit else 85.0
                # ==============================================================

                nvme_temps[simple_name] = {
                    'temp': temp,
                    'temp_str': temp_str,
                    'crit': crit_for_alert,
                    'alerta_temp': alerta_temp   # ← novo campo usado no script principal
                }

        return nvme_temps

    except Exception as e:
        print(f"Erro ao ler temperaturas NVMe: {e}")
        return {}
        
    
if __name__ == "__main__":
    temps = get_nvme_temps()

    if not temps:
        print("Nenhum NVMe detectado.")
    else:
        for name, data in temps.items():
            print(f"{name}:")
            print(f"  Temperatura atual : {data['temp_str']}")
            print(f"  Alerta a partir de: {data['alerta_temp']}°C")
            print(f"  Crítico exibido   : {data['crit']}°C")

