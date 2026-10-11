# Futuro e escala · NaPlanta

> Pesquisa de outubro de 2026. Números de mercado vêm de fontes citadas no fim. Alguns são material de marketing das próprias empresas e estão marcados como tal.

## 1. Onde o NaPlanta está no mercado

| Quem | Para quem | Modelo | Lacuna que o NaPlanta ocupa |
|---|---|---|---|
| **Órulo** | Corretores (150 mil, segundo a empresa) | Integração com incorporadoras, tabelas e materiais | Não é feito para o comprador final |
| **DWV** | Corretores e imobiliárias (750+ incorporadoras, segundo a empresa) | App gratuito, dados de mercado | Idem |
| **ZAP / VivaReal** | Comprador | Anunciante paga, CPL de R$ 50 a 100 | Só aparece quem anuncia e mistura usados |
| **Portais de lançamentos regionais** | Comprador | Sites de corretoras | Cobertura parcial, com viés de quem vende |
| **NaPlanta** | **Comprador** | Gratuito, neutro, dados direto da fonte | Visão completa, local e atualizada todo dia |

**Mercado de Mogi:** segundo o Secovi-SP, o valor lançado em Mogi das Cruzes foi de R$ 899 milhões em 9 meses de 2025, com 1.582 unidades lançadas e 2.208 vendidas. A cidade subiu para o 10º lugar entre 41 cidades do interior e da Grande SP. O MCMV movimentou mais de R$ 440 milhões em financiamentos na cidade (2024 ao 1º semestre de 2025, segundo a Caixa). **A demanda local existe e está crescendo.**

## 2. Diferenciais que ninguém oferece hoje

1. **"O que mudou" para o comprador:** alertas de lançamento, de mudança de etapa e de esgotado. Órulo e DWV fazem isso para corretor, não para quem compra.
2. **Linha do tempo do empreendimento:** quando apareceu, quando começou a obra, se atrasou. Isso é inteligência de mercado que hoje só existe dentro das incorporadoras.
3. **Selo "pode ser MCMV":** a maior parte da demanda de Mogi é MCMV, e nenhum mapa ajuda a filtrar por isso. Os tetos de 2026 variam por faixa, de R$ 275 mil a R$ 600 mil. É preciso confirmar no simulador oficial antes de publicar regras.
4. **Selo de regularidade:** a lei obriga a publicidade a informar o número do **registro da incorporação** (memorial) e o cartório. Coletar esse número quando a incorporadora publica e mostrar "registro informado ✓" seria um diferencial de **segurança para o comprador**. Não existe base aberta nacional de memoriais, então seria só o número divulgado, sem validação no cartório.
5. **Mobilidade real:** tempo a pé ou de ônibus até a estação, em vez de linha reta.

## 3. Como escalar

### Geografia
| Etapa | Região | O que muda |
|---|---|---|
| Agora | Mogi e Alto Tietê, mais as capitais que as fontes já cobrem | — |
| Próximo | Grande SP leste (Guarulhos, Suzano, Itaquá, Arujá) | +5 a 10 coletores |
| Depois | Campinas, Sorocaba, São José dos Campos | Mesmo código e coletores por região |
| Longo prazo | Capitais | Muitas fontes, então o trabalho vira manter coletores |

**Gargalo de escala:** cada fonte é um coletor a manter. Para 50+ fontes:
- **Testes de `parse()` com HTML salvo:** obrigatórios.
- **Coletores genéricos:** muitas incorporadoras usam os mesmos sistemas (WordPress, JSON-LD `ApartmentComplex`, Next.js). Um coletor que lê JSON-LD já cobriria várias de uma vez (a Vibra já funciona assim).
- **Parcerias:** a incorporadora envia um feed (JSON ou XML) em troca de visibilidade neutra. Isso inverte a relação e elimina o scraping.

### Infraestrutura (quando, não se)
| Gatilho | Mudança |
|---|---|
| Usuários pedindo alertas | Supabase (Postgres + auth) + Resend ou Brevo para e-mail |
| Mais de 3 mil empreendimentos | Dividir `dados.json` por estado e carregar sob demanda |
| Coleta acima de 1 h | Coletores em paralelo (um job do Actions por fonte) |
| Fontes que barram datacenter | Runner próprio (Raspberry Pi ou VPS) |
| Tráfego alto | Cloudflare Pages ou CDN na frente do GitHub Pages (grátis) |

**Não migrar antes do gatilho:** o modelo estático é o que permite custo zero e velocidade.

### Canal
- **SEO local** é o principal canal: páginas por empreendimento (feito), por cidade e bairro, e conteúdo como "lançamentos perto da estação Brás Cubas".
- **WhatsApp:** links com prévia (feito) e, no futuro, uma lista de transmissão semanal "o que mudou em Mogi".
- **App instalável (PWA):** já é instalável. Push no iPhone funciona desde o iOS 16.4, mas **só com o app na tela inicial** e com estabilidade menor que no Android. Para alertas, o e-mail é mais confiável.

