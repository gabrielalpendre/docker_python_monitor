from functions.services import get_server_info
from flask import Blueprint, render_template_string, jsonify, request
import os
import json

FLASK_PREFIX = os.getenv('PREFIX', '')
bp_reports = Blueprint('reports', __name__)
REPORTS_DIR = os.getenv('REPORTS_DIR', 'files/reports')


@bp_reports.route(f'{FLASK_PREFIX}/reports', methods=['GET'])
def reports():
    server_hostname, _ = get_server_info()
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
    <title>Relatorios</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet" />
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/vue@2.6.14/dist/vue.min.js"></script>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <link rel="icon" type="image/x-icon" href="{{ url_for('static', filename='images/favicon.ico') }}">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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
            <label for="reportStack" class="form-label">Stack:</label>
            <select id="reportStack" class="form-select form-select-sm">
                <option value="all">Todas</option>
            </select>
        </div>
        <div class="col-md-2">
            <label for="reportDate" class="form-label">Data:</label>
            <select id="reportDate" class="form-select form-select-sm"></select>
        </div>
        <div class="col-md-2">
            <label for="startHour" class="form-label">Hora Início:</label>
            <input type="time" id="startHour" class="form-control form-control-sm">
        </div>
        <div class="col-md-2">
            <label for="endHour" class="form-label">Hora Fim:</label>
            <input type="time" id="endHour" class="form-control form-control-sm">
        </div>
        <div class="col-md-1 d-flex align-items-end">
            <button id="generateBtn" class="btn btn-primary btn-sm w-100">Gerar</button>
        </div>
        <div class="col-md-1 d-flex align-items-end">
            <div class="form-check form-switch">
                <input class="form-check-input" type="checkbox" id="autoRefresh">
                <label class="form-check-label" for="autoRefresh">Auto Refresh</label>
            </div>
        </div>
    </div>
</div>

<div class="container mb-4">
    <div id="chartContainer" class="chart-flex" style="display:none;"></div>
</div>

<script>
const available = {{ available_list | tojson }};
const reportType = document.getElementById('reportType');
const reportDate = document.getElementById('reportDate');
const reportStack = document.getElementById('reportStack');
const startHour = document.getElementById('startHour');
const endHour = document.getElementById('endHour');
const autoRefreshCheckbox = document.getElementById('autoRefresh');

let autoRefreshInterval = null;

function populateDates(type, keepDate=false) {
    const prevDate = reportDate.value;
    reportDate.innerHTML = '';
    (available[type] || []).forEach(date => {
        const opt = document.createElement('option');
        opt.value = date;
        opt.textContent = date;
        reportDate.appendChild(opt);
    });
    if (keepDate && prevDate && (available[type] || []).includes(prevDate)) {
        reportDate.value = prevDate;
    }
    populateStacks(type);
}

function populateStacks(type){
    reportStack.innerHTML = '<option value="all">Todas</option>';
    if(type==='services'){
        const date = reportDate.value;
        if(!date) return;
        fetch(`/reports/data?file=${date}_services_report.json`)
            .then(r => r.json())
            .then(data => {
                const stacks = [...new Set(
                    data.flatMap(e => e.data.map(d => {
                        const parts = d.Service.split('_');
                        return parts.length > 1 ? parts.slice(0,-1).join('_') : d.Service;
                    }))
                )];
                reportStack.innerHTML = '<option value="all">Todas</option>';
                stacks.forEach(s => {
                    const opt = document.createElement('option');
                    opt.value = s;
                    opt.textContent = s;
                    reportStack.appendChild(opt);
                });
            });
        reportStack.parentElement.style.display='block';
    } else {
        reportStack.parentElement.style.display='none';
    }
}

populateDates('services');
reportType.addEventListener('change', ()=>populateDates(reportType.value, true));
reportDate.addEventListener('change', ()=>populateStacks(reportType.value));

const body = document.body;
const themeIcon = document.getElementById('themeIcon');

function updateAllChartsTheme() {
    const charts = Chart.instances;
    Object.values(charts).forEach(chart => refreshChartColors(chart));
}

