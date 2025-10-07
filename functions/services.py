import subprocess
import socket
import re
import os
import json
from prettytable import PrettyTable
from dotenv import load_dotenv
from functions.log import log_message

load_dotenv(override=True)

REPORTS_DIR = os.getenv('REPORTS_DIR', 'files/reports')
os.makedirs(REPORTS_DIR, exist_ok=True)

def get_server_info(return_db_info=False):
    ip = os.getenv('SERVER_IP', socket.gethostbyname(socket.gethostname()))
    server_hostname = os.getenv('SERVER_HOSTNAME', socket.gethostname())
    db_hostname = os.getenv('DB_HOSTNAME')
    db_ip = os.getenv('DB_HOST1')
    if return_db_info:
        return db_hostname, db_ip
    else:
        return server_hostname, ip

def get_status_emoji(value, value_ok, value_nok):
    if value <= value_ok:
        return "🟢"
    elif value <= value_nok:
        return "🟡"
    else:
        return "🔴"

def get_server_load():
    uptime = "Unknown"
    actual = average = high = 0.0
    try:
        if os.path.exists("/host_proc_loadavg"):
            with open("/host_proc_loadavg", "r") as f:
                loadavg = f.read().strip().split()
                actual = float(loadavg[0].replace(',', '.'))
                average = float(loadavg[1].replace(',', '.'))
                high = float(loadavg[2].replace(',', '.'))
            try:
                with open("/host_proc_uptime", "r") as f:
                    uptime_seconds = float(f.read().split()[0])
                    hours = int(uptime_seconds // 3600)
                    minutes = int((uptime_seconds % 3600) // 60)
                    uptime = f"{hours}:{minutes:02d}"
            except:
                uptime = "Unknown"
            return [
                ("uptime", uptime),
                ("actual", actual, get_status_emoji(actual, 10, 30)),
                ("average", average, get_status_emoji(average, 10, 30)),
                ("high", high, get_status_emoji(high, 10, 30))
            ]
    except Exception as e:
        return [("error", f"Erro ao verificar o load: {e}")]

    # 🔸 Se falhar, usa fallback com 'w'
    try:
        result = subprocess.run(['w'], capture_output=True, text=True, check=True)
        line = result.stdout.splitlines()[0]
        uptime_match = re.search(r'up\s+(.*?),\s+\d+\s+user', line)
        if uptime_match:
            uptime = uptime_match.group(1).strip()
            # Ajustar uptime para hh:mm
            if "min" in uptime:
                minutes = re.findall(r'\d+', uptime)
                uptime = f"0:{minutes[0].zfill(2)}"
            elif ":" not in uptime:
                uptime = f"{uptime}:00"
        load_match = re.search(r'load average[s]?:\s*([\d.,]+),\s*([\d.,]+),\s*([\d.,]+)', line)
        if load_match:
            actual = float(load_match.group(1).replace(',', '.'))
            average = float(load_match.group(2).replace(',', '.'))
            high = float(load_match.group(3).replace(',', '.'))
            return [
                ("uptime", uptime),
                ("actual", actual, get_status_emoji(actual, 10, 30)),
                ("average", average, get_status_emoji(average, 10, 30)),
                ("high", high, get_status_emoji(high, 10, 30))
            ]
    except Exception as e:
        return [("error", f"Erro ao verificar o load: {e}")]

def test_tcp_connection(host, port):
    try:
        with socket.create_connection((host, port), timeout=5):
            return "🟢"
    except (socket.timeout, socket.error) as e:
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(5)
            test_socket.connect((host, port))
            test_socket.close()
            return "🟢"
        except (socket.timeout, socket.error) as e:
            return "🔴" 

def get_services():
    try:
        result = subprocess.run(
            ['docker', 'service', 'ls', '--format', '{{.Name}} {{.Replicas}} {{.Ports}}'],
            capture_output=True, text=True, check=True
        )
        services = []
        for line in result.stdout.splitlines():
            parts = line.split(maxsplit=2)
            if len(parts) < 2:
                continue
            service_name = parts[0]
            replicas = parts[1]
            raw_ports = parts[2] if len(parts) > 2 else "N/A"
            running, desired = map(int, replicas.split('/'))
            if running == desired:
                status = f"🟢 {replicas}"
            elif running == 0:
                status = f"🔴 {replicas}"
            else:
                status = f"🟡 {replicas}"
            match = re.search(r":(\d+)->", raw_ports)
            port = match.group(1) if match else "N/A"
            services.append((service_name, status, port, running > 0))
        return services
    except subprocess.CalledProcessError as e:
        print(f"Erro ao obter servicos: {e}")
        os._exit(1)

def get_docker_stats(all_services):
    try:
        result = subprocess.run(
            ['docker', 'stats', '--no-stream', '--format', '{{.Name}} {{.CPUPerc}} {{.MemUsage}}'],
            capture_output=True, text=True, check=True
        )
        raw_stats = {}
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) < 3:
                continue
            container_name = parts[0]
            cpu_usage = parts[1].replace('%', '')
            memory_usage = parts[2]
            service_name = container_name.split('.')[0]
            if service_name not in all_services:
                continue
            try:
                cpu_value = float(cpu_usage)
            except ValueError:
                cpu_value = 0.0

            if service_name not in raw_stats or cpu_value > raw_stats[service_name][0]:
                raw_stats[service_name] = (cpu_value, memory_usage)
        stats_dict = {}
        for service_name, (cpu_value, memory_usage) in raw_stats.items():
            if cpu_value < 80:
                cpu_status = f"🟢 {cpu_value:.2f}%"
            elif cpu_value < 100:
                cpu_status = f"🟡 {cpu_value:.2f}%"
            else:
                cpu_status = f"🔴 {cpu_value:.2f}%"

            memory_status = f"🟢 {memory_usage}"
            if "GiB" in memory_usage:
                memory_status = f"🟡 {memory_usage}"

            stats_dict[service_name] = (cpu_status, memory_status)
        return stats_dict

    except subprocess.CalledProcessError as e:
        print(f"Erro ao obter estatísticas do Docker: {e}")
        return {}

def generate_table_from_stats(type):
    filename = os.path.join(REPORTS_DIR, f"{type}_report_latest.json")
    if not os.path.exists(filename):
        return None, None
    with open(filename, 'r') as file:
        data = json.load(file)
    if not data:
        return None, None
    last_entry = sorted(data, key=lambda x: x["timestamp"], reverse=True)[0]
    timestamp = last_entry["timestamp"] 
    stats = last_entry.get("data", [])
    table = PrettyTable()
    table.field_names = ["Service", "Replicas", "CPU Usage", "Memory Usage", "IP:Port"]
    if isinstance(stats, list):
        for stat in stats:
            service = stat.get("Service", "N/A")
            replicas = stat.get("Replicas", "N/A")
            cpu_usage = stat.get("CPU Usage", "N/A")
            memory_usage = stat.get("Memory Usage", "N/A")
            ip_port = stat.get("IP:Port", "N/A")
            table.add_row([service, replicas, cpu_usage, memory_usage, ip_port])

    table.sortby = "Replicas"
    rows = table._rows
    rows.sort(key=lambda x: (
        "🔴" in x[1],  # Status das replicas
        "🔴" in x[2],  # Status do CPU
        "🔴" in x[3],  # Status da Memória
        "🔴" in x[4],  # Status de IP:Port
        "🟡" in x[1],  # Caso nao haja 🔴, verifique 🟡 nas replicas
        "🟡" in x[2],  # Verifique 🟡 no CPU
        "🟡" in x[3],  # Verifique 🟡 na Memória
        "🟡" in x[4],  # Verifique 🟡 em IP:Port
    ), reverse=True)
    return timestamp, table

def load_report_data(report_type):
    filename = os.path.join(REPORTS_DIR, f"{report_type}_report_latest.json")
    if not os.path.exists(filename):
        return None, []
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
            if not data:
                return None, []
            last_entry = data[-1]
            timestamp = last_entry.get("timestamp")
            report_data = last_entry.get("data", [])
            return timestamp, report_data
    except json.JSONDecodeError:
        return None, []