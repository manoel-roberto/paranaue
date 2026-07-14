<template>
  <div class="parametros-container">
    <!-- Cabeçalho do Módulo -->
    <div class="page-header">
      <div class="header-info">
        <h2 class="page-title">Parâmetros do Sistema</h2>
        <p class="page-subtitle">Gerencie as tabelas salariais e parâmetros de cálculo da UEFS.</p>
      </div>
    </div>

    <!-- Abas de Parâmetros -->
    <Card class="tab-card shadow-sm">
      <template #content>
        <TabView>
          <!-- Aba Vencimento Básico -->
          <TabPanel header="Vencimento Básico">
            <div class="tab-actions-header">
              <h3 class="tab-section-title">Tabela de Vencimento Básico</h3>
              <Button 
                label="Novo Vencimento" 
                icon="pi pi-plus" 
                class="new-btn" 
                @click="openNewVencimentoDialog" 
              />
            </div>

            <DataTable 
              :value="vencimentos" 
              :loading="loading" 
              stripedRows 
              responsiveLayout="stack" 
              breakpoint="960px"
              class="p-datatable-sm custom-datatable"
              dataKey="id"
              :rows="10"
              :paginator="vencimentos.length > 10"
              emptyMessage="Nenhum vencimento básico cadastrado."
            >
              <Column field="classe" header="Classe" sortable class="column-classe"></Column>
              <Column field="referencia" header="Referência" sortable class="column-referencia"></Column>
              <Column field="valor" header="Valor" sortable class="column-valor">
                <template #body="slotProps">
                  {{ formatCurrency(slotProps.data.valor) }}
                </template>
              </Column>
              
              <Column header="Ações" class="column-actions" headerStyle="width: 160px; text-align: center" bodyStyle="text-align: center">
                <template #body="slotProps">
                  <div class="actions-wrapper">
                    <Button 
                      icon="pi pi-eye" 
                      text 
                      rounded 
                      severity="secondary" 
                      class="action-btn"
                      title="Consultar"
                      @click="viewVencimento(slotProps.data)" 
                    />
                    <Button 
                      icon="pi pi-pencil" 
                      text 
                      rounded 
                      severity="primary" 
                      class="action-btn edit-btn"
                      title="Editar"
                      @click="editVencimento(slotProps.data)" 
                    />
                    <Button 
                      icon="pi pi-trash" 
                      text 
                      rounded 
                      severity="danger" 
                      class="action-btn delete-btn"
                      title="Excluir"
                      @click="confirmDelete(slotProps.data)" 
                    />
                  </div>
                </template>
              </Column>
            </DataTable>
          </TabPanel>

          <!-- Aba GSTU -->
          <TabPanel header="GSTU">
            <div class="tab-actions-header">
              <h3 class="tab-section-title">Tabela GSTU</h3>
              <Button 
                label="Novo GSTU" 
                icon="pi pi-plus" 
                class="new-btn" 
                @click="openNewGstuDialog" 
              />
            </div>

            <DataTable 
              :value="gstus" 
              :loading="gstuLoading" 
              stripedRows 
              responsiveLayout="stack" 
              breakpoint="960px"
              class="p-datatable-sm custom-datatable"
              dataKey="id"
              :rows="10"
              :paginator="gstus.length > 10"
              emptyMessage="Nenhuma gratificação GSTU cadastrada."
            >
              <Column field="nivel" header="Nível" sortable class="column-nivel"></Column>
              <Column field="valor" header="Valor" sortable class="column-valor">
                <template #body="slotProps">
                  {{ formatCurrency(slotProps.data.valor) }}
                </template>
              </Column>
              
              <Column header="Ações" class="column-actions" headerStyle="width: 160px; text-align: center" bodyStyle="text-align: center">
                <template #body="slotProps">
                  <div class="actions-wrapper">
                    <Button 
                      icon="pi pi-eye" 
                      text 
                      rounded 
                      severity="secondary" 
                      class="action-btn"
                      title="Consultar"
                      @click="viewGstu(slotProps.data)" 
                    />
                    <Button 
                      icon="pi pi-pencil" 
                      text 
                      rounded 
                      severity="primary" 
                      class="action-btn edit-btn"
                      title="Editar"
                      @click="editGstu(slotProps.data)" 
                    />
                    <Button 
                      icon="pi pi-trash" 
                      text 
                      rounded 
                      severity="danger" 
                      class="action-btn delete-btn"
                      title="Excluir"
                      @click="confirmDeleteGstu(slotProps.data)" 
                    />
                  </div>
                </template>
              </Column>
            </DataTable>
          </TabPanel>
        </TabView>
      </template>
    </Card>

    <!-- Dialog Tri-Modal para Novo Vencimento / Edição / Visualização -->
    <Dialog 
      v-model:visible="displayDialog" 
      :header="dialogHeader" 
      :modal="true" 
      :draggable="false"
      class="custom-dialog"
      :style="{ width: '450px' }"
      @hide="closeDialog"
    >
      <form @submit.prevent="saveVencimento" class="vencimento-form">
        <!-- Classe -->
        <div class="form-field">
          <label for="classe" class="form-label">Classe</label>
          <InputText 
            id="classe" 
            v-model.trim="form.classe" 
            placeholder="Ex: Assistente, Adjunto, Titular" 
            :disabled="submitting || dialogMode === 'view'"
            required
            autofocus
            class="w-full"
          />
        </div>

        <!-- Referência -->
        <div class="form-field">
          <label for="referencia" class="form-label">Referência</label>
          <InputText 
            id="referencia" 
            v-model.trim="form.referencia" 
            placeholder="Ex: Nível 1, Grau A, Ref 1" 
            :disabled="submitting || dialogMode === 'view'"
            required
            class="w-full"
          />
        </div>

        <!-- Valor -->
        <div class="form-field">
          <label for="valor" class="form-label">Valor (R$)</label>
          <InputNumber 
            id="valor" 
            v-model="form.valor" 
            mode="currency" 
            currency="BRL" 
            locale="pt-BR" 
            :min="0.01"
            placeholder="R$ 0,00"
            :disabled="submitting || dialogMode === 'view'"
            required
            class="w-full"
            inputClass="w-full"
          />
        </div>

        <!-- Footer do Form / Botões -->
        <div class="form-actions">
          <Button 
            type="button" 
            :label="dialogMode === 'view' ? 'Fechar' : 'Cancelar'" 
            :icon="dialogMode === 'view' ? 'pi pi-check' : 'pi pi-times'" 
            class="p-button-text p-button-secondary cancel-btn" 
            :disabled="submitting"
            @click="closeDialog" 
          />
          <Button 
            v-if="dialogMode !== 'view'"
            type="submit" 
            label="Salvar" 
            icon="pi pi-check" 
            class="save-submit-btn" 
            :loading="submitting" 
          />
        </div>
      </form>
    </Dialog>

    <!-- Dialog Tri-Modal para Novo GSTU / Edição / Visualização -->
    <Dialog 
      v-model:visible="displayGstuDialog" 
      :header="gstuDialogHeader" 
      :modal="true" 
      :draggable="false"
      class="custom-dialog"
      :style="{ width: '450px' }"
      @hide="closeGstuDialog"
    >
      <form @submit.prevent="saveGstu" class="vencimento-form">
        <!-- Nível -->
        <div class="form-field">
          <label for="nivel" class="form-label">Nível</label>
          <InputText 
            id="nivel" 
            v-model.trim="gstuForm.nivel" 
            placeholder="Ex: Nível 1, Nível 2" 
            :disabled="gstuSubmitting || gstuDialogMode === 'view'"
            required
            autofocus
            class="w-full"
          />
        </div>

        <!-- Valor -->
        <div class="form-field">
          <label for="gstu-valor" class="form-label">Valor (R$)</label>
          <InputNumber 
            id="gstu-valor" 
            v-model="gstuForm.valor" 
            mode="currency" 
            currency="BRL" 
            locale="pt-BR" 
            :min="0.01"
            placeholder="R$ 0,00"
            :disabled="gstuSubmitting || gstuDialogMode === 'view'"
            required
            class="w-full"
            inputClass="w-full"
          />
        </div>

        <!-- Footer do Form / Botões -->
        <div class="form-actions">
          <Button 
            type="button" 
            :label="gstuDialogMode === 'view' ? 'Fechar' : 'Cancelar'" 
            :icon="gstuDialogMode === 'view' ? 'pi pi-check' : 'pi pi-times'" 
            class="p-button-text p-button-secondary cancel-btn" 
            :disabled="gstuSubmitting"
            @click="closeGstuDialog" 
          />
          <Button 
            v-if="gstuDialogMode !== 'view'"
            type="submit" 
            label="Salvar" 
            icon="pi pi-check" 
            class="save-submit-btn" 
            :loading="gstuSubmitting" 
          />
        </div>
      </form>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useToast } from 'primevue/usetoast';