function applyTheme(theme) {
    body.classList.remove('dark-mode', 'light-mode');
    body.classList.add(`${theme}-mode`);
    localStorage.setItem('theme', theme);
    themeIcon.className = theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon';
}

function refreshChartColors(chart) {
    const isDark = body.classList.contains('dark-mode');
    const axisColor = isDark ? '#eee' : '#333';
    const gridColor = isDark ? 'rgba(0,0,0,0.05)' : 'rgba(255,255,255,0.05)';
    const chartBg = isDark ? 'rgba(40,40,40,0.8)' : 'rgba(255,255,255,0.95)';
    chart.options.scales.x.ticks.color = axisColor;
    chart.options.scales.x.grid.color = gridColor;
    chart.options.scales.y.ticks.color = axisColor;
    chart.options.scales.y.grid.color = gridColor;
    chart.options.plugins.title.color = axisColor;
    chart.options.plugins.legend.labels.color = axisColor;
    const bgPlugin = chart.config.plugins.find(p => p.id === 'customBackground');
    if (bgPlugin) {
        bgPlugin.beforeDraw = chart => {
            const {ctx, chartArea} = chart;
            if(!chartArea) return;
            ctx.save();
            ctx.fillStyle = chartBg;
            ctx.fillRect(chartArea.left, chartArea.top, chartArea.right - chartArea.left, chartArea.bottom - chartArea.top);
            ctx.restore();
        };
    }
    chart.update('none');
}

applyTheme(localStorage.getItem('theme') || 'dark');
document.getElementById('toggleTheme').addEventListener('click', () => {
    const newTheme = body.classList.contains('dark-mode') ? 'light' : 'dark';
    applyTheme(newTheme);
    updateAllChartsTheme();
});

document.getElementById('generateBtn').addEventListener('click', generateReport);

autoRefreshCheckbox.addEventListener('change', ()=>{
    if(autoRefreshCheckbox.checked){
        reportDate.value = available[reportType.value][0] || '';
        reportDate.disabled = true;
        startHour.disabled = true;
        endHour.disabled = true;

        const updateLast5Min = ()=>{
            const now = new Date();
            const past = new Date(now.getTime()-5*60000);
            startHour.value=`${String(past.getHours()).padStart(2,'0')}:${String(past.getMinutes()).padStart(2,'0')}`;
            endHour.value=`${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`;
        };
        updateLast5Min();
        generateReport();
        if(autoRefreshInterval) clearInterval(autoRefreshInterval);
        autoRefreshInterval = setInterval(()=>{
            updateLast5Min();
            generateReport();
        }, 60000);
    } else {
        reportDate.disabled = false;
        startHour.disabled = false;
        endHour.disabled = false;
        if(autoRefreshInterval) clearInterval(autoRefreshInterval);
    }
});

