import { createApp } from 'vue';
import App from './App.vue';

// Import Bootstrap and BootstrapVueNext (BootstrapVue 3)
import 'bootstrap/dist/css/bootstrap.css';
import 'bootstrap-vue-3/dist/bootstrap-vue-3.css';
import 'bootstrap-icons/font/bootstrap-icons.css';


// Import BootstrapVue 3 plugin
import BootstrapVue3 from 'bootstrap-vue-3';
import { Chart, registerables, ArcElement } from 'chart.js';
import ChartDataLabels from 'chartjs-plugin-datalabels';

Chart.register(...registerables, ArcElement, ChartDataLabels);

const app = createApp(App);

// Use BootstrapVue 3
app.use(BootstrapVue3);

app.mount('#app');
