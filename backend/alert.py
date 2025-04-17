from flask import Blueprint, jsonify, request
from dotenv import load_dotenv
from functions.alerts import save_alert_config, load_alert_config, load_alert_schedules, save_alert_schedules
from functions.scheduler import restart_scheduler, get_scheduler_interval
import os

load_dotenv(override=True)
FLASK_PREFIX = os.getenv('PREFIX', '')

bp_load_config = Blueprint('alert_config', __name__)
bp_toggle_alert = Blueprint('alert_toggle', __name__)
bp_get_a_schedule = Blueprint('get_alert_schedule', __name__)
bp_upd_a_schedule = Blueprint('update_alert_schedule', __name__)

@bp_get_a_schedule.route(f'{FLASK_PREFIX}/get_alert_schedule', methods=['GET'])
def get_alert_schedule():
    return jsonify(load_alert_schedules())

@bp_upd_a_schedule.route(f'{FLASK_PREFIX}/update_alert_schedule', methods=['POST'])
def update_alert_schedule():
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({"error": "Formato inválido de dados"}), 400
    try:
        tool = data.get("tool")
        schedule = data.get("schedule")
        if tool not in ['telegram', 'teams']:
            return jsonify({"error": "Ferramenta inválida"}), 400
        if not isinstance(schedule, list):
            return jsonify({"error": "Formato de agenda inválido"}), 400
        scheduler_interval = get_scheduler_interval()
        save_alert_schedules(tool, schedule)
        restart_scheduler(scheduler_interval)
        return jsonify({"message": "Horários atualizados com sucesso!"})
    except (ValueError, TypeError) as e:
        print(f"Error: {e}")
        return jsonify({"error": "Valor inválido"}), 400

@bp_load_config.route(f'{FLASK_PREFIX}/alert_config', methods=['GET'])
def alert_config():
    config = load_alert_config()
    return jsonify(config)

@bp_toggle_alert.route(f'{FLASK_PREFIX}/alert_toggle', methods=['POST'])
def alert_toggle():
    data = request.get_json()
    telegram_data = data.get('telegram')
    teams_data = data.get('teams')
    if telegram_data is None or teams_data is None:
        return jsonify({"error": "telegram and teams are required"}), 400
    save_alert_config(telegram_data, teams_data)
    return jsonify({
        "status": "success",
        "telegram": telegram_data,
        "teams": teams_data
    })
