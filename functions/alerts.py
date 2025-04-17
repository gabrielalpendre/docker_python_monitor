import os
import json
import requests
from dotenv import load_dotenv
from functions.log import log_message

load_dotenv(override=True)

ALERTS_DIR = os.getenv('ALERTS_DIR', 'files/alerts')
os.makedirs(ALERTS_DIR, exist_ok=True)

ALERTS_CONFIG_FILE= os.path.join(ALERTS_DIR, "alert_config.json")
SCHEDULE_FILE = os.path.join(ALERTS_DIR, 'alert_schedules.json')

def load_alert_config():
    if not os.path.exists(ALERTS_CONFIG_FILE):
        log_message('info', "### Criando arquivo de configuracções de log")
        save_alert_config(telegram="disabled", teams="disabled")
    try:
        with open(ALERTS_CONFIG_FILE, 'r') as f:
            config = json.load(f)
        return {
            "telegram": config.get("telegram"),
            "teams": config.get("teams")
        }
    except Exception as e:
        print(f"Erro ao carregar a configuração: {e}")

def save_alert_config(telegram, teams):
    config = {
        "telegram": "enabled" if telegram else "disabled", #if telegram true
        "teams": "enabled" if teams else "disabled" #if teams true
    }
    try:
        with open(ALERTS_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        log_message('warning', "### Configurações de alerta atualizadas")
    except Exception as e:
        print(f"Erro ao salvar a configuração: {e}")
        
def load_alerts_state(type):
    ALERTS_FILE = os.path.join(ALERTS_DIR, f"alerts_{type}.json")
    try:
        with open(ALERTS_FILE, 'r') as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print(f"Erro ao decodificar o arquivo JSON {ALERTS_FILE}. Criando um novo arquivo.")
        save_alerts_state(type, {})  # Corrigido: agora passa o `type` e o `state`
        return {}

def save_alerts_state(type, state):
    ALERTS_FILE = os.path.join(ALERTS_DIR, f"alerts_{type}.json")
    with open(ALERTS_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def load_alert_schedules():
    if not os.path.exists(SCHEDULE_FILE):
        return {"telegram": [], "teams": []}
    with open(SCHEDULE_FILE, 'r') as f:
        return json.load(f)

def save_alert_schedules(tool, schedule_list):
    data = load_alert_schedules()
    data[tool] = schedule_list
    with open(SCHEDULE_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    return True

def check_send_alert(service_name, current_state, previous_state, server_hostname):
    """
    Verifica se houve mudança no current_state do serviço e envia o alerta se necessário.
    A notificação é enviada somente se o estado anterior for diferente do atual.
    """
    if not os.path.exists(ALERTS_CONFIG_FILE):
        save_alert_config(telegram="disabled", teams="disabled")

    with open(ALERTS_CONFIG_FILE, "r") as file:
        alert_config = json.load(file)

    telegram = alert_config.get("telegram")
    teams = alert_config.get("teams")

    previous_status = previous_state.get(service_name, "on")

    if previous_status != current_state:
        message = f"\n{current_state} {service_name}\nHostname: {server_hostname}"

        if telegram == "enabled":
            send_telegram_alert(message)

        if teams == "enabled":
            send_teams_alert(current_state, service_name, message)

def send_telegram_alert(message):
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    response = requests.post(url, json=payload)
    log_message(f'warning',"### Enviando alerta do telegram")
    return response.json()

def send_teams_alert(current_state, service_name, message):
    webhook_url = os.getenv("TEAMS_WEBHOOK_URL")
    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": f"{current_state} {service_name}",
        "themeColor": "0078D7",
        "title": "alerta",
        "text": message
    }
    response = requests.post(webhook_url, json=payload)
    log_message("warning", "### Enviando alerta para o Microsoft Teams")
    return response.json()

