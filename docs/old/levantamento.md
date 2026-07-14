# Especificação de Requisitos: Sistema de Cálculo de Impacto Financeiro (UEFS)

Este documento detalha o levantamento de requisitos para o desenvolvimento de uma aplicação web destinada a unificar e automatizar o cálculo de impacto financeiro decorrente de alterações funcionais (promoção, progressão e alteração de carga horária) de servidores docentes e técnicos-administrativos da Universidade Estadual de Feira de Santana (UEFS). A aplicação substituirá o controle atual baseado em planilhas eletrônicas.

---

## 1. Visão Geral e Problema
Atualmente, os cálculos de impacto financeiro da Pró-Reitoria de Gestão e Desenvolvimento de Pessoas (PGDP) são realizados por meio de planilhas eletrônicas distintas para docentes e técnicos. Este processo manual apresenta riscos como:
*   Falta de padronização nas fórmulas e tabelas utilizadas.
*   Dificuldade de manutenção de histórico de tabelas salariais.
*   Erros manuais ao consolidar dados e calcular retroativos.
*   Dificuldade em simular impactos orçamentários coletivos para tomadas de decisão.

A nova aplicação irá unificar e automatizar essas regras em uma única ferramenta web facilitada e segura.

---

## 2. Escopo e Regras de Negócio

### 2.1. Carreiras, Hierarquias e Estruturas de Progressão

Para unificar as tabelas salariais no banco de dados e realizar os cálculos automatizados, a aplicação utilizará a seguinte estruturação de cargos e carreiras:

#### 2.1.1. Docentes
*   **Hierarquia:** Classes (Auxiliar, Assistente, Adjunto, Titular, Pleno) e Níveis (A, B).
*   **Cargas Horárias (CH):** 20 horas, 40 horas e Dedicação Exclusiva (DE).
*   **Abreviação de Classes (Sigla):** O sistema deve mapear a classe por extenso do docente em uma sigla de 3 letras por meio da seguinte regra lógica por extenso:
    *   *Regra:* Se a classe por extenso for **Auxiliar**, mapeia para **AUX**; se for **Assistente**, mapeia para **ASS**; se for **Adjunto**, mapeia para **ADJ**; se for **Titular**, mapeia para **TIT**; caso contrário (classe **Pleno**), mapeia para **PLENO**.
*   **Código Identificador de Remuneração-Base:** Composto pela concatenação de `Sigla` + `Nível (A/B)` + `Carga Horária (20/40/DE)` (ex: `AUX-A-20`, `ASS-A-20`, `ADJ-B-20`, `ADJ-A-DE`).
*   **Vantagens de Carreira:**
    *   **Incentivo à Titulação:** Percentual aplicado sobre o Vencimento-Base com base no maior título (ex: Especialização, Mestrado, Doutorado).
    *   **Incentivo por Produção Científica:** Percentual sobre o Vencimento-Base.
    *   **Abono de Permanência:** Valor da contribuição previdenciária devolvido aos aptos a aposentadoria em atividade.

#### 2.1.2. Analistas Universitários (Carreira A)
*   **Hierarquia:** Graus (I, II, III, IV, etc.) e Referências (E, EE, M, D, S) vinculadas à titulação:
    *   *Referência E:* 1 Especialização (mínimo 360h).
    *   *Referência EE:* 2 Especializações (360h cada) ou 1 Especialização (mínimo 600h).
    *   *Referência M:* Mestrado.
    *   *Referência D:* Doutorado.
    *   *Referência S:* Sem título (Referência básica).
*   **Interstício:** Mínimo de 24 meses de efetivo exercício na referência para progressão horizontal; mínimo de 36 meses no grau para promoção vertical.
*   **Requisitos para Promoção (Grau):** Ser aprovado em pelo menos 1 PFAC (Programa de Formação e Aperfeiçoamento Continuado) e considerado apto em pelo menos 1 ADF (Avaliação de Desempenho Funcional) no período em que permaneceu no mesmo Grau.

#### 2.1.3. Técnicos Universitários (Carreira T)
*   **Hierarquia:** Graus (I, II, III, IV) e Referências numéricas (1, 2, 3) vinculadas a cursos de aperfeiçoamento:
    *   *Referência 2:* 180h integralizadas em diversos cursos de aperfeiçoamento (mínimo de 8h/curso).
    *   *Referência 3:* 240h integralizadas em diversos cursos de aperfeiçoamento (mínimo de 20h/curso).