## 4. Modelos de receita possíveis (sem perder a neutralidade)

| Modelo | Como | Risco à neutralidade |
|---|---|---|
| **Relatório de mercado** para incorporadoras e imobiliárias | Lançamentos, velocidade de saída, etapas por bairro (dados que o NaPlanta já tem) | Baixo |
| **Feed oficial "verificado"** | Incorporadora integra o feed e ganha selo de dados oficiais (todas aparecem igual) | Baixo |
| **API de dados** para corretores e fintechs | Plano pago por volume | Baixo |
| **Lead qualificado** (o comprador pede contato) | O CPL no mercado é de R$ 15 a 100, mas é material de agências e não foi verificado | **Alto:** só com transparência total e sem ranking pago |
| Anúncio destacado | — | **Evitar:** destrói o diferencial |

## 5. Riscos legais e éticos

- **Scraping no Brasil:** raspar páginas públicas sem burlar barreiras não é ilícito em si. A ANPD trata scraping de **dados pessoais** como tratamento sujeito à LGPD (Radar Tecnológico nº 3, nov/2024). **O NaPlanta não coleta dados pessoais**, e isso deve continuar como regra.
- **Termos de uso:** checar os termos de cada site novo, além do `robots.txt`.
- **Fotos:** pertencem às incorporadoras. Hoje são miniaturas com crédito e link. Para uso comercial, é preciso autorização ou parceria.
- **Alertas por e-mail:** exigem consentimento explícito, descadastro em 1 clique e política de privacidade (LGPD).
- **Exatidão:** sempre "segundo o site da incorporadora", com link. Nunca afirmar disponibilidade nem preço.

## 6. Ideias para o UMC Summit
- Mostrar o painel "O que mudou" ao vivo: o dado de hoje contra o de ontem.
- Mostrar números de cobertura: 900+ empreendimentos, 11 fontes, custo de operação R$ 0.
- Mostrar a ética como diferencial técnico: `robots.txt`, fontes públicas, nenhum dado pessoal.
- Roadmap: alertas, mais cidades e o selo MCMV.

## Fontes
- [Órulo](https://www.orulo.com.br/) · [Órulo na Google Play](https://play.google.com/store/apps/details?id=br.com.orulo&hl=en_US) · [DWV para corretores](https://site.dwvapp.com.br/corretores-e-imobiliarias/)
- [Lançamentos Online](https://www.lancamentosonline.com.br/plataforma-lancamentos-online.html) · [Guia Lançamentos](https://guialancamentos.com.br/)
- [O Diário de Mogi: MCMV movimenta R$ 440 mi](https://www.odiariodemogi.net.br/mogi/minha-casa-minha-vida-movimenta-r-440-milhoes-de-financiamentos-em-mogi-das-cruzes/)
- [Secovi-SP: pesquisas do mercado imobiliário](https://secovi.com.br/pesquisa-secovi-sp-do-mercado-imobiliario-julho-2025/)
- [Pavão & Associados: registro do memorial de incorporação](https://pavaoeassociados.com.br/registro-do-memorial-de-incorporacao-demonstra-transparencia-e-da-seguranca-ao-comprador-sobre-intencao-da-construtora-de-entregar-imovel-vendido-na-planta/) · [Direcional: memorial de incorporação](https://www.direcional.com.br/blog/meu-apartamento/memorial-de-incorporacao/)
- [Assis e Mendes: web scraping e LGPD](https://assisemendes.com.br/web-scraping-e-lgpd-riscos-juridicos-do-uso-de-dados-publicos/) · [Jus.com.br: web scraping na LGPD](https://jus.com.br/artigos/87950/web-sscraping-na-lei-geral-protecao-de-dados-pessoais)
- [Morada.ai: CPL em lançamentos](https://morada.ai/blog/custo-por-lead-lancamento-imobiliario/) · [Papo Imobiliário: CPL, CAC e conversão](https://www.papoimobiliario.com/cpl-cac-e-conversao-os-numeros-que-definem-o-crescimento-das-imobiliarias-em-2026-2/)
- [ValorFinal: MCMV 2026](https://valorfinal.com.br/guia/minha-casa-minha-vida-2026)
- [MagicBell: limitações do PWA no iOS](https://www.magicbell.com/blog/pwa-ios-limitations-safari-support-complete-guide)
- [SEOJuice: schema.org em 2026](https://seojuice.com/blog/schema-org-2026-what-google-reads/)
- [GeoSampa: alvarás](https://prefeitura.sp.gov.br/web/licenciamento/w/noticias/265348) · [Insper: base de alvarás](https://acessopde.datascience.insper.edu.br/base-de-dados-de-alvaras-de-construcao/)
