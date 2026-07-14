<template>
  <div class="servidores-container">
    <!-- Cabeçalho do Módulo -->
    <div class="page-header">
      <div class="header-info">
        <h2 class="page-title">Gestão de Servidores</h2>
        <p class="page-subtitle">Listagem e cadastro de servidores da instituição.</p>
      </div>
      <Button 
        label="Novo Servidor" 
        icon="pi pi-plus" 
        class="new-btn" 
        @click="openNewServidorDialog" 
      />
    </div>

    <!-- Tabela de Servidores -->
    <Card class="table-card shadow-sm">
      <template #content>
        <DataTable 
          :value="servidores" 
          :loading="loading" 
          stripedRows 
          responsiveLayout="stack" 
          breakpoint="960px"
          class="p-datatable-sm custom-datatable"
          dataKey="id"
          :rows="10"
          :paginator="servidores.length > 10"
          emptyMessage="Nenhum servidor cadastrado."
        >
          <Column field="nome" header="Nome" sortable class="column-nome"></Column>
          
          <Column field="cpf" header="CPF" class="column-cpf">
            <template #body="slotProps">
              {{ formatCPF(slotProps.data.cpf) }}
            </template>
          </Column>
          
          <Column field="data_nascimento" header="Data de Nascimento" class="column-data">
            <template #body="slotProps">
              {{ formatDateBR(slotProps.data.data_nascimento) }}
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
                  @click="viewServidor(slotProps.data)" 
                />
                <Button 
                  icon="pi pi-pencil" 
                  text 
                  rounded 
                  severity="primary" 
                  class="action-btn edit-btn"
                  title="Editar"
                  @click="editServidor(slotProps.data)" 
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
      </template>
    </Card>

    <!-- Dialog para Novo Servidor / Edição / Visualização -->
    <Dialog 
      v-model:visible="displayDialog" 
      :header="dialogHeader" 
      :modal="true" 
      :draggable="false"
      class="custom-dialog"
      :style="{ width: '450px' }"
      @hide="closeDialog"
    >
      <form @submit.prevent="saveServidor" class="servidor-form">
        <!-- Nome -->
        <div class="form-field">
          <label for="nome" class="form-label">Nome Completo</label>
          <InputText 
            id="nome" 
            v-model.trim="form.nome" 
            placeholder="Digite o nome completo" 
            :disabled="submitting || dialogMode === 'view'"
            required
            autofocus
            class="w-full"
          />
        </div>

        <!-- CPF -->
        <div class="form-field">
          <label for="cpf" class="form-label">CPF</label>
          <InputMask 
            id="cpf" 
            v-model="form.cpf" 
            mask="999.999.999-99" 
            placeholder="000.000.000-00" 
            :disabled="submitting || dialogMode === 'view'"
            required
            class="w-full"
          />
        </div>

        <!-- Data de Nascimento -->
        <div class="form-field">
          <label for="data_nascimento" class="form-label">Data de Nascimento</label>
          <DatePicker 
            id="data_nascimento" 
            v-model="form.data_nascimento" 
            dateFormat="dd/mm/yy" 
            placeholder="dd/mm/aaaa"
            :disabled="submitting || dialogMode === 'view'"
            showIcon
            iconDisplay="input"
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useToast } from 'primevue/usetoast';
import { useConfirm } from 'primevue/useconfirm';
import api from '../services/api';

// Componentes PrimeVue v4
import Card from 'primevue/card';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Button from 'primevue/button';
import Dialog from 'primevue/dialog';
import InputText from 'primevue/inputtext';
import InputMask from 'primevue/inputmask';
import DatePicker from 'primevue/datepicker';

const toast = useToast();
const confirm = useConfirm();

// Estados reativos
const servidores = ref([]);
const loading = ref(false);
const submitting = ref(false);
const displayDialog = ref(false);
const dialogMode = ref('create'); // 'create', 'edit', 'view'
const selectedServidorId = ref(null);

const initialFormState = {
  nome: '',
  cpf: '',
  data_nascimento: null
};

const form = ref({ ...initialFormState });

// Título do modal dinâmico
const dialogHeader = computed(() => {
  if (dialogMode.value === 'view') return 'Visualizar Servidor';
  if (dialogMode.value === 'edit') return 'Editar Servidor';
  return 'Cadastrar Novo Servidor';
});

// Carregar lista de servidores
const fetchServidores = async () => {
  loading.value = true;
  try {
    const response = await api.get('/api/v1/servidores');
    servidores.value = response.data;
  } catch (error) {
    console.error('Erro ao buscar servidores:', error);
    toast.add({
      severity: 'error',
      summary: 'Erro de Carregamento',
      detail: 'Não foi possível carregar a lista de servidores.',
      life: 5000
    });
  } finally {
    loading.value = false;
  }
};

// Abrir dialog para cadastro
const openNewServidorDialog = () => {
  dialogMode.value = 'create';
  selectedServidorId.value = null;
  form.value = { ...initialFormState };
  displayDialog.value = true;
};

// Parser local de data da API para Date Object (evita deslocamentos de timezone)
const parseDateFromAPI = (dateStr) => {
  if (!dateStr) return null;
  const parts = dateStr.split('-');
  if (parts.length !== 3) return null;
  // Mês no JS Date é 0-indexado
  return new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
};

