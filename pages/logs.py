from flask import Blueprint, Response
from dotenv import load_dotenv
from functions.log import read_log_file
import os

load_dotenv(override=True)
FLASK_PREFIX = os.getenv('PREFIX', '')

bp_logs = Blueprint('logs', __name__)

@bp_logs.route(f'{FLASK_PREFIX}/logs', methods=['GET'])
def logs():
    def generate_logs():
        log_lines = read_log_file()
        for line in log_lines:
            yield f"data: {line}"

    return Response(generate_logs(), content_type='text/event-stream')
