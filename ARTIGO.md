# De API de brinquedo a produção: evoluindo uma API de análise de sentimento

Como uma API FastAPI de ~100 linhas virou um serviço com testes, CI, cache, multi-idioma, batch assíncrono, SSE e observabilidade — com números reais de benchmark no final.

## O ponto de partida

O projeto começou como a maioria dos projetos de estudo: uma API FastAPI que expunha o VADER (NLTK) para análise de sentimento, organizada em camadas (`routes` → `services` → `repositories`), com um Dockerfile e um pipeline que rodava `ruff` na `main`. Funcionava. E era isso.

O problema é que "funciona na minha máquina" não é um critério de engenharia. Faltava tudo o que separa um exemplo de tutorial de um serviço que você colocaria a assinatura embaixo:

- Zero testes automatizados
- CI que só rodava em push para a `main`
- Sem tratamento de erros (qualquer exceção vazava stack trace)
- `requirements.txt` sem pin de versão — e com um bug: uma linha `routes` listada como dependência do PyPI quebrava `pip install` em ambiente limpo
- Dockerfile com `COPY ../` (que nem funciona com contexto na raiz) e rodando como root

Este artigo é o caminho de lá até cá.

## Primeira parada: a base (testes, CI, Docker)

Antes de qualquer feature nova, a fundação. A regra que segui: **nada de código novo sem rede de proteção embaixo.**

### Testes em três camadas

A aplicação já tinha a separação `routes` → `services` → `repositories`, então os testes seguiram a mesma fronteira:

- **Repository** (`test_repository.py`): o VADER é determinístico, então testei textos claramente positivos, negativos e neutros verificando os sinais dos scores (`compound`, `pos`, `neg`, `neu`) — sem mocks. Quando a dependência é rápida e determinística, mock é só ruído.
- **Service** (`test_service.py`): aqui o repository é mockado, porque o que importa é a lógica de negócio — classificação por thresholds (`> 0.05`, `< -0.05`), agregação de estatísticas, fronteira de valores.
- **Routes** (`test_routes.py`): os endpoints via `TestClient`, cobrindo sucesso e os erros 400 (texto/lista vazia) e 422 (payload acima dos limites).

### CI que roda a cada commit

O pipeline original só rodava na `main` — ou seja, você descobria que quebrou algo *depois* do merge. Ajustei para rodar em qualquer push e PR, com jobs paralelos: lint, format check, mypy e testes com cobertura mínima em matrix de Python 3.11/3.12.

### Docker sem surpresas

Dockerfile multi-stage com `python:3.12-slim`, usuário não-root e — detalhe importante — o **léxico do VADER pré-baixado no build**. Sem isso, o primeiro request em produção depende de um download em runtime. Cold start não deveria depender de rede.

```dockerfile
ENV NLTK_DATA=/usr/local/share/nltk_data
RUN python -c "import nltk; nltk.download('vader_lexicon', download_dir='/usr/local/share/nltk_data')"
```

## A API em si: contrato primeiro

Com a base pronta, o próximo passo foi tratar a API como um **produto com contrato**, não como um script HTTP:

- **Versionamento** (`/v1/...`): dá para evoluir sem quebrar clientes.
- **OpenAPI rica**: `response_model`, `summary`, `description`, exemplos e tags em todos os endpoints. Schemas de resposta tipados (`AnalyzeResponse`, `SentimentScores`) em vez de dicionários soltos — se o contrato está no tipo, o mypy e o `/docs` trabalham por você.
- **Validação de payload**: `Field(max_length=10_000)` no texto e `max_length=100` na lista. Uma API pública sem limite de tamanho é um DoS de brinquedo esperando acontecer.
- **`GET /`** com metadados e **`GET /health`** para liveness probes.

## Features que valem um parágrafo cada

### Multi-idioma: VADER para inglês, LeIA para português

