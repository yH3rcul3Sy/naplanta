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
- O grupo de concorrência `publicacao` impede duas execuções ao mesmo tempo (a segunda espera na fila).
- A coleta manual (Run workflow) sempre coleta.

## Como medir

```bash
python coleta/agendamento.py 7
```

Lê a API pública do GitHub (sem token). Para cada execução: horário previsto (lido do título `Coleta diária (<cron>)`, gravado a partir deste PR), criação, início, fim, atraso (início − previsto), resultado e se o job `coleta` rodou ou foi pulado.

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

## Observações (preencher)

| Dia | Primeira execução agendada que rodou | Atraso | Coleta concluída às | Falhas |
|---|---|---|---|---|
| | | | | |
