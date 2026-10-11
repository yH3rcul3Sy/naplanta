# Briefing de design e revisão · NaPlanta

## Parte 1 · Briefing

### Objetivo
Fazer quem procura imóvel na planta **encontrar, entender e confiar** num lançamento em menos de um minuto, sem cadastro e sem corretor.

### Público e contexto de uso
- **Celular primeiro:** a busca por imóvel começa no celular, muitas vezes por link no WhatsApp.
- Pessoas de 25 a 45 anos, muitas comprando o primeiro imóvel e sem familiaridade com termos como "breve lançamento" ou "memorial".
- Uso em momentos curtos: no ônibus, no intervalo do trabalho.

### Personalidade da marca
| É | Não é |
|---|---|
| Neutro, direto, confiável | Vendedor, apelativo, "oportunidade imperdível" |
| Local (Mogi e Alto Tietê) | Genérico de portal nacional |
| Transparente sobre limites | Promessa de dados perfeitos |

**Tom de voz:** frases curtas, sem jargão de corretor, sempre dizendo de onde vem a informação ("segundo o site da Helbor").

### Identidade visual atual
| Elemento | Valor |
|---|---|
| Cor da marca | Verde `#1f6f4a` (fundo claro `#e7f2ec`) |
| Etapas | Breve `#c58a1a` · Lançamento `#d0582a` · Obras `#2f6fc4` · Pronto `#1f8a58` |
| Fundo e texto | `#f6f5f2` e `#1d1d1b` |
| Tipografia | Fonte do sistema (rápida, sem download) |
| Raio | 10 a 12 px · Alvo de toque 44 px no celular |
| Logo | "Na**Planta**" com "Planta" em verde, e ícone de traço preto |

### Princípios
1. **O mapa é o produto:** tudo leva de volta a ele.
2. **Confiança visível:** data da coleta, fonte de cada dado e avisos de limite à vista.
3. **Nada sem saída:** todo card termina num site oficial ou numa página compartilhável.
4. **Rápido em 4G:** sem fontes externas, fotos pequenas, lista sob demanda.

### Entregáveis de design pedidos (próximas fases)
- Tela de boas-vindas com explicação em uma linha (ver revisão, item A1).
- Componente de alerta ("me avise de novos lançamentos aqui").
- Comparador de até 3 empreendimentos.
- Imagem de compartilhamento (`og:image`) própria, com marca, em 1200×630.

---

## Parte 2 · Revisão (outubro de 2026)

Testado no navegador em 375 px (celular), 1024 px (notebook), 1280 px e 800 px.

### O que já está bom
- Mapa e lista sincronizados, com cor por etapa e legenda.
- No celular, alternar entre mapa e lista com um botão fixo no polegar funciona bem.
- Acessibilidade de base: foco visível, `aria-live` no total, alvos de 44 px e `prefers-reduced-motion`.
- Avisos honestos: "localização aproximada" e "dados de 30/09: o site não respondeu".
- Carrega rápido, sem banner de cookies (não há rastreamento).

### Corrigido nesta revisão
| Problema | Correção |
|---|---|
| Em notebooks (801 a 1279 px) os filtros ficavam espremidos, com rótulos sobrepostos e o botão "Sobre os dados" cortado | Os filtros descem para uma segunda linha |
| Links do card quebravam com um "·" solto | Links lado a lado: "Ver na construtora ↗" e "Detalhes e compartilhar" |
| Texto secundário em 12 px, difícil de ler | Passou para 13 px |
| O visitante não sabia se os dados eram de hoje | O total mostra "· atualizado hoje" |
| Faltavam meta tags para Google e WhatsApp | Description, keywords, Open Graph, Twitter Card e canonical em todas as páginas |

### Pendências, em ordem de impacto para "clientes"
| # | Problema | Sugestão | Esforço |
|---|---|---|---|
| A1 | **Quem chega pela primeira vez não sabe o que é o NaPlanta.** Não há frase de valor | Faixa fina sobre o mapa, que some após o primeiro clique: "Todos os lançamentos na planta de Mogi, direto das incorporadoras. Atualizado todo dia." | P |
| A2 | **Falta a pergunta nº 1: "cabe no meu bolso?"** | Sem coletar preço, indicar "pode ser MCMV" quando a área e o tipo sugerem a faixa, com link para o simulador da Caixa | M |
| A3 | Sem ordenação | Ordenar por "mais novos", "mais perto da estação" e "entrega mais cedo" | P |
| A4 | O popup do mapa repete o card inteiro e fica longo | Popup curto (foto, nome, etapa, 2 botões) | P |
| A5 | No celular, a legenda encosta no botão "Ver lista" | Legenda recolhível ou no canto superior | P |
| A6 | A imagem de compartilhamento é o ícone do app | `og:image` 1200×630 com a marca e, nas páginas, a foto do prédio (já feito) | P |
| A7 | Sem modo escuro | Variáveis de cor já existem, falta `prefers-color-scheme` | M |
| A8 | Identidade fraca para diferenciar no mercado | Ilustração ou padrão de "planta baixa" como assinatura visual, fonte própria para títulos | M |
| A9 | O termo "etapa" confunde quem está começando | Tooltip ou glossário: "Breve lançamento = ainda não começou a vender" | P |

P = até meio dia · M = um a dois dias.

### O que já é diferencial frente a ZAP, VivaReal e Órulo
- Só imóveis novos, de **todas** as incorporadoras cobertas, sem ranking pago.
- Painel **"O que mudou"**: ninguém mostra mudança de etapa dia a dia para o comprador.
- **Estação e serviços próximos** em cada card.
- **Transparência da fonte**, com uma página pública sobre os dados.