function generateReport() {
    const type = reportType.value;
    const date = reportDate.value;
    const stackSel = reportStack.value;
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
        .then(rawData=>{
            if(rawData.error) return alert(rawData.error);

            const chartContainer = document.getElementById('chartContainer');
            chartContainer.innerHTML=''; 
            chartContainer.style.display='flex';
            chartContainer.style.flexDirection='column';
            chartContainer.style.gap='20px';

            const filteredData = rawData.filter(e=>{
                const [h,m] = e.timestamp.slice(11,16).split(':').map(Number);
                const total = h*60+m;
                return total >= startH*60+startM && total <= endH*60+endM;
            });

            if(filteredData.length===0) return alert('Nenhum dado encontrado no intervalo selecionado.');

            const timestamps = [];
            const dataMap = {};
            filteredData.forEach(e=>{
                const t = e.timestamp.slice(11,16);
                dataMap[t] = e.data;
            });

            const sortedTimes = Object.keys(dataMap).sort();
            let lastTime = startH*60+startM-5;
            sortedTimes.forEach(t=>{
                const [h,m] = t.split(':').map(Number);
                const current = h*60+m;
                let diff = current - lastTime;
                while(diff>5){
                    lastTime += 5;
                    const lh = Math.floor(lastTime/60);
                    const lm = lastTime%60;
                    const ts = `${String(lh).padStart(2,'0')}:${String(lm).padStart(2,'0')}`;
                    timestamps.push(ts);
                    dataMap[ts]=[];
                    diff = current - lastTime;
                }
                timestamps.push(t);
                lastTime=current;
            });

            if(type==='server'){
                const wrapper = document.createElement('div');
                wrapper.style.display='flex';
                wrapper.style.alignItems='center';
                wrapper.style.gap='10px';

                const cpuDiv = document.createElement('div');
                cpuDiv.className='chart-box';
                const cpuCanvas = document.createElement('canvas');
                cpuCanvas.id='cpuChart';
                cpuDiv.appendChild(cpuCanvas);

                // SLO calculado com os dados filtrados pelo horário
                const sloDiv = addSLOIndicator(rawData, type); 
                wrapper.appendChild(cpuDiv);
                wrapper.appendChild(sloDiv);
                chartContainer.appendChild(wrapper);

                // Prepara dados do chart
                const values = filteredData.map(e=>parseFloat(e.data?.[0]?.Actual?.replace(/[^\d.]/g,'')||0));
                const timestampsFiltered = filteredData.map(e=>e.timestamp.slice(11,16));
                const dataset = { "{{ server_hostname }}": values };

                renderChart('cpuChart','Server Load (Actual)',timestampsFiltered,dataset,true);
            } else {
                const stacks = [...new Set(rawData.flatMap(e => e.data.map(d => {
                    const parts = d.Service.split('_');
                    return parts.length > 1 ? parts.slice(0,-1).join('_') : d.Service;
                })))];

                stacks.forEach(stack => {
                    if(stackSel !== 'all' && stackSel !== stack) return;

                    const stackDiv = document.createElement('div');
                    stackDiv.className='chart-stack-wrapper';
                    stackDiv.style.display='flex';
                    stackDiv.style.gap='20px';
                    stackDiv.style.alignItems='flex-start';

                    const chartsCol = document.createElement('div');
                    chartsCol.className='chart-col';
                    chartsCol.style.display='flex';
                    chartsCol.style.flexDirection='column';
                    chartsCol.style.gap='20px';

                    const chartsRow = document.createElement('div');
                    chartsRow.style.display='flex';
                    chartsRow.style.gap='20px';

                    const cpuDiv = document.createElement('div');
                    cpuDiv.className='chart-box';
                    cpuDiv.style.flex='1';
                    const cpuCanvas = document.createElement('canvas');
                    cpuCanvas.id = `cpuChart_${stack}`;
                    cpuDiv.appendChild(cpuCanvas);

                    const memDiv = document.createElement('div');
                    memDiv.className='chart-box';
                    memDiv.style.flex='1';
                    const memCanvas = document.createElement('canvas');
                    memCanvas.id = `memChart_${stack}`;
                    memDiv.appendChild(memCanvas);

                    chartsRow.appendChild(cpuDiv);
                    chartsRow.appendChild(memDiv);
                    chartsCol.appendChild(chartsRow);
                    stackDiv.appendChild(chartsCol);

                    const sloDiv = addSLOIndicator(rawData, type, stack); // SLO para o dia inteiro
                    sloDiv.style.alignSelf='center';
                    stackDiv.appendChild(sloDiv);

                    chartContainer.appendChild(stackDiv);

                    const cpuData = {}, memData = {};
                    const services = [...new Set(filteredData.flatMap(e => e.data.filter(d => {
                        const sName = d.Service.split('_').length > 1 ? d.Service.split('_').slice(0,-1).join('_') : d.Service;
                        return sName === stack;
                    }).map(d => d.Service)))];

                    services.forEach(s => { cpuData[s] = {}; memData[s] = {}; });

                    timestamps.forEach(ts => {
                        filteredData.forEach(e => {
                            if(e.timestamp.slice(11,16) === ts){
                                e.data.forEach(d => {
                                    const sName = d.Service.split('_').length > 1 ? d.Service.split('_').slice(0,-1).join('_') : d.Service;
                                    if(sName !== stack) return;
                                    cpuData[d.Service][ts] = parseFloat(d["CPU Usage"]?.replace(/[^\d.]/g,'')||0);
                                    memData[d.Service][ts] = parseFloat(d["Memory Usage"]?.replace(/[^\d.]/g,'')||0);
                                });
                            }
                        });
                        services.forEach(s => {
                            if(cpuData[s][ts]===undefined) cpuData[s][ts]=0;
                            if(memData[s][ts]===undefined) memData[s][ts]=0;
                        });
                    });

                    const cpuFilled = {}, memFilled = {};
                    services.forEach(s => {
                        cpuFilled[s] = timestamps.map(t=>cpuData[s][t]);
                        memFilled[s] = timestamps.map(t=>memData[s][t]);
                    });

                    renderChart(cpuCanvas.id, 'Uso de CPU (%)', timestamps, cpuFilled);
                    renderChart(memCanvas.id, 'Uso de Memória (MiB)', timestamps, memFilled);
                });
            }
        });
}

