from flask import Blueprint, jsonify, request
from functions.services import load_report_data
from functions.alerts import load_alerts_state
from dotenv import load_dotenv
import os

load_dotenv(override=True)
FLASK_PREFIX = os.getenv('PREFIX', '')

if FLASK_PREFIX != '/homol':
    bp_queues = Blueprint('queues', __name__)
    bp_queues_status = Blueprint('queues_status', __name__)

    @bp_queues.route(f'{FLASK_PREFIX}/queues/<tipo>', methods=['GET'])
    def queues(tipo):
        if tipo == "prd":
            aws_account = "prd"
        elif tipo == "old":
            aws_account = "old"
        else:
            return jsonify({'error': 'Parâmetro tipo inválido'}), 400

        timestamp, report_data = load_report_data(f"queues_{aws_account}")
        if not report_data:
            return jsonify({'error': 'No report data available'}), 500

        return jsonify({
            'timestamp': timestamp,
            'data': report_data
        })

    @bp_queues_status.route(f'{FLASK_PREFIX}/queues/status', methods=['GET'])
    def queues_status():
        tipo = request.args.get("tipo")
        if tipo == "producao":
            aws_account = "prd"
        elif tipo == "antiga":
            aws_account = "old"
        else:
            return jsonify({'error': 'Parâmetro tipo inválido'}), 400

        query_status = load_alerts_state(f"queues_{aws_account}")
        return jsonify(query_status)