import { useConfirm } from 'primevue/useconfirm';
import api from '../services/api';

// Componentes PrimeVue v4
import Card from 'primevue/card';
import TabView from 'primevue/tabview';
import TabPanel from 'primevue/tabpanel';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Button from 'primevue/button';
import Dialog from 'primevue/dialog';
import InputText from 'primevue/inputtext';
import InputNumber from 'primevue/inputnumber';

const toast = useToast();
const confirm = useConfirm();

// ============================================
// ESTADOS E MÉTODOS - VENCIMENTO BÁSICO
// ============================================
const vencimentos = ref([]);
const loading = ref(false);
const submitting = ref(false);
const displayDialog = ref(false);
const dialogMode = ref('create'); // 'create', 'edit', 'view'
const selectedVencimentoId = ref(null);

const initialFormState = {
  classe: '',
  referencia: '',
  valor: null
};

const form = ref({ ...initialFormState });

const dialogHeader = computed(() => {
  if (dialogMode.value === 'view') return 'Visualizar Parâmetro de Vencimento';
  if (dialogMode.value === 'edit') return 'Editar Parâmetro de Vencimento';
  return 'Cadastrar Novo Vencimento Básico';
});

const fetchVencimentos = async () => {
  loading.value = true;
  try {
    const response = await api.get('/api/v1/vencimentos');
    vencimentos.value = response.data;
  } catch (error) {
    console.error('Erro ao buscar vencimentos básicos:', error);
    toast.add({
      severity: 'error',
      summary: 'Erro de Carregamento',
      detail: 'Não foi possível carregar a lista de vencimentos básicos.',
      life: 5000
    });
  } finally {
    loading.value = false;
  }
};

