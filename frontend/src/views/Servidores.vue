<template>
  <div class="servidores-container">
    <!-- Cabeçalho do Módulo -->
    <div class="page-header">
      <div class="header-info">
        <h2 class="page-title">Gestão de Servidores</h2>
        <p class="page-subtitle">Listagem, cadastro e prontuário de servidores da instituição.</p>
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
          
          <Column header="Ações" class="column-actions" headerStyle="width: 200px; text-align: center" bodyStyle="text-align: center">
            <template #body="slotProps">
              <div class="actions-wrapper">
                <Button 
                  icon="pi pi-folder-open" 
                  text 
                  rounded 
                  severity="secondary" 
                  class="action-btn prontuario-btn"
                  title="Prontuário"
                  @click="openProntuario(slotProps.data)" 
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

    <!-- Dialog para Novo Servidor / Edição -->
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

        <div class="form-actions">
          <Button 
            type="button" 
            label="Cancelar" 
            icon="pi pi-times" 
            class="p-button-text p-button-secondary cancel-btn" 
            :disabled="submitting"
            @click="closeDialog" 
          />
          <Button 
            type="submit" 
            label="Salvar" 
            icon="pi pi-check" 
            class="save-submit-btn" 
            :loading="submitting" 
          />
        </div>
      </form>
    </Dialog>

    <!-- Dialog Prontuário do Servidor (Grande/Premium) -->
    <Dialog
      v-model:visible="displayProntuarioDialog"
      header="Prontuário Funcional do Servidor"
      :modal="true"
      :draggable="false"
      class="custom-prontuario-dialog"
      :style="{ width: '80vw' }"
      @hide="closeProntuario"
    >
      <div v-if="selectedServidor" class="prontuario-layout">
        <!-- Sidebar Info -->
        <div class="prontuario-sidebar">
          <div class="profile-avatar-container">
            <i class="pi pi-user avatar-icon"></i>
            <h3 class="profile-name">{{ selectedServidor.nome }}</h3>
            <span class="profile-badge">Servidor UEFS</span>
          </div>
          <Divider />
          <div class="profile-meta">
            <div class="meta-item">
              <span class="meta-title">CPF</span>
              <span class="meta-desc">{{ formatCPF(selectedServidor.cpf) }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-title">Nascimento</span>
              <span class="meta-desc">{{ formatDateBR(selectedServidor.data_nascimento) }}</span>
            </div>
          </div>
        </div>

        <!-- Main Content (Abas) -->
        <div class="prontuario-main">
          <TabView>
            <TabPanel header="Vínculos Funcionais">
              <div class="tab-header-row">
                <h3 class="tab-title">Vínculos do Servidor</h3>
                <Button 
                  label="Novo Vínculo" 
                  icon="pi pi-plus" 
                  size="small" 
                  class="save-submit-btn" 
                  @click="openNovoVinculoDialog" 
                />
              </div>

              <div v-if="loadingVinculos" class="loading-state">
                <i class="pi pi-spin pi-spinner spinner-icon"></i>
                <p>Carregando vínculos...</p>
              </div>
              <div v-else-if="!vinculos.length" class="empty-state">
                <p>Nenhum vínculo funcional cadastrado para este servidor.</p>
              </div>
              <div v-else class="vinculos-cards-list">
                <div v-for="vinculo in vinculos" :key="vinculo.id" class="vinculo-card mb-4">
                  <div class="vinculo-card-header">
                    <div class="vinculo-header-left">
                      <span class="matricula-badge">Matrícula: {{ vinculo.matricula }}</span>
                      <span class="cargo-title">{{ getCargoNome(vinculo.cargo_id) }}</span>
                    </div>
                    <span :class="['status-badge', vinculo.ativo ? 'status-ativo' : 'status-inativo']">
                      {{ vinculo.ativo ? 'Ativo' : 'Inativo' }}
                    </span>
                  </div>

                  <div class="vinculo-card-body">
                    <!-- Meta info grids -->
                    <div class="meta-grid">
                      <div class="meta-col">
                        <span class="label">Admissão</span>
                        <span class="value">{{ formatDateBR(vinculo.data_admissao) }}</span>
                      </div>
                      <div class="meta-col">
                        <span class="label">Regime Previdenciário</span>
                        <span class="value">{{ formatEnum(vinculo.regime_previdenciario) }}</span>
                      </div>
                      <div class="meta-col">
                        <span class="label">Previdência Complementar</span>
                        <span class="value">{{ vinculo.participante_prev_complementar ? `Sim (${vinculo.aliquota_coparticipacao_complementar}%)` : 'Não' }}</span>
                      </div>
                      <div class="meta-col">
                        <span class="label">Tipo de Vínculo</span>
                        <span class="value">{{ formatEnum(vinculo.tipo_vinculo) }}</span>
                      </div>
                    </div>

                    <Divider />

                    <!-- Histórico Funcional -->
                    <div class="inner-section mb-4">
                      <div class="inner-header">
                        <h4 class="inner-title"><i class="pi pi-history mr-2"></i>Histórico Funcional (Enquadramentos)</h4>
                        <Button 
                          label="Novo Enquadramento" 
                          icon="pi pi-plus" 
                          size="small" 
                          severity="success" 
                          outlined 
                          @click="openNovoHistoricoDialog(vinculo)" 
                        />
                      </div>
                      
                      <DataTable :value="historicosPorVinculo[vinculo.id] || []" class="p-datatable-sm" stripedRows>
                        <Column header="Início">
                          <template #body="slotProps">
                            {{ formatDateBR(slotProps.data.data_inicio) }}
                          </template>
                        </Column>
                        <Column header="Fim">
                          <template #body="slotProps">
                            {{ slotProps.data.data_fim === '9999-12-31' ? 'Vigente (Indefinido)' : formatDateBR(slotProps.data.data_fim) }}
                          </template>
                        </Column>
                        <Column header="Classe / Nível">
                          <template #body="slotProps">
                            {{ getVencimentoDesc(slotProps.data.tabela_vencimento_id) }}
                          </template>
                        </Column>
                        <Column header="GSTU">
                          <template #body="slotProps">
                            {{ getGstuDesc(slotProps.data.tabela_gstu_id) }}
                          </template>
                        </Column>
                        <Column header="CET" field="cet_percentual">
                          <template #body="slotProps">
                            {{ slotProps.data.cet_percentual }}%
                          </template>
                        </Column>
                        <Column header="Insalubridade" field="insalubridade_percentual">
                          <template #body="slotProps">
                            {{ slotProps.data.insalubridade_percentual }}%
                          </template>
                        </Column>
                        <Column header="VPESS" field="vpess_valor">
                          <template #body="slotProps">
                            {{ formatCurrency(slotProps.data.vpess_valor) }}
                          </template>
                        </Column>
                      </DataTable>
                    </div>

                    <Divider />

                    <!-- Averbações -->
                    <div class="inner-section">
                      <div class="inner-header">
                        <h4 class="inner-title"><i class="pi pi-calendar mr-2"></i>Averbações de Tempo</h4>
                        <Button 
                          label="Nova Averbação" 
                          icon="pi pi-plus" 
                          size="small" 
                          severity="success" 
                          outlined 
                          @click="openNovaAverbacaoDialog(vinculo)" 
                        />
                      </div>

                      <DataTable :value="averbacoesPorVinculo[vinculo.id] || []" class="p-datatable-sm" stripedRows>
                        <Column header="Data Averbação">
                          <template #body="slotProps">
                            {{ formatDateBR(slotProps.data.data_averbacao) }}
                          </template>
                        </Column>
                        <Column header="Dias" field="dias_averbados"></Column>
                        <Column header="Tipo" field="tipo_averbacao"></Column>
                        <Column header="Nº Processo" field="processo_numero"></Column>
                      </DataTable>
                    </div>
                  </div>
                </div>
              </div>
            </TabPanel>
          </TabView>
        </div>
      </div>
    </Dialog>

    <!-- Dialog Novo Vínculo -->
    <Dialog
      v-model:visible="displayVinculoDialog"
      header="Cadastrar Novo Vínculo"
      :modal="true"
      :draggable="false"
      class="custom-dialog"
      :style="{ width: '450px' }"
    >
      <form @submit.prevent="saveVinculo" class="servidor-form">
        <div class="form-field">
          <label class="form-label">Matrícula</label>
          <InputText v-model.trim="vinculoForm.matricula" placeholder="Digite a matrícula" required />
        </div>

        <div class="form-field">
          <label class="form-label">Cargo</label>
          <Dropdown 
            v-model="vinculoForm.cargo_id" 
            :options="cargos" 
            optionLabel="nome" 
            optionValue="id" 
            placeholder="Selecione o cargo" 
            required 
          />
        </div>

        <div class="form-field">
          <label class="form-label">Data de Admissão</label>
          <DatePicker v-model="vinculoForm.data_admissao" dateFormat="dd/mm/yy" placeholder="dd/mm/aaaa" required />
        </div>

        <div class="form-field">
          <label class="form-label">Regime Previdenciário</label>
          <Dropdown 
            v-model="vinculoForm.regime_previdenciario" 
            :options="regimes" 
            optionLabel="label" 
            optionValue="value" 
            placeholder="Selecione o regime" 
            required 
          />
        </div>

        <div class="form-field flex-row-align">
          <Checkbox v-model="vinculoForm.participante_prev_complementar" :binary="true" id="prev_comp" />
          <label for="prev_comp" class="form-label mb-0 pointer">Participa de Previdência Complementar?</label>
        </div>

        <div v-if="vinculoForm.participante_prev_complementar" class="form-field">
          <label class="form-label">Alíquota Coparticipação (%)</label>
          <InputNumber v-model="vinculoForm.aliquota_coparticipacao_complementar" :min="0" :max="100" :minFractionDigits="2" :maxFractionDigits="2" required />
        </div>

        <div class="form-field">
          <label class="form-label">Tipo de Vínculo</label>
          <Dropdown 
            v-model="vinculoForm.tipo_vinculo" 
            :options="tiposVinculo" 
            optionLabel="label" 
            optionValue="value" 
            placeholder="Selecione o tipo de vínculo" 
            required 
          />
        </div>

        <div class="form-actions">
          <Button type="button" label="Cancelar" icon="pi pi-times" class="p-button-text p-button-secondary cancel-btn" @click="displayVinculoDialog = false" />
          <Button type="submit" label="Salvar Vínculo" icon="pi pi-check" class="save-submit-btn" :loading="vinculoSubmitting" />
        </div>
      </form>
    </Dialog>

    <!-- Dialog Novo Enquadramento (Histórico Funcional) -->
    <Dialog
      v-model:visible="displayHistoricoDialog"
      header="Cadastrar Novo Enquadramento"
      :modal="true"
      :draggable="false"
      class="custom-dialog"
      :style="{ width: '500px' }"
    >
      <form @submit.prevent="saveHistorico" class="servidor-form">
        <div class="form-field">
          <label class="form-label">Data de Início da Vigência</label>
          <DatePicker v-model="historicoForm.data_inicio" dateFormat="dd/mm/yy" placeholder="dd/mm/aaaa" required />
        </div>

        <div class="form-field flex-row-align">
          <Checkbox v-model="historicoForm.definir_fim" :binary="true" id="def_fim" />
          <label for="def_fim" class="form-label mb-0 pointer">Definir data de fim?</label>
        </div>

        <div v-if="historicoForm.definir_fim" class="form-field">
          <label class="form-label">Data de Fim da Vigência</label>
          <DatePicker v-model="historicoForm.data_fim" dateFormat="dd/mm/yy" placeholder="dd/mm/aaaa" required />
        </div>

        <div class="form-field">
          <label class="form-label">Classe / Nível (Tabela Vencimento)</label>
          <Dropdown 
            v-model="historicoForm.tabela_vencimento_id" 
            :options="vencimentos" 
            optionLabel="desc" 
            optionValue="id" 
            placeholder="Selecione a classe/nível" 
            filter
            required 
          />
        </div>

        <div class="form-field">
          <label class="form-label">Grau / Referência (GSTU) - Opcional</label>
          <Dropdown 
            v-model="historicoForm.tabela_gstu_id" 
            :options="gstuLista" 
            optionLabel="desc" 
            optionValue="id" 
            placeholder="Selecione a GSTU" 
            filter
            showClear
          />
        </div>

        <div class="form-field">
          <label class="form-label">CET (%)</label>
          <InputNumber v-model="historicoForm.cet_percentual" :min="0" :max="500" :minFractionDigits="2" :maxFractionDigits="2" required />
        </div>

        <div class="form-field">
          <label class="form-label">Insalubridade (%)</label>
          <InputNumber v-model="historicoForm.insalubridade_percentual" :min="0" :max="100" :minFractionDigits="2" :maxFractionDigits="2" required />
        </div>

        <div class="form-field">
          <label class="form-label">VPESS (Valor)</label>
          <InputNumber v-model="historicoForm.vpess_valor" :min="0" :minFractionDigits="2" :maxFractionDigits="2" required />
        </div>

        <div class="form-field">
          <label class="form-label">Função Comissionada (Opcional)</label>
          <Dropdown 
            v-model="historicoForm.tabela_comissao_id" 
            :options="comissoes" 
            optionLabel="desc" 
            optionValue="id" 
            placeholder="Selecione a comissão" 
            filter
            showClear
          />
        </div>

        <div v-if="historicoForm.tabela_comissao_id" class="form-field">
          <label class="form-label">Percentual Estabilizado (%)</label>
          <InputNumber v-model="historicoForm.percentual_estabilizado" :min="0" :max="100" :minFractionDigits="2" :maxFractionDigits="2" required />
        </div>

        <div class="form-actions">
          <Button type="button" label="Cancelar" icon="pi pi-times" class="p-button-text p-button-secondary cancel-btn" @click="displayHistoricoDialog = false" />
          <Button type="submit" label="Salvar Enquadramento" icon="pi pi-check" class="save-submit-btn" :loading="historicoSubmitting" />
        </div>
      </form>
    </Dialog>

    <!-- Dialog Nova Averbação -->
    <Dialog
      v-model:visible="displayAverbacaoDialog"
      header="Cadastrar Nova Averbação"
      :modal="true"
      :draggable="false"
      class="custom-dialog"
      :style="{ width: '450px' }"
    >
      <form @submit.prevent="saveAverbacao" class="servidor-form">
        <div class="form-field">
          <label class="form-label">Data da Averbação</label>
          <DatePicker v-model="averbacaoForm.data_averbacao" dateFormat="dd/mm/yy" placeholder="dd/mm/aaaa" required />
        </div>

        <div class="form-field">
          <label class="form-label">Dias Averbados</label>
          <InputNumber v-model="averbacaoForm.dias_averbados" :min="1" required />
        </div>

        <div class="form-field">
          <label class="form-label">Tipo de Averbação</label>
          <Dropdown 
            v-model="averbacaoForm.tipo_averbacao" 
            :options="tiposAverbacao" 
            optionLabel="label" 
            optionValue="value" 
            placeholder="Selecione o tipo" 
            required 
          />
        </div>

        <div class="form-field">
          <label class="form-label">Número do Processo</label>
          <InputText v-model.trim="averbacaoForm.processo_numero" placeholder="Ex: PROC-1234/2026" required />
        </div>

        <div class="form-actions">
          <Button type="button" label="Cancelar" icon="pi pi-times" class="p-button-text p-button-secondary cancel-btn" @click="displayAverbacaoDialog = false" />
          <Button type="submit" label="Salvar Averbação" icon="pi pi-check" class="save-submit-btn" :loading="averbacaoSubmitting" />
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
import Dropdown from 'primevue/dropdown';
import InputNumber from 'primevue/inputnumber';
import Checkbox from 'primevue/checkbox';
import Divider from 'primevue/divider';
import TabView from 'primevue/tabview';
import TabPanel from 'primevue/tabpanel';

const toast = useToast();
const confirm = useConfirm();

// Estados reativos principais
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

// Estados reativos prontuário
const displayProntuarioDialog = ref(false);
const selectedServidor = ref(null);
const vinculos = ref([]);
const loadingVinculos = ref(false);
const historicosPorVinculo = ref({});
const averbacoesPorVinculo = ref({});

// Lookups
const cargos = ref([]);
const vencimentos = ref([]);
const gstuLista = ref([]);
const comissoes = ref([]);

// Estados reativos diálogos secundários
const displayVinculoDialog = ref(false);
const vinculoSubmitting = ref(false);
const vinculoForm = ref({
  matricula: '',
  data_admissao: null,
  cargo_id: null,
  regime_previdenciario: null,
  participante_prev_complementar: false,
  aliquota_coparticipacao_complementar: 0.0,
  tipo_vinculo: null,
  ativo: true
});

const displayHistoricoDialog = ref(false);
const historicoSubmitting = ref(false);
const activeVinculoForHistorico = ref(null);
const historicoForm = ref({
  data_inicio: null,
  definir_fim: false,
  data_fim: null,
  tabela_vencimento_id: null,
  tabela_gstu_id: null,
  cet_percentual: 0.0,
  insalubridade_percentual: 0.0,
  vpess_valor: 0.0,
  tabela_comissao_id: null,
  percentual_estabilizado: 0.0
});

const displayAverbacaoDialog = ref(false);
const averbacaoSubmitting = ref(false);
const activeVinculoForAverbacao = ref(null);
const averbacaoForm = ref({
  dias_averbados: 30,
  tipo_averbacao: 'ATS',
  data_averbacao: null,
  processo_numero: ''
});

// Enums / Lookups definidos estaticamente
const regimes = [
  { label: 'BAPREV - Regime Próprio', value: 'BAPREV_REGIME_PROPRIO' },
  { label: 'PREVBAHIA - Complementar', value: 'PREVBAHIA_COMPLEMENTAR' }
];

const tiposVinculo = [
  { label: 'Estatutário', value: 'ESTATUTARIO' },
  { label: 'REDA', value: 'REDA' },
  { label: 'CLT', value: 'CLT' }
];

const tiposAverbacao = [
  { label: 'Adicional por Tempo de Serviço (ATS)', value: 'ATS' },
  { label: 'Aposentadoria', value: 'APOSENTADORIA' }
];

const dialogHeader = computed(() => {
  if (dialogMode.value === 'view') return 'Visualizar Servidor';
  if (dialogMode.value === 'edit') return 'Editar Servidor';
  return 'Cadastrar Novo Servidor';
});

// Carregar servidores
const fetchServidores = async () => {
  loading.value = true;
  try {
    const response = await api.get('/api/v1/servidores');
    servidores.value = response.data;
  } catch (error) {
    console.error(error);
    toast.add({
      severity: 'error',
      summary: 'Erro',
      detail: 'Não foi possível carregar a lista de servidores.',
      life: 5000
    });
  } finally {
    loading.value = false;
  }
};

// Carregar lookups gerais
const fetchGeneralLookups = async () => {
  try {
    const [cargosRes, vencRes, gstuRes, comissoesRes] = await Promise.all([
      api.get('/api/v1/servidores/cargos'),
      api.get('/api/v1/vencimentos'),
      api.get('/api/v1/gstu'),
      api.get('/api/v1/parametros/comissao')
    ]);

    cargos.value = cargosRes.data;
    vencimentos.value = vencRes.data.map(v => ({
      ...v,
      desc: `${v.classe} - Nível ${v.nivel_grau} - CH ${v.carga_horaria}h (R$ ${formatNumber(v.valor_base)})`
    }));
    gstuLista.value = gstuRes.data.map(g => ({
      ...g,
      desc: `${g.grau} - Ref ${g.referencia} (R$ ${formatNumber(g.valor_gstu)})`
    }));
    comissoes.value = comissoesRes.data.map(c => ({
      ...c,
      desc: `${c.simbolo} (R$ ${formatNumber(c.valor_comissao)})`
    }));
  } catch (error) {
    console.error('Erro ao carregar lookups:', error);
  }
};

onMounted(() => {
  fetchServidores();
  fetchGeneralLookups();
});

// Ações do Servidor
const openNewServidorDialog = () => {
  dialogMode.value = 'create';
  selectedServidorId.value = null;
  form.value = { ...initialFormState };
  displayDialog.value = true;
};

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

const closeDialog = () => {
  displayDialog.value = false;
  selectedServidorId.value = null;
  form.value = { ...initialFormState };
};

const saveServidor = async () => {
  const cpfClean = form.value.cpf.replace(/\D/g, '');
  if (cpfClean.length !== 11) {
    toast.add({ severity: 'warn', summary: 'Validação', detail: 'CPF inválido.', life: 4000 });
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
      toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Servidor atualizado!', life: 3000 });
    } else {
      await api.post('/api/v1/servidores', payload);
      toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Servidor cadastrado!', life: 3000 });
    }
    closeDialog();
    fetchServidores();
  } catch (error) {
    console.error(error);
    toast.add({ severity: 'error', summary: 'Erro', detail: error.response?.data?.detail || 'Erro ao salvar.', life: 5000 });
  } finally {
    submitting.value = false;
  }
};

