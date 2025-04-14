from flask import Blueprint, jsonify
from functions.services import generate_table_from_stats
from dotenv import load_dotenv
import os

load_dotenv(override=True)
FLASK_PREFIX = os.getenv('PREFIX', '')

bp_stats = Blueprint('stats', __name__)

@bp_stats.route(f'{FLASK_PREFIX}/stats')
def stats():
    timestamp, report_data = generate_table_from_stats()

    if not report_data:
        return jsonify({'error': 'No report data available'}), 500

    # Transforma as linhas da tabela em uma lista de dicionários
    table_data = [
        dict(zip(report_data.field_names, row))
        for row in report_data._rows
    ]

    return jsonify({
        'timestamp': timestamp,
        'data': table_data
    })
