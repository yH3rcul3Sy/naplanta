# Fluxos do app · NaPlanta

## 1. Primeira visita (mapa)

```mermaid
flowchart TD
    A[Abre o site] --> B[Carrega dados.json, mudancas.json, status.json]
    B -->|falhou| X[Mensagem: não foi possível carregar]
    B --> C[Cidade padrão: Mogi das Cruzes<br>só na planta]
    C --> D[Mapa com pinos por etapa + lista de cards]
    D --> E{O que faz?}
    E -->|Clica no pino| F[Popup + card destacado na lista]
    E -->|Clica no card| G[Mapa centraliza e abre o popup]
    E -->|Muda filtros| H[Lista e mapa refeitos<br>contador de filtros]
    E -->|Novidades| I[Painel O que mudou · 30 dias]
    F & G --> J{Próximo passo}
    J -->|Ver na construtora| K[Site oficial · nova aba]
    J -->|Detalhes e compartilhar| L[Página do empreendimento]
```

## 2. Celular

```mermaid
flowchart LR
    M[Mapa em tela cheia] -->|botão Ver lista| N[Lista em tela cheia]
    N -->|botão Ver mapa| M
    N -->|toca no card| M2[Volta ao mapa com popup aberto]
    M -->|Filtros| O[Painel de filtros abre no topo]
```

## 3. Vindo do Google ou de um link compartilhado

```mermaid
flowchart TD
    G[Busca no Google: nome do prédio ou lançamento em cidade] --> P[site/e/nome-cidade-xxxx.html]
    W[Link no WhatsApp com prévia: foto, nome, etapa] --> P
    P -->|Ver no site da construtora| K[Site oficial]
    P -->|Ver no mapa| Q["index.html?e=nome-cidade-xxxx"]
    Q --> R[Troca a cidade se precisar, abre o pino e destaca o card]
    P -->|Todos os empreendimentos| L[site/e/ · lista por cidade]
```

## 4. Painel "O que mudou"

```mermaid
flowchart TD
    A[Botão Novidades<br>contador = eventos dos últimos 7 dias] --> B[Lista os eventos dos últimos 30 dias<br>da cidade filtrada, agrupados por dia]
    B -->|Novo ou mudou de etapa| C[Clica: fecha o painel e abre no mapa]
    B -->|Saiu do site| D[Desabilitado: provavelmente esgotado]
```

## 5. Coleta diária (bastidores)

```mermaid
sequenceDiagram
    participant GA as GitHub Actions (06h)
    participant PC as PC do projeto (12h)
    participant S as Sites das incorporadoras
    participant OSM as Nominatim / Overpass
    participant GH as Repositório (main)
    participant P as GitHub Pages
    GA->>S: 11 fontes (Cury e Sousa Araujo barram o GitHub)
    GA->>OSM: localização e arredores dos novos
    GA->>GH: commit dos dados (fontes falhas mantêm os de ontem)
    GA->>P: gera páginas e publica
    PC->>GH: reset para a main
    PC->>S: 11 fontes (todas respondem)
    PC->>GH: commit + pull --rebase + push
    GH->>P: push dispara a publicação
```

## 6. Estados de um empreendimento

```mermaid
stateDiagram-v2
    [*] --> Novo: aparece no site da incorporadora
    Novo --> BreveLancamento
    Novo --> Lancamento
    BreveLancamento --> Lancamento
    Lancamento --> EmObras
    EmObras --> Pronto
    BreveLancamento --> Saiu
    Lancamento --> Saiu: 100% vendido ou retirado
    EmObras --> Saiu
    Pronto --> Saiu
    Saiu --> [*]
```

Cada transição vira um evento em `mudancas.json` (`novo`, `etapa` ou `saiu`), guardado por 180 dias.
