<template>
  <div class="simulacao-container">
    <!-- Cabeçalho -->
    <div class="page-header">
      <div class="header-info">
        <h2 class="page-title">Simulação de Impacto Financeiro</h2>
        <p class="page-subtitle">Simule novos cenários de enquadramento, progressão e reajustes.</p>
      </div>
    </div>

    <div class="grid layout-grid">
      <!-- Painel de Configuração da Simulação -->
      <div class="col-12 lg:col-4 config-panel">
        <Card class="shadow-sm border border-round">
          <template #title>
            <span class="card-title-text"><i class="pi pi-cog mr-2"></i>Parâmetros da Simulação</span>
          </template>
          <template #content>
            <form @submit.prevent="runSimulation" class="sim-form">
              <!-- Servidor -->
              <div class="form-field">
                <label class="form-label">Servidor Beneficiário</label>
                <Dropdown 
                  v-model="simForm.servidor_id" 
                  :options="servidores" 
                  optionLabel="nome" 
                  optionValue="id" 
                  placeholder="Selecione o servidor" 
                  filter
                  required 
                />
              </div>

              <!-- Novo Vencimento -->
              <div class="form-field">
                <label class="form-label">Novo Vencimento Básico</label>
                <Dropdown 
                  v-model="simForm.novo_vencimento_id" 
                  :options="vencimentos" 
                  optionLabel="desc" 
                  optionValue="id" 
                  placeholder="Selecione a classe/nível" 
                  filter
                  required 
                />
              </div>

              <!-- Novo GSTU -->
              <div class="form-field">
                <label class="form-label">Novo GSTU (Opcional)</label>
                <Dropdown 
                  v-model="simForm.novo_gstu_id" 
                  :options="gstus" 
                  optionLabel="desc" 
                  optionValue="id" 
                  placeholder="Selecione a GSTU" 
                  filter
                  showClear
                />
              </div>

              <!-- Data de Vigência -->
              <div class="form-field">
                <label class="form-label">Data de Vigência da Simulação</label>
                <DatePicker 
                  v-model="simForm.data_vigencia" 
                  dateFormat="dd/mm/yy" 
                  placeholder="dd/mm/aaaa"
                  required 
                />
              </div>

              <!-- Mês de Férias -->
              <div class="form-field">
                <label class="form-label">Mês de Gozo de Férias</label>
                <Dropdown 
                  v-model="simForm.mes_ferias" 
                  :options="mesesAno" 
                  optionLabel="label" 
                  optionValue="value" 
                  placeholder="Selecione o mês" 
                  required 
                />
              </div>

              <div class="form-actions-full">
                <Button 
                  type="submit" 
                  label="Calcular Impacto" 
                  icon="pi pi-sliders-h" 
                  class="save-submit-btn w-full mt-3" 
                  :loading="calculating" 
                />
              </div>
            </form>
          </template>
        </Card>
      </div>

      <!-- Painel de Resultados da Simulação -->
      <div class="col-12 lg:col-8 results-panel">
        <div v-if="!resultado" class="no-result-placeholder">
          <i class="pi pi-sliders-h placeholder-big-icon mb-3"></i>
          <h3>Pronto para Simular</h3>
          <p>Preencha os parâmetros da simulação ao lado e clique em "Calcular Impacto".</p>
        </div>

        <div v-else class="results-content">
          <!-- KPIs -->
          <div class="kpis-grid mb-4">
            <div class="kpi-card shadow-sm border border-round card-mensal">
              <span class="kpi-label">Impacto Mensal Bruto</span>
              <h2 class="kpi-value">{{ formatCurrency(resultado.impacto_mensal) }}</h2>
              <span class="kpi-sub">+{{ formatPercent(resultado.percentual_impacto) }}%</span>
            </div>

            <div class="kpi-card shadow-sm border border-round card-anual-1">
              <span class="kpi-label">Impacto Primeiro Ano (13º+Férias)</span>
              <h2 class="kpi-value">{{ formatCurrency(resultado.impacto_anual_primeiro_ano) }}</h2>
              <span class="kpi-sub">Vigência Proporcional</span>
            </div>

            <div class="kpi-card shadow-sm border border-round card-anual-est">
              <span class="kpi-label">Impacto Anual Estimado (12m)</span>
              <h2 class="kpi-value">{{ formatCurrency(resultado.impacto_anual_estimado) }}</h2>
              <span class="kpi-sub">Ano Completo</span>
            </div>

            <div class="kpi-card shadow-sm border border-round card-retroativo">
              <span class="kpi-label">Total Retroativo Estimado</span>
              <h2 class="kpi-value">{{ formatCurrency(resultado.retroativo_total) }}</h2>
              <span class="kpi-sub">Vigência Retroativa</span>
            </div>
          </div>

          <!-- Ações do Resultado -->
          <div class="result-actions-row mb-4">
            <Button 
              label="Exportar Relatório PDF" 
              icon="pi pi-file-pdf" 
              severity="danger" 
              class="p-button-sm border-round" 
              @click="exportPDF" 
            />
          </div>

          <TabView>
            <!-- Comparativo de Rubricas -->
            <TabPanel header="Comparativo de Rubricas">
              <DataTable :value="comparativoRubricas" class="p-datatable-sm shadow-sm" stripedRows>
                <Column field="rubrica" header="Rubrica" class="font-bold"></Column>
                <Column header="Cenário Atual">
                  <template #body="slotProps">
                    {{ formatCurrency(slotProps.data.atual) }}
                  </template>
                </Column>
                <Column header="Cenário Proposto">
                  <template #body="slotProps">
                    {{ formatCurrency(slotProps.data.proposto) }}
                  </template>
                </Column>
                <Column header="Diferença Mensal">
                  <template #body="slotProps">
                    <span :class="{'text-green font-bold': slotProps.data.diferenca > 0, 'text-muted': slotProps.data.diferenca === 0}">
                      +{{ formatCurrency(slotProps.data.diferenca) }}
                    </span>
                  </template>
                </Column>
              </DataTable>
            </TabPanel>

            <!-- Evolução de Retroativos -->
            <TabPanel header="Demonstrativo de Competências Retroativas">
              <div v-if="!resultado.detalhes_retroativos.length" class="text-center py-4 text-muted">
                Não há impactos retroativos para a data de vigência selecionada (vigência futura ou atual).
              </div>
              <DataTable v-else :value="resultado.detalhes_retroativos" class="p-datatable-sm shadow-sm" stripedRows>
                <Column field="competencia" header="Competência"></Column>
                <Column header="Diferença Retroativa Devida">
                  <template #body="slotProps">
                    <span class="text-green font-bold">+{{ formatCurrency(slotProps.data.impacto) }}</span>
                  </template>
                </Column>
              </DataTable>
            </TabPanel>
          </TabView>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useToast } from 'primevue/usetoast';
