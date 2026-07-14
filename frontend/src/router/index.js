import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../stores/auth';

// Definição das rotas do sistema UEFS
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { guestOnly: true },
  },
  {
    path: '/',
    component: () => import('../layouts/AdminLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
      },
      {
        path: 'servidores',
        name: 'Servidores',
        component: () => import('../views/Servidores.vue'),
      },
      {
        path: 'parametros',
        name: 'Parametros',
        component: () => import('../views/Parametros.vue'),
      },
      {
        path: 'simulacao',
        name: 'Simulacao',
        component: () => import('../views/Simulacao.vue'),
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

// Guard de Navegação (Navigation Guard) para Controle de Acesso
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();
  
  // Verifica regras de autenticação associadas à rota
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    // Caso a rota exija autenticação e o usuário esteja deslogado, vai para login
    next('/login');
  } else if (to.meta.guestOnly && authStore.isAuthenticated) {
    // Caso seja uma rota para visitantes (ex: tela de login) e o usuário já esteja logado, vai para o Dashboard
    next('/');
  } else {
    // Permite a navegação para a rota de destino
    next();
  }
});

export default router;
