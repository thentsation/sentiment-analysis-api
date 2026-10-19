"""Starts the Python and the Telvax version of the service, one at a time, loads each with `ab` and prints a table.

Every scenario is `ab` with 20 connections (10 for the batch), no keep-alive, on this machine. Cache hit: the same text
each time. Cache miss: the cache entry expires at once, so every request runs the analyzer. Batch: `analyze_multiple`
with 100 different texts. The numbers compare the two on one machine, they are not absolute.
"""

import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

PYTHON_MAIN = os.environ.get("PYTHON_MAIN", "/python/src/main.py")
TELVAX_SERVICE = os.environ.get("TELVAX_SERVICE", "/service")
SCALE = float(os.environ.get("COMPARE_SCALE", "1"))
CORES = os.cpu_count() or 1

EN = {"text": "I love this product, it is absolutely amazing!", "language": "en"}
PT = {"text": "Eu amo este produto, é absolutamente incrível!", "language": "pt"}
WORDS = ["wonderful", "terrible", "fine", "awful", "great", "boring", "lovely", "slow", "fast", "broken"]
BATCH = {
    "texts": [f"The {WORDS[i % 10]} service number {i} was {WORDS[(i * 3) % 10]} today." for i in range(100)],
    "language": "en",
}

# (name, body file, path, requests, connections, cache expires at once)
SCENARIOS = [
    ("Cache hit (texto repetido)", EN, "/v1/analyze", 3000, 20, False),
    ("Cache miss (inglês)", EN, "/v1/analyze", 2000, 20, True),
    ("Cache miss (português)", PT, "/v1/analyze", 2000, 20, True),
    ("Lote de 100 textos", BATCH, "/v1/analyze_multiple", 200, 10, True),
]


def servers():
    python = [sys.executable, PYTHON_MAIN]
    return [
        ("Python, 1 worker", python, {"WORKERS": "1"}),
        (f"Python, {CORES} workers", python, {"WORKERS": str(CORES)}),
        ("Telvax", [TELVAX_SERVICE], {}),
    ]


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def rss_mb(pid):
    """Resident memory of a process and its children, in MB."""
    parent = {}
    try:
        entries = os.listdir("/proc")
    except OSError:
        return 0.0
    for entry in entries:
        if entry.isdigit():
            try:
                with open(f"/proc/{entry}/status") as f:
                    parent[int(entry)] = int(re.search(r"PPid:\s+(\d+)", f.read()).group(1))
            except (OSError, AttributeError):
                pass
    tree, grew = {pid}, True
    while grew:
        grew = False
        for p, pp in parent.items():
            if pp in tree and p not in tree:
                tree.add(p)
                grew = True
    total = 0
    for p in tree:
        try:
            with open(f"/proc/{p}/status") as f:
                total += int(re.search(r"VmRSS:\s+(\d+) kB", f.read()).group(1))
        except (OSError, AttributeError):
            pass
    return total / 1024


