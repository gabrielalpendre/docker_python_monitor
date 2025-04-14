import os
import json

ADMIN_DIR = os.getenv('ADMIN_DIR', 'files/admin')
os.makedirs(ADMIN_DIR, exist_ok=True)

EXCLUDED_SERVICES_FILE = os.path.join(ADMIN_DIR, "excluded_services.json")
REPORTS_SERVICES_FILE = os.path.join(ADMIN_DIR, "reports_execution_time.json")

def save_execution_time(execution_time):
    """Salva o tempo de execucao no arquivo JSON, mantendo apenas as últimas 30 entradas, em segundos, e inclui a chave interval_time."""
    execution_data = {
        "execution_time": execution_time
    }
    
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

def get_medium_execution_time():
    """Calcula o tempo medio de execucao com base nos dados do arquivo JSON, em segundos e retorna um farol com emoji."""
    if os.path.exists(REPORTS_SERVICES_FILE):
        with open(REPORTS_SERVICES_FILE, 'r') as json_file:
            data = json.load(json_file)
        execution_times = data.get('execution_times', [])
        if execution_times:
            total_time = sum([entry['execution_time'] for entry in execution_times])
            average_time = total_time / len(execution_times)
            average_time = round(average_time, 2)
            if average_time < 2:
                return f"{average_time} s 🟢"
            elif average_time <= 10:
                return f"{average_time} s 🟡"
            else:
                return f"{average_time} s 🔴"
        else:
            return "0 s 🔴"
    else:
        return "0 s 🔴"

def save_excluded_services(excluded_services):
    with open(EXCLUDED_SERVICES_FILE, 'w') as file:
        json.dump(excluded_services, file, indent=4)

def get_excluded_services():
    if os.path.exists(EXCLUDED_SERVICES_FILE):
        with open(EXCLUDED_SERVICES_FILE, 'r') as file:
            return json.load(file)
    return []
