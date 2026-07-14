<template>
  <div class="placeholder-container">
    <Card class="placeholder-card shadow-sm">
      <template #title>
        <div class="placeholder-header">
          <i class="pi pi-sliders-h placeholder-icon"></i>
          <h2 class="placeholder-title">Simulação de Impacto</h2>
        </div>
      </template>
      <template #content>
        <p class="placeholder-message">Esta página está em desenvolvimento.</p>
        <p class="placeholder-description">
          Aqui será possível realizar projeções financeiras, simular reajustes e analisar a evolução de carreira dos servidores da UEFS.
        </p>
      </template>
    </Card>
  </div>
</template>

<script setup>
import Card from 'primevue/card';
</script>

<style scoped>
.placeholder-container {
  padding: 1rem;
}

.placeholder-card {
  border-radius: 6px;
  border: 1px solid var(--p-surface-200);
}

.placeholder-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.placeholder-icon {
  font-size: 1.5rem;
  color: var(--p-primary-color);
}

.placeholder-title {
  margin: 0;
  font-size: 1.375rem;
  font-weight: 700;
  color: var(--p-surface-900);
}

.placeholder-message {
  font-weight: 600;
  color: var(--p-surface-700);
  margin-top: 0;
  margin-bottom: 0.5rem;
}

.placeholder-description {
  color: var(--p-surface-500);
  font-size: 0.875rem;
  margin: 0;
}
</style>
