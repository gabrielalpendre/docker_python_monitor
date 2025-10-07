import os
from flask import Blueprint, jsonify
from datetime import datetime
from dotenv import load_dotenv
from functions.alerts import load_alerts_state

load_dotenv(override=True)
FLASK_PREFIX = os.getenv('PREFIX', '')

if FLASK_PREFIX != '/homol':
    from functions.queryes import get_query_counts
    bp_queryes = Blueprint('queryes', __name__)
    bp_queryes_status = Blueprint('queryes_status', __name__)

    @bp_queryes.route(f'{FLASK_PREFIX}/queryes', methods=['GET'])
    def queryes():
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        query_results = get_query_counts()
        if not query_results:
            return jsonify({"error": "No report data available", "timestamp": timestamp}), 500
        def safe_get(key):
            item = query_results.get(key, {})
            return {
                "count": item.get("count", 0),
                "percentage": item.get("percentage", ""),
                "status": item.get("status_icon", "❓")
            }
        response_data = {
            "timestamp": timestamp,
            "data": {
                "id2": safe_get("id2"),
                "id3": safe_get("id3"),
                "id4": safe_get("id4"),
                "id5": safe_get("id5"),
                "id6": safe_get("id6"),
                "id7": safe_get("id7"),
                "id8": safe_get("id8")
            }
        }

        return jsonify(response_data)

    @bp_queryes_status.route(f'{FLASK_PREFIX}/queryes/status', methods=['GET'])
    def queryes_status():
        query_status = load_alerts_state("queryes")
        return jsonify (query_status)