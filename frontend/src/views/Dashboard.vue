<template>
  <div class="dashboard-container">
    <!-- Header Corporativo -->
    <header class="dashboard-header">
      <div class="header-content">
        <h1 class="logo">UEFS Financeiro</h1>
        <div class="user-menu" v-if="authStore.user">
          <span class="user-greeting">
            Bem-vindo, <strong class="username">{{ authStore.user.username }}</strong>
          </span>
          <Button 
            label="Sair" 
            icon="pi pi-sign-out" 
            class="p-button-outlined p-button-sm logout-btn" 
            @click="handleLogout" 
          />
        </div>
      </div>
    </header>
    
    <!-- Painel de Conteúdo Principal -->
    <main class="dashboard-main">
      <Card class="content-card shadow-sm">
        <template #title>
          <h2 class="card-title">Painel de Simulações</h2>
        </template>
        <template #content>
          <div class="welcome-message">
            <p>Você está autenticado no <strong>Sistema de Cálculo de Impacto Financeiro da UEFS</strong>.</p>
            <p class="text-secondary">Este painel permite realizar simulações de evolução de carreira e reajustes salariais para os servidores públicos da UEFS.</p>
          </div>
        </template>
      </Card>
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';

// Importação dos componentes do PrimeVue v4
import Card from 'primevue/card';
import Button from 'primevue/button';

const authStore = useAuthStore();
const router = useRouter();

/**
 * Realiza o logout do usuário e redireciona para a tela de login
 */
const handleLogout = () => {
  authStore.logout();
  router.push('/login');
};
</script>

<style scoped>
.dashboard-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--p-surface-50);
}

.dashboard-header {
  background-color: #ffffff;
  border-bottom: 1px solid var(--p-surface-200);
  padding: 0.875rem 2rem;
  box-sizing: border-box;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.logo {
  font-size: 1.25rem;
  font-weight: 800;
  margin: 0;
  color: var(--p-primary-color, #10b981);
  letter-spacing: -0.02em;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 1.25rem;
}

.user-greeting {
  font-size: 0.875rem;
  color: var(--p-surface-600);
}

.username {
  color: var(--p-surface-900);
}

.logout-btn {
  border-radius: 4px;
}

.dashboard-main {
  flex: 1;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 2rem;
  box-sizing: border-box;
}

.content-card {
  border-radius: 6px;
  border: 1px solid var(--p-surface-200);
}

.card-title {
  margin: 0 0 0.5rem 0;
  font-size: 1.375rem;
  font-weight: 700;
  color: var(--p-surface-900);
}

.welcome-message p {
  margin: 0 0 0.75rem 0;
  line-height: 1.6;
  font-size: 1rem;
}

.welcome-message p.text-secondary {
  color: var(--p-surface-500);
  font-size: 0.875rem;
  margin-bottom: 0;
}
</style>
