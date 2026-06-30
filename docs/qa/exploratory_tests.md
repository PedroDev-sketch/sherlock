# Relatórios de Testes Exploratórios

## Sessão 1: Sherlock Web MVP & Precisão do Engine

### Parte 1 - Escolha da Funcionalidade
**Funcionalidade Selecionada:** Fluxo de Busca Síncrono na Web (Frontend MVP e integração com SherlockService) e Precisão do Engine de Busca (CLI/Web).

### Parte 2 - Compreensão da Funcionalidade
**Personas:** Investigadores de inteligência de fontes abertas (OSINT), jornalistas, detetives privados, pesquisadores ou usuários curiosos que precisam rastrear a presença digital de um nome de usuário.
**Domínio:** Ferramenta de OSINT focada em automatizar a raspagem (scraping) de perfis em centenas de redes sociais e fóruns para encontrar contas ativas.
**Fluxo Principal:** O usuário acessa a página inicial, insere um username válido no formulário e clica em buscar. O sistema processa o pedido síncrono no backend e renderiza uma nova página listando os sites onde a conta foi encontrada.
**Arquitetura:** O sistema agora possui uma camada de Interface (UI/Templates Django), uma camada de Serviços (Views do Django que validam o input e repassam para a ferramenta Sherlock) e a infraestrutura de rede que conecta o Sherlock aos sites externos (`data.json`).

### Parte 3 - Planejamento da Exploração

| Caminho | Cenários Planejados para Exploração |
| :--- | :--- |
| **Fluxos Funcionais** | Buscar um usuário existente na web; Buscar um usuário altamente improvável (para forçar o status vazio e caçar Falsos Positivos). |
| **Falhas e Erros** | Enviar o formulário sem preencher dados; Inserir caracteres não permitidos; Simular um timeout da API. |
| **UI / UX** | Checar se a estrutura de badges (cores dinâmicas) renderiza corretamente; Verificar se as mensagens de alerta são claras ao usuário. |
| **Aspectos Transversais** | Testar o desempenho da página durante buscas demoradas; Tentar injetar scripts maliciosos (Segurança/XSS). |

### Parte 4 - Sessão de Exploração

#### Técnica 1: Error Guessing (Adivinhação de Erros)
* **Ação:** O que acontece se eu reenviar um request clicando no botão "voltar" do navegador ou dar F5 durante a busca?
* **Ação:** Injeção de payload `<script>alert('XSS')</script>` no formulário.
* **Ação (Precisão):** Buscar por um usuário impossível de existir (ex: `hjsdh238947jhsdjh238947`) para checar se a arquitetura engole falsos positivos baseados em layout/API.

#### Técnica 2: Boundary Value Analysis (Análise de Valor Limite)
* **Ação:** Enviar um username com exatos 100 caracteres (limite máximo que definimos no CharField).
* **Ação:** Enviar um username com apenas 1 caractere.

#### Técnica 3: Tabela de Decisão
		
| Condições (Causas) | TC1 (Caminho Feliz) | TC2 (Timeout de Rede) | TC3 (Entrada Inválida) | TC4 (Nenhum Site Achado) |
| :--- | :--- | :--- | :--- | :--- |
| Nome de usuário válido? | V | V | F | V |
| Rede respondeu a tempo? | V | F | N/A | V |
| Encontrou o usuário em > 0 sites? | V | N/A | N/A | F |
| **Ações (Efeitos)** | | | | |
| Invoca SherlockService.search()? | Sim | Sim | Não | Sim |
| Exibe erro de validação? | Não | Não | Sim | Não |
| Exibe alerta de Timeout (error-state)? | Não | Sim | Não | Não |
| Exibe alerta de vazio (empty-state)? | Não | Não | Não | Sim |
| Exibe a lista de sites encontrados? | Sim | Não | Não | Não |

### Parte 5 - Relatório e Defeitos Encontrados

**Funcionalidades exploradas:** Fluxo de entrada, validação web, precisão de parsing do Sherlock.
**Técnicas utilizadas:** Error Guessing, Boundary Value Analysis e Tabela de Decisão.

#### Novos cenários descobertos e Defeitos (Severidade):
1. **[Alta] Congelamento da Interface Síncrona:** Durante o fluxo funcional, o usuário clica em "Finalizar/Buscar", o sistema aciona o SherlockService de forma síncrona e a tela congela. Não existe nenhum feedback visual (loading/spinner) avisando que o sistema está trabalhando. Isso faz o usuário apertar o botão repetidas vezes, acumulando requisições e travando o servidor local.
2. **[Média] Falsos Negativos em Limite Inferior:** O envio de strings de 1 caractere (Valor Limite), embora válido no nosso regex atual, causa comportamentos erráticos em redes sociais de terceiros (que exigem no mínimo 3 caracteres), resultando em dezenas de falsos negativos no retorno do Sherlock.
3. **[Crítica] Falsos Positivos por Limite de Tamanho da API Externa (Caso BoardGameGeek):** Usando *Error Guessing* com uma string longa aleatória (`hjsdh238947jhsdjh238947`), a ferramenta apontou a existência da conta no site `BoardGameGeek`.
   * **Causa Raiz:** O site está configurado no `data.json` para procurar o texto `"isValid":true` como prova de que o usuário não existe. Porém, para nomes com mais de 20 caracteres, a API deles retorna: `{"isValid":false,"message":"Username must be less than 20 characters long."}`. Como o Sherlock não achou `true`, ele deduziu (erroneamente) que a conta existe.

#### Melhorias sugeridas (Ações):
* **Imediato (Bug/UX):** Bloquear o botão de "Buscar" logo após o primeiro clique e adicionar um ícone de carregamento (spinner) na interface Web.
* **Médio Prazo (Performance):** Transformar a busca síncrona em assíncrona, para liberar o processamento do servidor web e evitar os problemas de desempenho diagnosticados durante o Error Guessing.
* **Manutenção do Core (Bug/Precisão):** Reportar/Corrigir a regra do `BoardGameGeek` no `data.json` e investigar se outros sites que usam validação de string estão gerando Falsos Positivos devido a erros de limite de caracteres das APIs parceiras.
