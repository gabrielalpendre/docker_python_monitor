from flask import Blueprint, jsonify
from functions.services import generate_table_from_stats, load_report_data
from functions.alerts import load_alerts_state
from dotenv import load_dotenv
import os

load_dotenv(override=True)
FLASK_PREFIX = os.getenv('PREFIX', '')

bp_stats = Blueprint('services', __name__)
bp_stats_status = Blueprint('stats_status', __name__)
bp_server = Blueprint('server', __name__)

@bp_stats.route(f'{FLASK_PREFIX}/backend/services', methods=['GET'])
def services():
    """
    Retrieves the status of all monitored services.
    ---
    tags:
      - Services
    responses:
      200:
        description: A list of services and their current status.
      500:
        description: No report data available.
    """
    timestamp, report_data = generate_table_from_stats("services")
    if not report_data:
        return jsonify({'error': 'No report data available'}), 500
    table_data = [
        dict(zip(report_data.field_names, row))
        for row in report_data._rows
    ]
    return jsonify({
        'timestamp': timestamp,
        'data': table_data
    })

@bp_server.route(f'{FLASK_PREFIX}/backend/server', methods=['GET'])
def server():
    """
    Retrieves server information.
    ---
    tags:
      - Server
    responses:
      200:
        description: Server information, such as hostname and IP.
    """
    _, table_data = load_report_data("server")
    return jsonify({"data": table_data})

@bp_stats_status.route(f'{FLASK_PREFIX}/backend/services/status', methods=['GET'])
def stats_status():
    """
    Retrieves the alert state for services.
    ---
    tags:
      - Services
    responses:
      200:
        description: The current and previous alert states for services.
    """
    stats_status = load_alerts_state("services")
    return jsonify (stats_status)