const openNewVencimentoDialog = () => {
  dialogMode.value = 'create';
  selectedVencimentoId.value = null;
  form.value = { ...initialFormState };
  displayDialog.value = true;
};

const viewVencimento = (vencimento) => {
  dialogMode.value = 'view';
  selectedVencimentoId.value = vencimento.id;
  form.value = {
    classe: vencimento.classe,
    referencia: vencimento.referencia,
    valor: Number(vencimento.valor)
  };
  displayDialog.value = true;
};

const editVencimento = (vencimento) => {
  dialogMode.value = 'edit';
  selectedVencimentoId.value = vencimento.id;
  form.value = {
    classe: vencimento.classe,
    referencia: vencimento.referencia,
    valor: Number(vencimento.valor)
  };
  displayDialog.value = true;
};

const confirmDelete = (vencimento) => {
  confirm.require({
    message: `Tem certeza de que deseja excluir o parâmetro "${vencimento.classe} - ${vencimento.referencia}"?`,
    header: 'Confirmação de Exclusão',
    icon: 'pi pi-exclamation-triangle',
    rejectProps: {
      label: 'Cancelar',
      severity: 'secondary',
      outlined: true
    },
    acceptProps: {
      label: 'Excluir',
      severity: 'danger'
    },
    accept: async () => {
      try {
        await api.delete(`/api/v1/vencimentos/${vencimento.id}`);
        toast.add({
          severity: 'success',
          summary: 'Sucesso',
          detail: 'Vencimento básico excluído com sucesso!',
          life: 3000
        });
        fetchVencimentos();
      } catch (error) {
        console.error('Erro ao excluir vencimento básico:', error);
        let errorMsg = 'Não foi possível excluir o vencimento básico.';
        if (error.response?.data?.detail) {
          const detail = error.response.data.detail;
          if (Array.isArray(detail)) {
            errorMsg = detail.map(e => `${e.loc[e.loc.length - 1]}: ${e.msg}`).join(' | ');
          } else {
            errorMsg = detail;
          }
        }
        toast.add({
          severity: 'error',
          summary: 'Erro de Exclusão',
          detail: errorMsg,
          life: 6000
        });
      }
    }
  });
};

const closeDialog = () => {
  displayDialog.value = false;
  selectedVencimentoId.value = null;
  form.value = { ...initialFormState };
};

