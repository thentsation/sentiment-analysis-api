# Benchmark: cache de análise de sentimento

Data: 2026-08-20

## Metodologia

- **Ferramenta:** locust 2.46.3 (processo único, 20 usuários virtuais, spawn imediato)
- **Duração:** 30s por cenário (20s no cenário PT-BR)
- **Servidor:** uvicorn, 1 worker, Python 3.14.3, macOS (Apple Silicon), client e server na mesma máquina (loopback)
- **Configuração:** `RATE_LIMIT_PER_MINUTE=1000000` (rate limit desativado), `LOG_LEVEL=warning`
- **Endpoint:** `POST /v1/analyze` com textos curtos (~40 caracteres)
- **Cenários** (`load_tests/benchmark.py`):
  - `CacheHitUser` — pool fixo de 10 textos em inglês; após o warmup, toda requisição é cache hit
  - `CacheMissUser` — textos únicos (uuid sufixado) em inglês; toda requisição executa o VADER
  - `PtCacheMissUser` — textos únicos em português; toda requisição executa o LeIA

Reprodução:

```bash
RATE_LIMIT_PER_MINUTE=1000000 make run
make benchmark
```

Números absolutos são conservadores (loopback + locust no mesmo processo da máquina);
a comparação relativa entre cenários é o que importa.

## Resultados

| Cenário | req/s | p50 (ms) | p95 (ms) | p99 (ms) | Requisições | Falhas |
| --- | --- | --- | --- | --- | --- | --- |
| Cache hit (EN) | 971 | 18 | 30 | 53 | 28.875 | 0 |
| Cache miss (EN, VADER) | 568 | 33 | 60 | 93 | 16.965 | 0 |
| Cache miss (PT, LeIA) | 458 | 41 | 95 | 140 | 9.131 | 0 |

## Interpretação

- **Cache hit vs miss (EN):** o cache aumenta a vazão em ~71% (971 vs 568 req/s)
  e reduz a latência p50 em ~45% (18ms vs 33ms). Em cargas com repetição de textos
  (redes sociais, reviews, monitoramento), a taxa de acerto tende a ser alta e o
  cache paga o custo do TTL/LRU rapidamente.
- **VADER vs LeIA (miss):** o LeIA é ~20% mais lento que o VADER em textos curtos
  (léxico PT-BR maior + normalização de acentuação), mas segue na casa de centenas
  de req/s por worker — muito acima do necessário para o caso de uso típico.
- **Zero falhas** em todos os cenários: sem 429 (rate limit desativado) e sem 5xx,
  validando estabilidade sob carga sustentada por 30s.

## Limitações

- Um worker; `WORKERS>1` multiplica a vazão aproximada (análise é CPU-bound e o
  GIL é liberado entre requests pelo uvicorn), mas cache/jobs são por processo.
- Não foram medidos `/v1/analyze_batch`, `/v1/analyze_stream` nem textos longos
  (o custo do analyzer cresce com o tamanho do texto).
