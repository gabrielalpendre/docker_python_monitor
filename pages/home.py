from flask import Blueprint, render_template_string
from functions.services import get_server_info
from dotenv import load_dotenv
import os

load_dotenv(override=True)
FLASK_PREFIX = os.getenv('PREFIX', '')

bp_home = Blueprint('home', __name__)

@bp_home.route(f'{FLASK_PREFIX}/home')
def home():
    server_hostname, _ = get_server_info()
    return render_template_string("""
    <html>
    <head>
        <title>Docker Service Stats</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet" />
        <script src="https://cdn.jsdelivr.net/npm/jquery@3.6.0/dist/jquery.min.js"></script>
        <style>
            .container {
                position: relative;
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
            .header-container {
                display: flex;
                justify-content: space-between;
                align-items: center;
                width: 100%;
            }
            .last-update {
                margin-left: auto;
                margin-right: 10px;
                margin-top: 0;
                text-align: right;
            }
            .table-responsive {
                margin-top: 20px;
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
            <!-- Última atualização -->
            <div id="last-update" class="last-update me-4 hidden md:flex flex-col text-end">
                <strong>Última atualização:</strong>
                <div id="last-update-time" class="fs-5"></div>
            </div>
            <!-- Botões -->
            <div class="buttons flex gap-2">
                <a href="{{ url_for('incidentes.incidentes') }}" class="btn btn-gray">Histórico de incidentes</a>
                {% if FLASK_PREFIX != '/homol' %}
                    <a href="{{ url_for('tabelas.tabelas') }}" class="btn btn-gray">Banco de Dados</a>
                {% endif %}
            </div>
        </nav>

        <div class="container mt-4">
            <div class="d-flex justify-content-between align-items-center">
                <div class="d-flex flex-column">
                    <h4 class="mb-3">Docker - {{ server_hostname }}</h4>
                </div>

            </div>
            <div id="loading" class="alert alert-info spaced-section">Carregando...</div>
            <div id="stats" class="table-responsive spaced-section"></div>
        </div>
        <script>
        function fetchStats() {
            $.get("{{ url_for('stats.stats') }}", function(data) {
                $('#loading').hide();
                if (data.data && data.data.length > 0) {
                    let table = `
                        <table class="table table-striped" id="service-table">
                            <thead>
                                <tr>
                                    <th>Service</th>
                                    <th>Replicas</th>
                                    <th>CPU Usage</th>
                                    <th>Memory Usage</th>
                                    <th>IP:Port</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;
                    data.data.forEach(row => {
                        table += `
                            <tr>
                                <td>${row["Service"]}</td>
                                <td>${row["Replicas"]}</td>
                                <td>${row["CPU Usage"]}</td>
                                <td>${row["Memory Usage"]}</td>
                                <td>${row["IP:Port"]}</td>
                            </tr>
                        `;
                    });
                    table += `</tbody></table>`;
                    $('#stats').html(table);
                } else {
                    $('#stats').html('<div class="alert alert-warning">Nenhum dado encontrado.</div>');
                }
                if (data.timestamp) {
                    $('#last-update-time').text(data.timestamp);
                    $('#last-update').show();
                } else {
                    $('#last-update').hide();
                }
            }).fail(function() {
                $('#loading').hide();
                $('#stats').html('<div class="alert alert-danger">Erro ao buscar os dados dos serviço.</div>');
                $('#last-update').hide();
            });
        }
        setInterval(fetchStats, 5000);
        fetchStats();
        </script>
    </body>
    </html>
    """, server_hostname=server_hostname, FLASK_PREFIX=FLASK_PREFIX)