const saveVencimento = async () => {
  if (form.value.valor === null || form.value.valor <= 0) {
    toast.add({
      severity: 'warn',
      summary: 'Validação',
      detail: 'O valor do vencimento básico deve ser maior que zero.',
      life: 4000
    });
    return;
  }

  submitting.value = true;
  const payload = {
    classe: form.value.classe,
    referencia: form.value.referencia,
    valor: form.value.valor
  };

  try {
    if (dialogMode.value === 'edit') {
      await api.put(`/api/v1/vencimentos/${selectedVencimentoId.value}`, payload);
      toast.add({
        severity: 'success',
        summary: 'Sucesso',
        detail: 'Vencimento básico atualizado com sucesso!',
        life: 3000
      });
    } else {
      await api.post('/api/v1/vencimentos', payload);
      toast.add({
        severity: 'success',
        summary: 'Sucesso',
        detail: 'Vencimento básico cadastrado com sucesso!',
        life: 3000
      });
    }
    closeDialog();
    fetchVencimentos();
  } catch (error) {
    console.error('Erro ao salvar vencimento básico:', error);
    let errorMsg = 'Não foi possível salvar o vencimento básico.';
    if (error.response?.data?.detail) {
      const detail = error.response.data.detail;
      if (Array.isArray(detail)) {
        errorMsg = detail.map(e => `${e.loc[e.loc.length - 1]}: ${e.msg}`).join(' | ');
      } else {
        errorMsg = detail;
      }
    }
    toast.add({
      severity: 'error',
      summary: 'Erro ao Salvar',
      detail: errorMsg,
      life: 6000
    });
  } finally {
    submitting.value = false;
  }
};

// ============================================
// ESTADOS E MÉTODOS - GSTU
// ============================================
const gstus = ref([]);
const gstuLoading = ref(false);
const gstuSubmitting = ref(false);
const displayGstuDialog = ref(false);
const gstuDialogMode = ref('create'); // 'create', 'edit', 'view'
const selectedGstuId = ref(null);

const initialGstuFormState = {
  nivel: '',
  valor: null
};

const gstuForm = ref({ ...initialGstuFormState });

const gstuDialogHeader = computed(() => {
  if (gstuDialogMode.value === 'view') return 'Visualizar Parâmetro GSTU';
  if (gstuDialogMode.value === 'edit') return 'Editar Parâmetro GSTU';
  return 'Cadastrar Nova Gratificação GSTU';
});

const fetchGstus = async () => {
  gstuLoading.value = true;
  try {
    const response = await api.get('/api/v1/gstu');
    gstus.value = response.data;
  } catch (error) {
    console.error('Erro ao buscar gratificações GSTU:', error);
    toast.add({
      severity: 'error',
      summary: 'Erro de Carregamento',
      detail: 'Não foi possível carregar a lista de gratificações GSTU.',
      life: 5000
    });
  } finally {
    gstuLoading.value = false;
  }
};

const openNewGstuDialog = () => {
  gstuDialogMode.value = 'create';
  selectedGstuId.value = null;
  gstuForm.value = { ...initialGstuFormState };
  displayGstuDialog.value = true;
};

const viewGstu = (gstu) => {
  gstuDialogMode.value = 'view';
  selectedGstuId.value = gstu.id;
  gstuForm.value = {
    nivel: gstu.nivel,
    valor: Number(gstu.valor)
  };
  displayGstuDialog.value = true;
};

const editGstu = (gstu) => {
  gstuDialogMode.value = 'edit';
  selectedGstuId.value = gstu.id;
  gstuForm.value = {
    nivel: gstu.nivel,
    valor: Number(gstu.valor)
  };
  displayGstuDialog.value = true;
};

const confirmDeleteGstu = (gstu) => {
  confirm.require({
    message: `Tem certeza de que deseja excluir o parâmetro GSTU "${gstu.nivel}"?`,
    header: 'Confirmação de Exclusão',
    icon: 'pi pi-exclamation-triangle',
    rejectProps: {
      label: 'Cancelar',
      severity: 'secondary',
      outlined: true
    },
    acceptProps: {
      label: 'Excluir',
      severity: 'danger'
    },
    accept: async () => {
      try {
        await api.delete(`/api/v1/gstu/${gstu.id}`);
        toast.add({
          severity: 'success',
          summary: 'Sucesso',
          detail: 'Gratificação GSTU excluída com sucesso!',
          life: 3000
        });
        fetchGstus();
      } catch (error) {
        console.error('Erro ao excluir GSTU:', error);
        let errorMsg = 'Não foi possível excluir a gratificação GSTU.';
        if (error.response?.data?.detail) {
          const detail = error.response.data.detail;
          if (Array.isArray(detail)) {
            errorMsg = detail.map(e => `${e.loc[e.loc.length - 1]}: ${e.msg}`).join(' | ');
          } else {
            errorMsg = detail;
          }
        }
        toast.add({
          severity: 'error',
          summary: 'Erro de Exclusão',
          detail: errorMsg,
          life: 6000
        });
      }
    }
  });
};

const closeGstuDialog = () => {
  displayGstuDialog.value = false;
  selectedGstuId.value = null;
  gstuForm.value = { ...initialGstuFormState };
};