import api from '../services/api';

// Componentes PrimeVue v4
import Card from 'primevue/card';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Button from 'primevue/button';
import Dropdown from 'primevue/dropdown';
import DatePicker from 'primevue/datepicker';
import TabView from 'primevue/tabview';
import TabPanel from 'primevue/tabpanel';

const toast = useToast();

// Estados reativos
const servidores = ref([]);
const vencimentos = ref([]);
const gstus = ref([]);
const calculating = ref(false);
const resultado = ref(null);
const comparativoRubricas = ref([]);
const simulacaoItemId = ref(null);

const simForm = ref({
  servidor_id: null,
  novo_vencimento_id: null,
  novo_gstu_id: null,
  data_vigencia: null,
  mes_ferias: 6
});

const mesesAno = [
  { label: 'Janeiro', value: 1 },
  { label: 'Fevereiro', value: 2 },
  { label: 'Março', value: 3 },
  { label: 'Abril', value: 4 },
  { label: 'Maio', value: 5 },
  { label: 'Junho', value: 6 },
  { label: 'Julho', value: 7 },
  { label: 'Agosto', value: 8 },
  { label: 'Setembro', value: 9 },
  { label: 'Outubro', value: 10 },
  { label: 'Novembro', value: 11 },
  { label: 'Dezembro', value: 12 }
];

// Carregar servidores e lookups
const loadData = async () => {
  try {
    const [servidoresRes, vencRes, gstuRes] = await Promise.all([
      api.get('/api/v1/servidores'),
      api.get('/api/v1/vencimentos'),
      api.get('/api/v1/gstu')
    ]);

    servidores.value = servidoresRes.data;
    vencimentos.value = vencRes.data.map(v => ({
      ...v,
      desc: `${v.classe} - Nível ${v.nivel_grau} - CH ${v.carga_horaria}h (R$ ${formatNumber(v.valor_base)})`
    }));
    gstus.value = gstuRes.data.map(g => ({
      ...g,
      desc: `${g.grau} - Ref ${g.referencia} (R$ ${formatNumber(g.valor_gstu)})`
    }));
  } catch (error) {
    console.error('Erro ao carregar dados:', error);
    toast.add({
      severity: 'error',
      summary: 'Erro de Carregamento',
      detail: 'Não foi possível inicializar os lookups.',
      life: 5000
    });
  }
};

onMounted(() => {
  loadData();
});

// Executar Simulação
const runSimulation = async () => {
  calculating.value = true;
  resultado.value = null;
  simulacaoItemId.value = null;

  const payload = {
    servidor_id: simForm.value.servidor_id,
    novo_vencimento_id: simForm.value.novo_vencimento_id,
    novo_gstu_id: simForm.value.novo_gstu_id,
    data_vigencia: formatDateToPayload(simForm.value.data_vigencia),
    mes_ferias: simForm.value.mes_ferias
  };

  try {
    const response = await api.post('/api/v1/simulacao', payload);
    const data = response.data;
    
    simulacaoItemId.value = data.id;
    resultado.value = data.resultado_calculo_json;
    
    buildComparativo(data.resultado_calculo_json);
    
    toast.add({
      severity: 'success',
      summary: 'Simulação Concluída',
      detail: 'O cálculo de impacto financeiro foi realizado com sucesso.',
      life: 3000
    });
  } catch (error) {
    console.error(error);
    toast.add({
      severity: 'error',
      summary: 'Erro no Cálculo',
      detail: error.response?.data?.detail || 'Erro desconhecido ao processar cálculo.',
      life: 6000
    });
  } finally {
    calculating.value = false;
  }
};

