import subprocess
import re

def get_nvme_temps():
    nvme_temps = {}
    try:
        result = subprocess.run(['sensors'], capture_output=True, text=True, check=True)
        output = result.stdout

        # Divide a saída em blocos (cada dispositivo começa com uma linha que não tem indentação)
        blocks = re.split(r'\n(?=[a-zA-Z0-9_-]+-pci-)', output)

        nvme_count = 0
        for block in blocks:
            # Só processa blocos que são de NVMe
            if '-pci-' not in block or 'nvme' not in block.lower():
                continue

            nvme_count += 1
            simple_name = f"NVMe {nvme_count}"

            temp = None
            crit = None

            # 1. Tenta pegar a linha "Composite:" (ainda existe em alguns sistemas)
            composite_match = re.search(r'Composite:\s*\+(\d+\.\d)°C.*?\(crit\s*=\s*\+(\d+\.\d)°C', block)
            if composite_match:
                temp = float(composite_match.group(1))
                crit = float(composite_match.group(2))
            else:
                # 2. Tenta pegar qualquer linha tempX: ou Sensor X: com crit
                lines = block.split('\n')
                for line in lines:
                    # Padrões comuns
                    m = re.search(r'(?:temp\d|Sensor \d|Composite).*?\+(\d+\.\d)°C.*?\(crit\s*=\s*\+(\d+\.\d)°C', line)
                    if m:
                        temp = float(m.group(1))
                        crit = float(m.group(2))
                        break
                    # Caso o crit não esteja na mesma linha (raro)
                    m2 = re.search(r'(?:temp\d|Sensor \d|Composite).*?\+(\d+\.\d)°C', line)
                    if m2 and temp is None:
                        temp = float(m2.group(1))

            # Se achou pelo menos a temperatura
            if temp is not None:
                temp_str = f"+{temp:.1f}°C"
                nvme_temps[simple_name] = {
                    'temp': temp,
                    'temp_str': temp_str,
                    'crit': crit if crit is not None else 85.0  # fallback razoável
                }

        return nvme_temps

    except Exception as e:
        print(f"Erro ao ler temperaturas NVMe: {e}")  # opcional: debug
        return {}


if __name__ == "__main__":
    print(get_nvme_temps())
