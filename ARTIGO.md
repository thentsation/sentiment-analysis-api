🇧🇷 Português | [🇺🇸 English](ARTIGO.en-us.md)

# Levando a sério uma API que eu escrevi numa tarde

A primeira versão dessa API tinha uns 100 linhas, rodava VADER em cima de texto em inglês e era exatamente o que parece: um exercício. Decidi tratá-la como se fosse para produção mesmo, e isso mudou quase tudo — menos a ideia original.

## O que eu tinha em mãos

Uma API FastAPI expondo VADER (NLTK) para análise de sentimento, já organizada em camadas (`routes` → `services` → `repositories`), com Dockerfile e um pipeline que rodava `ruff` na `main`. Rodava. Só isso.

"Funciona na minha máquina" não é critério de engenharia, e eu sabia disso enquanto escrevia. Faltava tudo o que separa um exemplo de tutorial de algo que eu assinaria embaixo: zero testes automatizados, CI que só rodava depois do push pra `main` (ou seja, eu descobria que quebrei algo depois do merge), nenhum tratamento de erro — qualquer exceção vazava stack trace pro cliente —, `requirements.txt` sem pin de versão e com um bug entretido: uma linha `routes` listada como dependência do PyPI que quebrava `pip install` num ambiente limpo, e um Dockerfile com `COPY ../` (que nem funciona com contexto de build na raiz) rodando como root.

## A regra que segui: nada de feature nova sem rede de proteção embaixo

Antes de mexer em qualquer coisa nova, construí a fundação.

A aplicação já tinha a separação `routes` → `services` → `repositories`, então os testes seguiram a mesma fronteira. No **repository** (`test_repository.py`), o VADER é determinístico, então testei textos claramente positivos, negativos e neutros checando o sinal dos scores (`compound`, `pos`, `neg`, `neu`) sem nenhum mock — quando a dependência é rápida e determinística, mockar é só ruído. No **service** (`test_service.py`), o repository é mockado porque o que importa ali é a lógica de negócio: classificação por thresholds (`> 0.05`, `< -0.05`), agregação de estatísticas, valores de fronteira. Nas **routes** (`test_routes.py`), os endpoints via `TestClient`, cobrindo sucesso e os erros 400 (texto ou lista vazia) e 422 (payload acima dos limites).

O CI original só rodava na `main`; mudei para rodar em qualquer push e PR, com jobs paralelos — lint, format check, mypy e testes com cobertura mínima em matrix de Python 3.11/3.12.

E o Docker ganhou multi-stage com `python:3.12-slim`, usuário não-root e um detalhe que eu quase deixei passar: o **léxico do VADER pré-baixado no build**.

```dockerfile
ENV NLTK_DATA=/usr/local/share/nltk_data
RUN python -c "import nltk; nltk.download('vader_lexicon', download_dir='/usr/local/share/nltk_data')"
```

Sem isso, o primeiro request em produção dependeria de um download em runtime — e cold start não deveria depender de rede.

## Tratando a API como contrato, não como script HTTP

Com a fundação de pé, o próximo passo foi parar de pensar nisso como "um endpoint que responde JSON" e começar a pensar como contrato: versionamento em `/v1/...` para poder evoluir sem quebrar quem já integrou; OpenAPI rica, com `response_model`, `summary`, `description`, exemplos e tags em cada endpoint; schemas de resposta tipados (`AnalyzeResponse`, `SentimentScores`) no lugar de dicionários soltos, porque se o contrato mora no tipo, o mypy e o `/docs` trabalham por mim; validação de payload (`Field(max_length=10_000)` no texto, `max_length=100` na lista) — uma API pública sem limite de tamanho é um DoS de brinquedo esperando acontecer; e `GET /` com metadados mais `GET /health` para liveness probe.

## Decisões que valem um parágrafo cada