const buildComparativo = (res) => {
  const rubricasMap = [
    { name: 'Vencimento Básico', key_atual: 'vencimento_atual', key_prop: 'vencimento_proposto' },
    { name: 'GSTU', key_atual: 'gstu_atual', key_prop: 'gstu_proposto' },
    { name: 'ATS', key_atual: 'ats_atual', key_prop: 'ats_proposto' },
    { name: 'CET', key_atual: 'cet_atual', key_prop: 'cet_proposto' },
    { name: 'Insalubridade', key_atual: 'insalubridade_atual', key_prop: 'insalubridade_proposto' },
    { name: 'Estabilidade Econômica', key_atual: 'estabilidade_atual', key_prop: 'estabilidade_proposto' },
    { name: 'VPESS', key_atual: 'vpess_atual', key_prop: 'vpess_proposto' },
    { name: 'Custo Total Mensal', key_atual: 'valor_total_atual', key_prop: 'valor_total_proposto' }
  ];

  comparativoRubricas.value = rubricasMap.map(r => {
    const at = res[r.key_atual] || 0;
    const prop = res[r.key_prop] || 0;
    return {
      rubrica: r.name,
      atual: at,
      proposto: prop,
      diferenca: prop - at
    };
  });
};

// Exportar PDF
const exportPDF = async () => {
  if (!simulacaoItemId.value) return;
  
  try {
    toast.add({
      severity: 'info',
      summary: 'Gerando PDF',
      detail: 'Seu relatório está sendo exportado...',
      life: 2000
    });

    const response = await api.get(`/api/v1/simulacao/${simulacaoItemId.value}/pdf`, {
      responseType: 'blob'
    });

    const blob = new Blob([response.data], { type: 'application/pdf' });
    const link = document.createElement('a');
    link.href = window.URL.createObjectURL(blob);
    link.download = `Relatorio_Simulacao_${simulacaoItemId.value.substring(0, 8)}.pdf`;
    link.click();
    window.URL.revokeObjectURL(link.href);
  } catch (error) {
    console.error(error);
    toast.add({
      severity: 'error',
      summary: 'Erro na Exportação',
      detail: 'Não foi possível fazer o download do PDF.',
      life: 5000
    });
  }
};

// Formatação helpers
const formatCurrency = (val) => {
  if (val === undefined || val === null) return 'R$ 0,00';
  return parseFloat(val).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
};

const formatPercent = (val) => {
  if (val === undefined || val === null) return '0,00';
  return parseFloat(val).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

const formatNumber = (val) => {
  if (val === undefined || val === null) return '0,00';
  return parseFloat(val).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

const formatDateToPayload = (date) => {
  if (!date) return '';
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};
</script>

<style scoped>
.simulacao-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.page-header {
  margin-bottom: 0.5rem;
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

.card-title-text {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--p-surface-800);
}

.sim-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
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

.save-submit-btn {
  background-color: var(--p-primary-color) !important;
  border-color: var(--p-primary-color) !important;
  font-weight: 600 !important;
}

.save-submit-btn:hover {
  background-color: var(--p-primary-600, #0d9488) !important;
  border-color: var(--p-primary-600, #0d9488) !important;
}

.w-full {
  width: 100%;
}

.layout-grid {
  display: grid;
  grid-template-columns: 350px 1fr;
  gap: 2rem;
}

@media (max-width: 992px) {
  .layout-grid {
    grid-template-columns: 1fr;
  }
}

.no-result-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 6rem 2rem;
  border: 2px dashed var(--p-surface-200);
  border-radius: 8px;
  background-color: var(--p-surface-50);
  color: var(--p-surface-400);
  text-align: center;
}

.placeholder-big-icon {
  font-size: 3rem;
}

/* KPIs */
.kpis-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.kpi-card {
  padding: 1.5rem;
  background-color: #ffffff;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.kpi-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--p-surface-400);
}

.kpi-value {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.kpi-sub {
  font-size: 0.75rem;
  font-weight: 600;
}

/* Cores específicas dos KPIs */
.card-mensal {
  border-left: 4px solid var(--p-primary-color) !important;
}
.card-mensal .kpi-sub {
  color: var(--p-primary-600);
}

.card-anual-1 {
  border-left: 4px solid #3b82f6 !important;
}
.card-anual-1 .kpi-sub {
  color: #2563eb;
}

.card-anual-est {
  border-left: 4px solid #10b981 !important;
}
.card-anual-est .kpi-sub {
  color: #059669;
}

.card-retroativo {
  border-left: 4px solid #f59e0b !important;
}
.card-retroativo .kpi-sub {
  color: #d97706;
}

.text-green {
  color: #059669;
}

.text-muted {
  color: var(--p-surface-400);
}
</style>
