new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data: {
        selectedType: "",
        selectedService: "",
        incidents: PAGE_DATA.history,
        types: PAGE_DATA.types,
        typeMap: PAGE_DATA.type_map,
        theme: localStorage.getItem('theme') || 'dark',
        logoLight: PAGE_DATA.logoLight,
        logoDark: PAGE_DATA.logoDark
    },
    computed: {
        filteredServices() {
            if (!this.selectedType) {
                const allServices = this.incidents.map(i => i.service);
                return [...new Set(allServices)].sort();
            }
            return this.typeMap[this.selectedType] || [];
        },
        filteredIncidents() {
            return this.incidents.filter(entry => {
                const matchType = !this.selectedType || entry.type === this.selectedType;
                const matchService = !this.selectedService || entry.service === this.selectedService;
                return matchType && matchService;
            });
        },
        logoSrc() {
            return this.theme === 'dark' ? this.logoDark : this.logoLight;
        },
        themeIcon() {
            return this.theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon';
        }
    },
    methods: {
        toggleTheme() {
            this.theme = this.theme === 'light' ? 'dark' : 'light';
            localStorage.setItem('theme', this.theme);
            document.body.className = this.theme + '-mode';
        },
        applyTheme() {
            document.body.className = this.theme + '-mode';
        }
    },
    mounted() {
        this.applyTheme();
    }
});