*   **Interstício para Progressão (Horizontal):** 12 meses no Grau I; 18 meses nos Graus II, III e IV.
*   **Interstício para Promoção (Vertical):** Mínimo de 36 meses no Grau I; 54 meses nos Graus II e III (reduzível para 48 a critério da administração). É requisito básico que o servidor esteja posicionado na *última referência* (Ref. 3) da GSTU do Grau ocupado.

#### 2.1.4. Auxiliares Administrativos (AUX)
*   Carreira regulamentada por regras similares de graus e referências.
    *   *Graus:* I ou II.
    *   *Carga Horária:* 30 ou 40 horas.
    *   *Exemplos de Códigos:* `AUX-30-I`, `AUX-40-I`, `AUX-30-II`, `AUX-40-II`.

#### 2.1.5. Códigos de Busca da Tabela Unificada (Técnicos/Analistas)
*   **Código de Vencimento-Base:** Composto por `[Tipo (A/T)]-[Carga Horária (30/40)]-[Grau (I, II, III...)]` (ex: `A-40-I`, `T-40-II`).
*   **Código de GSTU:** Composto por `[Tipo (A/T)]-[Carga Horária (30/40)]-[Grau]-[Referência]` (ex: `A-40-IV-M`, `T-40-II-2`).
*   **Técnico de Nível Superior (TNS):** Códigos para compatibilidade histórica: `TNS-30-I`, `TNS-40-I`, `TNS-30-I-1`, `TNS-40-I-1`.
*   **Funções Comissionadas:** Símbolos cadastrados: `DAS-2A`, `DAS-2B`, `DAS-2C`, `DAS-2D`, `DAS-3`, `DAI-4`, `DAI-5`.

---

### 2.2. Detalhamento dos Cálculos e Parâmetros do Cadastro do Servidor

O cálculo do impacto financeiro compara a remuneração antiga (atual) e a proposta. A base de dados do cadastro de servidores (importada via CSV ou editada na tela do servidor) deve conter as referências exatas para alimentar esses cálculos.

#### 2.2.1. Vencimento-Base (Dif_Sal)
*   **Origem no Cadastro:** O sistema identifica o salário-base atual consultando o código do servidor (ex: `A-40-I` ou `AUX-40-I`) na tabela salarial correspondente à data de vigência do processo.
*   **Fórmula:** `Dif_Sal = Vencimento_Novo - Vencimento_Antigo`.

#### 2.2.2. Gratificação de Suporte Técnico-Universitário (GSTU)
*   **Origem no Cadastro:** O sistema identifica o valor de GSTU atual consultando a chave de GSTU (ex: `A-40-IV-M` ou `T-40-II-2`) na tabela correspondente ao período do cálculo.
*   **Fórmula:** `Dif_GSTU = GSTU_Nova - GSTU_Antiga`.

#### 2.2.3. Adicional por Tempo de Serviço (ATS)
*   **Origem no Cadastro:**
    *   `%ATS` (ou Anuênios): Percentual acumulado atualmente pelo servidor (ex: `18%`).
    *   `Averb` (Averbação): Indicador booleano (`Sim` / `Não`).
    *   `Dias_Averbados` / `DATA-Averb`: Tempo de serviço anterior averbado pelo servidor.
    *   `Data_Admissão`: Data de admissão no cargo efetivo.
*   **Lógica de Cálculo da Data de ATS (Data Base):**
    *   *Regra por Extenso:* Para determinar a data base de contagem de tempo para ATS (incorporando averbações retroativas de tempo trabalhado, como sob regime REDA), verifica-se se o indicador de Averbação está marcado como **Sim**. 
        *   **Se Sim:** A data base do ATS será a **Data de Admissão do servidor subtraída do total de Dias Averbados**.
        *   **Se Não:** A data base do ATS será a própria **Data de Admissão**.
        Essa data resultante será a referência cronológica para contagem de tempo de serviço e concessão de adicionais.
