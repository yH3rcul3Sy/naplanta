# Plano de implementação · NaPlanta

Fases curtas, cada uma entregável sozinha. Esforço estimado para uma pessoa.

## Fase 0 · Feito (até out/2026)
- 11 fontes, mapa, filtros, novidades, página "Sobre os dados".
- Segurança (CSP, SRI, actions fixadas), validação de dados, queda aceita após 3 coletas.
- Coleta local agendada para Cury e Sousa Araujo.
- Página por empreendimento, sitemap, Search Console, meta tags.
- Ajustes de layout para notebook e "atualizado hoje".

## Fase 1 · Confiabilidade e primeira impressão (1 a 2 semanas)
| Tarefa | Por quê | Esforço |
|---|---|---|
| Testes de `parse()` com 1 a 2 HTMLs salvos por fonte (`pytest`), rodando no Actions antes da coleta | Detectar mudança de layout antes de virar dado errado | 2 dias |
| Faixa de boas-vindas (A1) | Primeira visita entender o produto | 0,5 dia |
| Popup curto e ordenação (A3, A4) | Uso mais fluido | 1 dia |
| Glossário de etapas (A9) | Público iniciante | 0,5 dia |
| `og:image` 1200×630 (A6) | Compartilhamento no WhatsApp | 0,5 dia |
| Alerta de fonte parada por e-mail (issue automática no GitHub) | Hoje o aviso só aparece na aba Actions | 0,5 dia |

## Fase 2 · Retenção (3 a 4 semanas)
| Tarefa | Detalhe | Esforço |
|---|---|---|
| **Alertas por e-mail** | "Me avise de novos em Mogi, 2 dorms". Supabase (tabela `alertas`) com confirmação por e-mail (double opt-in, LGPD). Um job após a coleta cruza `mudancas.json` com os filtros e envia via Resend ou Brevo (camada gratuita) | 1 semana |
| Analytics sem cookies | Plausible, Umami ou GoatCounter, para medir cliques na construtora sem banner de cookies | 0,5 dia |
| Runner dedicado | Raspberry Pi ou VPS barata como *self-hosted runner*, tirando a dependência do PC | 1 dia |
| Domínio próprio | `naplanta.com.br` no GitHub Pages | 0,5 dia |
| +5 incorporadoras do Alto Tietê | Mapear quem lança em Mogi, Suzano, Arujá e Itaquaquecetuba e checar o `robots.txt` | 1 semana |

## Fase 3 · Diferenciais (1 a 2 meses)
| Tarefa | Detalhe |
|---|---|
| Indicador MCMV (A2) | Faixa provável por área, tipo e cidade, com link para o simulador oficial |
| Tempo a pé real | OSRM ou OpenRouteService, calculado na coleta e guardado em cache |
| Comparador | Até 3 empreendimentos lado a lado (só front-end) |
| Histórico do empreendimento | Linha do tempo de etapas na página dele (dados já existem em `mudancas.json`) |
| Página por cidade e bairro | "Lançamentos em Mogi das Cruzes", para SEO local |
| Modo escuro e identidade visual (A7, A8) | |

## Fase 4 · Escala (ver `futuro.md`)
Outras regiões metropolitanas, API pública de dados, parcerias com incorporadoras.

## Como trabalhar
- Uma branch por tarefa, PR para a `main` (o push na `main` publica).
- Toda lógica nova com `assert` ou teste. Rodar `python -c "import coletar"` antes do push.
- Nova fonte: checar o `robots.txt` antes de escrever o coletor.
