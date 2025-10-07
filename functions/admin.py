import os
import json

ADMIN_DIR = os.getenv('ADMIN_DIR', 'files/admin')
os.makedirs(ADMIN_DIR, exist_ok=True)

EXCLUDED_SERVICES_FILE = os.path.join(ADMIN_DIR, "excluded_services.json")

def save_execution_time(type, execution_time):
    """Salva o tempo de execucao no arquivo JSON, mantendo apenas as últimas 30 entradas, em segundos, e inclui a chave interval_time."""
    execution_data = {
        "execution_time": execution_time
    }
    REPORTS_SERVICES_FILE = os.path.join(ADMIN_DIR, f"{type}_execution_time.json")
    
    if os.path.exists(REPORTS_SERVICES_FILE):
        with open(REPORTS_SERVICES_FILE, 'r') as json_file:
            data = json.load(json_file)
            if not isinstance(data, dict):
                data = {"execution_times": []}
    else:
        data = {"execution_times": []}
    
    data["execution_times"].append(execution_data)

    if len(data["execution_times"]) > 30:
        data["execution_times"] = data["execution_times"][-30:]
    
    with open(REPORTS_SERVICES_FILE, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def get_medium_execution_time(type):
    """Calcula o tempo medio de execucao com base nos dados do arquivo JSON, em segundos e retorna um farol com emoji."""
    REPORTS_SERVICES_FILE = os.path.join(ADMIN_DIR, f"{type}_execution_time.json")
    if os.path.exists(REPORTS_SERVICES_FILE):
        with open(REPORTS_SERVICES_FILE, 'r') as json_file:
            data = json.load(json_file)
        execution_times = data.get('execution_times', [])
        if execution_times:  # Verifica se há entradas
            total_time = sum([entry['execution_time'] for entry in execution_times])
            average_time = total_time / len(execution_times)
            average_time = round(average_time, 2)
            if average_time < 5:
                return f"{average_time} s 🟢"  # Verde
            elif average_time <= 15:
                return f"{average_time} s 🟡"  # Amarelo
            else:
                return f"{average_time} s 🔴"  # Vermelho
        else:
            return "0 s 🔴"  # Caso nao haja tempos de execucao
    else:
        return "0 s 🔴"  # Caso o arquivo nao exista

def save_excluded_services(excluded_services):
    with open(EXCLUDED_SERVICES_FILE, 'w') as file:
        json.dump(excluded_services, file, indent=4)

def get_excluded_services():
    if os.path.exists(EXCLUDED_SERVICES_FILE):
        with open(EXCLUDED_SERVICES_FILE, 'r') as file:
            return json.load(file)
    return []
