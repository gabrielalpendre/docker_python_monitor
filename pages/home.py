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
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/vue@2.6.14/dist/vue.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
        <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
        <link rel="icon" type="image/x-icon" href="{{ url_for('static', filename='images/favicon.ico') }}">
    </head>
    <body>
        <div id="app">
            <nav class="navbar navbar-light bg-white shadow-sm px-4 d-flex justify-content-between align-items-center">
                <div class="d-flex align-items-center"><img :src="logoSrc" alt="GABRL" height="25" class="me-3" /></div>
                <div class="last-update text-end">
                    <strong>Última atualização:</strong>
                    <div class="fs-5">[[ lastUpdate ]]</div>
                </div>
                <div class="buttons d-flexgap-2">
                    <a href="{{ url_for('incidentes.incidentes') }}" class="btn btn-secondary btn-sm">Histórico de incidentes</a>
                    <a href="{{ url_for('reports.reports') }}" class="btn btn-secondary btn-sm">Relatórios</a>
                    {% if FLASK_PREFIX != '/homol' %}
                        <a href="{{ url_for('filas.filas') }}" class="btn btn-secondary btn-sm">Filas AWS</a>
                        <a href="{{ url_for('tabelas.tabelas') }}" class="btn btn-secondary btn-sm">Banco de Dados</a>
                    {% endif %}
                    <button class="btn btn-secondary ms-3" @click="toggleTheme" title="Alternar tema">
                        <i :class="theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon'"></i>
                    </button>
                </div>
            </nav>

            <div class="container mt-4">
                <div class="d-flex align-items-center justify-content-start">
                    <div class="me-3">
                        <h4 class="m-0">Docker - {{ server_hostname }}</h4>
                    </div>
                    <div class="fs-6">
                        <strong>Carga do Servidor:</strong>
                        <span data-bs-toggle="tooltip" data-bs-placement="top" title="Carga média nos últimos 1 minuto">
                            [[ status.actual ]]
                        </span> |
                        <span data-bs-toggle="tooltip" data-bs-placement="top" title="Carga média nos últimos 5 minutos">
                            [[ status.average ]]
                        </span> |
                        <span data-bs-toggle="tooltip" data-bs-placement="top" title="Carga média nos últimos 15 minutos">
                            [[ status.high ]]
                        </span>
                        <i class="bi bi-info-circle-fill text-secondary"></i>
                        &nbsp;|&nbsp;
                        <strong>Uptime:</strong> 
                        <span data-bs-toggle="tooltip" data-bs-placement="top" title="Tempo em horas e minutos">
                            [[ status.uptime ]]<span class="text-muted"> (h:m)</span> 
                        </span>
                    </div>
                </div>

                <div v-if="loading" class="alert alert-info spaced-section">Carregando...</div>
                <div v-else-if="services.length === 0" class="alert alert-warning spaced-section">Nenhum dado encontrado.</div>
                <div v-else class="table-responsive spaced-section">
                    <table class="table table-striped">
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
                            <tr v-for="row in services" :key="row.Service">
                                <td>[[ row["Service"] ]]</td>
                                <td>[[ row["Replicas"] ]]</td>
                                <td>[[ row["CPU Usage"] ]]</td>
                                <td>[[ row["Memory Usage"] ]]</td>
                                <td>[[ row["IP:Port"] ]]</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <script>
new Vue({
    el: "#app",
    delimiters: ['[[', ']]'],
    data: {
        services: [],
        loading: true,
        lastUpdate: "",
        status: {
            uptime: "Carregando...",
            actual: "N/A",
            average: "N/A",
            high: "N/A"
        },
        theme: 'dark',  // inicial padrão
        logoLight: href="{{ url_for('static', filename='images/logo.png') }}",
        logoDark: "{{ url_for('static', filename='images/logo.png') }}"
    },
    computed: {
        logoSrc() {
            return this.theme === 'dark' ? this.logoDark : this.logoLight;
        },
        themeIcon() {
            return this.theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon';
        }
    },
    methods: {
        fetchStats() {
            axios.get("{{ url_for('services.services') }}")
                .then(response => {
                    this.loading = false;
                    const data = response.data;
                    this.services = data.data || [];
                    this.lastUpdate = data.timestamp || "";
                })
                .catch(() => {
                    this.loading = false;
                    this.services = [];
                    this.lastUpdate = "";
                });
        },
        fetchServerStatus() {
            axios.get("{{ url_for('server.server') }}")
                .then(response => {
                    const data = response.data?.data?.[0] || {};
                    this.status.uptime = data.Uptime || "N/A";
                    this.status.actual = data.Actual || "N/A";
                    this.status.average = data.Average?.toFixed?.(2) ?? "N/A";
                    this.status.high = data.High?.toFixed?.(2) ?? "N/A";
                })
                .catch(() => {
                    this.status = {
                        uptime: "Erro",
                        actual: "N/A",
                        average: "N/A",
                        high: "N/A"
                    };
                });
        },
        toggleTheme() {
            this.theme = this.theme === 'light' ? 'dark' : 'light';
            localStorage.setItem('theme', this.theme);
            document.body.className = `${this.theme}-mode`;
        },
        applyTheme() {
            this.theme = localStorage.getItem('theme') || 'dark';
            document.body.className = `${this.theme}-mode`;
        }
    },
    mounted() {
        this.applyTheme();
        this.fetchStats();
        this.fetchServerStatus();
        setInterval(() => {
            this.fetchStats();
            this.fetchServerStatus();
        }, 5000);
    }
});
        </script>

        <!-- Bootstrap Tooltip Activation -->
        <script>
            document.addEventListener('DOMContentLoaded', function () {
                const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
                tooltipTriggerList.map(function (tooltipTriggerEl) {
                    return new bootstrap.Tooltip(tooltipTriggerEl);
                });
            });
        </script>
    </body>
    </html>
    """, server_hostname=server_hostname, FLASK_PREFIX=FLASK_PREFIX)