**Multi-idioma sem reescrever o pipeline.** VADER só entende inglês. Para PT-BR usei o [LeIA](https://github.com/RafJaa/LeIA), um fork do VADER adaptado para português, plugado como um dispatcher simples no repository:

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

O detalhe que virou nota de rodapé importante: o pacote `leia` publicado no PyPI é um **stub vazio** — o projeto real nunca foi empacotado direito. Resolvi vendorizando o módulo (arquivo único + léxicos) em `src/vendor/leia/`, excluído de lint e mypy. Código de terceiros sob meu próprio controle de versão, imutável e auditável, em vez de depender de um pacote quebrado no PyPI.

**Cache, porque a carga é determinística.** Análise de sentimento aqui é CPU-bound pura e determinística — mesmo texto, mesmo score, sempre. É o caso de uso perfeito para cache. Implementei in-memory com TTL e eviction LRU, chaveado por `(language, text)`:

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

Cargas com texto repetido (reviews, redes sociais, monitoramento) têm taxa de acerto alta, e os números lá embaixo mostram o retorno disso.

**Batch sem segurar conexão.** `POST /v1/analyze_batch` responde `202 Accepted` com um job ID na hora; o processamento roda em background e o cliente consulta `GET /v1/results/{job_id}` até `completed` (ou `failed`).

**Streaming sem WebSocket.** Para quem quer resultado progressivo, `POST /v1/analyze_stream` responde com Server-Sent Events — um evento `data` por texto analisado, terminando com `event: done`. Funciona com um `curl -N` puro.

## Sem visibilidade eu não conserto nada

`GET /metrics` em formato Prometheus, com contadores de HTTP por método/rota/status, histograma de latência, distribuição de sentimentos por idioma, hits/misses do cache e jobs por status. Structured logging (`structlog`) em JSON, com `request_id` por request — gerado ou propagado via `X-Request-ID` — porque quando algo quebra eu quero filtrar por um ID e ver a linha exata, não caçar em texto solto. Header `X-Process-Time-Ms` em toda resposta. Sentry opcional, ligado só setando `SENTRY_DSN`. Rate limiting por IP (429 + `Retry-After`) e headers de segurança. Tudo configurável via variáveis de ambiente com `pydantic-settings`, e um `make dev` que sobe com reload pro dia a dia.

## Os números

Metodologia completa em `docs/benchmarks/`; o resumo é locust com 20 usuários virtuais, 30s por cenário, 1 worker, textos curtos:

| Cenário | req/s | p50 | p95 | p99 |
| --- | --- | --- | --- | --- |
| Cache hit (EN) | **971** | 18ms | 30ms | 53ms |
| Cache miss (EN, VADER) | 568 | 33ms | 60ms | 93ms |
| Cache miss (PT, LeIA) | 458 | 41ms | 95ms | 140ms |

+71% de vazão e -45% de latência no p50 só por não recalcular o que já foi calculado, zero falhas em todos os cenários. O LeIA é cerca de 20% mais lento que o VADER — léxico maior, normalização de acentuação — mas está longe de ser gargalo.

## O que eu levo daqui

O PyPI mente às vezes — verificar o que se instala é parte do trabalho, não paranoia; vendorizar código pequeno e estável é uma opção legítima quando o pacote oficial está quebrado. Cobertura de código também precisa de contexto: o código vendored derrubava a métrica pra 33%, e só excluir `src/vendor` do coverage revelou o número real — 98% nas 412 linhas que são efetivamente minhas. Estado in-memory tem dono: com `WORKERS > 1`, cada processo tem seu próprio cache e job store; pra este caso isso é aceitável, mas foi uma decisão consciente e documentada, não um acidente — se algum dia precisar de consistência global, o próximo passo é Redis. E uma pegadinha específica do FastAPI: `app.mount('/metrics')` responde 307 (redirect para `/metrics/`) e o Prometheus não segue redirect — resolvi expondo como rota normal com `generate_latest()`. Por fim, cada feature virou um commit isolado com lint, types e testes passando antes do próximo — o `git log` acabou sendo a narrativa mais honesta desse processo todo.

## Onde a API está agora

72 testes, 98% de cobertura, threshold de 90% bloqueando no CI. `ruff` (lint + format) e `mypy` limpos a cada push, CI em matrix de Python, build de Docker validada em todo push. API versionada e documentada, com cache, batch, streaming, rate limit e métricas. Benchmark reproduzível com `make benchmark`.
