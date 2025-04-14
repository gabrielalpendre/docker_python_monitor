from flask import Blueprint, request, jsonify, render_template_string
from functions.admin import get_excluded_services, save_excluded_services, get_medium_execution_time
from functions.scheduler import get_scheduler_interval
from functions.services import get_services
from dotenv import load_dotenv
import os

load_dotenv(override=True)

FLASK_PREFIX = os.getenv('PREFIX', '')
ADMIN_DIR = os.getenv('ADMIN_DIR', '')
VERSAO = os.getenv('VERSAO', 'local')

bp_admin = Blueprint('admin', __name__)

@bp_admin.route(f'{FLASK_PREFIX}/admin', methods=['GET', 'POST'])
def admin():
    services = get_services()
    excluded_services = get_excluded_services()
    tempo_medio = get_medium_execution_time()
    interval_data = get_scheduler_interval()
    current_interval = interval_data.get("interval_time") if isinstance(interval_data, dict) else interval_data

    if request.method == 'POST':
        form_type = request.json.get('form_type')

        if form_type == 'excludedForm':
            selected_services = request.json.get('excluded_services')
            save_excluded_services(selected_services)
            return jsonify({'message': 'Alterado!'})

    return render_template_string("""
    <html>
        <head>
            <title>Administracao de Servicos</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet" />
            <style>
                .spaced-section {
                    margin-top: 50px;
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
                .field_interval {
                    max-width: 70px;
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
                <!-- Botões -->
                <div class="d-flex">
                    <div class="text-end mb-2 mt-2 px-4">{{ VERSAO }}</div>
                    <a href="{{ url_for('logs.logs') }}" class="btn btn-gray btn-refresh me-2">Service Logs</a>
                    <!-- <a href="/reset_log" onclick="resetLog()" class="btn btn-gray btn-refresh me-2">Reset Log</a> -->
                    <a href="{{ url_for('incidentes.incidentes') }}" class="btn btn-gray me-2">Incidentes</a>
                    {% if FLASK_PREFIX != '/homol' %}
                        <a href="{{ url_for('tabelas.tabelas') }}" class="btn btn-gray me-2">Banco de Dados</a>
                    {% endif %}
                    <a href="{{ url_for('home.home') }}" class="btn btn-gray me-2">Home</a>
                </div>
            </nav>
            <div>
                <div class="container mt-4">
                    <div class="d-flex justify-content-between align-items-center">
                        <div class="d-flex flex-column">
                            <h2 class="mb-3">Administracao de servicos</h2>
                            <div>
                                <strong class="d-inline">Tempo medio da duracao da execucao do relatório:</strong> 
                                <span id="tempo_medio" class="fs-5 d-inline">{{ tempo_medio }}</span>
                            </div>
                        </div>

                    </div>
                    <div class="d-flex justify-content-between align-items-center">
                        <div class="d-flex spaced-section">
                            <form id="intervalForm" method="POST">
                                <input type="hidden" name="form_type" value="intervalForm">
                                <div class="mb-3">
                                    <div class="d-flex align-items-center">
                                        <h5 class="me-2">Alterar intervalo de execucao do relatório</h5>
                                        <button type="submit" id="updateInterval" class="btn btn-primary mt-3">Alterar</button>
                                    </div>
                                    <div class="d-flex align-items-center">
                                        <label for="current_interval" class="form-label me-2">Intervalo (em segundos):</label>
                                        <input class="field_interval form-control" type="number" id="current_interval" name="current_interval" min="1" value="{{ current_interval }}">
                                    </div>
                                </div>
                            </form>
                        </div>
                        <!-- <div class="spaced-section d-flex flex-column align-items-center"> -->
                        <!-- Telegram Toggle -->
                        <div class="d-flex align-items-center me-4">
                            <h5 class="mb-3 me-2">Alertas do Telegram</h5>
                            <div class="form-check form-switch">
                                <input class="form-check-input me-2" type="checkbox" id="toggleTelegramLogs">
                                <label class="form-check-label" for="toggleTelegramLogs"></label>
                            </div>
                        </div>

                        <!-- Teams Toggle -->
                        <div class="d-flex align-items-center">
                            <h5 class="mb-3 me-2">Alertas do Teams</h5>
                            <div class="form-check form-switch">
                                <input class="form-check-input me-2" type="checkbox" id="toggleTeamsLogs">
                                <label class="form-check-label" for="toggleTeamsLogs"></label>
                            </div>
                        </div>
                    </div>
                    <div class="d-flex align-items-center">
                        <form id="excludedForm" method="POST">
                            <input type="hidden" name="form_type" value="excludedForm">
                            <div class="d-flex align-items-center">
                                <h5 class="mb-0 mr-3 me-2">Marque os servicos para excluir do monitoramento</h5>
                                <button type="submit" class="btn btn-primary mt-3 ml-3">Salvar</button>
                            </div>
                            {% for service in services %}
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" name="excluded_services" value="{{ service[0] }}" {% if service[0] in excluded_services %}checked{% endif %}>
                                    <label class="form-check-label">{{ service[0] }}</label>
                                </div>
                            {% endfor %}
                        </form>
                    </div>
                </div>
            </div>
            <script>
            document.getElementById('intervalForm').addEventListener('submit', (e) => {
                e.preventDefault(); // Evita o envio tradicional do formulário
                const intervalo = parseInt(document.getElementById('current_interval').value);
                if (isNaN(intervalo) || intervalo <= 0) {
                    alert("Por favor, insira um intervalo válido maior que 0.");
                    return;
                }
                fetch("{{ url_for('set_interval.set_interval') }}", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ interval: intervalo })
                })
                .then(response => response.json())
                .then(data => {
                    alert(data.message || data.error);
                    location.reload(); // Recarrega a página após alteracao bem-sucedida
                })
                .catch(console.error);
            });
            document.getElementById('excludedForm').addEventListener('submit', (e) => {
                e.preventDefault(); // Prevent form submission
                const selectedServices = [];
                const checkboxes = document.querySelectorAll('input[name="excluded_services"]:checked');
                checkboxes.forEach(checkbox => {
                    selectedServices.push(checkbox.value);
                });
                fetch("{{ url_for('admin.admin') }}", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ form_type: 'excludedForm', excluded_services: selectedServices })
                })
                .then(response => response.json())
                .then(data => {
                    alert(data.message || data.error);
                })
                .catch(console.error);
            });
            function loadAlertConfig() {
                fetch("{{ url_for('load_config.load_config') }}")
                    .then(response => response.json())
                    .then(data => {
                        // Telegram
                        const telegramToggle = document.getElementById('toggleTelegramLogs');
                        telegramToggle.checked = data.telegram_alerts_enabled;
                        telegramToggle.nextElementSibling.innerText = telegramToggle.checked ? "Ativado" : "Desativado";
                        // Teams
                        const teamsToggle = document.getElementById('toggleTeamsLogs');
                        teamsToggle.checked = data.teams_alerts_enabled;
                        teamsToggle.nextElementSibling.innerText = teamsToggle.checked ? "Ativado" : "Desativado";
                    })
                    .catch(console.error);
            }
            function toggleAlertState() {
                const telegramToggle = document.getElementById('toggleTelegramLogs');
                const teamsToggle = document.getElementById('toggleTeamsLogs');
                const payload = {
                    telegram_alerts_enabled: telegramToggle.checked,
                    teams_alerts_enabled: teamsToggle.checked
                };
                fetch('{{ url_for('toggle_alert.toggle_alert') }}', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                })
                .then(response => {
                    if (!response.ok) throw new Error("Erro ao atualizar alertas");
                    return response.json();
                })
                .then(data => {
                    telegramToggle.nextElementSibling.innerText = telegramToggle.checked ? "Ativado" : "Desativado";
                    teamsToggle.nextElementSibling.innerText = teamsToggle.checked ? "Ativado" : "Desativado";
                })
                .catch(error => {
                    alert(error.message);
                    console.error(error);
                });
            }
            window.onload = loadAlertConfig;
            document.getElementById('toggleTelegramLogs').addEventListener('change', toggleAlertState);
            document.getElementById('toggleTeamsLogs').addEventListener('change', toggleAlertState);
            </script>
        </body>
    </html>
    """, services=services, excluded_services=excluded_services, tempo_medio=tempo_medio, current_interval=current_interval, FLASK_PREFIX=FLASK_PREFIX, VERSAO=VERSAO)
