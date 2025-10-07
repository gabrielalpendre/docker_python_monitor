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
    filter_type = request.args.get('type')
    history, services, types, type_map = load_incidents(filter_service, filter_type)

    return render_template_string("""
<html>
<head>
    <title>Histórico de Erros</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet" />
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/vue@2.6.14/dist/vue.min.js"></script>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <link rel="icon" type="image/x-icon" href="{{ url_for('static', filename='images/favicon.ico') }}">
</head>
<body>
    <div id="app">
        <!-- Header -->
        <nav class="navbar navbar-light bg-white shadow-sm px-4 d-flex justify-content-between align-items-center h-40">
            <div class="d-flex align-items-center">
                <img :src="logoSrc" alt="GABRL" height="25" class="me-3" />
            </div>
            <div class="buttons d-flex gap-2">
                <a href="{{ url_for('incidentes.incidentes') }}" class="btn btn-gray btn-refresh">Refresh</a>
                <a href="{{ url_for('home.home') }}" class="btn btn-gray">Home</a>
                <button class="btn btn-secondary ms-3" @click="toggleTheme" title="Alternar tema">
                    <i :class="theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon'"></i>
                </button>
            </div>
        </nav>

        <div class="container mt-4">
            <div class="d-flex justify-content-between align-items-center">
                <h3 class="mb-0">Histórico de Alertas do dia</h3>
            </div>

            <div class="filter-group mb-3">
                <label class="form-label mb-0" for="type">Tipo:</label>
                <select class="form-select" v-model="selectedType" id="type">
                    <option value="">Todos</option>
                    <option v-for="type in types" :key="type" :value="type">[[ type ]]</option>
                </select>

                <label class="form-label mb-0" for="service" style="margin-left: 1rem;">Serviço:</label>
                <select class="form-select" v-model="selectedService" id="service">
                    <option value="">Todos</option>
                    <option v-for="service in filteredServices" :key="service" :value="service">[[ service ]]</option>
                </select>
            </div>

            <table class="table table-striped table-responsive">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Service</th>
                        <th>Motivo</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="entry in filteredIncidents" :key="entry.timestamp + entry.service">
                        <td>[[ entry.timestamp ]]</td>
                        <td>[[ entry.service ]]</td>
                        <td><pre style="white-space: pre-wrap; margin: 0;">[[ entry.reason ]]</pre></td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
    new Vue({
        el: '#app',
        delimiters: ['[[', ']]'],
        data: {
            selectedType: "",
            selectedService: "",
            incidents: {{ history | tojson }},
            types: {{ types | tojson }},
            typeMap: {{ type_map | tojson }},
            theme: localStorage.getItem('theme') || 'dark',
            logoLight: href="{{ url_for('static', filename='images/logo.png') }}",
            logoDark: "{{ url_for('static', filename='images/logo.png') }}"
        },
        computed: {
            filteredServices() {
                if (!this.selectedType) {
                    const allServices = this.incidents.map(i => i.service);
                    return [...new Set(allServices)].sort();
                }
                return this.typeMap[this.selectedType] || [];
            },
            filteredIncidents() {
                return this.incidents.filter(entry => {
                    const matchType = !this.selectedType || entry.type === this.selectedType;
                    const matchService = !this.selectedService || entry.service === this.selectedService;
                    return matchType && matchService;
                });
            },
            logoSrc() {
                return this.theme === 'dark' ? this.logoDark : this.logoLight;
            }
        },
        methods: {
            toggleTheme() {
                this.theme = this.theme === 'light' ? 'dark' : 'light';
                localStorage.setItem('theme', this.theme);
                document.body.className = this.theme + '-mode';
            },
            applyTheme() {
                document.body.className = this.theme + '-mode';
            }
        },
        mounted() {
            this.applyTheme();
        },
        watch: {
            theme(newTheme) {
                document.body.className = newTheme + '-mode';
            }
        }
    });
    </script>
</body>
</html>
""", history=history, services=services, types=types, type_map=type_map)
