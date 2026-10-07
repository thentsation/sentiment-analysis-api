🇧🇷 Português | [🇺🇸 English](README.md)

# API de Análise de Sentimento

Aplicação FastAPI que realiza análise de sentimento em textos usando o NLTK VADER (inglês) e o LeIA (português).

## Funcionalidades

- Análise de sentimento de um único texto ou de múltiplos textos (EN/PT).
- Análise em lote assíncrona: envie lotes grandes e consulte os resultados pelo ID do job.
- Streaming de análise progressiva via Server-Sent Events (SSE).
- Cache de resultados com TTL e endpoint administrativo de invalidação.
- Rate limiting, headers de segurança e CORS.
- Observabilidade: `/metrics` no formato Prometheus, logging estruturado com request id e integração com Sentry.
- Endpoints de health check e metadados da API.
- API versionada sob `/v1` com documentação OpenAPI rica.

## Requisitos

- Python 3.11 ou superior
- FastAPI, Uvicorn, NLTK (veja `config/requirements.txt`)

## Instalação

1. Clone o repositório:

   ```bash
   git clone https://github.com/ntsation/sentiment-analysis-api.git
   cd sentiment-analysis-api
   ```

2. Crie o ambiente virtual e instale as dependências:

   ```bash
   make install
   ```

   Ou manualmente:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r config/requirements.txt
   ```

## Uso

1. Execute a aplicação:

   ```bash
   make run
   ```

   A API vai subir em `http://127.0.0.1:8000`.

2. Para desenvolvimento com auto-reload:

   ```bash
   make dev
   ```

### Targets do Make

| Target | Descrição |
| --- | --- |
| `make install` | Cria a `.venv` e instala as dependências (runtime + dev) |
| `make run` | Executa a aplicação |
| `make dev` | Executa com auto-reload (uvicorn) |
| `make test` | Executa a suíte de testes |
| `make coverage` | Executa os testes com relatório de cobertura |
| `make lint` | Executa `ruff check .` |
| `make format` | Executa `ruff format .` |
| `make typecheck` | Executa `mypy` |
| `make load-test` | Executa a interface de teste de carga do locust |
| `make benchmark` | Executa o benchmark de cache (hit vs miss, EN/PT) — requer o servidor rodando com `RATE_LIMIT_PER_MINUTE` alto |
| `make docker-build` | Constrói a imagem Docker |
| `make docker-run` | Executa o container Docker na porta 8000 |
| `make clean` | Remove caches e artefatos |

### Configuração

As configurações são lidas de variáveis de ambiente (ou de um arquivo `.env` — veja `.env.example`):

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `HOST` | `0.0.0.0` | Host de bind |
| `PORT` | `8000` | Porta de bind |
| `LOG_LEVEL` | `info` | Nível de log do Uvicorn |
| `LOG_FORMAT` | `json` | Formato do log: `json` ou `console` |
| `WORKERS` | `1` | Processos worker do Uvicorn |
| `RATE_LIMIT_PER_MINUTE` | `100` | Requisições por minuto por cliente |
| `CORS_ORIGINS` | `["*"]` | Origens permitidas (lista JSON) |
| `ADMIN_TOKEN` | _(vazio)_ | Quando definido, `DELETE /v1/cache` exige o header `X-Admin-Token` |
| `CACHE_MAXSIZE` | `10000` | Número máximo de entradas em cache |
| `CACHE_TTL_SECONDS` | `300` | TTL das entradas de cache |
| `JOB_STORE_MAXSIZE` | `100` | Número máximo de jobs de lote mantidos em memória |
| `SENTRY_DSN` | _(vazio)_ | Habilita o rastreamento de erros do Sentry quando definido |
| `SENTRY_TRACES_SAMPLE_RATE` | `1.0` | Taxa de amostragem de traces do Sentry |

Nota: com `WORKERS > 1`, cada worker mantém seu próprio cache em memória, job store e
registro de métricas (por processo). Use um único worker ou um armazenamento externo
compartilhado se precisar de consistência global.

