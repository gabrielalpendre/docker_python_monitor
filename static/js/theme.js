document.addEventListener('DOMContentLoaded', () => {
    const body = document.body;
    const toggleBtn = document.getElementById('toggleTheme');
    const themeIcon = document.getElementById('themeIcon');

    function applyTheme(theme) {
        body.classList.remove('dark-mode', 'light-mode');
        body.classList.add(theme + '-mode');
        localStorage.setItem('theme', theme);

        if (themeIcon) {
            themeIcon.className = theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon';
        }
    }

    const savedTheme = localStorage.getItem('theme') || 'dark';
    applyTheme(savedTheme);

    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const newTheme = body.classList.contains('dark-mode') ? 'light' : 'dark';
            applyTheme(newTheme);

            if (typeof updateAllChartsTheme === 'function') {
                updateAllChartsTheme();
            }
        });
    }
});