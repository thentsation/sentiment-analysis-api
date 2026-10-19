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
    ("Cache hit, one text", EN, "/v1/analyze", 3000, 20, False),
    ("Cache miss, English", EN, "/v1/analyze", 2000, 20, True),
    ("Cache miss, Portuguese", PT, "/v1/analyze", 2000, 20, True),
    ("100 texts in a request", BATCH, "/v1/analyze_multiple", 200, 10, True),
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
                print(f"  {name}: {label} ...", flush=True)
                # One request first, so the first scenario does not pay for the first call.
                ab(server.url + path, body, 20, 1)
                results[label] = ab(server.url + path, body, max(20, int(requests * SCALE)), connections)
            memory = max(memory, rss_mb(server.process.pid))
        finally:
            server.stop()
    return results, memory, start


def main():
    print(f"{CORES} cores. Running each version alone, one after the other; this takes a few minutes.\n", flush=True)
    rows = []
    for name, command, env in servers():
        rows.append((name, *measure(name, command, env)))
    print("\nRequests per second (p50 / p99 in ms), 20 connections, no keep-alive\n")
    header = ["Scenario"] + [r[0] for r in rows]
    table = [header]
    for label, *_ in SCENARIOS:
        line = [label]
        for _, results, _, _ in rows:
            r = results.get(label)
            line.append("failed" if r is None else f"{r['rate']:,.0f} ({r['p50']} / {r['p99']})" + (f" !{r['bad']} bad" if r["bad"] else ""))
        table.append(line)
    table.append(["Memory after the runs"] + [f"{r[2]:.0f} MB" for r in rows])
    table.append(["Start until /health answers"] + [f"{r[3]:.2f} s" for r in rows])
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
    print("\nTelvax against the better Python run: " + ", ".join(f"{k} {v:.1f}x" for k, v in best.items()))
    print("One machine, one short run each: compare the two, do not read the numbers as absolute.")


if __name__ == "__main__":
    main()
