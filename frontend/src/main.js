import { createApp } from 'vue';
import { createPinia } from 'pinia';
import PrimeVue from 'primevue/config';
import Aura from '@primevue/themes/aura';
import ToastService from 'primevue/toastservice';
import ConfirmationService from 'primevue/confirmationservice';
import 'primeicons/primeicons.css';

import App from './App.vue';
import router from './router';
import { useAuthStore } from './stores/auth';

// Criação da aplicação Vue
const app = createApp(App);

// Registro dos Serviços do PrimeVue
app.use(ToastService);
app.use(ConfirmationService);

// Inicialização do Pinia
const pinia = createPinia();
app.use(pinia);

// Registro do Vue Router
app.use(router);

// Configuração do PrimeVue v4 com o tema Aura
app.use(PrimeVue, {
  theme: {
    preset: Aura,
    options: {
      prefix: 'p',
      darkModeSelector: 'system', // Adota o tema claro/escuro do sistema operacional
      cssLayer: false
    }
  }
});

// Inicialização do estado de autenticação (recuperação de sessão do localStorage)
const authStore = useAuthStore();
authStore.init();

// Monta a aplicação no elemento raiz
app.mount('#app');
