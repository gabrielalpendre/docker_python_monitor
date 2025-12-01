const app = new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data: {
        tabelas: {},
        loading: true,
        erro: false,
        lastUpdate: "",
        theme: localStorage.getItem('theme') || 'dark',
        logo: PAGE_DATA.logo,
        labels: {
            "id2": "LabelID2",
            "id3": "LabelID3",
            "id4": "LabelID4",
            "id5": "LabelID5",
            "id6": "LabelID6",
            "id7": "LabelID7",
            "id8": "LabelID8"
        }
    },
    computed: {
        logoSrc() {
            // O logo não muda com o tema neste caso, mas mantemos a lógica para consistência
            return this.logo;
        },
    },
    methods: {
        fetchData() {
            this.loading = true;
            this.erro = false;
            axios.get(PAGE_DATA.queryes_url)
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
        this.fetchData();
        setInterval(() => {
            this.fetchData();
        }, 30000);

        // Ouve o evento de mudança de tema para manter o estado do Vue em sincronia
        window.addEventListener('theme:change', (e) => {
            if (this.theme !== e.detail.theme) {
                this.theme = e.detail.theme;
            }
        });
    }
});