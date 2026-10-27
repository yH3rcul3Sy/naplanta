# Plano de implementação · NaPlanta

Fases curtas, cada uma entregável sozinha.

Estado atualizado em 27/10/2026. O roadmap vigente, com prioridades e critérios, está em `docs/auditoria-2026-10.md`; este plano registra o que já foi entregue.

## Feito (até 27/10/2026)
- 23 fontes, mapa, filtros, novidades, página "Sobre os dados".
- Segurança (CSP, SRI, actions fixadas), validação de dados, queda aceita após 3 coletas.
- Página por empreendimento (com linha do tempo das etapas), páginas por cidade, sitemap, Search Console, meta tags.
- Ajustes de layout para notebook e "atualizado hoje".
- Boas-vindas com glossário, popup curto, ordenação, selo e filtro MCMV, menu compacto no celular.
- Domínio próprio (naplanta.app.br) com HTTPS, imagem de compartilhamento, logo NP (kit em `docs/marca/kit`).
- Breadcrumbs, "Outros na cidade", "Como chegar", FAQ, privacidade, 404, llms.txt.
- Arquitetura em camadas (`docs/arquitetura.md`).
- Testes em todo push e PR (lint, autotestes, coletores contra páginas gravadas, validação dos JSONs, sintaxe do JS); a publicação só sai com a bateria verde e o artefato validado (PR #9).
- Aviso de fonte parada por issue automática no GitHub.
- Alertas por e-mail por cidade via Brevo (página `alertas.html`, listas por cidade).
- Analytics sem cookies (GoatCounter).
- Agendamento com 4 horários e registro de atrasos (`docs/agendamento.md`).
- Coleta em casa: runner self-hosted no servidor `servtestes`, IP residencial para as fontes que bloqueiam datacenter (PR #16). Substituiu a antiga coleta local no PC, removida.

## Pendente
| Tarefa | Detalhe | Origem |
|---|---|---|
| Token de privilégio mínimo para o timer de casa | Token fine-grained só do `naplanta` no lugar do login do `gh` | `docs/agendamento.md` |
| Mais incorporadoras do Alto Tietê | Mogi tem 38 dos 1.208 empreendimentos; checar o `robots.txt` antes | auditoria, P2 |
| Coletor genérico por dado estruturado | JSON-LD, WordPress REST e `__NEXT_DATA__` | auditoria, P2 |
| Métricas de base, inventário das fotos, critérios de quarentena | Contatos às incorporadoras só com aprovação | auditoria, Fase 0/1 |
| Indicador MCMV (A2) | Faixa provável por área, tipo e cidade, com link para o simulador oficial | — |
| Tempo a pé real | OSRM ou OpenRouteService, calculado na coleta e guardado em cache | — |
| Comparador | Até 3 empreendimentos lado a lado (só front-end) | — |
| Páginas por bairro | As por cidade já existem | — |
| Modo escuro (A7) | | — |

## Depois · Escala (ver `futuro.md`)
Outras regiões metropolitanas, API pública de dados, parcerias com incorporadoras.

## Como trabalhar
- Uma branch por tarefa, PR para a `main` (o push na `main` publica).
- Toda lógica nova com `assert` ou teste. A bateria `coleta/testes/tudo.sh` roda em todo push e PR (no Windows, ao menos `python -c "import coletar"` antes do push).
- Nova fonte: checar o `robots.txt` antes de escrever o coletor.
