from flask import Blueprint, request, jsonify, render_template_string
from functions.admin import get_excluded_services, save_excluded_services, get_medium_execution_time
from functions.scheduler import get_scheduler_interval
from functions.services import get_services
from dotenv import load_dotenv
import os

load_dotenv(override=True)

FLASK_PREFIX = os.getenv('PREFIX', '')
ADMIN_DIR = os.getenv('ADMIN_DIR', '')
VERSAO = os.getenv('VERSAO', 'development')

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
                    <div class="d-flex flex-column">
                        <h2 class="mb-3">Administracao de servicos</h2>
                    </div>
                    <div class="d-flex flex-row spaced-section">
                        <div id="servicos" class="w-50 pe-3">
                            <div>
                                <h5 class="d-inline">Tempo medio da execucao do relatório:</h5> 
                                <span id="tempo_medio" class="fs-5 d-inline">{{ tempo_medio }}</span>
                            </div>
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
                        <div id="agendamentos" class="w-50 ps-3"
                            <!-- Gerenciamento de Alertas -->
                            <h5>Ferramentas de Alerta</h5><br>
                            <div class="mb-4">
                                <div class="d-flex mb-2">
                                    <select id="service-selector" class="form-select form-select-sm me-2" style="width: auto;">
                                        <option value="telegram">Telegram</option>
                                        <option value="teams">Teams</option>
                                    </select>
                                    <input type="time" id="global-time" class="form-control form-control-sm me-2" />
                                    <select id="global-action" class="form-select form-select-sm me-2" style="width: auto;">
                                        <option value="on">Ativar</option>
                                        <option value="off">Desativar</option>
                                    </select>
                                    <button onclick="addSchedule()" class="btn btn-sm btn-primary">Adicionar</button>
                                </div>
                            </div>
                            <div id="schedule-container"></div>
                        </div>
                    </div>    
                </div>
            </div>
            <script>
                let currentSchedules = {};
                document.addEventListener('DOMContentLoaded', () => {
                    setupFormListeners();
                    fetchSchedules(); // Apenas essa chamada aqui
                });
                function setupFormListeners() {
                    const intervalForm = document.getElementById('intervalForm');
                    if (intervalForm) {
                        intervalForm.addEventListener('submit', (e) => {
                            e.preventDefault();
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
                                location.reload();
                            })
                            .catch(console.error);
                        });
                    }
                    const excludedForm = document.getElementById('excludedForm');
                    if (excludedForm) {
                        excludedForm.addEventListener('submit', (e) => {
                            e.preventDefault();
                            const selectedServices = Array.from(document.querySelectorAll('input[name="excluded_services"]:checked'))
                                .map(checkbox => checkbox.value);
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
                    }
                }
                function loadAlertConfig() {
                    fetch("{{ url_for('alert_config.alert_config') }}")
                        .then(response => response.json())
                        .then(data => {
                            // Convertendo "enabled"/"disabled" para booleanos
                            const telegramEnabled = data.telegram === "enabled";
                            const teamsEnabled = data.teams === "enabled";
                            setToggleState('Telegram', telegramEnabled);
                            setToggleState('Teams', teamsEnabled);
                        })
                        .catch(console.error);
                }
                function setToggleState(service, isEnabled) {
                    const toggle = document.getElementById(`toggle${service}Logs`);
                    if (toggle) {
                        toggle.checked = isEnabled;
                        toggle.nextElementSibling.innerText = isEnabled ? "Ativado" : "Desativado";
                        toggle.removeEventListener('change', toggleAlertState);
                        toggle.addEventListener('change', toggleAlertState);
                    }
                }
                function toggleAlertState() {
                    const payload = {
                        telegram: document.getElementById('toggleTelegramLogs')?.checked,
                        teams: document.getElementById('toggleTeamsLogs')?.checked
                    };
                    fetch('{{ url_for('alert_toggle.alert_toggle') }}', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    })
                    .then(response => {
                        if (!response.ok) throw new Error("Erro ao atualizar alertas");
                        return response.json();
                    })
                    .then(() => {
                        setToggleState('Telegram', payload.telegram);
                        setToggleState('Teams', payload.teams);
                    })
                    .catch(error => {
                        alert(error.message);
                        console.error(error);
                    });
                }
                function fetchSchedules() {
                    fetch("{{ url_for('get_alert_schedule.get_alert_schedule') }}")
                        .then(res => res.json())
                        .then(data => {
                            currentSchedules = data;
                            renderSchedules();
                            loadAlertConfig();
                        })
                        .catch(console.error);
                }
                function renderSchedules() {
                    const container = document.getElementById('schedule-container');
                    container.innerHTML = '';
                    ['telegram', 'teams'].forEach(tool => {
                        const title = tool.charAt(0).toUpperCase() + tool.slice(1);
                        const scheduleList = currentSchedules[tool] || [];
                        const html = `
                            <div class="mb-4">
                                <div class="d-flex align-items-center mb-2">
                                    <strong class="me-2 mb-0">${title}</strong>
                                    <div class="form-check form-switch">
                                        <input class="form-check-input me-2" type="checkbox" id="toggle${title}Logs">
                                        <label class="form-check-label" for="toggle${title}Logs"></label>
                                    </div>
                                </div>
                                <ul id="${tool}-schedule-list">
                                    ${scheduleList.map((s, i) => `
                                        <li>
                                            ${s.time} - ${s.action.toUpperCase()}
                                            <button onclick="removeSchedule('${tool}', ${i})" class="btn btn-sm btn-danger ms-2">Remover</button>
                                        </li>`).join('')}
                                </ul>
                            </div>
                        `;
                        container.innerHTML += html;
                    });
                    attachToggleListeners();
                }
                function attachToggleListeners() {
                    ['Telegram', 'Teams'].forEach(title => {
                        const toggle = document.getElementById(`toggle${title}Logs`);
                        if (toggle) {
                            toggle.removeEventListener('change', toggleAlertState);
                            toggle.addEventListener('change', toggleAlertState);
                        }
                    });
                }
                function addSchedule() {
                    const tool = document.getElementById('service-selector').value;
                    const time = document.getElementById('global-time').value;
                    const action = document.getElementById('global-action').value;
                    if (!time) return alert("Horário inválido.");
                    const updatedSchedule = [...(currentSchedules[tool] || []), { time, action }];
                    updateScheduleOnServer(tool, updatedSchedule);
                }
                function removeSchedule(tool, index) {
                    const updatedSchedule = [...(currentSchedules[tool] || [])];
                    updatedSchedule.splice(index, 1);
                    updateScheduleOnServer(tool, updatedSchedule);
                }
                function updateScheduleOnServer(tool, schedule) {
                    fetch("{{ url_for('update_alert_schedule.update_alert_schedule') }}", {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ tool, schedule })
                    })
                    .then(() => fetchSchedules())
                    .catch(console.error);
                }
            </script>
        </body>
    </html>
    """, services=services, excluded_services=excluded_services, tempo_medio=tempo_medio, current_interval=current_interval, FLASK_PREFIX=FLASK_PREFIX, VERSAO=VERSAO)
