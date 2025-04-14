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
                #query {
                    font-size: 2.5rem;
                    font-weight: bold;
                }
                .table-responsive {
                    max-width: 100%;
                    overflow-x: auto;
                }
                table {
                    width: 100%;
                    table-layout: fixed;
                }
                td, th {
                    text-align: center;
                    height: 80px;
                    vertical-align: middle;
                    font-size: 1.5rem;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }
            </style>
        </head>
        <body>
            <!-- Header -->
            <nav class="navbar navbar-light bg-white shadow-sm px-4 flex justify-between items-center h-10 overflow-hidden">
                <!-- Logo + Título -->
                <div class="flex items-center">
                    <img src="https://assets.lwtecnologia.com.br/public/OFICIAL_BLACK.png" alt="Logo" height=25 me-3" />
                    <!--<h5 class="text-xl font-medium leading-none">Monitoramento</h5>-->
                </div>

                <div id="last-update" class="last-update me-2 hidden">
                    <strong>Última atualização:</strong>
                    <div id="last-update-time" class="fs-5"></div>
                </div>

                <div class="buttons flex gap-2">
                    <a href="{{ url_for('incidentes.incidentes') }}" class="btn btn-gray text-sm px-3 py-1">Histórico de incidentes</a>
                    <a href="{{ url_for('home.home') }}" class="btn btn-gray text-sm px-3 py-1">Home</a>
                </div>
            </nav>
            <div class="container mt-4">
                <div class="header-container">
                    <div class="d-flex flex-column">
                        <h4 class="mb-3">Banco de Dados - {{ db_hostname }}</h4>
                    </div>

                </div>
                <br>
                <div id="loading" class="alert alert-info spaced-section">Carregando...</div>
                <div id="query" class="table-responsive spaced-section"></div>
                <div id="erro" class="alert alert-danger">Erro ao buscar os dados do banco de dados.</div>
            </div>
            <script>
            $('#erro').hide();
            function fetchQuery() {
                $.get("{{ url_for('query.query') }}", function(data) {
                    if (data.results) {
                        $('#loading').hide();

                        if (data.timestamp) {
                            $('#last-update-time').text(data.timestamp);
                            $('#last-update').show();
                        } else {
                            $('#last-update').hide();
                        }
                        let html = `
                            <table class="table table-striped" id="service-table">
                                <thead>
                                    <tr>
                                        <th>Tabela</th>
                                        <th>Quantidade de Registros</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>`;
                        const labels = {
                            "lock_no_banco": "LOCK NO BANCO",
                            "multas_mensagens_erro_nao_tratadas": "multas mensagensErro nao tratadas",
                            "multas_mensagens_erro_tratadas": "multas mensagensErro já tratadas"
                        };
                        for (const key in data.results) {
                            html += `
                                <tr>
                                    <td>${labels[key] || key}</td>
                                    <td>${data.results[key].count}</td>
                                    <td>${data.results[key].status}</td>
                                </tr>`;
                        }
                        html += `</tbody></table>`;
                        $('#query').html(html);
                    } else {
                        $('#last-update').hide();
                    }
                }).fail(function() {
                    $('#loading').hide();
                    $('#erro').show();
                    $('#last-update').hide();
                });   
            }
            setInterval(fetchQuery, 30000);  // Atualiza a cada 30 segundos
            fetchQuery();  // Chama uma vez no início para carregar imediatamente
            </script>
        </body>
        </html>
        """, db_hostname=db_hostname)