const confirmDelete = (servidor) => {
  confirm.require({
    message: `Excluir definitivamente o servidor "${servidor.nome}"?`,
    header: 'Confirmação de Exclusão',
    icon: 'pi pi-exclamation-triangle',
    acceptProps: { label: 'Excluir', severity: 'danger' },
    rejectProps: { label: 'Cancelar', severity: 'secondary', outlined: true },
    accept: async () => {
      try {
        await api.delete(`/api/v1/servidores/${servidor.id}`);
        toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Servidor excluído!', life: 3000 });
        fetchServidores();
      } catch (error) {
        toast.add({ severity: 'error', summary: 'Erro', detail: error.response?.data?.detail || 'Erro ao excluir.', life: 6000 });
      }
    }
  });
};

// ============================================
// MÉTODOS DO PRONTUÁRIO
// ============================================
const openProntuario = (servidor) => {
  selectedServidor.value = servidor;
  displayProntuarioDialog.value = true;
  fetchVinculos(servidor.id);
};

const closeProntuario = () => {
  displayProntuarioDialog.value = false;
  selectedServidor.value = null;
  vinculos.value = [];
  historicosPorVinculo.value = {};
  averbacoesPorVinculo.value = {};
};

const fetchVinculos = async (servidorId) => {
  loadingVinculos.value = true;
  try {
    const response = await api.get(`/api/v1/servidores/${servidorId}/vinculos`);
    vinculos.value = response.data;
    
    // Buscar histórico e averbações de cada vínculo
    await Promise.all(response.data.map(async (v) => {
      await Promise.all([
        fetchHistoricos(v.id),
        fetchAverbacoes(v.id)
      ]);
    }));
  } catch (error) {
    console.error(error);
  } finally {
    loadingVinculos.value = false;
  }
};

