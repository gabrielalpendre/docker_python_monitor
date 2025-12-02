document.addEventListener('DOMContentLoaded', function () {
    const toggleThemeButton = document.getElementById('toggleTheme');
    const themeIcon = document.getElementById('themeIcon');

    function applyTheme(theme) {
        if (theme === 'dark') {
            document.documentElement.classList.add('dark-mode');
            if (themeIcon) {
                themeIcon.classList.remove('bi-sun-fill');
                themeIcon.classList.add('bi-moon-fill');
            }
        } else {
            document.documentElement.classList.remove('dark-mode');
            if (themeIcon) {
                themeIcon.classList.remove('bi-moon-fill');
                themeIcon.classList.add('bi-sun-fill');
            }
        }
    }

    // Aplica o tema e o ícone corretos no carregamento da página
    const currentTheme = localStorage.getItem('theme') || 'light';
    applyTheme(currentTheme);

    // Adiciona o evento de clique ao botão
    if (toggleThemeButton) {
        toggleThemeButton.addEventListener('click', function (e) {
            e.preventDefault();
            const newTheme = document.documentElement.classList.contains('dark-mode') ? 'light' : 'dark';
            localStorage.setItem('theme', newTheme);
            applyTheme(newTheme);
            window.dispatchEvent(new CustomEvent('theme:change', { detail: { theme: newTheme } }));
        });
    }
});