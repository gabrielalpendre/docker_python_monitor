from flask import Blueprint, jsonify, request
from dotenv import load_dotenv
from functions.alerts import save_alert_config, load_alert_config
import os

load_dotenv(override=True)
FLASK_PREFIX = os.getenv('PREFIX', '')

bp_load_config = Blueprint('load_config', __name__)
bp_toggle_alert = Blueprint('toggle_alert', __name__)

@bp_load_config.route(f'{FLASK_PREFIX}/load_config', methods=['GET'])
def load_config():
    config = load_alert_config()
    return jsonify(config)

@bp_toggle_alert.route(f'{FLASK_PREFIX}/toggle_alert', methods=['POST'])
def toggle_alert():
    data = request.get_json()
    telegram_alerts_enabled = data.get('telegram_alerts_enabled')
    teams_alerts_enabled = data.get('teams_alerts_enabled')

    if telegram_alerts_enabled is None or teams_alerts_enabled is None:
        return jsonify({"error": "telegram_alerts_enabled and teams_alerts_enabled are required"}), 400

    save_alert_config(telegram_alerts_enabled, teams_alerts_enabled)

    return jsonify({
        "status": "success",
        "telegram_alerts_enabled": telegram_alerts_enabled,
        "teams_alerts_enabled": teams_alerts_enabled
    })