// Ação de Visualizar Servidor
const viewServidor = (servidor) => {
  dialogMode.value = 'view';
  selectedServidorId.value = servidor.id;
  form.value = {
    nome: servidor.nome,
    cpf: formatCPF(servidor.cpf),
    data_nascimento: parseDateFromAPI(servidor.data_nascimento)
  };
  displayDialog.value = true;
};

// Ação de Editar Servidor
const editServidor = (servidor) => {
  dialogMode.value = 'edit';
  selectedServidorId.value = servidor.id;
  form.value = {
    nome: servidor.nome,
    cpf: formatCPF(servidor.cpf),
    data_nascimento: parseDateFromAPI(servidor.data_nascimento)
  };
  displayDialog.value = true;
};

// Confirmação e Exclusão de Servidor
const confirmDelete = (servidor) => {
  confirm.require({
    message: `Tem certeza de que deseja excluir o servidor "${servidor.nome}"?`,
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
        await api.delete(`/api/v1/servidores/${servidor.id}`);
        toast.add({
          severity: 'success',
          summary: 'Sucesso',
          detail: 'Servidor excluído com sucesso!',
          life: 3000
        });
        fetchServidores();
      } catch (error) {
        console.error('Erro ao excluir servidor:', error);
        
        let errorMsg = 'Não foi possível excluir o servidor.';
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

// Fechar dialog
const closeDialog = () => {
  displayDialog.value = false;
  selectedServidorId.value = null;
  form.value = { ...initialFormState };
};

// Formata Data Object local para YYYY-MM-DD para o payload da API
const formatDateToPayload = (date) => {
  if (!date) return '';
  if (typeof date === 'string') {
    return date.substring(0, 10);
  }
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

// Salvar / Atualizar servidor
const saveServidor = async () => {
  const cpfClean = form.value.cpf.replace(/\D/g, '');
  
  if (cpfClean.length !== 11) {
    toast.add({
      severity: 'warn',
      summary: 'Validação',
      detail: 'O CPF informado deve conter 11 dígitos.',
      life: 4000
    });
    return;
  }

  if (!form.value.data_nascimento) {
    toast.add({
      severity: 'warn',
      summary: 'Validação',
      detail: 'A data de nascimento é obrigatória.',
      life: 4000
    });
    return;
  }

  submitting.value = true;

  const payload = {
    nome: form.value.nome,
    cpf: cpfClean,
    data_nascimento: formatDateToPayload(form.value.data_nascimento)
  };

  try {
    if (dialogMode.value === 'edit') {
      await api.put(`/api/v1/servidores/${selectedServidorId.value}`, payload);
      toast.add({
        severity: 'success',
        summary: 'Sucesso',
        detail: 'Servidor atualizado com sucesso!',
        life: 3000
      });
    } else {
      await api.post('/api/v1/servidores', payload);
      toast.add({
        severity: 'success',
        summary: 'Sucesso',
        detail: 'Servidor cadastrado com sucesso!',
        life: 3000
      });
    }
    closeDialog();
    fetchServidores();
  } catch (error) {
    console.error('Erro ao salvar servidor:', error);
    
    // Tratamento de erros detalhados da API
    let errorMsg = 'Não foi possível salvar o servidor.';
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

// Formatação visual de CPF para a tabela
const formatCPF = (cpf) => {
  if (!cpf) return '';
  const clean = cpf.replace(/\D/g, '');
  if (clean.length !== 11) return cpf;
  return `${clean.slice(0, 3)}.${clean.slice(3, 6)}.${clean.slice(6, 9)}-${clean.slice(9)}`;
};

// Formatação visual de data para a tabela (de YYYY-MM-DD para DD/MM/YYYY)
const formatDateBR = (dateStr) => {
  if (!dateStr) return '';
  const parts = dateStr.split('-');
  if (parts.length !== 3) return dateStr;
  return `${parts[2]}/${parts[1]}/${parts[0]}`;
};

// Ciclo de vida
onMounted(() => {
  fetchServidores();
});
</script>

<style scoped>
.servidores-container {
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

.new-btn {
  background-color: var(--p-primary-color) !important;
  border-color: var(--p-primary-color) !important;
  border-radius: 4px !important;
  font-weight: 600 !important;
  font-size: 0.875rem !important;
  transition: background-color 0.2s ease;
}

.new-btn:hover {
  background-color: var(--p-primary-600, #0d9488) !important;
  border-color: var(--p-primary-600, #0d9488) !important;
}

.table-card {
  border-radius: 6px;
  border: 1px solid var(--p-surface-200);
  background-color: #ffffff;
}

.custom-datatable {
  font-size: 0.875rem;
}

.column-nome {
  font-weight: 600;
  color: var(--p-surface-900);
}

.column-cpf, .column-data {
  color: var(--p-surface-700);
}

.column-actions {
  display: flex;
  justify-content: center;
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

.servidor-form {
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
  background-color: var(--p-primary-600, #0d9488) !important;
  border-color: var(--p-primary-600, #0d9488) !important;
}

.w-full {
  width: 100%;
}
</style>
