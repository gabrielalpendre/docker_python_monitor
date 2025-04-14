import os
import sys
import json
import pytz
import time
from datetime import datetime
from functions.services import get_server_info, get_services, get_docker_stats, test_tcp_connection
from functions.admin import get_excluded_services, get_excluded_services, save_execution_time
from functions.alerts import load_alerts_state, save_alerts_state, check_send_alert

INCIDENTS_DIR = os.getenv('INCIDENTS_DIR', 'files/incidentes')
REPORTS_DIR = os.getenv('REPORTS_DIR', 'files/reports')
os.makedirs(INCIDENTS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

def generate_report():
    start_time = time.time()
    server_hostname, server_ip = get_server_info()
    services = get_services()
    excluded_services = get_excluded_services()
    all_services = [s[0] for s in services if s[3]]
    stats = get_docker_stats(all_services)
    formatted_stats = []
    incidents_services = []

    alerts_state = load_alerts_state("services")

    previous_state = alerts_state.get("previous_state", {})
    last_state = alerts_state.get("last_state", {})

    for service_name, current_state, port, _ in services:
        cpu_usage, memory_usage = stats.get(service_name, ("N/A", "N/A"))
        ip_and_port = f"{test_tcp_connection(server_ip, int(port))} http://{server_ip}:{port}" if port != "N/A" else "N/A"
        
        formatted_stats.append({
            "Service": service_name,
            "Replicas": current_state,
            "CPU Usage": cpu_usage,
            "Memory Usage": memory_usage,
            "IP:Port": ip_and_port
        })
        if service_name not in excluded_services:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            reason = f"{current_state} | {cpu_usage} | {memory_usage} | {ip_and_port}"
            incident_conditions = [
                ("🔴" in current_state, "Servico está indisponível"),
                ("🔴" in cpu_usage, "Problema de CPU"),
                ("🔴" in memory_usage, "Problema de Memória")
                #("🔴" in ip_and_port, "Problema de Conexao")
            ]
            
            for condition, msg in incident_conditions:
                if condition:
                    incidents_services.append({
                        "service": service_name,
                        "timestamp": timestamp,
                        "reason": reason
                    })
            check_send_alert(service_name, current_state, previous_state, server_hostname)
            last_state[service_name] = current_state

    alerts_state["previous_state"] = last_state
    alerts_state["last_state"] = last_state
    save_alerts_state("services",alerts_state)
    
    save_report_to_file(formatted_stats)
    
    if incidents_services:
        save_incidents_to_file(incidents_services)
        
    execution_time = time.time() - start_time
    save_execution_time(execution_time)
    
def save_report_to_file(stats):
    filename = os.path.join(REPORTS_DIR, f"{datetime.now().strftime('%Y-%m-%d')}_report.json")
    filename_latest = os.path.join(REPORTS_DIR, f"{datetime.now().strftime('%Y-%m-%d')}_report_latest.json")
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as file:
                data = json.load(file)
                if not isinstance(data, list):
                    data = []
        else:
            data = []

        if stats:
            timestamp = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%Y-%m-%d %H:%M:%S")
            new_report = {"timestamp": timestamp, "data": stats}
            data.append(new_report)

            temp_filename = os.path.join(REPORTS_DIR, f"tmp.{datetime.now().strftime('%Y-%m-%d')}_report.json")
            with open(temp_filename, 'w') as temp_file:
                json.dump(data, temp_file, indent=4)
            os.replace(temp_filename, filename)

            temp_filename_latest = os.path.join(REPORTS_DIR, f"tmp.{datetime.now().strftime('%Y-%m-%d')}_report_latest.json")
            with open(temp_filename_latest, 'w') as temp_file_latest:
                json.dump([new_report], temp_file_latest, indent=4)
            os.replace(temp_filename_latest, filename_latest)
    except Exception as e:
        print(f"Erro ao salvar o relatório: {e}", file=sys.stderr)

def save_incidents_to_file(history):
    try:
        filename = os.path.join(INCIDENTS_DIR, f"{datetime.now().strftime('%Y-%m-%d')}_incidentes.json")
        temp_filename = os.path.join(INCIDENTS_DIR, f"tmp.{datetime.now().strftime('%Y-%m-%d')}_incidentes.json")
        if os.path.exists(filename):
            with open(filename, 'r') as file:
                existing_data = json.load(file)
        else:
            existing_data = []
        existing_data.extend(history)
        with open(temp_filename, 'w') as temp_file:
            json.dump(existing_data, temp_file, indent=4)
        os.replace(temp_filename, filename)
    except Exception as e:
        print(f"Erro ao salvar os incidentes: {e}", file=sys.stderr)

def load_incidents(filter_service=None):
    """Carrega e ordena os incidentes do dia, opcionalmente filtrando por servico."""
    filename = os.path.join(INCIDENTS_DIR, f"{datetime.now().strftime('%Y-%m-%d')}_incidentes.json")
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            data = json.load(file)
    else:
        data = []
    data = sorted(data, key=lambda x: x['timestamp'], reverse=True)
    if filter_service:
        data = [entry for entry in data if entry['service'] == filter_service]
    data = data[:1000]
    services = list(set(entry['service'] for entry in data))
    return data, services