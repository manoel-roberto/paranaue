<template>
  <Toast />
  <ConfirmDialog />
  <router-view />
</template>

<script setup>
import Toast from 'primevue/toast';
import ConfirmDialog from 'primevue/confirmdialog';
// Ponto de entrada básico estruturado para renderizar as views do roteador
</script>

<style>
/* Reset de layout e estilos globais integrados ao PrimeVue */
html,
body,
#app {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  font-family: var(--p-font-family, system-ui, -apple-system, sans-serif);
  background-color: var(--p-surface-50, #f8fafc);
  color: var(--p-surface-900, #0f172a);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>
