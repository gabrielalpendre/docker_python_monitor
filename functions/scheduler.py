from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from functions.reports import generate_report
from functions.log import log_message
import threading
import json
import os

ADMIN_DIR = os.getenv('ADMIN_DIR', 'files/admin')
INTERVAL_SERVICES_FILE = os.path.join(ADMIN_DIR, "interval_execution_time.json")
DEFAULT_INTERVAL = 5

scheduler = None
scheduler_lock = threading.Lock()

def start_scheduler():
    """ Inicia o agendador se ele ainda nao estiver rodando. """
    global scheduler, scheduler_interval
    with scheduler_lock:
        if scheduler and scheduler.running:
            log_message(f'warning', "### O agendador já está em execucao.")
            return

        executors = {'default': ThreadPoolExecutor(10)}
        scheduler = BackgroundScheduler(executors=executors)

        try:
            scheduler.add_job(generate_report, 'interval', seconds=scheduler_interval, id='generate_report', replace_existing=True)
            scheduler.start()
            log_message(f'warning', "### Agendador iniciado com sucesso.")
        except Exception as e:
            log_message('error', f"Erro ao agendar o job: {e}")

def stop_scheduler():
    """ Para o agendador de forma segura. """
    global scheduler
    with scheduler_lock:
        if scheduler:
            scheduler.shutdown(wait=False)
            scheduler = None
            log_message(f'warning', "### Agendador parado com sucesso.")

def restart_scheduler(interval_seconds):
    """ Reinicia o job com um novo intervalo e recria a thread. """
    global scheduler, scheduler_interval
    with scheduler_lock:
        if scheduler:
            job = scheduler.get_job('generate_report')
            if job:
                job.remove()
                log_message(f'warning', "### Job antigo removido.")

            scheduler.shutdown(wait=False)
            scheduler = None
            log_message(f'warning', "### Agendador antigo parado.")

        scheduler_interval = interval_seconds
        executors = {'default': ThreadPoolExecutor(10)}
        scheduler = BackgroundScheduler(executors=executors)

        try:
            scheduler.add_job(generate_report, 'interval', seconds=scheduler_interval, id='generate_report', replace_existing=True)
            scheduler.start()
            log_message('warning', f"### Agendador reiniciado com intervalo de {scheduler_interval} segundos.")
        except Exception as e:
            log_message('error', f"Erro ao reiniciar o job: {e}")

def run_scheduler_in_background():
    """ Inicia o agendador em uma nova thread. """
    scheduler_thread = threading.Thread(target=start_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()

def get_scheduler_interval():
    """Recupera o valor de interval_time do arquivo JSON, criando o arquivo se nao existir."""
    if not os.path.exists(INTERVAL_SERVICES_FILE):
        with open(INTERVAL_SERVICES_FILE, 'w') as json_file:
            json.dump({'interval_time': DEFAULT_INTERVAL}, json_file)
    with open(INTERVAL_SERVICES_FILE, 'r') as json_file:
        data = json.load(json_file)
    return data.get('interval_time', DEFAULT_INTERVAL)

scheduler_interval = get_scheduler_interval()