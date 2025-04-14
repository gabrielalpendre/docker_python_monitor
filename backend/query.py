from flask import Blueprint, jsonify
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv(override=True)
FLASK_PREFIX = os.getenv('PREFIX', '')

if FLASK_PREFIX != '/homol':
    from functions.queryes import get_query_counts
    bp_query = Blueprint('query', __name__)

    @bp_query.route(f'{FLASK_PREFIX}/query')
    def query():
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        query_results = get_query_counts()

        if not query_results:
            return jsonify({"error": "No report data available", "timestamp": timestamp}), 500

        response_data = {
            "timestamp": timestamp,
            "results": {
                "lock_no_banco": {
                    "count": query_results["id1"]["count"],
                    "status": query_results["id1"]["status_icon"]
                },
                "multas_mensagens_erro_nao_tratadas": {
                    "count": query_results["id2"]["count"],
                    "status": query_results["id2"]["status_icon"]
                },
                "multas_mensagens_erro_tratadas": {
                    "count": query_results["id3"]["count"],
                    "status": query_results["id3"]["status_icon"]
                }
            }
        }

        return jsonify(response_data)