# NaPlanta · Auditoria completa e roadmap (14/10/2026)

Auditoria feita sobre o código, os dados publicados, o histórico do repositório, as execuções do GitHub Actions e o site no ar (naplanta.app.br). Nenhum código foi alterado durante a auditoria.

Legenda usada em todo o documento:
**[C]** confirmado por inspeção, com a evidência indicada · **[H]** hipótese ou risco ainda não verificado · **[R]** recomendação.

---

## 1. Resumo executivo

**Situação atual.** O NaPlanta é um site estático (GitHub Pages) alimentado por uma coleta diária em Python (GitHub Actions) que lê os sites de **23 incorporadoras** e publica **1.206 empreendimentos** em `dados.json`, com **97% georreferenciados**, histórico de mudanças, páginas por empreendimento e por cidade, alertas por e-mail e página de transparência. A base técnica é boa para o tamanho do projeto: arquitetura em camadas, coletores isolados, teste de leitura por fonte, proteção contra coletas incompletas, Lighthouse 100 em acessibilidade e SEO. **Não há motivo para reescrever o sistema.**

**Principais riscos (por ordem de impacto):**

1. **28% do mapa está envelhecendo.** Cury, Direcional, Sousa Araujo e J.Bianchi (343 empreendimentos) recusam os servidores do GitHub; desde 13/10 só mantêm a última coleta que funcionou. [C]
2. **A coleta diária não é confiável no horário.** O agendamento do GitHub atrasou 7 h em 13/10 (e foi cancelado por tempo), não disparou no horário em 14/10 e a reserva rodou com 4 h 20 de atraso. [C]
3. **Risco jurídico com fotos.** O site republica **1.119 fotos** das incorporadoras (25 MB em `site/fotos`). Fotografia é obra protegida (Lei 9.610/98, art. 7º e 29). [C quanto ao fato; jurídico depende de advogado]
4. **A proteção de dados só olha volume.** A regra de queda (>30%) protege contra coleta incompleta, mas não contra mudanças absurdas por campo (coordenada que salta de cidade, etapa que regride, nome trocado). Dados brutos não são guardados, então não dá para reprocessar. [C]
5. **Testes não rodam a cada push.** Código novo chega ao site sem passar por `testar.py`; esta semana dois bugs de caractere invisível em regex passaram despercebidos até a revisão manual. [C]

**Principais oportunidades.** Os portais (ZAP/VivaReal, apto.vc) e as plataformas para corretor (Órulo, DWV) vendem **lead e estoque**; nenhum dos encontrados mostra ao comprador o **histórico verificável** das informações públicas (quando apareceu, quando mudou de etapa, quando sumiu) nem a **idade e a origem** de cada dado. O NaPlanta já coleta isso diariamente e pode tornar essa transparência o seu diferencial.

---

## 2. Diagnóstico técnico

### 2.1 Retrato do sistema [C]

| Item | Estado medido |
|---|---|
| Código | Python ~2.900 linhas (coleta), JS ~480 linhas (front), HTML ~530 linhas |
| Camadas | `fontes/` (23 coletores) → `dominio/` (regras puras com autotestes) → `infra/` (rede, geo, fotos, repositório, Brevo) → `app/` (casos de uso) → `publicacao/` (páginas estáticas) |
| Dados | `dados.json` 580 KB (106 KB com gzip), `mudancas.json` 35 eventos desde 25/09, `status.json` por fonte |
| Coleta | GitHub Actions, agendada 05:23 + reserva 11:23 (BRT), limite de 3 h; respeita robots.txt e Crawl-delay; pausa de 1 s |
| Publicação | GitHub Pages via Actions; páginas `/e/` e `/lancamentos/` geradas no deploy (1.323 URLs no sitemap) |
| Repositório | público, 91 commits, `.git` 34 MB, dependências com versão fixa e Dependabot semanal |
| Site | Lighthouse (celular): Acessibilidade 100, SEO 100, Boas práticas 96 (único item: imagens em baixa resolução) |

### 2.2 Problemas confirmados