*   **Regra de Cálculo do Percentual de ATS (Lei 6.677/1994):**
    *   *Primeiro Quinquênio:* **5%** ao completar 5 anos (60 meses) de efetivo exercício (contados a partir da `DATA_ATS`).
    *   *Acumulação Anual:* **+1% ao ano completo** após o 5º ano (ex: 6 anos = 6%, 7 anos = 7%, etc.).
    *   *Conceito do 6º Ano (Vigência):* O acréscimo de ATS incide no contracheque a partir do mês em que o servidor completa 5 anos.
    *   *Verificação no Período (`ATS-Antes`):* O sistema compara a data de vigência da promoção/progressão com a data do próximo aniversário de serviço (`DATA_ATS + Anos_Serviço`). Se o servidor completar um ano adicional de serviço antes da vigência do processo, o novo percentual de ATS do cálculo é atualizado (`%ATS_Novo = %ATS_Antigo + 1%` ou `+5%`).
*   **Fórmula:** `Dif_ATS = (%ATS_Novo * Vencimento_Novo) - (%ATS_Antigo * Vencimento_Antigo)`.

#### 2.2.4. Condições Especiais de Trabalho (CET)
*   **Origem no Cadastro:** Percentual de CET atual atribuído ao servidor (ex: `30%`, `50%` ou `125%`).
*   **Fórmula:** `Dif_CET = (%CET_Novo * Vencimento_Novo) - (%CET_Antigo * Vencimento_Antigo)`.

#### 2.2.5. Insalubridade
*   **Origem no Cadastro:** Grau de Insalubridade associado ao cadastro do servidor, armazenado como percentual (ex: `0%`, `20%`, `30%` ou `40%`) aplicável sobre o vencimento-base.
*   **Fórmula:** `Dif_Insalubridade = (%Insalubridade_Nova * Vencimento_Novo) - (%Insalubridade_Antiga * Vencimento_Antigo)`.
    *   *Nota:* Se a insalubridade for paga como valor fixo ou se a base de cálculo for distinta por lei, o sistema deve utilizar o percentual do cadastro sob o vencimento-base correspondente ao período de apuração.

#### 2.2.6. Vantagem Pessoal (VPESS)
*   **Origem no Cadastro:** Valor monetário fixo (R$) que o servidor já possui incorporado em seu contracheque (`V. Pessoal`).
*   **Fórmula:** `Dif_VPESS = VPESS_Nova - VPESS_Antiga`.
    *   *Nota:* Geralmente este componente é mantido constante (`Dif = 0`), a menos que o processo implique em absorção ou reajuste específico da vantagem pessoal registrado na nova proposta.

#### 2.2.7. Estabilidade Econômica (Estabilização)
*   **Origem no Cadastro:**
    *   `Estabil.` / `Símbolo Estabilizado`: Identificador da Função Comissionada estabilizada (ex: `DAS-2C`, `DAS-3`).
    *   `%Estabilizado` / `Fator`: Percentual de incorporação concedido ao servidor (ex: `30%`).
*   **Lógica de Cálculo:**
    *   *Regra por Extenso:* O valor da estabilidade econômica é indexado ao valor do cargo em comissão correspondente. O cálculo verifica se o servidor possui um Símbolo Estabilizado cadastrado (diferente de zero/vazio):
        *   **Se possuir:** Busca-se o valor financeiro do Símbolo na tabela salarial de funções comissionadas (GSTU-base) e multiplica-se esse valor pelo percentual de incorporação (%Estabilizado) cadastrado no registro do servidor (por exemplo, 30% do valor do símbolo DAS-2C).
        *   **Se não possuir (vazio ou zero):** O valor da estabilidade é zero.
*   **Fórmula:** `Dif_Estab = Valor_Estabilidade_Novo - Valor_Estabilidade_Antigo`.

#### 2.2.8. Encargo Patronal (Previdenciário)
*   **Origem no Cadastro:** Data de admissão do servidor ou tipo de regime de previdência configurado em seu registro.
*   **Lógica de Alíquotas:**
    *   **24%:** Servidores antigos com admissão histórica no Estado da Bahia até o ano de **2007**.
    *   **28%:** Servidores admitidos a partir de **2008** (padrão atual).
*   **Fórmula:** `Encargo_Patronal = (Dif_Sal + Dif_GSTU + Dif_CET + Dif_ATS + Dif_Insalubridade + Dif_Estab + Dif_VPESS) * %Patronal`.
    *   *(Nota: O encargo patronal incide sobre todas as rubricas salariais que compõem a base previdenciária).*

---

### 2.3. Temporalidade e Proporcionalidade dos Cálculos

