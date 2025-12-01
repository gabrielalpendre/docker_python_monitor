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
        theme: localStorage.getItem('theme') || 'dark',
        logoLight: URLS.logoLight,
        logoDark: URLS.logoDark
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
            axios.get(URLS.services)
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
            axios.get(URLS.server)
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

        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
});