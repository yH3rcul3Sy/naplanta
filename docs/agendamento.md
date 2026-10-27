# Agendamento da coleta · registro de observação

**Objetivo:** decidir com evidência se os horários nativos do GitHub Actions bastam ou se é preciso um gatilho externo (com token). A decisão será tomada após **7 dias** de observação com os 4 horários (a partir do merge do PR da Fase 0).

## Configuração em observação

| Horário (Brasília) | Cron (UTC) | Papel |
|---|---|---|
| 05:23 | `23 8 * * *` | principal |
| 08:23 | `23 11 * * *` | reserva |
| 11:23 | `23 14 * * *` | reserva |
| 14:23 | `23 17 * * *` | reserva |

- Brasília é UTC-3 o ano todo (sem horário de verão desde 2019).
- Execuções agendadas só coletam se ainda não houve coleta no dia (`status.json`); as demais encerram em segundos (job `coleta` = `skipped`).
- Duas filas de concorrência: `publicacao-coleta` (agendadas e manuais) e `publicacao-push` (pushes na main). Dentro de cada fila não rodam duas ao mesmo tempo; o GitHub mantém só 1 execução esperando por fila (a nova substitui a antiga). Os deploys das duas filas são serializados pelo grupo `pages` do job `publicar`.
- Uma reserva que não aparece pode ter sido substituída na fila por outra reserva: antes de concluir que não rodou, conferir execuções canceladas ou na fila.
- A coleta manual (Run workflow) sempre coleta.

## Coleta em casa (desde 26/10/2026)

Cury, Sousa Araujo, J.Bianchi e Direcional bloqueiam IP de datacenter (auditoria, D1), então a coleta principal roda num runner self-hosted no PC do mantenedor, com IP residencial. O GitHub continua orquestrando: testes, commit dos dados e publicação são os mesmos.

| Horário (Brasília) | Quem dispara | Onde coleta |
|---|---|---|
| 04:53 | timer do systemd no PC (`gh workflow run coleta.yml -f local=casa`) | runner `casa-danilo` (label `casa`) |
| 05:23, 08:23, 11:23, 14:23 | agendamento do GitHub | `ubuntu-latest`; só coletam se a de casa não rodou no dia |

- PC desligado ou dormindo às 04:53: o timer dispara quando ele ligar (`Persistent=true`). Até lá as agendadas coletam no GitHub sem as 4 fontes; a de casa, por ser manual, coleta de novo e completa o dia.
- O repositório é público: PRs de fork de qualquer contribuidor externo pedem aprovação antes de rodar (Settings → Actions), para nenhum código de terceiros chegar ao runner.

**Na máquina** (Ubuntu, `loginctl enable-linger` para os serviços rodarem sem sessão aberta): `bash coleta/casa/instalar.sh`. Ele cria tudo em `.casa/` (fora do git) e pode rodar de novo sem estragar nada.

| O quê | Onde |
|---|---|
| Runner do GitHub (`casa-danilo`, label `casa`) | `.casa/runner`; PATH dos jobs na unit `naplanta-runner.service` |
| Python 3.12 dos jobs | `.casa/venv`, primeiro no PATH dos jobs |
| Units do systemd | modelos em `coleta/casa/`, geradas em `.casa/systemd/` e ligadas com `systemctl --user link` |
| `gh` (dispara o timer e abre a issue de fonte parada) e `uv` | `~/.local/bin`, com `gh auth login` feito |

## Como medir

```bash
python coleta/agendamento.py 7
```

Lê a API pública do GitHub (sem token). Para cada execução: horário previsto (lido do título `Coleta diária (<cron>)`, gravado a partir deste PR), criação, início, fim, atraso (início − previsto), resultado e se o job `coleta` rodou ou foi pulado.

## Estado da validação em produção

| Etapa | Estado | Evidência |
|---|---|---|
| Merge na main | confirmado em 14/10/2026 | PR #9, commit `26db17e` |
| Publicação pelo fluxo novo (testes → páginas → validação do artefato → deploy) | confirmada em 14/10/2026, sem coleta (push) | execução 38653246098; sitemap com 1.207 páginas de empreendimento |
| Coleta real pelo fluxo novo (testes → coleta → validação → commit de dados → publicação) | confirmada em 15/10/2026 (agendada das 05:23, concluída às 11:24) | `python coleta/agendamento.py` |
| Observação de 7 dias | concluída (15 a 21/10); acompanhamento seguiu até 27/10 | tabela abaixo |

