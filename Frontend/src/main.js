import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'

import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'

import '@fortawesome/fontawesome-free/css/all.min.css'
import '@/assets/styles/styles.css'
import 'bootstrap-icons/font/bootstrap-icons.css';

const app = createApp(App)
app.use(store)
app.use(router)
app.mount('#app')