const fetchHistoricos = async (vinculoId) => {
  try {
    const response = await api.get(`/api/v1/servidores/vinculos/${vinculoId}/historico`);
    historicosPorVinculo.value[vinculoId] = response.data;
  } catch (error) {
    console.error(error);
  }
};

const fetchAverbacoes = async (vinculoId) => {
  try {
    const response = await api.get(`/api/v1/servidores/vinculos/${vinculoId}/averbacoes`);
    averbacoesPorVinculo.value[vinculoId] = response.data;
  } catch (error) {
    console.error(error);
  }
};

// Diálogos Secundários (Vínculo, Histórico, Averbação)
const openNovoVinculoDialog = () => {
  vinculoForm.value = {
    matricula: '',
    data_admissao: null,
    cargo_id: null,
    regime_previdenciario: 'BAPREV_REGIME_PROPRIO',
    participante_prev_complementar: false,
    aliquota_coparticipacao_complementar: 0.0,
    tipo_vinculo: 'ESTATUTARIO',
    ativo: true
  };
  displayVinculoDialog.value = true;
};

const saveVinculo = async () => {
  vinculoSubmitting.value = true;
  const payload = {
    ...vinculoForm.value,
    data_admissao: formatDateToPayload(vinculoForm.value.data_admissao)
  };
  try {
    await api.post(`/api/v1/servidores/${selectedServidor.value.id}/vinculos`, payload);
    toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Vínculo cadastrado!', life: 3000 });
    displayVinculoDialog.value = false;
    fetchVinculos(selectedServidor.value.id);
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Erro', detail: error.response?.data?.detail || 'Erro ao salvar vínculo.', life: 5000 });
  } finally {
    vinculoSubmitting.value = false;
  }
};

