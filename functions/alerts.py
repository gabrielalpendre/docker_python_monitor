import os
import json
import requests
from dotenv import load_dotenv
from functions.log import log_message

load_dotenv(override=True)


ALERTS_DIR = os.getenv('ALERTS_DIR', 'files/alerts')
os.makedirs(ALERTS_DIR, exist_ok=True)

ALERTS_CONFIG_FILE= os.path.join(ALERTS_DIR, "alert_config.json")

def load_alert_config():
    if not os.path.exists(ALERTS_CONFIG_FILE):
        # Cria arquivo com os valores padrão se não existir
        save_alert_config(telegram_alerts_enabled=True, teams_alerts_enabled=False)
    
    try:
        with open(ALERTS_CONFIG_FILE, 'r') as f:
            config = json.load(f)
        return {
            "telegram_alerts_enabled": config.get("telegram_alerts_enabled", True),
            "teams_alerts_enabled": config.get("teams_alerts_enabled", False)
        }
    except Exception as e:
        print(f"Erro ao carregar a configuração: {e}")
        return {
            "telegram_alerts_enabled": True,
            "teams_alerts_enabled": False
        }

def save_alert_config(telegram_alerts_enabled, teams_alerts_enabled):
    config = {
        "telegram_alerts_enabled": telegram_alerts_enabled,
        "teams_alerts_enabled": teams_alerts_enabled
    }
    try:
        with open(ALERTS_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        log_message('warning', "### Configurações de alerta atualizadas (Telegram e Teams)")
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

def check_send_alert(service_name, current_state, previous_state, server_hostname):
    """
    Verifica se houve mudança no current_state do serviço e envia o alerta se necessário.
    A notificação é enviada somente se o estado anterior for diferente do atual.
    """
    if not os.path.exists(ALERTS_CONFIG_FILE):
        save_alert_config(telegram_alerts_enabled=False, teams_alerts_enabled=False)

    with open(ALERTS_CONFIG_FILE, "r") as file:
        alert_config = json.load(file)

    telegram_alerts_enabled = alert_config.get("telegram_alerts_enabled", False)
    teams_alerts_enabled = alert_config.get("teams_alerts_enabled", False)

    previous_status = previous_state.get(service_name, "on")

    if previous_status != current_state:
        message = f"\n{current_state} {service_name}\nHostname: {server_hostname}"

        if telegram_alerts_enabled:
            send_telegram_alert(message)

        if teams_alerts_enabled:
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