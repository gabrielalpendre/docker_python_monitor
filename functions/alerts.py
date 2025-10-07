import os
import json
import requests
import boto3
from datetime import datetime
from dotenv import load_dotenv
from functions.log import log_message

load_dotenv(override=True)
PYTHON_ENV = os.getenv('PYTHON_ENV', 'local')

ALERTS_DIR = os.getenv('ALERTS_DIR', 'files/alerts')
os.makedirs(ALERTS_DIR, exist_ok=True)

ALERTS_CONFIG_FILE= os.path.join(ALERTS_DIR, "alert_config.json")
SCHEDULE_FILE = os.path.join(ALERTS_DIR, 'alert_schedules.json')

def load_alert_config():
    if not os.path.exists(ALERTS_CONFIG_FILE):
        log_message('info', "### Criando arquivo de configuracções de log")
        save_alert_config(telegram=False, teams=False)
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
        "telegram": "enabled" if telegram else "disabled",
        "teams": "enabled" if teams else "disabled",
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    try:
        with open(ALERTS_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        log_message('warning', "### Configuracoes de alerta atualizadas")
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
        save_alerts_state(type, {})
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

telegram_miner_chat_id = os.getenv("TELEGRAM_MINER_CHAT_ID")
telegram_infra_chat_id = os.getenv("TELEGRAM_INFRA_CHAT_ID")
to_addresses_miner = [os.getenv('MAIL_TO_MINER')]
to_addresses_infra = [os.getenv('MAIL_TO_INFRA')]

def check_send_alert(service_name, current_state, previous_state, server_hostname, alert_endpoint, alert_from):
    """
    Verifica se houve mudança no current_state do serviço e envia o alerta se necessário.
    A notificação é enviada somente se o estado anterior for diferente do atual.
    """
    message = f"\n{current_state} {service_name}\n{server_hostname}"
    mail_subject = f"Alerta {service_name}"
    mail_body = f"{current_state} {service_name}"
    previous_status = previous_state.get(service_name)
    if previous_status != current_state and alert_from == 'function':
        if PYTHON_ENV != 'debug':
            if alert_endpoint == "telegram_miner":
                send_telegram_alert(message, telegram_miner_chat_id)
                send_email_alert(mail_subject, mail_body, to_addresses_miner)
            else:
                current_alert_config = load_alert_config()
                telegram = current_alert_config.get("telegram")
                teams = current_alert_config.get("teams")
                if telegram == "enabled":
                    send_telegram_alert(message, telegram_infra_chat_id)
                if teams == "enabled":
                    send_teams_alert(current_state, service_name, message)
        else:
            print(f"[DEBUG] - Mensagem do alerta: {message}")
    elif alert_from != 'function':
        if alert_endpoint == "telegram_miner":
            response = send_telegram_alert(message, telegram_miner_chat_id)
        elif alert_endpoint == "telegram_infra":
            response = send_telegram_alert(message, telegram_infra_chat_id)
        elif alert_endpoint == "mail_miner":
            response = send_email_alert(mail_subject, mail_body, to_addresses_miner)
        elif alert_endpoint == "mail_infra":
            response = send_email_alert(mail_subject, mail_body, to_addresses_infra)
        return response

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

def send_telegram_alert(message, chat_id):
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    response = requests.post(url, json=payload)
    log_message(f'warning',"### Enviando alerta do telegram {chat_id}")
    data = response.json()
    
    return {
        "message_id": data.get("result", {}).get("message_id"),
        "chat_id": data.get("result", {}).get("chat", {}).get("id"),
        "chat_title": data.get("result", {}).get("chat", {}).get("title"),
        "text": data.get("result", {}).get("text")
    }

def send_email_alert(subject, body, to_addresses):
    mail_from = os.getenv("MAIL_FROM")
    ses = boto3.client(
        'ses',
        region_name='us-east-1',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    response = ses.send_email(
        Source=mail_from,
        Destination={'ToAddresses': to_addresses},
        Message={
            'Subject': {'Data': subject},
            'Body': {'Text': {'Data': body}}
        }
    )
    log_message("warning", "### Enviando alerta para o e-mail")

    return {
        "message_id": response.get("MessageId"),
        "chat_id": to_addresses[0] if isinstance(to_addresses, list) else to_addresses,
        "chat_title": subject,
        "text": body
    }