| # | Problema | Evidência |
|---|---|---|
| D1 | 4 fontes bloqueiam o GitHub | `status.json`: Cury, Sousa Araujo, J.Bianchi, Direcional com `ok: false` desde 13/10. Teste com check-host.net: Cury 403 em 29 de 40 países e **403 até de servidor em São Paulo**; J.Bianchi e Direcional 403 em ~90% dos nós; Sousa Araujo responde fora, mas falha no GitHub. |
| D2 | Agendamento instável | API de Actions: 13/10 a coleta das 06:00 começou 16:30 UTC e foi cancelada aos 60 min; 14/10 nenhuma execução no horário, reserva com 4 h 20 de atraso. A documentação do GitHub admite atrasos e descarte em horários de pico ([doc](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows), [análise](https://itime.day/articles/github-actions-cron-delays)). |
| D3 | Testes fora do push | `coleta.yml`: `testar.py` só roda no job de coleta, que é pulado em `push`. |
| D4 | Fotos de terceiros republicadas | `site/fotos`: 1.119 arquivos `.webp` (25 MB), miniaturas das fotos das incorporadoras. |
| D5 | Pinos empilhados | 171 empreendimentos em 73 coordenadas repetidas. Parte é legítima (fases do mesmo condomínio: Cidade Maia, SuperCittà). Parte é erro: 6 empreendimentos distintos da Cury no Rio (Luzes do Rio, Cartola, Pixinguinha, Farol da Guanabara, Ciata) no mesmo ponto `-22.89722,-43.20472`. |
| D6 | Possíveis duplicados | 3 pares com mesmo nome e cidade: "Residencial Pixinguinha" (Cury, 2x), "Américas 19", "Helbor VM125", "Stories - Belém". Precisa conferir se são fases distintas. |
| D7 | Campos muito esparsos | Sem área: 777 (64%); sem dormitórios: 328 (27%); sem previsão de entrega: 1.144 (95%); sem foto: 17. |
| D8 | Histórico frágil a mudança de URL | `comparar()` identifica o empreendimento pela URL da fonte; se a incorporadora mudar o link, gera "saiu" + "novo" falsos. Só rastreia mudança de **etapa**; não registra mudança de entrega, área, endereço ou nome. |
| D9 | Proteção só por volume | `QUEDA_MAXIMA = 0.3` e `COLETAS_PARA_ACEITAR_QUEDA = 3` (`dominio/mudancas.py`); `campos_sumidos()` só avisa. Não há validação de variação por campo nem quarentena. |
| D10 | Sem dados brutos | Só o dado normalizado é guardado; não é possível reprocessar uma coleta com um coletor corrigido. O histórico do Git de `dados.json` funciona como cópia diária, mas não guarda o HTML de origem. |
| D11 | Metadescrição da privacidade desatualizada | `privacidade.html`: "não coleta dados pessoais", mas os alertas guardam e-mail (o texto da página explica; só a meta está errada). |
| D12 | Uso intenso de serviços públicos de mapa | Geocodificação em lote no Nominatim e no Photon públicos. Há cache (1,9 MB) e pausa de 1 s, mas a política do Nominatim desencoraja uso em lote ([política](https://operations.osmfoundation.org/policies/nominatim/)); o Photon público pede uso moderado. |
| D13 | Falhas silenciosas por caractere invisível | Esta semana, dois `\b` viraram o caractere de controle backspace ao editar regex, e os testes não pegaram. |

### 2.3 Verificado e sem problema [C]

- **Segredos:** nenhuma chave no histórico do Git (a única ocorrência suspeita era um falso positivo dentro de imagem); a chave da Brevo fica em secret do Actions.
- **Workflows:** `permissions: {}` no topo e permissão mínima por job; actions fixadas por hash de commit.
- **XSS:** todo texto vindo das fontes passa por `esc()` antes de ir ao HTML; `fonte` e `imagem` são validados (`problemas()` exige URL do domínio da fonte; imagens servidas localmente).
- **CSP** por meta tag, sem script inline, SRI nos scripts de CDN.
- **Isolamento de falhas:** cada fonte roda em `try`; uma fonte quebrada mantém os dados anteriores e não derruba as outras; uma issue "Fonte parada" é aberta e fechada sozinha.
- **robots.txt e Crawl-delay** respeitados no código (`infra/rede.py`), não só na documentação.
- **Atribuição** do OpenStreetMap no mapa; link para a página oficial em cada empreendimento.

### 2.4 Precisa investigar [H]

- Termos de uso de cada um dos 23 sites (alguns proíbem coleta automatizada nos termos mesmo com robots.txt liberado).
- Se os pares do D6 são duplicados ou fases.
- Desempenho real no celular (Lighthouse foi rodado sem a parte de performance; o carregamento medido é leve: 6,7 KB de HTML + 106 KB de dados).
- Se os commits do coleta-bot contam como atividade para a regra que desliga agendamentos após 60 dias sem atividade em repositório público ([doc](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows)).
- Onde a Brevo processa os dados (DPA e subprocessadores) para a transparência sobre transferência internacional.

---

## 3. Lista de correções (por gravidade)

| ID | Correção | Impacto | Solução | Prioridade | Esforço | Depende de |
|---|---|---|---|---|---|---|
| F1 | Fontes bloqueadas (D1) | 28% dos dados envelhecem | (a) pedir autorização ou feed às 4 incorporadoras; (b) feed XML que elas já mandam a portais; (c) mostrar idade e esconder após N dias | **P0** | M | — |
| F2 | Agendamento instável (D2) | dia sem atualização | gatilho externo (cron-job.org → API `workflow_dispatch`) com token de escopo mínimo | **P0** | P | token |
| F3 | Testes no push (D3) | bug chega ao site | job `testes` em push/PR: `testar.py` + autotestes + `ruff` | **P0** | P | — |
| F4 | Fotos (D4) | risco jurídico | validar com advogado; até lá: pedir autorização, creditar, oferecer remoção | **P1** | M | advogado |
| F5 | Pinos empilhados (D5) | pino errado | regra: mesma coordenada para nomes sem palavra em comum → marcar `aprox` e tentar endereço | **P1** | P | — |
| F6 | Validação por campo (D9) | dado absurdo publicado | guarda por campo + quarentena (ver seção 6) | **P1** | M | — |
| F7 | Identidade estável (D8) | histórico falso | chave composta (construtora + nome normalizado + cidade) como reserva da URL | **P1** | P | — |
| F8 | Lint de caracteres de controle (D13) | bug silencioso | `ruff` + teste que falha se houver `\x00-\x08` em `.py` | **P1** | P | F3 |
| F9 | Metadescrição da privacidade (D11) | inconsistência | corrigir o texto | **P2** | P | — |
| F10 | Duplicados (D6) | card repetido | conferir e deduplicar por chave composta | **P2** | P | F7 |

---

## 4. Roadmap completo

### Estado das tarefas (atualizado em 14/10/2026)

Ajustes decididos depois da auditoria: agendamento primeiro sem token (4 horários nativos, 7 dias de observação); quarentena com revisão manual para mudanças graves, sem aceitar automaticamente após 3 coletas; pedido de uso das fotos às 23 incorporadoras antes de decidir suspensão; dados brutos só estruturados e com retenção definida.

| Tarefa | Estado | Evidência |
|---|---|---|
| F3/F8 Testes em push e PR, lint, validação dos JSONs, deploy depende dos testes | na main (PR #9, 14/10); publicação validada em produção; **coleta real pelo fluxo novo pendente** (15/10) | PR #9; execução 38653246098 |
| F2 Agendamento: 4 horários nativos + registro de horários | na main desde 14/10; **aguarda a primeira coleta real e 7 dias de observação** | `docs/agendamento.md`, `coleta/agendamento.py` |
| Métricas de base (`docs/metricas.md`) | não iniciado | — |
| Contatos às 4 fontes bloqueadas + pedido de fotos às 23 | não iniciado (nada é enviado sem aprovação) | — |
| Inventário das fotos e opções | não iniciado | — |
| Critérios de quarentena (documento) | não iniciado | — |

### Fase 0 — Estabilização (semana 1)

| Iniciativa | P | Impacto | Esforço | Critério de conclusão | Como validar |
|---|---|---|---|---|---|
| Gatilho externo da coleta (F2) | P0 | Alto | P | 7 dias seguidos com coleta antes das 07:00 | `status.json.coleta` diário |
| Testes em todo push (F3, F8) | P0 | Alto | P | PR com coletor quebrado fica vermelho | quebrar um fixture de propósito |
| E-mails às 4 fontes bloqueadas (F1a) | P0 | Alto | P | e-mails enviados e registrados | respostas em `docs/fontes.md` |
| Linha de base de métricas | P0 | Médio | P | tabela da seção 12 preenchida | arquivo `docs/metricas.md` |

### Fase 1 — Integridade dos dados (semanas 2–4)

| Iniciativa | P | Impacto | Esforço | Critério de conclusão | Validação |
|---|---|---|---|---|---|
| Guardas por campo + quarentena (F6) | P1 | Alto | M | coordenada que muda >5 km, etapa que regride ou nome trocado vão para `quarentena.json` | teste com coleta adulterada |
| Identidade estável (F7) e deduplicação (F10) | P1 | Médio | P | mudança de URL não gera "saiu/novo" | teste com URL trocada |
| Pinos empilhados (F5) | P1 | Médio | P | ≤ 20 coordenadas repetidas entre nomes distintos | script de contagem |
| Decisão sobre fotos (F4) | P1 | Alto (jurídico) | M | parecer ou autorização registrados | — |
| Histórico de status (`status-historico.json`) | P1 | Médio | P | taxa de sucesso por fonte nos últimos 30 dias | página de transparência |

### Fase 2 — Base profissional (mês 2)

| Iniciativa | P | Impacto | Esforço | Critério | Validação |
|---|---|---|---|---|---|
| Dados brutos por coleta (HTML/JSON gzip por fonte e dia) num branch `brutos` ou R2 | P2 | Alto | M | reprocessar um dia antigo com coletor novo | rodar `reprocessar.py 2026-11-01` |
| Histórico de todos os campos (não só etapa) | P2 | Alto | M | linha do tempo mostra mudança de entrega/área | página de empreendimento |
| Mapa: agrupar fases do mesmo condomínio | P2 | Médio | P | fases com o mesmo ponto viram um pino com lista | inspeção visual |
| Geocodificação própria (Photon ou Nominatim em contêiner no Actions, se o volume crescer) | P3 | Baixo hoje | M | 0 chamadas a serviço público | log da coleta |

### Fase 3 — Produto e diferenciais (meses 2–3)

Ver o backlog na seção 10.

### Fase 4 — Infraestrutura (sob gatilho)

Migrar só quando um critério da seção 7 for atingido.

### Fase 5 — Conformidade contínua

Revisão trimestral de: termos das fontes, robots.txt (já automático), política de privacidade, pedidos de remoção e matriz jurídica.

---

## 5. Arquitetura recomendada

Mantém o que existe e acrescenta três peças: **gatilho externo**, **camada de dados brutos** e **quarentena**.

```
cron-job.org (05:23) ──API──► GitHub Actions: coleta
                                  │
   ┌──────────────────────────────┼──────────────────────────────┐
   │ 1. testar.py (fixtures)      │                              │
   │ 2. por fonte, isolado:       ▼                              │
   │    baixa ──► BRUTO (gzip, por fonte/dia, branch "brutos")   │
   │          └─► coletor (parse) ──► NORMALIZADO (valida campos)│
   │                                   │                         │
   │ 3. guardas: volume (já existe) + por campo (novo)           │
   │       ok ──► dados.json            suspeito ──► quarentena  │
   │ 4. geo (cache) · fotos · arredores                          │
   │ 5. mudancas.json (todos os campos) · status + histórico     │
   └─────────────────────────────────────────────────────────────┘
                                  │ commit
                                  ▼
            Publicação: paginas.py ──► GitHub Pages (estático)
                                  │
      alertas (Brevo, 20h) ◄──────┘     issue "Fonte parada" (já existe)
```

---

## 6. Plano de evolução da coleta

### 6.1 Fontes atuais

| Situação | Fontes |
|---|---|
| Funcionando no GitHub (19) | Helbor, C.A.C, Tenda, Integra, Damebe, EZTEC, Econ, Metrocasa, Vibra, Árbore, GFR, Scopel, Ribeira, Lumiar, Jeronimo da Veiga, Evo Life, Lumy, Graal, Longitude |
| Bloqueiam servidores (4) | Cury (bloqueia qualquer datacenter), Direcional, J.Bianchi (bloqueiam fora do Brasil), Sousa Araujo (bloqueia o GitHub) |
| Fora por regra (robots.txt ou bloqueio antibot) | MRV, Plano&Plano, Habras, Cyrela, EDK |

### 6.2 Fontes que bloqueiam: estratégia sustentável (sem contornar bloqueio)

1. **Autorização direta**: e-mail pedindo liberação do agente `NaPlantaBot` (Cloudflare permite liberar por agente ou IP) ou um feed.
2. **Feed de portal**: incorporadoras costumam enviar XML de estoque a portais. Pedir o mesmo arquivo é a fonte mais estável possível.
3. **Coleta assistida**: rodar `python coleta/coletar.py` numa conexão residencial quando possível, para essas fontes. É opcional e não deve ser a única via.
4. **Transparência**: o card já mostra a data dos dados; adicionar regra de exibição (por exemplo, esconder da lista padrão após 30 dias sem atualização, mantendo no histórico).

### 6.3 Generalizar a proteção existente

A regra atual (`quedas()`) está correta para volume e deve ser mantida. Acrescentar **guardas por campo**, aplicadas empreendimento a empreendimento:

| Mudança | Regra | Ação |
|---|---|---|
| Coordenada move > 5 km | improvável sem erro | quarentena; mantém posição anterior |
| Cidade muda | idem | quarentena |
| Etapa regride (ex.: em obras → lançamento) | raro, mas acontece (relançamento) | publica, marca `revisar` |
| Nome muda totalmente (sem palavra em comum) | pode ser outro empreendimento na mesma URL | quarentena |
| Campo some em > 50% da fonte | já existe (`campos_sumidos`) | mantém aviso, passa a reter o valor anterior |

Quarentena = arquivo `quarentena.json` publicado no repositório e listado na issue de monitoramento; um item sai da quarentena se a mesma mudança se repetir em 3 coletas (mesma lógica de `COLETAS_PARA_ACEITAR_QUEDA`).

### 6.4 Monitoramento

- Já existe: issue automática "Fonte parada", avisos `::warning::` no log.
- Acrescentar: `status-historico.json` (sucesso por fonte por dia), alerta quando a coleta do dia não acontecer até 09:00 (o próprio gatilho externo pode avisar por e-mail em falha).

---

## 7. Comparativo de hospedagem

| | A. Econômica (atual + ajustes) | B. Intermediária | C. Crescimento |
|---|---|---|---|
| Componentes | GitHub Pages; Actions; cron-job.org; Brevo grátis; GoatCounter | A + Cloudflare R2 (brutos e fotos) + Workers (gatilho e API leve) | Front em Cloudflare Pages; Postgres gerenciado (Supabase Pro); coleta em Actions ou contêiner agendado |
| Custo mensal | US$ 0 (domínio .app.br pago à parte, anual) | US$ 0–5 (R2 grátis até 10 GB-mês; Workers pago US$ 5/mês se precisar) ([Workers](https://developers.cloudflare.com/workers/platform/pricing/), [R2](https://developers.cloudflare.com/r2/pricing/)) | ~US$ 25+/mês (Supabase Pro inclui US$ 10 de computação; plano grátis pausa após 1 semana sem uso) ([Supabase](https://supabase.com/pricing)) |
| Vantagens | zero custo, zero servidor, histórico no Git | brutos e fotos fora do Git; gatilho confiável | consultas, contas de usuário, painel |
| Limites | Pages: site ≤ 1 GB, banda ~100 GB/mês, não é para fim primariamente comercial ([limites](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)); agendamento instável | mais uma conta e um ponto de falha | custo fixo, backup e segurança de banco |
| Manutenção | baixa | baixa-média | média-alta |

**Recomendação: ficar na A** com o gatilho externo. Critérios objetivos para migrar:

- **Para B:** repositório > 500 MB, ou fotos/brutos > 200 MB, ou necessidade de API para outro cliente.
- **Para C:** funcionalidade que exige conta de usuário (favoritos sincronizados, painel do corretor), mais de 10 mil empreendimentos, ou monetização direta (o GitHub Pages não deve hospedar site primariamente comercial).

---

## 8. Plano de segurança

| Risco | Gravidade | Probabilidade | Situação | Medida |
|---|---|---|---|---|
| Vazamento da chave da Brevo | Alta | Baixa | [C] protegida em secret | rotacionar a cada 6 meses; escopo mínimo |
| Token do gatilho externo (F2) | Média | Média | não existe ainda | token fine-grained só com `actions:write` neste repositório; expiração 1 ano |
| Ação de terceiro comprometida | Alta | Baixa | [C] fixadas por hash | manter Dependabot |
| XSS por dado das fontes | Alta | Baixa | [C] `esc()` + CSP | teste automatizado com nome contendo `<script>` |
| Inscrição em massa nos alertas (spam) | Baixa | Média | [C] dupla confirmação | monitorar volume na Brevo |
| Clickjacking | Baixa | Baixa | Pages não permite cabeçalhos | aceitar; reavaliar se migrar para B |
| Perda de dados | Média | Baixa | [C] histórico no Git | backup mensal do repositório (clone espelho) |
| Indisponibilidade da fonte de mapa | Baixa | Média | [C] cache | geocodificação própria se crescer |

**Resposta a incidente** (documentar em `docs/incidentes.md`): 1) revogar chave/token; 2) reverter o commit de dados (`git revert`); 3) republicar; 4) registrar causa e prevenção.

---

## 9. Matriz de conformidade jurídica

> Este quadro organiza questões; não é parecer jurídico. Itens marcados "Sim" precisam de advogado.

| Questão | Dados/operações | Base a verificar | Medida preventiva | Prioridade | Advogado |
|---|---|---|---|---|---|
| Fotos das incorporadoras | miniaturas republicadas | Lei 9.610/98 art. 7º VII, 29, 108 ([texto](https://www.wipo.int/wipolex/en/text/1290)) | autorização por e-mail; crédito; remoção imediata a pedido; alternativa: link sem copiar | P1 | **Sim** |
| Coleta automatizada | leitura de páginas públicas | termos de uso de cada site; robots.txt | registrar termos de cada fonte; respeitar opt-out (já existe via robots) | P1 | Sim |
| Base de dados das incorporadoras | compilação de dados factuais | Lei 9.610 art. 7º XIII (compilações) | coletar só fatos; não copiar textos descritivos | P2 | Sim |
| E-mails dos alertas | e-mail + cidades na Brevo | LGPD art. 7º I (consentimento), art. 33 (transferência internacional), Res. CD/ANPD 19/2024 | informar país de processamento e DPA da Brevo ([DPA](https://help.brevo.com/hc/en-us/articles/15403782599570)) na privacidade | P1 | Recomendável |
| Analytics | visitas agregadas | LGPD | GoatCounter sem cookie e sem IP (já informado) | P3 | Não |
| Precisão das informações | etapa, endereço | CDC (publicidade e informação), responsabilidade civil | aviso de fonte e data em cada dado (já existe); não afirmar preço/entrega como fato | P1 | Recomendável |
| Marcas e logotipos | nomes das incorporadoras | Lei 9.279/96 | uso nominativo (só nome), sem logotipos | P3 | Não |
| Marca "NaPlanta" | nome e logo | INPI: "NAPLANTA" indeferido na classe 36 em 2020 | pedir marca mista nas classes 42 e 35 | P2 | Recomendável |
| Remoção e correção | qualquer dado | boa prática e LGPD | canal (contato@) já existe; prazo de resposta publicado | P2 | Não |

---

## 10. Backlog de funcionalidades e diferenciais

**Referências de mercado.** O apto.vc vende lead e monitoramento de mercado pago às incorporadoras ([apto.vc](https://apto.vc/marketing-imobiliario/monitoramento-de-mercado)); ZAP e VivaReal separam lançamentos, mas o modelo é anúncio. Órulo e DWV são ferramentas para corretor, com estoque e tabelas ([DWV](https://webcatalog.io/en/apps/dwv)). Não encontrei quem ofereça ao comprador o histórico público e verificável das informações.

| # | Item | Valor | Viabilidade | Ordem |
|---|---|---|---|---|
| 1 | **Selo de atualização por card** (verde ≤ 2 dias, amarelo ≤ 15, cinza > 15, com data) | alto | já há dados | rápido |
| 2 | **Linha do tempo completa** (todas as mudanças de campo, não só etapa) | alto | precisa de F7 e do histórico por campo | médio |
| 3 | **Fases agrupadas** num pino | médio | simples | rápido |
| 4 | **Comparar 2–3 empreendimentos** lado a lado | médio | só front | rápido |
| 5 | **Página da incorporadora** (portfólio, cobertura, frequência de atualização) | médio | dados existentes | rápido |
| 6 | **Estatísticas por cidade** (lançamentos por mês, etapas) | médio | precisa de histórico de meses | médio |
| 7 | **Alertas por empreendimento** (não só por cidade) | alto | Brevo + lista por empreendimento | médio |
| 8 | **Detecção de atraso** (entrega prometida vs etapa) | alto, diferencial | só para os 5% com entrega | estratégico |
| 9 | **Painel interno de coletores** (taxa de sucesso, quarentena) | médio | `status-historico.json` | médio |
| 10 | Busca por nome/bairro | médio | só front | rápido |

Descartados por ora: contas de usuário, preços (mudam por unidade, risco de erro alto), comparação com portais.

---

## 11. Plano de 7, 30, 60 e 90 dias

| Prazo | Entregas verificáveis |
|---|---|
| **7 dias** | F2 (gatilho externo), F3 + F8 (testes e lint no push), e-mails às 4 fontes enviados, métricas de base registradas |
| **30 dias** | F5, F6, F7, F9, F10; histórico de status; decisão registrada sobre fotos; selo de atualização (backlog 1) e fases agrupadas (3) |
| **60 dias** | dados brutos guardados; histórico por campo; linha do tempo completa (2); página da incorporadora (5); comparar (4) |
| **90 dias** | alertas por empreendimento (7); estatísticas por cidade (6); revisão jurídica concluída; política de privacidade atualizada; reavaliar infraestrutura pelos critérios da seção 7 |

---

## 12. Indicadores de sucesso

| Indicador | Hoje (14/10) | Meta 90 dias | Como medir |
|---|---|---|---|
| Coletas diárias concluídas antes das 08:00 | 0 de 2 nos últimos dias | ≥ 95% | `status.json` + histórico |
| Fontes atualizadas no dia | 19 de 23 (83%) | ≥ 95% | `status.json` |
| Empreendimentos com dados ≤ 2 dias | 863 de 1.206 (72%) | ≥ 95% | idade por fonte |
| Com pino | 1.165 de 1.206 (97%) | ≥ 98% | `lat` presente |
| Pino exato (sem `aprox`) | 1.102 (91%) | ≥ 95% | `aprox` ausente |
| Coordenadas repetidas entre nomes distintos | a medir após F5 | ≤ 20 | script |
| Itens em quarentena por coleta | não existe | < 1% | `quarentena.json` |
| Tempo da coleta | ~50 min | < 60 min | Actions |
| Lighthouse (acessibilidade, SEO, práticas) | 100 / 100 / 96 | ≥ 95 | Lighthouse mensal |
| Inscritos nos alertas | a medir na Brevo | crescimento mensal | Brevo |

---

## Fontes consultadas

- GitHub: [limites do Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits), [desativação de agendamentos](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows), [atrasos de cron](https://itime.day/articles/github-actions-cron-delays)
- OpenStreetMap: [política do Nominatim](https://operations.osmfoundation.org/policies/nominatim/)
- Cloudflare: [Workers](https://developers.cloudflare.com/workers/platform/pricing/), [limites](https://developers.cloudflare.com/workers/platform/limits), [R2](https://developers.cloudflare.com/r2/pricing/)
- [Supabase pricing](https://supabase.com/pricing)
- Lei 9.610/98 ([WIPO Lex](https://www.wipo.int/wipolex/en/text/1290)); decisões sobre uso de fotografia sem autorização ([TJPB](https://www.tjpb.jus.br/w/quarta-c%C3%A2mara-entende-que-uso-de-fotografias-sem-autoriza%C3%A7%C3%A3o-do-autor-gera-indeniza%C3%A7%C3%A3o-1))
- LGPD, transferência internacional ([Confidata](https://confidata.com.br/blog/lgpd-comentada-18-transferencia-internacional-hipoteses)); [DPA da Brevo](https://help.brevo.com/hc/en-us/articles/15403782599570)
- Mercado: [apto.vc](https://apto.vc/marketing-imobiliario/monitoramento-de-mercado), [DWV](https://webcatalog.io/en/apps/dwv)
- Medições próprias: Lighthouse (14/10), check-host.net (14/10), API de Actions do GitHub, `site/*.json`