const openNovoHistoricoDialog = (vinculo) => {
  activeVinculoForHistorico.value = vinculo;
  historicoForm.value = {
    data_inicio: null,
    definir_fim: false,
    data_fim: null,
    tabela_vencimento_id: null,
    tabela_gstu_id: null,
    cet_percentual: 0.0,
    insalubridade_percentual: 0.0,
    vpess_valor: 0.0,
    tabela_comissao_id: null,
    percentual_estabilizado: 0.0
  };
  displayHistoricoDialog.value = true;
};

const saveHistorico = async () => {
  historicoSubmitting.value = true;
  const payload = {
    ...historicoForm.value,
    data_inicio: formatDateToPayload(historicoForm.value.data_inicio),
    data_fim: historicoForm.value.definir_fim && historicoForm.value.data_fim 
      ? formatDateToPayload(historicoForm.value.data_fim) 
      : '9999-12-31'
  };
  // Deletar a flag temporária
  delete payload.definir_fim;

  try {
    await api.post(`/api/v1/servidores/vinculos/${activeVinculoForHistorico.value.id}/historico`, payload);
    toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Enquadramento cadastrado!', life: 3000 });
    displayHistoricoDialog.value = false;
    fetchHistoricos(activeVinculoForHistorico.value.id);
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Erro', detail: error.response?.data?.detail || 'Erro ao salvar enquadramento.', life: 5000 });
  } finally {
    historicoSubmitting.value = false;
  }
};

