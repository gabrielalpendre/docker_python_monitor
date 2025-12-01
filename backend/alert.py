from flask import Blueprint, jsonify, request
from dotenv import load_dotenv
from functions.alerts import save_alert_config, load_alert_config, load_alerts_state, load_alert_schedules, save_alert_schedules, check_send_alert
from functions.scheduler import restart_scheduler, get_scheduler_interval
from functions.services import get_server_info
import os

load_dotenv(override=True)
FLASK_PREFIX = os.getenv('PREFIX', '')

bp_load_config = Blueprint('alert_config', __name__)
bp_toggle_alert = Blueprint('alert_toggle', __name__)
bp_test_alert = Blueprint('test_alert', __name__)
bp_send_alert = Blueprint('send_alert', __name__)
bp_get_a_schedule = Blueprint('get_alert_schedule', __name__)
bp_upd_a_schedule = Blueprint('update_alert_schedule', __name__)

@bp_get_a_schedule.route(f'{FLASK_PREFIX}/backend/alert/schedule', methods=['GET'])
def get_alert_schedule():
    """
    Retrieves the alert schedules for all tools.
    ---
    tags:
      - Alerts
    responses:
      200:
        description: A JSON object with alert schedules for each tool (e.g., telegram, teams).
        schema:
          type: object
          properties:
            telegram:
              type: array
              items:
                type: object
            teams:
              type: array
              items:
                type: object
    """
    return jsonify(load_alert_schedules())

@bp_upd_a_schedule.route(f'{FLASK_PREFIX}/backend/alert/schedule', methods=['POST'])
def update_alert_schedule():
    """
    Updates the alert schedule for a specific tool.
    ---
    tags:
      - Alerts
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            tool:
              type: string
              description: The alert tool to configure.
              enum: ['telegram', 'teams']
            schedule:
              type: array
              description: A list of schedule objects.
              items:
                type: object
                properties:
                  time:
                    type: string
                    example: "09:00"
                  action:
                    type: string
                    enum: ['on', 'off']
    """
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

@bp_load_config.route(f'{FLASK_PREFIX}/backend/alert/config', methods=['GET'])
def alert_config():
    """
    Retrieves the current alert configuration.
    ---
    tags:
      - Alerts
    responses:
      200:
        description: The current configuration for alert tools (enabled/disabled).
        schema:
          type: object
          properties:
            telegram:
              type: string
            teams:
              type: string
    """
    current_alert_config = load_alert_config()
    return jsonify(current_alert_config)

@bp_toggle_alert.route(f'{FLASK_PREFIX}/backend/alert/toggle', methods=['POST'])
def alert_toggle():
    """
    Enables or disables alert tools (Telegram, Teams).
    ---
    tags:
      - Alerts
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            telegram:
              type: boolean
              description: Enable or disable Telegram alerts.
              example: true
            teams:
              type: boolean
              description: Enable or disable Teams alerts.
              example: false
    """
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

@bp_test_alert.route(f'{FLASK_PREFIX}/backend/alert/test', methods=['POST'])
def test_alert():
    """
    Sends a test alert to a specified channel.
    ---
    tags:
      - Alerts
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            type:
              type: string
              description: The type of service to test.
              enum: ['queryes', 'services', 'queues', 'server']
            service_name:
              type: string
              description: The name of the service to test.
              example: "webapp"
            chat_name:
              type: string
              description: The destination chat/channel for the alert.
              enum: ['telegram_miner', 'telegram_infra', 'mail_miner', 'mail_infra']
    """
    data = request.get_json()

    alert_type = data.get("type")
    service_name = data.get("service_name")
    chat_name = data.get("chat_name")

    if alert_type not in {"queryes", "services", "queues", "server"}:
        return jsonify({
            "error": "Parâmetro 'type' inválido. Esperado 'queryes','services', 'queues' ou 'server'."
        }), 400

    if chat_name not in {"telegram_miner", "telegram_infra", "mail_miner", "mail_infra"}:
        return jsonify({
            "error": "Parâmetro 'chat_name' inválido. Esperado 'telegram_miner', 'telegram_infra', 'mail_miner' ou 'mail_infra'."
        }), 400

    if not service_name:
        return jsonify({
            "error": "Parâmetro 'service_name' obrigatório. Faça um get na rota 'type' para listar os serviços disponíveis."
        }), 400

    alerts_state = load_alerts_state(alert_type)
    previous_state = alerts_state.get("previous_state", {})
    current_state = alerts_state.get("last_state", {}).get(service_name)

    if current_state is None:
        return jsonify({
            "error": f"Serviço '{service_name}' não encontrado no estado atual."
        }), 400

    try:
        if alert_type == 'services':
            hostname, _ = get_server_info()
        elif alert_type == 'queryes':
            hostname, _ = get_server_info(return_db_info=True)
        else:
            raise ValueError(f"Tipo de alerta desconhecido: {alert_type}")

        response = check_send_alert(service_name, current_state, previous_state, hostname, chat_name, 'api')
        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": f"Erro ao processar o alerta: {str(e)}"}), 500

@bp_send_alert.route(f'{FLASK_PREFIX}/backend/alert/send', methods=['POST'])
def send_alert():
    """
    Sends an alert externally to a specified channel.
    ---
    tags:
      - Alerts
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            service_name:
              type: string
              description: The name of the service.
              example: "external_api"
            current_state:
              type: string
              description: The current state of the service, starting with an emoji.
              example: "🔴 Falha na Backend externa"
            chat_name:
              type: string
              description: The destination chat/channel for the alert.
              enum: ['telegram_miner', 'telegram_infra', 'mail_miner', 'mail_infra']
    """
    data = request.get_json()
    required_fields = ['service_name', 'current_state', 'chat_name']
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        return jsonify({
            "error": f"Campos obrigatórios ausentes: {', '.join(missing_fields)}"
        }), 400

    service_name = data['service_name']
    current_state = data['current_state']
    chat_name = data['chat_name']

    if chat_name not in {"telegram_miner", "telegram_infra", "mail_miner", "mail_infra"}:
        return jsonify({
            "error": "Parâmetro 'chat_name' inválido. Esperado 'telegram_miner', 'telegram_infra', 'mail_miner' ou 'mail_infra'."
        }), 400

    if not current_state.startswith(("🔴", "🟡", "🟢")):
        return jsonify({
            "error": "O campo 'current_state' deve começar com um dos seguintes faróis: 🔴, 🟡 ou 🟢."
        }), 400

    response = check_send_alert(service_name, current_state, {}, "", chat_name, 'external')
    return jsonify(response), 200
