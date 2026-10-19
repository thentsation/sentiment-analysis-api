🇧🇷 Português | [🇺🇸 English](README.md)

# API de Análise de Sentimento

Análise de sentimento em textos com VADER (inglês) e LeIA (português), escrita em [Telvax](https://github.com/telvax/telvax).
O serviço é um programa com a mesma organização do serviço Python (`src/main.tvx`, `config`, `models`, `routes`, `services`, `vendor/leia`) e roda como um único binário, com os
léxicos dentro dele. Começou como uma aplicação FastAPI; os scores das duas versões são os mesmos (veja [Testes](#testes)).

## Funcionalidades

- Análise de sentimento de um único texto ou de múltiplos textos (EN/PT).
- Análise em lote assíncrona: envie lotes grandes e consulte os resultados pelo ID do job; com `DATABASE_URL` os jobs sobrevivem a um reinício.
- Streaming de análise progressiva via Server-Sent Events (SSE).
- Cache de resultados com TTL e endpoint administrativo de invalidação.
- Rate limiting, headers de segurança e CORS.
- Observabilidade: `/metrics` no formato Prometheus, logs em JSON com request id.
- Endpoints de health check e metadados da API.
- API versionada sob `/v1` com documento OpenAPI gerado a partir dos tipos.

## Requisitos

- O comando `telvax`, ou Docker. Veja [telvax/telvax](https://github.com/telvax/telvax) para instalar.

## Uso

```bash
make run          # http://127.0.0.1:8000
make dev          # logs em texto
make test         # os scores contra o serviço Python
make api-test     # chama todas as rotas de um servidor em execução
make build        # um binário: ./sentiment-analysis-api
```

`make run` é `telvax serve src/main.tvx --port 8000 --metrics --log-format json --cors '*' --rate-limit 100/min --security-headers`.

### Targets do Make

| Target | Descrição |
| --- | --- |
| `make run` | Executa a aplicação |
| `make dev` | Executa com logs em texto |
| `make check` | Verifica os tipos do programa |
| `make test` | Executa os testes |
| `make format` | Formata `src/` |
| `make lint` | Verifica formatação e lint |
| `make build` | Gera um binário com o programa e os léxicos |
| `make api-test` | Chama todas as rotas de um servidor em execução |
| `make load-test` | Abre a interface de teste de carga do Locust (instalado em `.venv`) |
| `make benchmark` | Executa o benchmark de cache (hit vs miss, EN/PT); o rate limit precisa ser alto |
| `make docker-build` | Gera a imagem Docker |
| `make docker-run` | Executa o container Docker na porta 8000 |
| `make clean` | Remove `.venv` e o binário |

### Configuração

O serviço lê variáveis de ambiente. As primeiras são lidas por todo binário feito com `telvax build --serve`:

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `HOST` | `0.0.0.0` | Host de bind |
| `PORT` | `8080` (`8000` na imagem) | Porta de bind; `--port` tem prioridade |
| `TELVAX_LOG_FORMAT` | _(nenhum)_ | `json` ou `text`: uma linha de log por requisição, com request id |
| `TELVAX_RATE_LIMIT` | _(nenhum)_ | Requisições por endereço de cliente, como `100/min` |
| `TELVAX_CORS` | _(nenhum)_ | Origens permitidas, `*` ou lista separada por vírgulas |
| `TELVAX_METRICS` | _(nenhum)_ | `1` serve `/metrics` |
| `TELVAX_SECURITY_HEADERS` | _(nenhum)_ | `1` adiciona os headers de segurança |
| `ADMIN_TOKEN` | _(vazio)_ | Quando definido, `DELETE /v1/cache` exige `X-Admin-Token` |
| `CACHE_MAXSIZE` | `10000` | Máximo de entradas de sentimento em cache |
| `CACHE_TTL_SECONDS` | `300` | TTL das entradas do cache |
| `JOB_STORE_MAXSIZE` | `100` | Máximo de jobs de lote mantidos em memória |
| `DATABASE_URL` | _(vazio)_ | Guarda os jobs de lote no PostgreSQL (exige também `TELVAX_LIVE=1`) |

Observações:

- Um processo atende todas as requisições, então cache, jobs e contadores são compartilhados; não existe `WORKERS`.
  Rode vários containers atrás de um balanceador e use `DATABASE_URL` se os jobs precisarem ser vistos por todos.
- Quando o cache enche, sai a primeira chave em ordem, não a mais antiga.
- Um erro no corpo da requisição é um `400` com `{"error": "invalid request", "details": [...]}`; um valor que o serviço
  rejeita (texto com mais de 10.000 caracteres, idioma diferente de `en` e `pt`, mais de 100 textos) é um `422` com
  `{"detail": "..."}`, como os outros erros do serviço.

### Docker

```bash
make docker-build
make docker-run
```

Ou com docker compose:

```bash
docker compose up --build
```

A imagem compila o programa com `ghcr.io/telvax/telvax` e leva só o binário, numa base distroless. O health check é
`/service --healthcheck /health`.

### Testes

`src/leia_test.tvx` tem 45 textos (inglês e português) com os scores que o serviço Python deu; foram gerados
rodando o NLTK VADER e o LeIA vendorizado da versão anterior sobre os textos. Outras 800 frases aleatórias (palavras dos
léxicos, negações, maiúsculas, pontuação, acentos, emoji) deram os mesmos scores nas duas versões.

```bash
make test
```

### Teste de carga

Suba a API e execute a interface do Locust (http://localhost:8089):

```bash
make run
make load-test
```

### Benchmark

Benchmark de cache hit vs cache miss (resultados e metodologia em [`docs/benchmarks/`](docs/benchmarks/)):

```bash
telvax serve src/main.tvx --rate-limit 1000000/min
make benchmark
```

## Endpoints da API

A documentação interativa está disponível em `/docs`; o documento OpenAPI está em `/openapi.json`.

### Meta

- **GET /** — Metadados da API (nome, versão, docs, lista de endpoints).
- **GET /health** — Health check.
- **GET /metrics** — Métricas no formato Prometheus: requisições e latência por rota, e os
  contadores do serviço como `telvax_counter_total{name="..."}` (`cache_hits`, `cache_misses`,
  `sentiment_analysis_<idioma>_<classe>`, `batch_jobs_<status>`).

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

- **pipeline_telvax.yaml** — em todo push/PR: `telvax check`, `fmt --check`, `lint`, os testes e um container que é
  construído, espera o health check e é chamado em todas as rotas por `tests/api.sh`.
- **pipeline_docker.yaml** — em todo push/PR: gera a imagem Docker e faz o scan.

## Estrutura do projeto

```
src/
├── main.tvx                       # App: rotas raiz e health
├── config.tvx                     # Configurações vindas do ambiente
├── db.tvx                         # Armazenamento dos jobs no PostgreSQL
├── models/
│   └── models.tvx                 # Tipos de requisição e resposta, limites de uma requisição
├── repositories/
│   └── sentiment_repository.tvx   # A análise de um texto
├── routes/
│   └── sentiment_routes.tvx       # As rotas /v1: análise, cache, jobs de lote, SSE
├── services/
│   ├── cache_service.tvx          # Cache de scores
│   ├── job_store.tvx              # Jobs de lote, em memória e no PostgreSQL
│   └── sentiment_service.tvx      # Sentimento pelo cache, classes
├── vendor/leia/
│   ├── leia.tvx                   # VADER e LeIA
│   └── lexicons/                  # Os léxicos, embutidos no binário
└── *_test.tvx                     # Testes: modelos, serviços e scores contra o serviço Python
tests/
└── api.sh                         # Chama todas as rotas de um servidor em execução
```
