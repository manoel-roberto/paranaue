<template>
  <div class="login-container">
    <Card class="login-card shadow-lg">
      <template #title>
        <div class="login-header">
          <h2 class="login-title">Acesso ao Sistema</h2>
          <p class="login-subtitle">Sistema de Impacto Financeiro UEFS</p>
        </div>
      </template>
      
      <template #content>
        <form @submit.prevent="handleLogin" class="login-form">
          <!-- Campo Usuário -->
          <div class="form-field">
            <label for="username" class="form-label">Usuário</label>
            <InputText 
              id="username" 
              v-model="username" 
              placeholder="Digite seu usuário" 
              :disabled="loading"
              class="w-full"
              required
              autocomplete="username"
            />
          </div>
          
          <!-- Campo Senha -->
          <div class="form-field">
            <label for="password" class="form-label">Senha</label>
            <Password 
              id="password" 
              v-model="password" 
              placeholder="Digite sua senha" 
              :feedback="false" 
              toggleMask 
              :disabled="loading"
              class="w-full"
              inputClass="w-full"
              required
              autocomplete="current-password"
            />
          </div>
          
          <!-- Alerta de Erro com Transição Suave -->
          <transition name="fade-slide">
            <Message v-if="error" severity="error" class="mt-2 w-full">
              {{ error }}
            </Message>
          </transition>
          
          <!-- Botão Entrar -->
          <Button 
            type="submit" 
            label="Entrar" 
            :loading="loading" 
            class="w-full mt-4" 
          />
        </form>
      </template>
    </Card>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';

// Importação direta dos componentes do PrimeVue v4 (otimizado para tree-shaking)
import Card from 'primevue/card';
import InputText from 'primevue/inputtext';
import Password from 'primevue/password';
import Button from 'primevue/button';
import Message from 'primevue/message';

const username = ref('');
const password = ref('');
const loading = ref(false);
const error = ref('');

const authStore = useAuthStore();
const router = useRouter();

/**
 * Submete o formulário de login e interage com a store Pinia
 */
const handleLogin = async () => {
  if (!username.value || !password.value) return;

  loading.value = true;
  error.value = '';
  
  try {
    const result = await authStore.login({
      username: username.value,
      password: password.value,
    });
    
    if (result && result.success) {
      router.push('/');
    } else {
      error.value = 'Usuário ou senha incorretos.';
    }
  } catch (err) {
    console.error('Falha na requisição de login:', err);
    
    // Extrai e formata mensagens detalhadas de validação do FastAPI
    if (err.response?.data?.detail) {
      const detail = err.response.data.detail;
      if (Array.isArray(detail)) {
        // Se for um array de erros de validação (FastAPI 422), junta as mensagens amigavelmente
        error.value = detail.map(e => {
          const field = e.loc ? e.loc[e.loc.length - 1] : 'dado';
          return `${field}: ${e.msg}`;
        }).join(' | ');
      } else {
        error.value = detail;
      }
    } else {
      error.value = 'Falha ao conectar com o servidor de autenticação.';
    }
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: var(--p-surface-50);
  padding: 1.5rem;
  box-sizing: border-box;
}

.login-card {
  width: 100%;
  max-width: 420px;
  border-radius: 6px; /* Geometria corporativa limpa */
  border: 1px solid var(--p-surface-200);
}

.login-header {
  text-align: center;
  margin-bottom: 1.5rem;
}

.login-title {
  margin: 0;
  font-size: 1.625rem;
  font-weight: 700;
  color: var(--p-surface-900);
  letter-spacing: -0.025em;
}

.login-subtitle {
  margin: 0.375rem 0 0 0;
  font-size: 0.875rem;
  color: var(--p-surface-500);
  font-weight: 400;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-label {
  font-weight: 600;
  font-size: 0.8125rem;
  color: var(--p-surface-700);
}

/* Utilitários locais */
.w-full {
  width: 100%;
}

.mt-2 {
  margin-top: 0.5rem;
}

.mt-4 {
  margin-top: 1rem;
}

/* Transições para o Alerta de Erro */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