*   **Impacto no Primeiro Ano (Ano de Vigência):** O cálculo deve ser proporcional ao número de meses restantes no ano civil, contado a partir do mês da data de vigência do desenvolvimento funcional.
    *   *Fórmula dos meses restantes:* `Meses_Restantes = 13 - Mes_Vigência`.
    *   *Proporcionalidade de 13º e Férias:* O cálculo do acréscimo temporário deve computar a fração proporcional ao período trabalhado para o 13º salário e o terço constitucional de férias.
*   **Impacto nos Anos Seguintes (Ano Cheio):** Projeção de 12 meses completos do novo salário acrescido de 13º salário e 1/3 de férias integrais.
*   **Histórico de Vigências de Tabelas (Retroativos):** Para garantir o cálculo retroativo correto, a aplicação deve conter um cadastro de Tabelas de Vencimentos e GSTU com datas de vigência explícitas (Data Início e Data Fim). Ao executar um cálculo retroativo, o sistema buscará a tabela salarial vigente no exato período selecionado.

---

## 3. Requisitos Funcionais (RF)

### 3.1. Importação e Banco de Dados
*   **RF001 - Importação de Base de Servidores:** O sistema deve permitir o upload de um arquivo em formato CSV contendo a folha e dados cadastrais dos servidores ativos (extraído do sistema de RH atual) para alimentar/atualizar a base de dados interna.
*   **RF002 - Cadastro Histórico de Tabelas:** O sistema deve fornecer uma interface administrativa para cadastro e edição de tabelas de vencimento e gratificações (GSTU) por período de vigência.

### 3.2. Operações de Simulação e Cálculo
*   **RF003 - Simulação Individual:** Permitir selecionar um servidor específico (por matrícula), buscar seus dados atuais e simular o impacto financeiro individual preenchendo as novas variáveis (Novo Grau, Nova Referência, Nova CH, Nova Vigência).
*   **RF004 - Geração de Memória de Cálculo (PDF):** O sistema deve gerar um documento PDF padronizado detalhando a memória de cálculo individual (semelhante ao layout de "RESUMO INDIVIDUAL" das planilhas) para anexação ao processo administrativo do servidor.
*   **RF005 - Simulação Coletiva (Simulação em Lote):** Permitir simular o impacto financeiro global de um grupo de servidores de forma simultânea (ex: simular a promoção de todos os Analistas elegíveis para o Grau seguinte no ano vigente) e exibir o impacto acumulado mensal, anual e encargos previdenciários.
*   **RF006 - Controle de Interstício e Requisitos:** Alertar os analistas da PGDP se o servidor cumpre os interstícios regulamentares e requisitos para promoção/progressão de acordo com as datas registradas em seu cadastro.

---

## 4. Requisitos Não Funcionais (RNF)
*   **RNF001 - Usabilidade:** A interface deve ser limpa, moderna, responsiva e de fácil manuseio por analistas de RH sem conhecimento técnico de banco de dados.
*   **RNF002 - Perfis de Acesso e Segurança:** Inicialmente, o acesso à aplicação será restrito a servidores da PGDP/SAAP via autenticação de usuário. O sistema deve estar arquitetado para suportar perfis de acesso adicionais no futuro (ex: módulo de autoconsulta para servidores simularem suas próprias progressões).
*   **RNF003 - Precisão de Cálculo:** As fórmulas matemáticas devem possuir precisão de duas casas decimais e estar estritamente alinhadas com as normas dos Decretos Estaduais da Bahia.

---

## 5. Priorização de Escopo (MoSCoW)

*   **MUST HAVE (Essencial para o lançamento):**
    *   Importação de base de servidores via CSV (RF001).
    *   Histórico de tabelas salariais com vigências temporais (RF002).
    *   Motor de cálculo de impacto individual com geração de PDF da Memória de Cálculo (RF003, RF004).
    *   Cálculo automático de proporcionalidade no 1º ano e encargos patronais (24%/28%).
*   **SHOULD HAVE (Importante mas não impeditivo):**
    *   Simulações coletivas/lote e relatórios consolidados (RF005).
    *   Alertas de verificação de requisitos mínimos e interstícios regulamentares (RF006).
*   **COULD HAVE (Desejável se houver tempo):**
    *   Geração de gráficos de impacto financeiro orçamentário.
    *   Módulo de auditoria interna para rastrear quem realizou cada simulação.
*   **WON'T HAVE (Fora de escopo para esta versão):**
    *   Integração em tempo real via API com o sistema de folha de pagamento corporativo do Estado (RH Bahia).