const saveGstu = async () => {
  if (gstuForm.value.valor === null || gstuForm.value.valor <= 0) {
    toast.add({
      severity: 'warn',
      summary: 'Validação',
      detail: 'O valor da GSTU deve ser maior que zero.',
      life: 4000
    });
    return;
  }

  gstuSubmitting.value = true;
  const payload = {
    nivel: gstuForm.value.nivel,
    valor: gstuForm.value.valor
  };

  try {
    if (gstuDialogMode.value === 'edit') {
      await api.put(`/api/v1/gstu/${selectedGstuId.value}`, payload);
      toast.add({
        severity: 'success',
        summary: 'Sucesso',
        detail: 'Gratificação GSTU atualizada com sucesso!',
        life: 3000
      });
    } else {
      await api.post('/api/v1/gstu', payload);
      toast.add({
        severity: 'success',
        summary: 'Sucesso',
        detail: 'Gratificação GSTU cadastrada com sucesso!',
        life: 3000
      });
    }
    closeGstuDialog();
    fetchGstus();
  } catch (error) {
    console.error('Erro ao salvar GSTU:', error);
    let errorMsg = 'Não foi possível salvar a gratificação GSTU.';
    if (error.response?.data?.detail) {
      const detail = error.response.data.detail;
      if (Array.isArray(detail)) {
        errorMsg = detail.map(e => `${e.loc[e.loc.length - 1]}: ${e.msg}`).join(' | ');
      } else {
        errorMsg = detail;
      }
    }
    toast.add({
      severity: 'error',
      summary: 'Erro ao Salvar',
      detail: errorMsg,
      life: 6000
    });
  } finally {
    gstuSubmitting.value = false;
  }
};

// ============================================
// AUXILIARES E LIFECYCLE
// ============================================
const formatCurrency = (value) => {
  if (value === undefined || value === null) return '';
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(Number(value));
};

onMounted(() => {
  fetchVencimentos();
  fetchGstus();
});
</script>

<style scoped>
.parametros-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.page-title {
  margin: 0;
  font-size: 1.625rem;
  font-weight: 700;
  color: var(--p-surface-900);
  letter-spacing: -0.025em;
}

.page-subtitle {
  margin: 0.25rem 0 0 0;
  font-size: 0.875rem;
  color: var(--p-surface-500);
}

.tab-card {
  border-radius: 6px;
  border: 1px solid var(--p-surface-200);
  background-color: #ffffff;
}

.tab-actions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.25rem;
}

.tab-section-title {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--p-surface-800);
}

.new-btn {
  background-color: var(--p-primary-color) !important;
  border-color: var(--p-primary-color) !important;
  border-radius: 4px !important;
  font-weight: 600 !important;
  font-size: 0.875rem !important;
  transition: background-color 0.2s ease;
}

.new-btn:hover {
  background-color: var(--p-primary-600, #004D3C) !important;
  border-color: var(--p-primary-600, #004D3C) !important;
}

.custom-datatable {
  font-size: 0.875rem;
}

.column-classe, .column-nivel {
  font-weight: 600;
  color: var(--p-surface-900);
}

.column-referencia {
  color: var(--p-surface-700);
}

.column-valor {
  font-weight: 600;
  color: var(--p-surface-900);
}

.actions-wrapper {
  display: flex;
  justify-content: center;
  gap: 0.25rem;
}

.action-btn {
  width: 2.25rem !important;
  height: 2.25rem !important;
  padding: 0 !important;
  display: inline-flex !important;
  align-items: center;
  justify-content: center;
  border-radius: 50% !important;
}

.edit-btn:hover {
  background-color: var(--p-primary-50, #e6f6f2) !important;
}

.delete-btn:hover {
  background-color: #fee2e2 !important;
}

/* Dialog e Form */
.custom-dialog {
  border-radius: 6px !important;
}

.vencimento-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  padding-top: 0.5rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.form-label {
  font-weight: 600;
  font-size: 0.8125rem;
  color: var(--p-surface-700);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.5rem;
  border-top: 1px solid var(--p-surface-100);
  padding-top: 1.25rem;
}

.cancel-btn {
  font-size: 0.875rem !important;
  border-radius: 4px !important;
  color: var(--p-surface-600) !important;
}

.cancel-btn:hover {
  background-color: var(--p-surface-100) !important;
}

.save-submit-btn {
  background-color: var(--p-primary-color) !important;
  border-color: var(--p-primary-color) !important;
  border-radius: 4px !important;
  font-weight: 600 !important;
  font-size: 0.875rem !important;
}

.save-submit-btn:hover {
  background-color: var(--p-primary-600, #004D3C) !important;
  border-color: var(--p-primary-600, #004D3C) !important;
}

.w-full {
  width: 100%;
}
</style>
