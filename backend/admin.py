
from functions.admin import get_medium_execution_time
from functions.log import reset_log_file
from functions.scheduler import restart_scheduler, set_scheduler_interval
from flask import Blueprint, jsonify, request 
from dotenv import load_dotenv 
import os

load_dotenv(override=True)
FLASK_PREFIX = os.getenv('PREFIX', '')

ADMIN_DIR = os.getenv('ADMIN_DIR', 'files/admin')
INTERVAL_SERVICES_FILE = os.path.join(ADMIN_DIR, "scheduler_interval.json")

bp_reset_log = Blueprint('reset_log', __name__)
bp_set_interval = Blueprint('set_interval', __name__)
bp_m_time = Blueprint('tempo_medio', __name__)

@bp_reset_log.route(f'{FLASK_PREFIX}/backend/admin/log/reset', methods=['GET'])
def reset_log():
    try:
        """
        Resets the application's log file.
        ---
        tags:
          - Admin
        responses:
          200:
            description: Log file has been reset successfully.
          500:
            description: Error resetting the log file.
        """
        result = reset_log_file()
        return jsonify(result), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@bp_set_interval.route(f'{FLASK_PREFIX}/backend/admin/scheduler/interval', methods=['POST'])
def set_interval():
    """
    Sets the execution interval for the background scheduler.
    ---
    tags:
      - Admin
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            interval:
              type: integer
              description: The new interval in seconds.
              example: 60
    responses:
      200:
        description: Scheduler interval updated successfully.
      400:
        description: Invalid input data.
    """
    data = request.get_json()
    if not isinstance(data, dict) or 'interval' not in data:
        return jsonify({"error": "Formato inválido de dados ou intervalo nao fornecido"}), 400
    try:
        new_interval = int(data['interval'])
        if new_interval <= 1:
            return jsonify({"error": "O intervalo deve ser maior que 0"}), 400
        set_scheduler_interval(new_interval)
        restart_scheduler(new_interval)
        return jsonify({"message": f"Intervalo atualizado para {new_interval} segundos"}), 200
    except (ValueError, TypeError) as e:
        print(f"Error: {e}")
        return jsonify({"error": "Valor inválido"}), 400

@bp_m_time.route(f'{FLASK_PREFIX}/backend/admin/scheduler/interval', methods=['GET'])
def tempo_medio():
    """
    Gets the average execution time of the scheduler task.
    ---
    tags:
      - Admin
    responses:
      200:
        description: Returns the average execution time.
        schema:
          type: object
          properties:
            tempo_medio:
              type: string
    """
    tempo_medio = get_medium_execution_time('scheduler')
    return {'tempo_medio': tempo_medio}
