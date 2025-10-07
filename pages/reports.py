from flask import Blueprint, render_template_string, jsonify, request
import os
import json

FLASK_PREFIX = os.getenv('PREFIX', '')
bp_reports = Blueprint('reports', __name__)
REPORTS_DIR = os.getenv('REPORTS_DIR', 'files/reports')


@bp_reports.route(f'{FLASK_PREFIX}/reports', methods=['GET'])
def reports():
    available = {'services': set(), 'server': set()}
    for f in os.listdir(REPORTS_DIR):
        if f.endswith('_services_report.json'):
            date = f.split('_')[0]
            available['services'].add(date)
        elif f.endswith('_server_report.json'):
            date = f.split('_')[0]
            available['server'].add(date)

    available_list = {k: sorted(list(v), reverse=True) for k, v in available.items()}

    return render_template_string(r"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <title>Histórico de Erros</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet" />
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/vue@2.6.14/dist/vue.min.js"></script>
        <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
        <link rel="icon" type="image/x-icon" href="{{ url_for('static', filename='images/favicon.ico') }}">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body.dark { background-color: #121212; color: #eee; }
            body.light { background-color: #f5f5f5; color: #333; }
            .container-section { 
                background-color: var(--section-bg);
                padding: 20px;
                border-radius: 8px;
                transition: background-color 0.3s;
                margin-bottom: 30px;
            }
            body.dark .container-section { --section-bg: #2b2b2b; }
            body.light .container-section { --section-bg: #e0e0e0; }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-light shadow-sm px-4" style="height:60px;">
            <div class="d-flex align-items-center gap-2">
                <img src="{{ url_for('static', filename='images/logo.png') }}" alt="Logo" height="25" />
            </div>
            <div class="buttons d-flex gap-2">
                <a href="{{ url_for('incidentes.incidentes') }}" class="btn btn-secondary btn-sm">Histórico de incidentes</a>
                <a href="{{ url_for('home.home') }}" class="btn btn-secondary btn-sm">Home</a>
                <button id="toggleTheme" class="btn btn-secondary ms-3" title="Alternar tema">
                    <i id="themeIcon" class="bi"></i>
                </button>
            </div>
        </nav>

        <!-- Formulário -->
        <div class="container mt-4 container-section">
            <h4>Gerar Relatório</h4>
            <div class="row mb-3">
                <div class="col-md-2">
                    <label for="reportType" class="form-label">Tipo de Relatório:</label>
                    <select id="reportType" class="form-select form-select-sm">
                        <option value="services">Serviços</option>
                        <option value="server">Servidor</option>
                    </select>
                </div>
                <div class="col-md-2">
                    <label for="reportDate" class="form-label">Data:</label>
                    <select id="reportDate" class="form-select form-select-sm"></select>
                </div>
                <div class="col-md-2">
                    <label for="reportService" class="form-label">Serviço:</label>
                    <select id="reportService" class="form-select form-select-sm">
                        <option value="all">Todos</option>
                    </select>
                </div>
                <div class="col-md-2">
                    <label for="startHour" class="form-label">Hora Início:</label>
                    <input type="time" id="startHour" class="form-control form-control-sm">
                </div>
                <div class="col-md-2">
                    <label for="endHour" class="form-label">Hora Fim:</label>
                    <input type="time" id="endHour" class="form-control form-control-sm">
                </div>
                <div class="col-md-2 d-flex align-items-end">
                    <button id="generateBtn" class="btn btn-primary btn-sm w-100">Gerar</button>
                </div>
            </div>
        </div>

        <!-- Gráficos -->
        <div class="container mb-4">
            <div id="chartContainer" class="chart-flex" style="display:none;">
                <div class="chart-box">
                    <canvas id="cpuChart"></canvas>
                </div>
                <div class="chart-box">
                    <canvas id="memChart"></canvas>
                </div>
            </div>
        </div>

        <script>
        const available = {{ available_list | tojson }};
        const reportType = document.getElementById('reportType');
        const reportDate = document.getElementById('reportDate');
        const reportService = document.getElementById('reportService');
        const startHour = document.getElementById('startHour');
        const endHour = document.getElementById('endHour');

        const cpuChartCanvas = document.getElementById('cpuChart');
        const memChartCanvas = document.getElementById('memChart');
        let cpuChart, memChart;

        function populateDates(type) {
            reportDate.innerHTML = '';
            (available[type] || []).forEach(date => {
                const opt = document.createElement('option');
                opt.value = date;
                opt.textContent = date;
                reportDate.appendChild(opt);
            });
            populateServices(type);
        }

        function populateServices(type){
            if(type === 'services'){
                reportService.innerHTML = '<option value="all">Todos</option>';
                const date = reportDate.value;
                if(date){
                    fetch(`/reports/data?file=${date}_services_report.json`)
                        .then(r=>r.json())
                        .then(data=>{
                            reportService.innerHTML = '<option value="all">Todos</option>'; // <-- limpar aqui!
                            const services = [...new Set(data.flatMap(e=>e.data.map(d=>d.Service)))];
                            services.forEach(s=>{
                                const opt = document.createElement('option');
                                opt.value = s;
                                opt.textContent = s;
                                reportService.appendChild(opt);
                            });
                        });
                }
                reportService.parentElement.style.display='block';
            } else {
                reportService.parentElement.style.display='none';
            }
        }

        populateDates('services');
        reportType.addEventListener('change', ()=>populateDates(reportType.value));
        reportDate.addEventListener('change', ()=>populateServices(reportType.value));

        // Tema
        const body = document.body;
        const themeIcon = document.getElementById('themeIcon');
        function applyTheme(theme) {
            body.classList.remove('dark','light');
            body.classList.add(theme);
            localStorage.setItem('theme', theme);
            themeIcon.className = theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon';
        }
        applyTheme(localStorage.getItem('theme') || 'dark');
        document.getElementById('toggleTheme').addEventListener('click', () => {
            const newTheme = body.classList.contains('dark') ? 'light' : 'dark';
            applyTheme(newTheme);
        });
        startHour.addEventListener('input', () => {
            if(startHour.value){
                const [h,m] = startHour.value.split(':').map(Number);
                endHour.min = `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}`;
                let newH = h+1; if(newH>23) newH=23;
                endHour.value = `${String(newH).padStart(2,'0')}:${String(m).padStart(2,'0')}`;
            } else { endHour.min="00:00"; endHour.value=""; }
        });

        document.getElementById('generateBtn').addEventListener('click', generateReport);

        function generateReport() {
            const type = reportType.value;
            const date = reportDate.value;
            const serviceSel = reportService.value;
            const start = startHour.value;
            const end = endHour.value;
            if(!date) return alert('Selecione uma data existente.');
            if(!start||!end) return alert('Informe o intervalo de horas.');
            const [startH,startM]=start.split(':').map(Number);
            const [endH,endM]=end.split(':').map(Number);
            if(endH*60+endM<=startH*60+startM) return alert('A hora final deve ser maior que a inicial.');
            const file = `${date}_${type}_report.json`;

            fetch(`/reports/data?file=${file}`)
                .then(r=>r.json())
                .then(data=>{
                    if(data.error) return alert(data.error);
                    document.getElementById('chartContainer').style.display='flex';

                    const timestamps = data.map(e=>e.timestamp.slice(11,16));

                    if(type==='server'){
                        cpuChartCanvas.style.display='block';
                        memChartCanvas.style.display='none';
                        const values = data.map(e=>{
                            const val=e.data[0]?.Actual||0;
                            return parseFloat(val.replace(/[^\d.]/g,''))||0;
                        });
                        renderChart('cpuChart','Server Actual',timestamps,{'Load do Server':values});
                    } else {
                        cpuChartCanvas.style.display='block';
                        memChartCanvas.style.display='block';
                        const services = serviceSel==='all' ? [...new Set(data.flatMap(e=>e.data.map(d=>d.Service)))] : [serviceSel];
                        const cpuData={}, memData={};
                        services.forEach(s=>{cpuData[s]=[]; memData[s]=[];});
                        data.forEach(entry=>{
                            entry.data.forEach(d=>{
                                if(services.includes(d.Service)){
                                    const cpu=parseFloat(d["CPU Usage"]?.replace(/[^\d.]/g,'')||0);
                                    const mem=parseFloat(d["Memory Usage"]?.replace(/[^\d.]/g,'')||0);
                                    cpuData[d.Service].push(cpu);
                                    memData[d.Service].push(mem);
                                }
                            });
                        });
                        renderChart('cpuChart','Uso de CPU (%)',timestamps,cpuData);
                        renderChart('memChart','Uso de Memória (MiB)',timestamps,memData);
                    }
                });
        }

        // Pré-carregar último relatório services últimos 30 minutos
        window.addEventListener('load', ()=>{
            const now = new Date();
            const past = new Date(now.getTime() - 30*60000); // 30 minutos atrás
            startHour.value = `${String(past.getHours()).padStart(2,'0')}:${String(past.getMinutes()).padStart(2,'0')}`;
            endHour.value = `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`;
            reportType.value = 'services';
            reportDate.value = (available['services'][0] || '');
            populateServices('services');
            setTimeout(generateReport, 500); // dá tempo de popular serviços antes
        });

        function renderChart(canvasId,label,labels,datasetsObj){
            const ctx=document.getElementById(canvasId).getContext('2d');
            const datasets=Object.keys(datasetsObj).map(k=>({label:k,data:datasetsObj[k],fill:false,borderWidth:2}));
            if(canvasId==='cpuChart'&&cpuChart) cpuChart.destroy();
            if(canvasId==='memChart'&&memChart) memChart.destroy();
            const chart=new Chart(ctx,{type:'line',data:{labels,datasets},options:{responsive:true,plugins:{legend:{position:'bottom'}},scales:{y:{beginAtZero:true}}}});
            if(canvasId==='cpuChart') cpuChart=chart; else memChart=chart;
        }
        </script>

    </body>
    </html>
    """, available_list=available_list)


@bp_reports.route(f'{FLASK_PREFIX}/reports/data', methods=['GET'])
def reports_data():
    filename = request.args.get('file')
    if not filename:
        return jsonify({'error':'Arquivo não especificado'}),400
    filepath = os.path.join(REPORTS_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({'error':f'Arquivo {filename} não encontrado'}),404
    with open(filepath,'r',encoding='utf-8') as f:
        data=json.load(f)
    return jsonify(data)