const openNovaAverbacaoDialog = (vinculo) => {
  activeVinculoForAverbacao.value = vinculo;
  averbacaoForm.value = {
    dias_averbados: 30,
    tipo_averbacao: 'ATS',
    data_averbacao: null,
    processo_numero: ''
  };
  displayAverbacaoDialog.value = true;
};

const saveAverbacao = async () => {
  averbacaoSubmitting.value = true;
  const payload = {
    ...averbacaoForm.value,
    data_averbacao: formatDateToPayload(averbacaoForm.value.data_averbacao)
  };
  try {
    await api.post(`/api/v1/servidores/vinculos/${activeVinculoForAverbacao.value.id}/averbacoes`, payload);
    toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Averbação cadastrada!', life: 3000 });
    displayAverbacaoDialog.value = false;
    fetchAverbacoes(activeVinculoForAverbacao.value.id);
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Erro', detail: error.response?.data?.detail || 'Erro ao salvar averbação.', life: 5000 });
  } finally {
    averbacaoSubmitting.value = false;
  }
};

// Helpers de formatação e nomes
const getCargoNome = (cargoId) => {
  const cargo = cargos.value.find(c => c.id === cargoId);
  return cargo ? cargo.nome : 'Cargo não identificado';
};

const getVencimentoDesc = (vencId) => {
  const venc = vencimentos.value.find(v => v.id === vencId);
  return venc ? `${venc.classe} - Nível ${venc.nivel_grau} (${venc.carga_horaria}h)` : 'Não informado';
};

