document.addEventListener('DOMContentLoaded', () => {
    setupFormListeners();
    fetchSchedules();
});

function setupFormListeners() {
    document.getElementById('intervalForm')?.addEventListener('submit', e => {
        e.preventDefault();
        const intervalo = parseInt(document.getElementById('current_interval').value);
        if (isNaN(intervalo) || intervalo <= 0) return alert("Intervalo inválido!");
        fetch(URLS.setInterval, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ interval: intervalo })
        }).then(r => r.json()).then(data => { alert(data.message || data.error); location.reload(); });
    });

    document.getElementById('excludedForm')?.addEventListener('submit', e => {
        e.preventDefault();
        const selectedServices = Array.from(document.querySelectorAll('input[name="excluded_services"]:checked')).map(c => c.value);
        fetch(URLS.admin, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ form_type: 'excludedForm', excluded_services: selectedServices })
        }).then(r => r.json()).then(data => { alert(data.message || data.error); });
    });
}

let currentSchedules = {};

function fetchSchedules() {
    fetch(URLS.getSchedule)
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
    fetch(URLS.updateSchedule, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tool, schedule })
    }).then(() => fetchSchedules()).catch(console.error);
}

function loadAlertConfig() {
    fetch(URLS.alertConfig).then(r => r.json()).then(data => {
        if (document.getElementById('toggleTelegramLogs')) document.getElementById('toggleTelegramLogs').checked = data.telegram === 'enabled';
        if (document.getElementById('toggleTeamsLogs')) document.getElementById('toggleTeamsLogs').checked = data.teams === 'enabled';
    }).catch(console.error);
}

function toggleAlertState() {
    const payload = {
        telegram: document.getElementById('toggleTelegramLogs')?.checked,
        teams: document.getElementById('toggleTeamsLogs')?.checked
    };
    fetch(URLS.alertToggle, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    }).then(r => r.json()).then(() => fetchSchedules()).catch(console.error);
}