from flask import Blueprint, render_template_string
from dotenv import load_dotenv
from functions.services import get_server_info
import os

load_dotenv(override=True)
FLASK_PREFIX = os.getenv('PREFIX', '')

if FLASK_PREFIX != '/homol':
    bp_tabelas = Blueprint('tabelas', __name__)

    @bp_tabelas.route(f'{FLASK_PREFIX}/tabelas')
    def tabelas():
        db_hostname, db_ip = get_server_info(return_db_info=True)
        return render_template_string("""
        <html>
        <head>
            <title>Docker Service Query</title>
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
                    <div class="d-flex align-items-center">
                        <img :src="logoSrc" alt="LW" height="25" class="me-3" />
                    </div>
                    <div class="last-update text-end" v-if="lastUpdate">
                        <strong>Última atualização:</strong>
                        <div class="fs-5">[[ lastUpdate ]]</div>
                    </div>
                    <div class="buttons d-flex gap-2">
                        <a href="{{ url_for('incidentes.incidentes') }}" class="btn btn-gray">Histórico de incidentes</a>
                        <a href="{{ url_for('filas.filas') }}" class="btn btn-gray">Filas AWS</a>
                        <a href="{{ url_for('home.home') }}" class="btn btn-gray">Home</a>
                        <button class="btn btn-secondary ms-3" @click="toggleTheme" title="Alternar tema">
                            <i :class="theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon'"></i>
                        </button>
                    </div>
                </nav>

                <div class="container mt-4">
                    <div class="header-container mb-3">
                        <h4>Banco de Dados - {{ db_hostname }}</h4>
                    </div>

                    <div v-if="erro" class="alert alert-danger spaced-section">Erro ao buscar os dados do banco de dados.</div>
                    <div v-else-if="loading" class="alert alert-info spaced-section">Carregando...</div>
                    <div v-else-if="Object.keys(tabelas).length === 0" class="alert alert-warning spaced-section">Nenhuma tabela encontrada.</div>

                    <div v-else class="table-responsive spaced-section">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>Tabela</th>
                                    <th>Quantidade de Registros</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="(info, key) in tabelas" :key="key">
                                    <td>[[ labels[key] || key ]]</td>
                                    <td>
                                        [[ info.count ]]
                                        <span v-if="info.percentage" class="text-muted">([[ info.percentage ]])</span>
                                    </td>
                                    <td>[[ info.status ]]</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <script>
            new Vue({
                el: '#app',
                delimiters: ['[[', ']]'],
                data: {
                    tabelas: {},
                    loading: true,
                    erro: false,
                    lastUpdate: "",
                    theme: 'dark',
                    logoLight: "{{ url_for('static', filename='images/logo.png') }}",
                    logoDark: "{{ url_for('static', filename='images/logo.png') }}",
                    labels: {
                        "multas_mensagens_erro_nao_tratadas": "MensagensComErro",
                        "multas_mensagens_erro_tratadas": "MensagensErroCorrigidas",
                        "renainf_percentual_da_meta": "RenainfMultas",
                        "renainf_d_percentual_da_meta": "RenainfDebitos",
                        "serpro_dia_semmulta_percentual_cpf": "Query6PLACA",
                        "serpro_dia_semmulta_percentual_cnpj": "Query6CNPJ",
                        "multaANTT_last5day": "MultaANTT_Ultimos5Dias"
                    }
                },
                computed: {
                    logoSrc() {
                        return this.theme === 'dark' ? this.logoDark : this.logoLight;
                    }
                },
                methods: {
                    toggleTheme() {
                        this.theme = this.theme === 'light' ? 'dark' : 'light';
                        localStorage.setItem('theme', this.theme);
                        document.body.className = `${this.theme}-mode`;
                    },
                    applyTheme() {
                        this.theme = localStorage.getItem('theme') || 'dark';
                        document.body.className = `${this.theme}-mode`;
                    },
                    fetchData() {
                        this.loading = true;
                        this.erro = false;
                        axios.get("{{ url_for('queryes.queryes') }}")
                            .then(response => {
                                const data = response.data;
                                if (data && data.data) {
                                    this.tabelas = data.data;
                                    this.lastUpdate = data.timestamp || "";
                                } else {
                                    this.tabelas = {};
                                    this.lastUpdate = "";
                                }
                                this.loading = false;
                            })
                            .catch(() => {
                                this.erro = true;
                                this.loading = false;
                                this.tabelas = {};
                            });
                    }
                },
                mounted() {
                    this.applyTheme();
                    this.fetchData();
                    setInterval(() => {
                        this.fetchData();
                    }, 30000);
                }
            });
            </script>
        </body>
        </html>
        """, db_hostname=db_hostname)
