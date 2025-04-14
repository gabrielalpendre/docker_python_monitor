from flask import Blueprint, render_template_string, request
from dotenv import load_dotenv
from functions.reports import load_incidents
import os

load_dotenv(override=True)
FLASK_PREFIX = os.getenv('PREFIX', '')

bp_incidentes = Blueprint('incidentes', __name__)

@bp_incidentes.route(f'{FLASK_PREFIX}/incidentes', methods=['GET'])
def incidentes():
    filter_service = request.args.get('service')
    history, services = load_incidents(filter_service)

    return render_template_string("""
    <html>
        <head>
            <title>Histórico de Erros</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet" />
<style>
    .filter-group {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    #service {
        max-width: 250px;
    }
    .btn-gray {
        background-color: #6c757d;
        border-color: #6c757d;
        color: white;
    }
    .btn-gray:hover {
        background-color: #5a6268;
        border-color: #545b62;
    }
    .btn-refresh {
        margin-right: 10px;
    }
    .table-responsive {
        overflow-x: auto;
    }
    table {
        min-width: 600px;
    }
    table th, table td {
        padding: 5px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        vertical-align: middle;
    }
</style>
        </head>
        <body>
            <!-- Header -->
            <nav class="navbar navbar-light bg-white shadow-sm px-4 flex justify-between items-center h-40">
                <!-- Logo + Título -->
            <div class="flex items-center">
                <img src="https://assets.lwtecnologia.com.br/public/OFICIAL_BLACK.png" alt="Logo" height="25" class="me-3" />
               <!--<h5 class="mb-0 text-xl font-medium">Monitoramento</h5>-->
            </div>
                <div class="d-flex">
                    <a href="{{ url_for('incidentes.incidentes') }}" class="btn btn-gray btn-refresh">Refresh</a>
                    <a href="{{ url_for('home.home') }}" class="btn btn-gray">Home</a>
                </div>
            </nav>
            <div class="container mt-4">
                <div class="d-flex justify-content-between align-items-center">
                    <h3 class="mb-0">Histórico de Alertas do dia</h3>
                </div>
                <form method="get" action="{{ url_for('incidentes.incidentes') }}" class="mt-4">
                    <div class="filter-group mb-3">
                        <label for="service" class="form-label mb-0">Filtrar por Servico:</label>
                        <select class="form-select" name="service" id="service">
                            <option value="">Todos</option>
                            {% for service in services %}
                            <option value="{{ service }}" {% if request.args.get('service') == service %}selected{% endif %}>{{ service }}</option>
                            {% endfor %}
                        </select>
                        <button type="submit" class="btn btn-primary">Filtrar</button>
                    </div>
                </form>
                
<table class="table table-striped table-responsive">
    <thead>
        <tr>
            <th style="min-width: 150px; text-align: left; vertical-align: top;">Timestamp</th>
            <th style="min-width: 150px; text-align: left; vertical-align: top;">Service</th>
            <th style="min-width: 400px; text-align: left; vertical-align: top;">Motivo</th>
        </tr>
    </thead>
    <tbody>
        {% for entry in history %}
        <tr>
            <td style="text-align: left; vertical-align: top;">{{ entry.timestamp }}</td>
            <td style="text-align: left; vertical-align: top;">{{ entry.service }}</td>
<td style="text-align: left; vertical-align: top;"><pre style="white-space: pre-wrap; margin: 0;">{{ entry.reason }}</pre></td>
        </tr>
        {% endfor %}
    </tbody>
</table>


            </div>
        </body>
    </html>
    """, history=history, services=services)