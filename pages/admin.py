from flask import Blueprint, request, jsonify, render_template_string
from functions.admin import get_excluded_services, save_excluded_services, get_medium_execution_time
from functions.scheduler import get_scheduler_interval
from functions.services import get_services
from dotenv import load_dotenv
import os

load_dotenv(override=True)

FLASK_PREFIX = os.getenv('PREFIX', '')
ADMIN_DIR = os.getenv('ADMIN_DIR', '')
VERSAO = os.getenv('VERSION', 'development')

bp_admin = Blueprint('admin', __name__)

@bp_admin.route(f'{FLASK_PREFIX}/admin', methods=['GET', 'POST'])
def admin():
    services = get_services()
    excluded_services = get_excluded_services()
    tempo_medio = get_medium_execution_time('scheduler')
    interval_data = get_scheduler_interval()
    current_interval = interval_data.get("interval_time") if isinstance(interval_data, dict) else interval_data

    if request.method == 'POST':
        form_type = request.json.get('form_type')
        if form_type == 'excludedForm':
            selected_services = request.json.get('excluded_services')
            save_excluded_services(selected_services)
            return jsonify({'message': 'Servico(s) excluidos!'})

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>Administração de Serviços</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet" />
        <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
        <link rel="icon" type="image/x-icon" href="{{ url_for('static', filename='images/favicon.ico') }}">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/toastify-js/src/toastify.min.css">
        <script src="https://cdn.jsdelivr.net/npm/toastify-js"></script>
        <style>
            body.dark { background-color: #121212; color: #eee; }
            body.light { background-color: #f5f5f5; color: #333; }
            .navbar { transition: background-color 0.3s; }
            .container-section { 
                background-color: var(--section-bg); 
                padding: 20px; 
                border-radius: 8px; 
                transition: background-color 0.3s; 
            }
            body.dark .container-section { --section-bg: #2b2b2b; }
            body.light .container-section { --section-bg: #e0e0e0; }
        </style>
    </head>
    <body>
        <!-- Header -->
        <nav class="navbar navbar-light shadow-sm px-4 flex justify-between items-center" style="height:60px;">
            <div class="d-flex align-items-center">
                <img src="{{ url_for('static', filename='images/logo.png') }}" alt="Logo" height="25" class="me-3" />
            </div>  
            <div class="d-flex align-items-center gap-2">
                <div class="text-end fw-bold">{{ VERSAO }}</div>
                <a href="{{ url_for('logs.logs') }}" class="btn btn-secondary btn-sm">Service Logs</a>
                <a href="{{ url_for('incidentes.incidentes') }}" class="btn btn-secondary btn-sm">Incidentes</a>
                <a href="{{ url_for('reports.reports') }}" class="btn btn-secondary btn-sm">Relatórios</a>
                {% if FLASK_PREFIX != '/homol' %}
                    <a href="{{ url_for('filas.filas') }}" class="btn btn-secondary btn-sm">Filas AWS</a>
                    <a href="{{ url_for('tabelas.tabelas') }}" class="btn btn-secondary btn-sm">Banco de Dados</a>
                {% endif %}
                <a href="{{ url_for('home.home') }}" class="btn btn-secondary btn-sm">Home</a>
                <button id="toggleTheme" class="btn btn-secondary ms-3" title="Alternar tema">
                    <i id="themeIcon" class="bi"></i>
                </button>
            </div>
        </nav>

        <div class="container mt-4 container-section">
            <h2>Administração de serviços</h2>
            <div class="row">
                <div class="col-md-6">
                    <p><strong>Tempo médio da execução do relatório:</strong> {{ tempo_medio }}</p>

                    <form id="intervalForm" class="mb-4">
                        <input type="hidden" name="form_type" value="intervalForm">
                        <div class="mb-2 d-flex align-items-center gap-2">
                            <label for="current_interval" class="form-label mb-0">Intervalo (segundos):</label>
                            <input type="number" class="form-control form-control-sm" id="current_interval" name="current_interval" min="1" value="{{ current_interval }}">
                            <button type="submit" class="btn btn-primary btn-sm">Alterar</button>
                        </div>
                    </form>

                    <form id="excludedForm">
                        <input type="hidden" name="form_type" value="excludedForm">
                        <p class="mb-2"><strong>Serviços excluídos do monitoramento:</strong></p>
                        {% for service in services %}
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="excluded_services" value="{{ service[0] }}" {% if service[0] in excluded_services %}checked{% endif %}>
                                <label class="form-check-label">{{ service[0] }}</label>
                            </div>
                        {% endfor %}
                        <button type="submit" class="btn btn-primary btn-sm mt-2">Salvar</button>
                    </form>
                </div>
                <div class="col-md-6">
                    <h5>Ferramentas de Alerta</h5>
                    <div class="mb-3 d-flex gap-2 align-items-center">
                        <select id="service-selector" class="form-select form-select-sm" style="width:auto;">
                            <option value="telegram">Telegram</option>
                            <option value="teams">Teams</option>
                        </select>
                        <input type="time" id="global-time" class="form-control form-control-sm">
                        <select id="global-action" class="form-select form-select-sm" style="width:auto;">
                            <option value="on">Ativar</option>
                            <option value="off">Desativar</option>
                        </select>
                        <button onclick="addSchedule()" class="btn btn-primary btn-sm">Adicionar</button>
                    </div>
                    <div id="schedule-container"></div>
                </div>
            </div>
        </div>

        <script>
            const body = document.body;
            const toggleBtn = document.getElementById('toggleTheme');
            const themeIcon = document.getElementById('themeIcon');
            function applyTheme(theme) {
                body.classList.remove('dark', 'light');
                body.classList.add(theme);
                localStorage.setItem('theme', theme);
                themeIcon.className = theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon';
            }
            const savedTheme = localStorage.getItem('theme') || 'dark';
            applyTheme(savedTheme);
            toggleBtn.addEventListener('click', () => {
                const newTheme = body.classList.contains('dark') ? 'light' : 'dark';
                applyTheme(newTheme);
            });
            // Form listeners
            document.addEventListener('DOMContentLoaded', () => {
                setupFormListeners();
                fetchSchedules();
            });

            function setupFormListeners() {
                document.getElementById('intervalForm')?.addEventListener('submit', e => {
                    e.preventDefault();
                    const intervalo = parseInt(document.getElementById('current_interval').value);
                    if (isNaN(intervalo) || intervalo <= 0) return alert("Intervalo inválido!");
                    fetch("{{ url_for('set_interval.set_interval') }}", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ interval: intervalo })
                    }).then(r => r.json()).then(data => { alert(data.message || data.error); location.reload(); });
                });

                document.getElementById('excludedForm')?.addEventListener('submit', e => {
                    e.preventDefault();
                    const selectedServices = Array.from(document.querySelectorAll('input[name="excluded_services"]:checked')).map(c => c.value);
                    fetch("{{ url_for('admin.admin') }}", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ form_type: 'excludedForm', excluded_services: selectedServices })
                    }).then(r => r.json()).then(data => { alert(data.message || data.error); });
                });
            }

            let currentSchedules = {};
            function fetchSchedules() {
                fetch("{{ url_for('get_alert_schedule.get_alert_schedule') }}")
                    .then(res => res.json())
                    .then(data => {
                        currentSchedules = data;
                        renderSchedules();
                        loadAlertConfig();
                    }).catch(console.error);
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
                                <strong class="me-2">${title}</strong>
                                <div class="form-check form-switch">
                                    <input class="form-check-input me-2" type="checkbox" id="toggle${title}Logs">
                                    <label class="form-check-label" for="toggle${title}Logs"></label>
                                </div>
                            </div>
                            <ul id="${tool}-schedule-list">
                                ${scheduleList.map((s, i) => `<li>${s.time} - ${s.action.toUpperCase()} <button onclick="removeSchedule('${tool}', ${i})" class="btn btn-sm btn-danger ms-2">Remover</button></li>`).join('')}
                            </ul>
                        </div>`;
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
                }).then(() => fetchSchedules()).catch(console.error);
            }

            function loadAlertConfig() {
                fetch("{{ url_for('alert_config.alert_config') }}")
                    .then(r => r.json())
                    .then(data => {
                        setToggleState('Telegram', data.telegram === 'enabled');
                        setToggleState('Teams', data.teams === 'enabled');
                    }).catch(console.error);
            }

            function setToggleState(service, isEnabled) {
                const toggle = document.getElementById(`toggle${service}Logs`);
                if (toggle) { toggle.checked = isEnabled; }
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
                }).then(r => r.json()).then(() => fetchSchedules()).catch(console.error);
            }
        </script>
    </body>
    </html>
    """, services=services, excluded_services=excluded_services, tempo_medio=tempo_medio, current_interval=current_interval, FLASK_PREFIX=FLASK_PREFIX, VERSAO=VERSAO)