O VADER só entende inglês. Para PT-BR, usei o [LeIA](https://github.com/RafJaa/LeIA) — um fork do VADER adaptado para português. A integração é um dispatcher no repository:

```python
ANALYZERS = {
    'en': VaderAnalyzer(),
    'pt': LeiaAnalyzer(),
}

def analyze_sentiment(text: str, language: str = 'en') -> dict[str, float]:
    analyzer = ANALYZERS.get(language)
    if analyzer is None:
        raise ValueError(f'Unsupported language: {language}')
    return analyzer.polarity_scores(text)
```

Curiosidade que rendeu capítulo de "lições aprendidas": o pacote `leia` publicado no PyPI é um **stub vazio** — o projeto real não tem empacotamento. Solução: vendorizei o módulo (arquivo único + léxicos) em `src/vendor/leia/`, excluindo a pasta de lint e mypy. Código de terceiros no meu controle de versão, imutável e auditável.

### Cache: a feature mais barata e mais lucrativa

Análise de sentimento é CPU-bound pura e **determinística**: mesmo texto, mesmo score, sempre. É o caso de uso perfeito de cache. Implementei um cache in-memory com TTL e eviction LRU, chaveado por `(language, text)`:

```python
def analyze_sentiment(self, text: str, language: str = 'en') -> dict[str, float]:
    if self._cache is not None:
        cached = self._cache.get(text, language)
        if cached is not None:
            return cached
    result = analyze_sentiment(text, language)
    if self._cache is not None:
        self._cache.set(text, language, result)
    return result
```

Carga com repetição de textos (reviews, redes sociais, monitoramento) tem taxa de acerto alta — e os números no final mostram o retorno.

### Batch assíncrono com job ID

Lote grande não deveria segurar a conexão. `POST /v1/analyze_batch` responde `202 Accepted` com um job ID na hora; o processamento roda em background e o cliente consulta `GET /v1/results/{job_id}` até `completed` (ou `failed`).

### Streaming com SSE

Para quem quer resultado progressivo, `POST /v1/analyze_stream` responde com Server-Sent Events: um evento `data` por texto analisado, terminando com `event: done`. Simples, funciona com um `curl -N` e não precisa de WebSocket.

## Observabilidade: você não pode consertar o que não vê

- **`GET /metrics` em formato Prometheus**: contadores de HTTP por método/rota/status, histograma de latência, distribuição de sentimentos por idioma, hits/misses do cache, jobs por status.
- **Structured logging (structlog)** em JSON, com `request_id` gerado por request (ou propagado do cliente via `X-Request-ID`). Quando algo quebra, você filtra por um ID e vê a linha exata.
- **Header `X-Process-Time-Ms`** em toda resposta.
- **Sentry opcional** — seta `SENTRY_DSN` e pronto, sem tocar em código.
- **Rate limiting** por IP (429 + `Retry-After`) e headers de segurança.

Tudo configurável por variáveis de ambiente via `pydantic-settings`, com um `make dev` que sobe com reload para o dia a dia.

## Os números (a parte que interessa)

Metodologia completa no repositório (`docs/benchmarks/`), mas o resumo: locust, 20 usuários virtuais, 30s por cenário, 1 worker, texts curtos:

| Cenário | req/s | p50 | p95 | p99 |
| --- | --- | --- | --- | --- |
| Cache hit (EN) | **971** | 18ms | 30ms | 53ms |
| Cache miss (EN, VADER) | 568 | 33ms | 60ms | 93ms |
| Cache miss (PT, LeIA) | 458 | 41ms | 95ms | 140ms |

**+71% de vazão e -45% de latência no p50** só por não recalcular o que já foi calculado. Zero falhas em todos os cenários. O LeIA é ~20% mais lento que o VADER (léxico maior + normalização de acentuação), mas está longe de ser gargalo.

## Lições que o tutorial não conta

1. **O PyPI mente às vezes.** Verifique o que você instala — o `leia` de lá era um arquivo vazio. Vendorizar código pequeno e estável é opção legítima.
2. **Cobertura de código precisa de contexto.** O código vendored derrubava a métrica para 33%. Excluir `src/vendor` do coverage reportou o número certo: **98% de cobertura nas 412 linhas que são minhas**.
3. **Estado in-memory tem dono.** Com `WORKERS > 1`, cada processo tem seu cache e job store. Para este caso (cache é só otimização, job store é efêmero) é aceitável — mas é uma decisão consciente, documentada, não um acidente. Se precisar de consistência global, o próximo passo é Redis.
4. **`app.mount('/metrics')` no FastAPI responde 307** para `/metrics` (redirect para `/metrics/`). O Prometheus não segue redirect. A solução foi expor como rota normal com `generate_latest()`.
5. **Commits pequenos e verdes.** Cada feature foi um commit com lint, types e testes passando. O `git log` virou a narrativa do artigo.

## Estado final

- 72 testes, 98% de cobertura, threshold de 90% bloqueando no CI
- ruff (lint + format) e mypy limpos, rodando a cada push
- CI em matrix de Python, build de Docker validada em todo push
- API versionada, documentada, com cache, batch, stream, rate limit e métricas
- Benchmark reproduzível com `make benchmark`