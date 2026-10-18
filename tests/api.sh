#!/bin/sh
# Calls a running server and checks every route. Usage: tests/api.sh [base-url]
# The expected scores are the ones the Python service (NLTK VADER and LeIA) gave for the same texts.
set -eu
BASE=${1:-http://127.0.0.1:8000}
FAILED=0

check() { # name expected actual
  if [ "$2" = "$3" ]; then
    echo "ok      $1"
  else
    echo "FAILED  $1: expected '$2', got '$3'"
    FAILED=1
  fi
}

post() { curl -sS -X POST "$BASE$1" -H 'content-type: application/json' -d "$2" -w '\n%{http_code}'; }
body() { printf '%s' "$1" | sed '$d'; }
code() { printf '%s' "$1" | tail -n 1; }

R=$(post /v1/analyze '{"text":"I love this!"}')
check "analyze status" 200 "$(code "$R")"
check "analyze compound" 0.6696 "$(body "$R" | jq -r .sentiment.compound)"
check "analyze language defaults to en" en "$(body "$R" | jq -r .language)"

R=$(post /v1/analyze '{"text":"MUITO BOM o dia","language":"pt"}')
check "analyze pt compound" 0.5473 "$(body "$R" | jq -r .sentiment.compound)"

R=$(post /v1/analyze '{"text":""}')
check "empty text is 400" 400 "$(code "$R")"
check "empty text detail" "No text provided" "$(body "$R" | jq -r .detail)"

R=$(post /v1/analyze '{"text":"x","language":"fr"}')
check "unknown language is 422" 422 "$(code "$R")"

R=$(post /v1/analyze_multiple '{"texts":["I love this!","I hate this!"]}')
check "analyze_multiple" "0.6696 -0.6114" "$(body "$R" | jq -r '[.results["I love this!"].compound, .results["I hate this!"].compound] | join(" ")')"

R=$(post /v1/analyze_multiple '{"texts":[]}')
check "no texts is 400" 400 "$(code "$R")"

R=$(post /v1/analyze_statistics '{"texts":["I love this!","I hate this!","the table"]}')
check "statistics" "1 1 1" "$(body "$R" | jq -r '[.statistics.positive, .statistics.negative, .statistics.neutral] | map(tostring) | join(" ")')"

check "sentiment_classes" "Scores greater than 0.05" "$(curl -sS "$BASE/v1/sentiment_classes" | jq -r .classes.positive)"

R=$(post /v1/analyze_batch '{"texts":["I love this!","I hate this!","fine"]}')
check "batch is 202" 202 "$(code "$R")"
JOB=$(body "$R" | jq -r .job_id)
check "batch results_url" "/v1/results/$JOB" "$(body "$R" | jq -r .results_url)"
STATUS=pending
for _ in $(seq 1 30); do
  STATUS=$(curl -sS "$BASE/v1/results/$JOB" | jq -r .status)
  [ "$STATUS" = completed ] && break
  sleep 0.2
done
check "batch completes" completed "$STATUS"
check "batch processed" 3 "$(curl -sS "$BASE/v1/results/$JOB" | jq -r .processed)"
check "unknown job is 404" 404 "$(curl -sS -o /dev/null -w '%{http_code}' "$BASE/v1/results/nope")"

STREAM=$(curl -sS -N -X POST "$BASE/v1/analyze_stream" -H 'content-type: application/json' -d '{"texts":["I love this!","I hate this!"]}')
check "stream data events" 2 "$(printf '%s\n' "$STREAM" | grep -c '^data: {"')"
check "stream ends with done" 1 "$(printf '%s\n' "$STREAM" | grep -c '^event: done')"

check "root name" "Sentiment Analysis API" "$(curl -sS "$BASE/" | jq -r .name)"
check "health" ok "$(curl -sS "$BASE/health" | jq -r .status)"
check "openapi" 3.0.3 "$(curl -sS "$BASE/openapi.json" | jq -r .openapi)"
check "metrics" yes "$(curl -sS "$BASE/metrics" | grep -q '^telvax_http_requests_total' && echo yes || echo no)"
check "process time header" 1 "$(curl -sSI "$BASE/health" | grep -ci '^x-process-time-ms:')"
check "labelled counter" yes "$(curl -sS "$BASE/metrics" | grep -q '^sentiment_analysis_total{language="en",sentiment="positive"}' && echo yes || echo no)"
R=$(post /v1/analyze '{"text":"x","top":1}')
check "a body that does not fit is 422 with detail" "422 array" "$(code "$R") $(body "$R" | jq -r '.detail | type')"
check "request id" 1 "$(curl -sSI "$BASE/health" | grep -ci '^x-request-id:')"
check "security headers" 1 "$(curl -sSI "$BASE/health" | grep -ci '^x-content-type-options: nosniff')"

R=$(curl -sS -X DELETE "$BASE/v1/cache" -w '\n%{http_code}')
check "cache invalidation" "cache invalidated" "$(body "$R" | jq -r .status)"

exit "$FAILED"