const getGstuDesc = (gstuId) => {
  if (!gstuId) return 'Sem gratificação';
  const gstu = gstuLista.value.find(g => g.id === gstuId);
  return gstu ? `${gstu.grau} - Ref ${gstu.referencia}` : 'GSTU';
};

const formatCPF = (cpf) => {
  if (!cpf) return '';
  const clean = cpf.replace(/\D/g, '');
  if (clean.length !== 11) return cpf;
  return `${clean.slice(0, 3)}.${clean.slice(3, 6)}.${clean.slice(6, 9)}-${clean.slice(9)}`;
};

const formatDateBR = (dateStr) => {
  if (!dateStr) return '';
  if (dateStr instanceof Date) {
    const day = String(dateStr.getDate()).padStart(2, '0');
    const month = String(dateStr.getMonth() + 1).padStart(2, '0');
    const year = dateStr.getFullYear();
    return `${day}/${month}/${year}`;
  }
  const parts = dateStr.split('-');
  if (parts.length !== 3) return dateStr;
  return `${parts[2]}/${parts[1]}/${parts[0]}`;
};

const parseDateFromAPI = (dateStr) => {
  if (!dateStr) return null;
  const parts = dateStr.split('-');
  if (parts.length !== 3) return null;
  return new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
};

const formatDateToPayload = (date) => {
  if (!date) return '';
  if (typeof date === 'string') return date.substring(0, 10);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const formatEnum = (val) => {
  if (!val) return '';
  return val.replace(/_/g, ' ');
};

const formatNumber = (val) => {
  return parseFloat(val).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

const formatCurrency = (val) => {
  return parseFloat(val).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
};
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

.prontuario-btn:hover {
  background-color: var(--p-surface-100) !important;
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

.flex-row-align {
  flex-direction: row;
  align-items: center;
  gap: 0.5rem;
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

.pointer {
  cursor: pointer;
}

/* Prontuário Layout */
.prontuario-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 2rem;
}

.prontuario-sidebar {
  background-color: var(--p-surface-50);
  border: 1px solid var(--p-surface-200);
  border-radius: 8px;
  padding: 1.5rem;
}

.profile-avatar-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 0.5rem;
}

.avatar-icon {
  font-size: 3rem;
  background-color: var(--p-primary-100);
  color: var(--p-primary-600);
  padding: 1.25rem;
  border-radius: 50%;
  margin-bottom: 0.5rem;
}

.profile-name {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--p-surface-900);
}

.profile-badge {
  font-size: 0.75rem;
  color: var(--p-primary-color);
  background-color: var(--p-primary-50);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-weight: 600;
}

.profile-meta {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1rem;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.meta-title {
  font-size: 0.75rem;
  color: var(--p-surface-400);
  text-transform: uppercase;
  font-weight: 600;
}

.meta-desc {
  font-size: 0.875rem;
  color: var(--p-surface-800);
  font-weight: 600;
}

.prontuario-main {
  min-width: 0;
}

.tab-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.tab-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 700;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 3rem;
}

.spinner-icon {
  font-size: 2rem;
  color: var(--p-primary-color);
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: var(--p-surface-400);
}

/* Vínculos Cards */
.vinculo-card {
  border: 1px solid var(--p-surface-200);
  border-radius: 8px;
  background-color: #ffffff;
  overflow: hidden;
}

.vinculo-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background-color: var(--p-surface-50);
  border-bottom: 1px solid var(--p-surface-200);
}

.vinculo-header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.matricula-badge {
  font-family: monospace;
  font-weight: 700;
  font-size: 0.9rem;
  background-color: var(--p-surface-200);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.cargo-title {
  font-weight: 600;
  font-size: 1rem;
  color: var(--p-surface-900);
}

.status-badge {
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.status-ativo {
  background-color: #d1fae5;
  color: #065f46;
}

.status-inativo {
  background-color: #f3f4f6;
  color: #374151;
}

.vinculo-card-body {
  padding: 1.5rem;
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
}

.meta-col {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.meta-col .label {
  font-size: 0.75rem;
  color: var(--p-surface-400);
}

.meta-col .value {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--p-surface-800);
}

.inner-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.inner-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--p-surface-900);
}
</style>
