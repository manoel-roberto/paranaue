<template>
  <div class="admin-container">
    <!-- Top Bar com Menubar do PrimeVue -->
    <header class="admin-header shadow-sm">
      <Menubar :model="menuItems" class="custom-menubar">
        <template #start>
          <div class="brand-logo" @click="goHome">
            <h1 class="logo">UEFS Financeiro</h1>
          </div>
        </template>
        
        <template #item="{ item, props, hasSubmenu }">
          <router-link v-if="item.route" v-slot="{ href, navigate, isActive }" :to="item.route" custom>
            <a :href="href" v-bind="props.action" @click="navigate" :class="{ 'active-link': isActive }" class="menu-item-link">
              <span :class="item.icon" class="menu-icon" />
              <span class="menu-label">{{ item.label }}</span>
            </a>
          </router-link>
        </template>
        
        <template #end>
          <div class="user-profile" v-if="authStore.user">
            <span class="user-greeting">
              Olá, <strong class="username">{{ authStore.user.username }}</strong>
            </span>
            <Button 
              label="Sair" 
              icon="pi pi-sign-out" 
              class="p-button-outlined p-button-sm logout-btn" 
              @click="handleLogout" 
            />
          </div>
        </template>
      </Menubar>
    </header>
    
    <!-- Área de Conteúdo Dinâmico -->
    <main class="admin-main">
      <div class="content-wrapper">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';

// Componentes PrimeVue
import Menubar from 'primevue/menubar';
import Button from 'primevue/button';

const authStore = useAuthStore();
const router = useRouter();

// Itens de navegação solicitados
const menuItems = ref([
  {
    label: 'Início',
    icon: 'pi pi-home',
    route: '/'
  },
  {
    label: 'Servidores',
    icon: 'pi pi-users',
    route: '/servidores'
  },
  {
    label: 'Parâmetros',
    icon: 'pi pi-cog',
    route: '/parametros'
  },
  {
    label: 'Simulação',
    icon: 'pi pi-sliders-h',
    route: '/simulacao'
  }
]);

const handleLogout = () => {
  authStore.logout();
  router.push('/login');
};

const goHome = () => {
  router.push('/');
};
</script>

<style scoped>
.admin-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--p-surface-50);
}

.admin-header {
  background-color: #ffffff;
  border-bottom: 1px solid var(--p-surface-200);
}

.custom-menubar {
  border: none !important;
  background: transparent !important;
  border-radius: 0 !important;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0.75rem 2rem;
  box-sizing: border-box;
}

.brand-logo {
  cursor: pointer;
  margin-right: 2rem;
}

.logo {
  font-size: 1.25rem;
  font-weight: 800;
  margin: 0;
  color: var(--p-primary-color);
  letter-spacing: -0.02em;
}

.menu-item-link {
  display: flex;
  align-items: center;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  color: var(--p-surface-600);
  text-decoration: none;
  font-weight: 500;
  transition: all 0.2s ease;
}

.menu-item-link:hover {
  background-color: var(--p-surface-100);
  color: var(--p-surface-900);
}

.active-link {
  background-color: var(--p-primary-50, #e6f6f2) !important;
  color: var(--p-primary-color) !important;
  font-weight: 600;
}

.menu-icon {
  margin-right: 0.5rem;
  font-size: 1rem;
}

.menu-label {
  font-size: 0.875rem;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  margin-left: 1.5rem;
}

.user-greeting {
  font-size: 0.875rem;
  color: var(--p-surface-600);
}

.username {
  color: var(--p-surface-900);
}

.logout-btn {
  border-radius: 4px !important;
  font-size: 0.8125rem !important;
  padding: 0.375rem 0.75rem !important;
}

.admin-main {
  flex: 1;
  width: 100%;
  box-sizing: border-box;
}

.content-wrapper {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  box-sizing: border-box;
}

/* Responsividade para telas menores */
@media (max-width: 960px) {
  .custom-menubar {
    padding: 0.5rem 1rem;
  }
  
  .user-profile {
    margin-left: 0;
    margin-top: 1rem;
    width: 100%;
    justify-content: space-between;
    border-top: 1px solid var(--p-surface-200);
    padding-top: 1rem;
  }
}
</style>
