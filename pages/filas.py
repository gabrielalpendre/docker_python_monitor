from flask import Blueprint, render_template_string
from dotenv import load_dotenv
import os

load_dotenv(override=True)
FLASK_PREFIX = os.getenv('PREFIX', '')

if FLASK_PREFIX != '/homol':
    bp_filas = Blueprint('filas', __name__)

    @bp_filas.route(f'{FLASK_PREFIX}/filas')
    def filas():
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
                    <div class="d-flex align-items-center"><img :src="logoSrc" alt="LW" height="25" class="me-3" /></div>
                    <div class="last-update text-end">
                        <strong>Última atualização:</strong>
                        <div class="fs-5">[[ lastUpdate ]]</div>
                    </div>
                    <div class="buttons d-flexgap-2">
                        <a href="{{ url_for('incidentes.incidentes') }}" class="btn btn-gray">Histórico de incidentes</a>
                        {% if FLASK_PREFIX != '/homol' %}
                            <a href="{{ url_for('tabelas.tabelas') }}" class="btn btn-gray">Banco de Dados</a>
                        {% endif %}
                        <a href="{{ url_for('home.home') }}" class="btn btn-gray">Home</a>
                        <button class="btn btn-secondary ms-3" @click="toggleTheme" title="Alternar tema">
                            <i :class="theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon'"></i>
                        </button>
                    </div>
                </nav>

                <div class="container mt-4">
                    <div class="d-flex align-items-center mb-3">
                        <h3 class="mb-0">Filas AWS</h3>
                        <div class="d-flex align-items-center" style="margin-left: 40px;">
                            <label class="form-label mb-0 me-2" for="type">Selecione a conta:</label>
                            <select class="form-select" v-model="tipoSelecionado" id="type" style="width: auto;">
                                <option value="producao">Produção</option>
                                <option value="antiga">Antiga</option>
                            </select>
                        </div>
                    </div>
                    <div v-if="loading" class="alert alert-info spaced-section">Carregando...</div>
                    <div v-else-if="queues.length === 0" class="alert alert-warning spaced-section">Nenhum dado encontrado.</div>
                    <div v-else class="table-responsive spaced-section">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>Queue</th>
                                    <th>Messages</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="row in queues" :key="row.Queue">
                                    <td>[[ row["Queue"] ]]</td>
                                    <td>[[ row["Messages"] ]]</td>
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
    queues: [],
    loading: true,
    lastUpdate: "",
    tipoSelecionado: "producao",
    theme: 'dark',
    logoLight: href="{{ url_for('static', filename='images/logo.png') }}",
    logoDark: "{{ url_for('static', filename='images/logo.png') }}"
},
methods: {
    fetchTable() {
        this.loading = true;

        let tipoMap = {
            producao: "prd",
            antiga: "old"
        };

        const tipoBackend = tipoMap[this.tipoSelecionado];

        axios.get(`{{ FLASK_PREFIX }}/queues/${tipoBackend}`)
        .then(response => {
            this.loading = false;
            const data = response.data;
            this.queues = data.data || [];
            this.lastUpdate = data.timestamp || "";
        })
        .catch(() => {
            this.loading = false;
            this.queues = [];
            this.lastUpdate = "";
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
    this.fetchTable();
    setInterval(() => {
        this.fetchTable();
    }, 15000);
},
computed: {
    logoSrc() {
        return this.theme === 'dark' ? this.logoDark : this.logoLight;
    }
},
                watch: {
                    tipoSelecionado() {
                        this.fetchTable();
                    }
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
        """, aws_env='AWS PROD', FLASK_PREFIX=FLASK_PREFIX)
