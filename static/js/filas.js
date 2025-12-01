new Vue({
    el: "#app",
    delimiters: ['[[', ']]'],
    data: {
        queues: [],
        loading: true,
        lastUpdate: "",
        tipoSelecionado: "producao",
        theme: localStorage.getItem('theme') || 'dark',
        logoLight: PAGE_DATA.logoLight,
        logoDark: PAGE_DATA.logoDark
    },
    methods: {
        fetchTable() {
            this.loading = true;

            let tipoMap = {
                producao: "prd",
                antiga: "old"
            };

            const tipoBackend = tipoMap[this.tipoSelecionado];

            axios.get(`${PAGE_DATA.queues_url}${tipoBackend}`)
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
            document.body.className = `${this.theme}-mode`;
        }
    },
    mounted() {
        this.applyTheme();
        this.fetchTable();
        setInterval(() => { this.fetchTable(); }, 15000);
    },
    computed: {
        logoSrc() {
            return this.theme === 'dark' ? this.logoDark : this.logoLight;
        },
        themeIcon() {
            return this.theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon';
        }
    },
    watch: {
        tipoSelecionado() { this.fetchTable(); }
    }
});