A primeira coleta bem-sucedida comprova o fluxo, não que o agendamento melhorou: essa conclusão só sai da comparação dos 7 dias com a linha de base.

## Linha de base (antes da mudança), medida em 14/10/2026 às 19:16

Agendamento único às 06:00 (`0 9 * * *`) até 14/10 de manhã; depois 05:23 + reserva 11:23. Execuções anteriores não registravam o horário previsto no título.

| Previsto (BRT) | Criada | Início | Fim | Resultado | Job coleta |
|---|---|---|---|---|---|
| 06:00 | 09/10 12:38 | 09/10 12:38 | 09/10 13:02 | success | success |
| manual | 10/10 10:43 | 10/10 10:43 | 10/10 11:05 | success | success |
| 06:00 | 10/10 11:53 | 10/10 11:53 | 10/10 12:15 | success | success |
| 06:00 | 11/10 12:10 | 11/10 12:10 | 11/10 12:32 | failure | failure |
| manual | 12/10 12:23 | 12/10 12:23 | 12/10 12:45 | success | success |
| 06:00 | 12/10 15:19 | 12/10 15:19 | 12/10 16:05 | success | success |
| manual | 12/10 18:35 | 12/10 18:35 | 12/10 19:25 | success | success |
| 06:00 | 13/10 13:30 | 13/10 13:30 | 13/10 14:31 | cancelled (limite de 60 min) | cancelled |
| 06:00 (14/10) | — | — | — | **não executada** | — |
| manual | 14/10 14:46 | 14/10 14:46 | 14/10 15:35 | success | success |
| 11:23 | 14/10 15:43 | 14/10 15:43 | 14/10 15:44 | success | skipped (já coletado) |

**Leitura:** nas 5 execuções agendadas para 06:00 que ocorreram, o atraso foi de **5 h 53 a 9 h 19** (média 7 h 06); em 14/10 a das 06:00 não ocorreu, e a reserva das 11:23 ocorreu com **4 h 20** de atraso.

## Critério de decisão (após 7 dias)

- **Fica como está** se em ≥ 6 dos 7 dias houver coleta concluída até 12:00.
- **Gatilho externo** (com token de privilégio mínimo) se em ≥ 2 dos 7 dias a primeira coleta concluída for depois das 12:00 ou não ocorrer.

## Observações (medidas em 27/10/2026 com `coleta/agendamento.py`)

| Dia | Primeira execução agendada que rodou | Atraso | Coleta concluída às | Falhas |
|---|---|---|---|---|
| 15/10 | 05:23 | 5 h 09 | 11:24 | — |
| 16/10 | 05:23 | 4 h 57 | 11:16 | — |
| 17/10 | 05:23 | 3 h 53 | 10:04 | — |
| 18/10 | 05:23 | 4 h 16 | 10:30 | — |
| 19/10 | 05:23 | 7 h 20 | **13:46** | depois das 12:00 |
| 20/10 | 05:23 | 5 h 17 | 11:28 | — |
| 21/10 | 05:23 | 5 h 33 | 11:43 | — |
| *22/10* | 05:23 | 5 h 32 | 11:46 | — |
| *23/10* | 05:23 | 5 h 12 | 11:17 | — |
| *24/10* | 05:23 | 4 h 23 | 10:21 | — |
| *25/10* | 05:23 | 4 h 51 | 10:52 | — |
| *26/10* | 05:23 | 6 h 54 | **12:50** | depois das 12:00 |
| *27/10* | 05:23 | 6 h 16 (criada 11:39) | — | não coletou: a coleta em casa, disparada à mão às 11:18, terminou antes (12:02) |

Em itálico, os dias depois da janela de 7 dias.

**Resultado da janela (15 a 21/10):** 6 de 7 dias com coleta concluída até 12:00. Pelo critério acima, **fica como está**.

**Mas a decisão mudou por outro motivo:** em 26/10 a coleta principal passou para a [coleta em casa](#coleta-em-casa-desde-26102026), por causa das 4 fontes que bloqueiam IP de datacenter (auditoria, D1). O timer do PC às 04:53 é, na prática, o gatilho externo previsto acima, e os horários do GitHub ficam de reserva. Os dias seguintes à janela confirmam que a reserva continua lenta (26/10 às 12:50; 27/10 com 6 h 16 de atraso).

**Pendente:** o critério pedia um token de privilégio mínimo para o gatilho externo. O timer usa o login do `gh` do mantenedor (escopos `repo`, `workflow`, `gist`, `read:org`, que valem para todos os repositórios). Falta trocar por um token fine-grained só do `naplanta`, com permissão só de Actions (escrita).
