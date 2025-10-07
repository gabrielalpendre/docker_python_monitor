from apscheduler.schedulers.background import BackgroundScheduler 
from apscheduler.executors.pool import ThreadPoolExecutor 
from functions.reports import generate_services_report, generate_server_report
from functions.aws import generate_queue_report
from functions.reports import save_execution_time
from functions.alerts import save_alert_config, load_alert_config, load_alert_schedules
from functions.log import log_message
import threading
import json
import os
import time

# === Diretórios e arquivos ===
ADMIN_DIR = os.getenv('ADMIN_DIR', 'files/admin')
ALERTS_DIR = os.getenv('ALERTS_DIR', 'files/alerts')
INTERVAL_SERVICES_FILE = os.path.join(ADMIN_DIR, "scheduler_interval.json")
SCHEDULE_ALERT_FILE = os.path.join(ALERTS_DIR, "alert_schedules.json")
FLASK_PREFIX = os.getenv('PREFIX', '')

DEFAULT_INTERVAL = 10

scheduler = None
scheduler_lock = threading.Lock()

def get_scheduler_interval():
    """Recupera o valor de interval_time do arquivo JSON, criando o arquivo se não existir."""
    if not os.path.exists(INTERVAL_SERVICES_FILE):
        with open(INTERVAL_SERVICES_FILE, 'w') as json_file:
            json.dump({'interval_time': DEFAULT_INTERVAL}, json_file)
    with open(INTERVAL_SERVICES_FILE, 'r') as json_file:
        data = json.load(json_file)
    return data.get('interval_time', DEFAULT_INTERVAL)

def set_scheduler_interval(interval: int) -> None:
    """Salva o intervalo no arquivo JSON."""
    with open(INTERVAL_SERVICES_FILE, 'w') as json_file:
        json.dump({"interval_time": interval}, json_file)
scheduler_interval = get_scheduler_interval()

# ==== Funções para criar os schedulers de reports ====
def scheduled_reports():
    start_time = time.time()
    generate_services_report()
    generate_server_report()
    if FLASK_PREFIX != '/homol':    
        start_time_queues = time.time()
        generate_queue_report('prd')
        generate_queue_report('old')
        execution_time_queues = time.time() - start_time_queues
        save_execution_time('queues', execution_time_queues)
    execution_time = time.time() - start_time
    save_execution_time('scheduler', execution_time)

def start_scheduler():
    """Inicia o agendador principal e o agendador de alertas se ainda não estiverem rodando."""
    global scheduler, scheduler_interval
    with scheduler_lock:
        if scheduler and scheduler.running:
            log_message('warning', "### O agendador já está em execução.")
            return
        executors = {'default': ThreadPoolExecutor(10)}
        scheduler = BackgroundScheduler(executors=executors)
        try:
            scheduler.add_job(scheduled_reports, 'interval', seconds=scheduler_interval, id='scheduled_reports', replace_existing=True)
            schedule_alert_jobs(scheduler)
            scheduler.start()
            log_message('warning', "### Agendador iniciado com sucesso.")
        except Exception as e:
            log_message('error', f"### Erro ao agendar os jobs: {e}")

def stop_scheduler():
    """Para o agendador de forma segura."""
    global scheduler
    with scheduler_lock:
        if scheduler:
            if scheduler.running:
                scheduler.shutdown(wait=False)
                log_message('warning', "### Agendador antigo parado.")
            scheduler = None
            log_message('warning', "### Agendador parado com sucesso.")

def restart_scheduler(interval_seconds):
    """Reinicia o job principal com novo intervalo e recria todos os jobs."""
    global scheduler, scheduler_interval
    with scheduler_lock:
        if scheduler:
            scheduler.shutdown(wait=False)
            scheduler = None
            log_message('warning', "### Agendador antigo parado.")
        scheduler_interval = interval_seconds
        executors = {'default': ThreadPoolExecutor(10)}
        scheduler = BackgroundScheduler(executors=executors)

        try:
            scheduler.add_job(scheduled_reports, 'interval', seconds=scheduler_interval, id='scheduled_reports', replace_existing=True)
            schedule_alert_jobs(scheduler)
            scheduler.start()
            log_message('warning', f"### Agendador reiniciado")
        except Exception as e:
            log_message('error', f"### Erro ao reiniciar os jobs: {e}")

def run_scheduler_in_background():
    """Inicia o agendador em uma nova thread."""
    scheduler_thread = threading.Thread(target=start_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()

# ==== Funções para alert scheduler ====
def call_toggle_alert(service, action, scheduled_time):
    """Atualiza o estado de alerta com base na configuração agendada."""
    try:
        schedule_data = load_alert_schedules()
        current_config = schedule_data.get(service, [])
        if not any(entry["time"] == scheduled_time and entry["action"] == action for entry in current_config):
            log_message('warning', f"### Ignorando ação [{action}] para [{service}] às {scheduled_time}")
            print(f"Ignorado {current_config}")
            return
        
        current_alert_config = load_alert_config()
        if service == 'telegram':
            telegram = True if action == 'on' else False
            teams = current_alert_config["teams"]
        elif service == 'teams':
            teams = True if action == 'on' else False
            telegram = current_alert_config["telegram"]
        
        save_alert_config(
            telegram=telegram,
            teams=teams
        )
        log_message('warning', f"### [{service}] alterado para {action}")
        
    except Exception as e:
        log_message('error', f"### Erro ao salvar configuração de alerta: {e}")
        
def schedule_alert_jobs(sched_instance):
    """Lê o JSON e agenda os alertas no agendador fornecido."""
    schedule_data = load_alert_schedules()
    for service, actions in schedule_data.items():
        if not actions:
            continue
        for entry in actions:
            try:
                hour, minute = map(int, entry['time'].split(':'))
                action = entry['action']
                job_id = f"{service}_{action}_{hour}_{minute}"
                sched_instance.add_job(
                    call_toggle_alert,
                    trigger='cron',
                    day_of_week='mon-fri',
                    hour=hour,
                    minute=minute,
                    args=[service, action, entry['time']],
                    id=job_id,
                    replace_existing=True
                )
                log_message('warning', f"### Job agendado: {job_id}")
            except Exception as e:
                log_message('error', f"### Erro ao agendar job para {service} {entry}: {e}")