class Server:
    def __init__(self, command, env, expires_at_once):
        self.port = free_port()
        full = dict(os.environ)
        full.update(
            HOST="127.0.0.1",
            PORT=str(self.port),
            RATE_LIMIT_PER_MINUTE="100000000",
            CACHE_TTL_SECONDS="0.00001" if expires_at_once else "300",
            **env,
        )
        self.command = command + (["--rate-limit", "100000000/min"] if command[0] == TELVAX_SERVICE else [])
        self.started = time.time()
        self.process = subprocess.Popen(
            self.command, env=full, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        self.url = f"http://127.0.0.1:{self.port}"
        for _ in range(600):
            try:
                urllib.request.urlopen(self.url + "/health", timeout=1).read()
                break
            except OSError:
                if self.process.poll() is not None:
                    raise SystemExit(f"{command[0]} stopped at start")
                time.sleep(0.05)
        else:
            raise SystemExit(f"{command[0]} did not answer on /health")
        self.start_seconds = time.time() - self.started

    def stop(self):
        self.process.terminate()
        try:
            self.process.wait(10)
        except subprocess.TimeoutExpired:
            self.process.kill()


def ab(url, body, requests, connections):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(body, f)
    out = subprocess.run(
        ["ab", "-n", str(requests), "-c", str(connections), "-p", f.name, "-T", "application/json", url],
        capture_output=True,
        text=True,
    ).stdout
    os.unlink(f.name)
    rate = re.search(r"Requests per second:\s+([\d.]+)", out)
    p50 = re.search(r"^\s+50%\s+(\d+)", out, re.M)
    p99 = re.search(r"^\s+99%\s+(\d+)", out, re.M)
    failed = re.search(r"Failed requests:\s+(\d+)", out)
    non2xx = re.search(r"Non-2xx responses:\s+(\d+)", out)
    if not rate:
        return None
    bad = int(failed.group(1)) + (int(non2xx.group(1)) if non2xx else 0) if failed else 0
    return {"rate": float(rate.group(1)), "p50": int(p50.group(1)), "p99": int(p99.group(1)), "bad": bad}


def measure(name, command, env):
    results, memory, start = {}, 0.0, 0.0
    for expires in (False, True):
        server = Server(command, env, expires)
        try:
            start = max(start, server.start_seconds)
            urllib.request.urlopen(server.url + "/health").read()
            for label, body, path, requests, connections, miss in SCENARIOS:
                if miss != expires:
                    continue
                print(f"  medindo {name}: {label} ...", flush=True)
                # One request first, so the first scenario does not pay for the first call.
                ab(server.url + path, body, 20, 1)
                results[label] = ab(server.url + path, body, max(20, int(requests * SCALE)), connections)
            memory = max(memory, rss_mb(server.process.pid))
        finally:
            server.stop()
    return results, memory, start


INTRO = """Comparação: serviço de análise de sentimento em Python (FastAPI) x em Telvax
===========================================================================
Máquina com {cores} núcleos. Cada versão roda sozinha, uma depois da outra, e recebe a mesma carga.
O teste leva cerca de um minuto.

Como cada número é medido
  - Uma ferramenta (ab, Apache Bench) manda requisições POST ao serviço sem parar, 20 ao mesmo tempo
    (10 no lote), cada uma numa conexão nova, e mede quanto o serviço aguenta.
  - O serviço guarda em memória o resultado de cada texto já analisado (o "cache"):
      Cache hit  = o texto já estava no cache; o serviço só devolve o resultado guardado (o caso mais barato).
      Cache miss = o texto não estava no cache; o serviço faz a análise de verdade (léxico, negações, pontuação).
                   Para forçar isso, o cache expira na hora, então toda requisição é uma análise nova.
      Lote de 100 textos = uma requisição com 100 textos diferentes, todos analisados de verdade.
"""

GUIDE = """
Como ler a tabela
  - Cada célula de cenário é "A (B / C)":
      A = requisições por segundo que o serviço respondeu (quanto MAIOR, melhor). Ex.: 1,000 quer dizer
          mil requisições respondidas por segundo. No lote, cada requisição tem 100 textos (multiplique por 100
          para ter textos analisados por segundo).
      B = p50, em milissegundos: metade das requisições respondeu em até esse tempo (o tempo típico).
      C = p99, em milissegundos: 99% das requisições responderam em até esse tempo; só 1% foi mais lenta
          (o pior caso comum). Quanto MENOR, melhor.
  - "Python, 1 worker" é um processo Python, como o serviço roda por padrão. "Python, N workers" usa um processo
    por núcleo da máquina (a forma comum de dar mais vazão ao Python). Telvax roda como um único processo
    que já usa vários núcleos.
  - Memória = memória residente do serviço (e de seus processos filhos) depois dos testes (menor é melhor).
  - Início = tempo até o serviço responder /health depois de ser iniciado (menor é melhor).
  - "Telvax contra o melhor Python" = requisições por segundo do Telvax dividido pelas do melhor Python
    (1 worker ou N workers) em cada cenário. 10x quer dizer dez vezes mais requisições por segundo.
  - O teste roda tudo na mesma máquina, o gerador de carga inclusive, e cada medição é curta. Serve para
    comparar as duas versões entre si, não para medir um valor absoluto.
"""


def main():
    print(INTRO.format(cores=CORES), flush=True)
    rows = []
    for name, command, env in servers():
        rows.append((name, *measure(name, command, env)))
    print("\nResultado: requisições por segundo (p50 / p99 em ms)\n")
    header = ["Cenário"] + [r[0] for r in rows]
    table = [header]
    for label, *_ in SCENARIOS:
        line = [label]
        for _, results, _, _ in rows:
            r = results.get(label)
            line.append("falhou" if r is None else f"{r['rate']:,.0f} ({r['p50']} / {r['p99']})" + (f" !{r['bad']} com erro" if r["bad"] else ""))
        table.append(line)
    table.append(["Memória depois dos testes"] + [f"{r[2]:.0f} MB" for r in rows])
    table.append(["Início até o /health responder"] + [f"{r[3]:.2f} s" for r in rows])
    widths = [max(len(row[i]) for row in table) for i in range(len(header))]
    for i, row in enumerate(table):
        print("| " + " | ".join(c.ljust(w) for c, w in zip(row, widths)) + " |")
        if i == 0:
            print("|" + "|".join("-" * (w + 2) for w in widths) + "|")
    best = {}
    for label, *_ in SCENARIOS:
        py = max((r[1][label]["rate"] for r in rows[:2] if r[1].get(label)), default=0)
        tv = rows[2][1].get(label)
        if py and tv:
            best[label] = tv["rate"] / py
    print("\nTelvax contra o melhor Python (requisições por segundo):")
    for k, v in best.items():
        print(f"  {k}: {v:.1f}x")
    print(GUIDE)


if __name__ == "__main__":
    main()