### Hooks de pre-commit

Instale os hooks (lint + format a cada commit):

```bash
pre-commit install
```

### Docker

```bash
make docker-build
make docker-run
```

Ou com docker compose:

```bash
docker compose up --build
```

### Teste de carga

Suba a API e execute a interface do locust (http://localhost:8089):

```bash
make run
make load-test
```

Exemplo headless:

```bash
.venv/bin/locust -f load_tests/locustfile.py --host http://localhost:8000 \
  --headless -u 50 -r 5 --run-time 30s
```

### Benchmark

Benchmark de cache hit vs cache miss (resultados e metodologia em
[`docs/benchmarks/`](docs/benchmarks/)):

```bash
RATE_LIMIT_PER_MINUTE=1000000 make run
make benchmark
```

## Endpoints da API

A documentação interativa está disponível em `/docs` (Swagger) e `/redoc`.

### Meta

- **GET /** — Metadados da API (nome, versão, docs, lista de endpoints).
- **GET /health** — Health check.
- **GET /metrics** — Métricas no formato Prometheus (contadores de requisições HTTP,
  histograma de latência, distribuição de sentimentos por idioma, hits/misses do cache,
  contadores de jobs de lote).

### Sentimento (`/v1`)

- **POST /v1/analyze** — Analisa um único texto (máximo de 10.000 caracteres).
  - **Corpo da requisição:**
    ```json
    {
      "text": "I love this!",
      "language": "en"
    }
    ```
    `language` é opcional (`en` ou `pt`, padrão `en`).
  - **Resposta:**
    ```json
    {
      "text": "I love this!",
      "language": "en",
      "sentiment": {
        "neg": 0.0,
        "neu": 0.182,
        "pos": 0.818,
        "compound": 0.6696
      }
    }
    ```

- **POST /v1/analyze_multiple** — Analisa múltiplos textos (máximo de 100), indexados pelo texto.

- **POST /v1/analyze_statistics** — Conta textos positivos/neutros/negativos.

- **GET /v1/sentiment_classes** — Thresholds de classificação.

### Lote (`/v1`)

- **POST /v1/analyze_batch** — Envia um lote para análise assíncrona. Retorna
  `202 Accepted` com um job id imediatamente:
  ```json
  {
    "job_id": "e2b1...",
    "status": "pending",
    "total": 2,
    "results_url": "/v1/results/e2b1..."
  }
  ```

- **GET /v1/results/{job_id}** — Consulta o status do job (`pending`, `processing`,
  `completed`, `failed`); inclui os resultados por texto quando concluído. Retorna `404`
  para jobs desconhecidos ou removidos.

### Streaming (`/v1`)

- **POST /v1/analyze_stream** — Resposta via Server-Sent Events com um evento `data`
  por texto analisado, finalizando com `event: done`.

### Admin (`/v1`)

- **DELETE /v1/cache** — Invalida o cache de sentimento. Exige o header
  `X-Admin-Token` quando `ADMIN_TOKEN` está configurado.

## CI/CD

- **pipeline_python.yaml** — a cada push/PR: `ruff check`, `ruff format --check`,
  `pytest` com cobertura (Python 3.11 e 3.12) e `mypy`.
- **pipeline_docker.yaml** — a cada push/PR: constrói a imagem Docker.

## Estrutura do projeto

```
src/
├── config.py              # Configurações Pydantic (via variáveis de ambiente)
├── main.py                # App factory, middlewares, rotas de metadados
├── middlewares/           # Rate limit, headers de segurança, métricas, contexto da requisição
├── models/                # Schemas de request/response
├── observability/         # Métricas Prometheus, structlog, Sentry
├── repositories/          # Dispatch dos analisadores (VADER/LeIA)
├── routes/                # Endpoints /v1
├── services/               # Lógica de negócio, cache, job store
└── vendor/                # Código de terceiros vendorizado (LeIA)
```