// Ajuste do SLO para considerar os dados da data selecionada
function addSLOIndicator(dayData, type, stack=null){
    if(type === 'server'){
        const values = [];

        dayData.forEach(e=>{
            e.data.forEach(d=>{
                values.push(parseFloat(d.Actual?.replace(/[^\d.]/g,'')||0));
            });
        });

        const total = values.length;
        const greenCount = values.filter(v => v<=10).length;
        const percent = total>0 ? Math.round((greenCount/total)*100) : 0;

        let color='green';
        if(percent < 85) color='red';
        else if(percent < 100) color='gold';

        const sloDiv = document.createElement('div');
        sloDiv.className='slo-indicator';
        sloDiv.innerHTML = `
            <strong>SLO Load</strong>
            <div style="color:${color};font-size:18px;font-weight:bold;">${percent}</div>
        `;
        return sloDiv;
    }

    // --- Serviços ---
    const svcMap = {};

    dayData.forEach(e=>{
        e.data.forEach(d=>{
            const fullSvc = d.Service;
            const sName = fullSvc.split('_').length>1 ? fullSvc.split('_').slice(0,-1).join('_') : fullSvc;
            if(stack && sName !== stack) return;

            if(!svcMap[fullSvc]) svcMap[fullSvc] = { healthy: 0, total: 0 };

            const repStr = d.Replicas || '';
            const m = repStr.match(/(\d+)\s*\/\s*(\d+)/);
            if(m){
                const avail = parseInt(m[1], 10);
                const desired = parseInt(m[2], 10);
                if(desired > 0 && avail >= desired) svcMap[fullSvc].healthy++;
                svcMap[fullSvc].total++;
            } else {
                svcMap[fullSvc].total++;
            }
        });
    });

    const sloDiv = document.createElement('div');
    sloDiv.className='slo-indicator';
    sloDiv.style.alignItems='flex-start';
    sloDiv.style.width='fit-content';
    sloDiv.style.maxWidth='320px';
    sloDiv.style.padding='8px 12px';
    sloDiv.style.borderRadius='10px';
    sloDiv.style.boxShadow='0 2px 6px rgba(0,0,0,0.2)';
    sloDiv.style.background='rgba(255,255,255,0.05)';
    sloDiv.style.fontSize='13px';
    sloDiv.style.wordBreak='break-word';

    const title = document.createElement('strong');
    title.textContent = 'SLO Disponibilidade';
    title.style.marginBottom='6px';
    sloDiv.appendChild(title);

    const list = document.createElement('div');
    list.style.display='flex';
    list.style.flexDirection='column';
    list.style.gap='3px';
    list.style.width='100%';

    const services = Object.keys(svcMap).sort();
    if(services.length === 0){
        const p = document.createElement('p');
        p.textContent = 'Nenhum serviço encontrado';
        p.style.margin='0';
        list.appendChild(p);
    } else {
        services.forEach(svc => {
            const { healthy, total } = svcMap[svc];
            const percent = total > 0 ? Math.round((healthy / total) * 100) : 0;
            let color = 'green';
            if(percent < 85) color = 'red';
            else if(percent < 100) color = 'gold';

            const row = document.createElement('div');
            row.style.display='flex';
            row.style.justifyContent='space-between';
            row.style.alignItems='center';
            row.style.gap='10px';
            row.style.padding='2px 0';
            row.style.borderBottom='1px solid rgba(255,255,255,0.05)';

            const name = document.createElement('span');
            name.textContent = svc;
            name.style.flex='1';
            name.style.overflowWrap='anywhere';

            const val = document.createElement('span');
            val.textContent = `${percent}`;
            val.style.fontWeight='bold';
            val.style.color=color;

            row.appendChild(name);
            row.appendChild(val);
            list.appendChild(row);
        });
    }

    sloDiv.appendChild(list);
    return sloDiv;
}

