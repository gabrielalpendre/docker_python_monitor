import os
import time
import boto3
from datetime import datetime
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from functions.log import log_message
from functions.services import get_status_emoji
from functions.reports import save_report_to_file, save_execution_time, save_incidents_to_file
from functions.alerts import check_send_alert, save_alerts_state, load_alerts_state

load_dotenv(override=True)

region_name = os.getenv('AWS_REGION', 'us-east-1')
aws_access_key_id_prod = os.getenv('AWS_ACCESS_KEY_ID_PROD')
aws_secret_access_key_prod = os.getenv('AWS_SECRET_ACCESS_KEY_PROD')
aws_account_id_prod = os.getenv('AWS_ID_PROD')
aws_access_key_id_old = os.getenv('AWS_ACCESS_KEY_ID_OLD')
aws_secret_access_key_old = os.getenv('AWS_SECRET_ACCESS_KEY_OLD')
aws_account_id_old = os.getenv('AWS_ID_OLD')


ALERTS_DIR = os.getenv('ALERTS_DIR', 'files/alerts')
os.makedirs(ALERTS_DIR, exist_ok=True)

def get_queue_attributes(sqs, queue_url):
    try:
        response = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['ApproximateNumberOfMessages']
        )
        return int(response['Attributes'].get('ApproximateNumberOfMessages', 0))
    except Exception as e:
        print(f"Erro ao obter atributos da fila {queue_url}: {e}")
        return 0

def process_queue(sqs, queue_url):
    queue_name = queue_url.split('/')[-1]
    message_count = get_queue_attributes(sqs, queue_url)
    queue_icon = get_status_emoji(message_count, 0, 100)
    return ("queues", queue_name, message_count, queue_icon)

def get_queues(sqs):
    try:
        start_time = time.time()
        response = sqs.list_queues()
        queue_urls = response.get('QueueUrls', [])
        # print(f"Found {len(queue_urls)} SQS queues.")
        queues = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(process_queue, sqs, url) for url in queue_urls]
            queues = []
            for future in as_completed(futures):
                try:
                    result = future.result()
                    queues.append(result)
                except Exception as e:
                    queues.append(("error", f"Erro ao processar fila: {e}"))
        execution_time = time.time() - start_time
        # print (f"get_queues: {execution_time:.2f} seconds")
        return queues
    except Exception as e:
        return [("error", f"Erro ao listar filas: {e}")]

def generate_queue_report(aws_account):
    if aws_account == 'prd':
        sqs_prod = boto3.client(
            'sqs',
            region_name=region_name,
            aws_access_key_id=aws_access_key_id_prod,
            aws_secret_access_key=aws_secret_access_key_prod
        )
        queues = get_queues(sqs_prod)
    if aws_account == 'old':
        sqs_old = boto3.client(
            'sqs',
            region_name=region_name,
            aws_access_key_id=aws_access_key_id_old,
            aws_secret_access_key=aws_secret_access_key_old
        )
        queues = get_queues(sqs_old)
    incidents_queues = []
    formatted_queues = []
    alerts_state = load_alerts_state(f"queues_{aws_account}")
    previous_state = alerts_state.get("previous_state", {})
    last_state = alerts_state.get("last_state", {})

    for item in queues:
        if item[0] == "error":
            log_message('warning',f"### Erro ao verificar {item[1]}")
            continue
        _, queue_name, message_count, cur_queue_icon = item
        current_state = f"{cur_queue_icon} {message_count}"
        prev_state = previous_state.get(queue_name, "")
        prev_queue_icon = prev_state.split()[0] if prev_state else None
        formatted_queues.append({
            "Queue": queue_name,
            "Messages": current_state
        })
        if prev_queue_icon != cur_queue_icon and "🟡" not in  {prev_queue_icon, cur_queue_icon}:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            incidents_queues.append({
                "service": queue_name,
                "type": f"Filas_{aws_account}",
                "timestamp": timestamp,
                "reason": current_state
            }) 
            last_state[queue_name] = current_state
            #log_message('warning',f"Incident detected for queues {queue_name}: {current_state}")
            #check_send_alert(queue_name, current_state, previous_state, aws_account, "telegram_infra", 'queues')
    alerts_state["previous_state"] = last_state
    alerts_state["last_state"] = last_state
    save_alerts_state(f"queues_{aws_account}", alerts_state)
    formatted_queues.sort(key=lambda x: {"🔴": 0, "🟡": 1, "🟢": 2}.get(x['Messages'].split()[0], 3))
    save_report_to_file(f"queues_{aws_account}", formatted_queues)
    if incidents_queues:
        save_incidents_to_file(incidents_queues)
    return {
        "queues": formatted_queues,
        "incidents_queues": incidents_queues
    }
