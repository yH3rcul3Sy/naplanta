# PRD · NaPlanta

> Documento de requisitos de produto. Versão 1.0 · outubro de 2026.

## 1. Problema

Quem quer comprar um imóvel na planta em Mogi das Cruzes e no Alto Tietê precisa abrir o site de cada incorporadora, um por um. Os portais grandes (ZAP, VivaReal) misturam usados e novos e cobram dos anunciantes, então a cobertura de lançamentos é incompleta. As plataformas especializadas em imóveis novos (Órulo, DWV) são feitas para **corretores**, não para quem compra.

Resultado: o comprador não tem uma visão única, atualizada e neutra do que está sendo lançado perto dele.

## 2. Proposta

Um mapa gratuito com **todos os lançamentos na planta** de uma região, com dados **direto dos sites das incorporadoras**, atualizado **todo dia**, sem corretor no meio.

Diferenciais:
- **Neutro:** não vende leads nem destaca quem paga. Cada card leva à página oficial.
- **Atualizado:** coleta diária e um painel "O que mudou" (novos, mudança de etapa, saídas).
- **Contexto do bairro:** estação de trem/metrô e serviços próximos.
- **Transparente:** página pública com a situação de cada fonte e as regras da coleta.

## 3. Público

| Persona | Necessidade | Como o NaPlanta atende |
|---|---|---|
| **Comprador da primeira casa** (25 a 40 anos, renda até R$ 13 mil, MCMV) | Saber o que cabe no bolso, perto do trabalho/estação | Filtros de cidade, dormitórios, área, distância da estação |
| **Investidor local** | Acompanhar lançamentos e o ritmo de obras | Painel de novidades, histórico de etapas |
| **Morador curioso** | "O que vão construir no meu bairro?" | Mapa e páginas por empreendimento |
| *(futuro)* **Corretor autônomo** | Carteira de lançamentos da região | Lista e páginas compartilháveis |

## 4. Escopo atual (v1, no ar)

- Mapa e lista sincronizados, com 900+ empreendimentos de 11 incorporadoras.
- Filtros: cidade, tipo, etapa, construtora, dormitórios, área mínima, distância da estação, incluir prontos.
- Foco padrão: Mogi das Cruzes e só imóveis **na planta** (breve lançamento, lançamento, em obras).
- Painel "O que mudou" (30 dias) e selo "Novo" (7 dias).
- Uma página por empreendimento, compartilhável e indexável, além da lista completa e do sitemap.
- Página "Sobre os dados" com a situação de cada fonte.
- Funciona no celular e pode ser instalado na tela inicial (PWA).

## 5. Fora do escopo (por decisão)

- **Preços:** não são coletados. Mudam toda semana, variam por unidade e criariam risco de informação errada.
- **Dados pessoais:** nenhum dado de pessoas é coletado. Não há login.
- **Sites que proíbem a coleta** (`robots.txt`) ou bloqueiam robôs: ficam de fora, sem contornar.
- **Imóveis usados.**

## 6. Requisitos funcionais

| # | Requisito | Situação |
|---|---|---|
| RF1 | Mostrar empreendimentos no mapa com cor por etapa | Feito |
| RF2 | Filtrar por cidade, tipo, etapa, construtora, dorms, área e estação | Feito |
| RF3 | Lista sincronizada com o mapa (clique no pino destaca o card) | Feito |
| RF4 | Painel de mudanças diárias | Feito |
| RF5 | Link para a página oficial da incorporadora | Feito |
| RF6 | Página própria por empreendimento, com link "Ver no mapa" | Feito |
| RF7 | Aviso quando a fonte está desatualizada ou o pino é aproximado | Feito |
| RF8 | Alerta por e-mail de novos lançamentos por filtro | Planejado (fase 2) |
| RF9 | Comparar empreendimentos lado a lado | Planejado (fase 3) |
| RF10 | Simulação de enquadramento no MCMV | Planejado (fase 3) |

## 7. Requisitos não funcionais

- **Custo zero** de operação (GitHub Pages e Actions).
- **Primeira carga** abaixo de 3 s em 4G (`dados.json` tem cerca de 70 KB comprimido).
- **Ética de coleta:** respeita `robots.txt`, identifica o robô, pausa de 1 s entre páginas.
- **Resiliência:** uma fonte que falha não derruba as outras. Os dados anteriores são mantidos.
- **Acessibilidade:** navegação por teclado, contraste AA, alvos de toque de 44 px.
- **Segurança:** CSP sem script inline, SRI na CDN e escape de todo texto vindo das fontes.

## 8. Métricas de sucesso

| Métrica | Meta (6 meses) | Como medir |
|---|---|---|
| Fontes atualizadas no dia | ≥ 90% | `status.json` |
| Empreendimentos do Alto Tietê cobertos | ≥ 80% dos ativos | Comparar com Secovi e portais |
| Páginas indexadas no Google | ≥ 500 | Search Console |
| Cliques para a incorporadora | crescendo mês a mês | Search Console e analytics sem cookies (fase 2) |
| Inscritos em alertas | 200 | Base de alertas (fase 2) |

## 9. Riscos

| Risco | Impacto | Mitigação |
|---|---|---|
| Incorporadora muda o site | Fonte para de atualizar | Testes de parse, alerta no Actions, dados anteriores mantidos |
| Incorporadora pede para sair | Perda de cobertura | Atender na hora. O robô já respeita `robots.txt` |
| Informação desatualizada leva a decisão errada | Reputação | Aviso de fonte parada, link sempre para a fonte oficial |
| Dependência do PC para Cury e Sousa Araujo | Dados velhos se o PC ficar desligado | Runner dedicado ou VPS (fase 2) |