// renderChart com cor do último ponto na legenda/rodapé
function renderChart(canvasId, label, labels, datasetsObj, isServer=false){
    const ctx = document.getElementById(canvasId).getContext('2d');
    const isDark = body.classList.contains('dark-mode');
    const chartBg = isDark ? 'rgba(40,40,40,0.8)' : 'rgba(255,255,255,0.95)';
    const axisColor = isDark ? '#eee' : '#333';
    const gridColor = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)';

    const datasets = Object.keys(datasetsObj).map(k => {
        const values = datasetsObj[k];
        const pointColors = values.map(v=>{
            if(isServer){
                return v<=10 ? 'rgb(0,200,0)' : v<=30 ? 'rgb(255,215,0)' : 'rgb(200,0,0)';
            } else if(label.includes('CPU')){
                return v<=80 ? 'rgb(0,200,0)' : v<=100 ? 'rgb(255,215,0)' : 'rgb(200,0,0)';
            } else if(label.includes('Memória')){
                return v<=512 ? 'rgb(0,200,0)' : v<=1024 ? 'rgb(255,215,0)' : 'rgb(200,0,0)';
            } else return 'rgb(0,0,255)';
        });
        const lastColor = pointColors[pointColors.length-1]; // cor do último ponto

        return {
            label: k,
            data: values,
            borderColor: 'rgba(128,128,128,0.6)',
            backgroundColor: lastColor,
            pointBackgroundColor: pointColors,
            pointBorderColor: pointColors,
            borderWidth: 1,
            fill: false,
            tension: 0.4,
            pointRadius: 3
        };
    });

    return new Chart(ctx, {
        type:'line',
        data:{labels,datasets},
        options:{
            responsive:true,
            plugins:{
                legend:{
                    position:'bottom',
                    labels:{ color:axisColor }
                },
                title:{ display:true, text:label, color:axisColor },
                tooltip:{
                    titleColor:axisColor,
                    bodyColor:axisColor,
                    callbacks:{ label: ctx => `${ctx.dataset.label}: ${ctx.formattedValue}` }
                }
            },
            scales:{
                x:{ ticks:{color:axisColor}, grid:{color:gridColor} },
                y:{ beginAtZero:true, ticks:{color:axisColor}, grid:{color:gridColor} }
            }
        },
        plugins:[{
            id:'customBackground',
            beforeDraw:chart=>{
                const {ctx, chartArea}=chart;
                if(!chartArea) return;
                ctx.save();
                ctx.fillStyle=chartBg;
                ctx.fillRect(chartArea.left, chartArea.top, chartArea.right-chartArea.left, chartArea.bottom-chartArea.top);
                ctx.restore();
            }
        }]
    });
}

window.addEventListener('load',()=>{
    const now=new Date();
    const past=new Date(now.getTime()-5*60000);
    startHour.value=`${String(past.getHours()).padStart(2,'0')}:${String(past.getMinutes()).padStart(2,'0')}`;
    let newH = now.getHours() + 1;
    if(newH>23) newH=23;
    endHour.value=`${String(newH).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`;
    reportType.value='services';
    reportDate.value=(available['services'][0]||'');
    populateStacks('services');
    setTimeout(generateReport,500);
});
</script>
</body>
</html>
""", server_hostname=server_hostname, available_list=available_list)


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
