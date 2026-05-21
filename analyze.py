"""
analyze.py — Turns parsed LogEntry records into useful answers.

Each function takes the list of entries and returns plain data structures,
so the CLI layer (cli.py) can decide how to print them.
"""

from collections import Counter, defaultdict
from statistics import median


def summary(entries):
    """High-level counts an on-call engineer wants at a glance."""
    total = len(entries)
    statuses = Counter(e.status for e in entries if e.status is not None)
    errors_4xx = sum(c for s, c in statuses.items() if 400 <= s < 500)
    errors_5xx = sum(c for s, c in statuses.items() if 500 <= s < 600)
    times = [e.response_ms for e in entries if e.response_ms is not None]
    methods = Counter(e.method for e in entries if e.method)
    return {
        "total_parsed": total,
        "status_counts": dict(sorted(statuses.items())),
        "errors_4xx": errors_4xx,
        "errors_5xx": errors_5xx,
        "method_counts": dict(methods.most_common()),
        "response_ms_avg": round(sum(times) / len(times), 1) if times else None,
        "response_ms_median": round(median(times), 1) if times else None,
        "response_ms_max": round(max(times), 1) if times else None,
    }


def slowest_endpoints(entries, n=10):
    """Average response time per path, slowest first. Path = method + path."""
    buckets = defaultdict(list)
    for e in entries:
        if e.response_ms is not None and e.path:
            key = f"{e.method or '?'} {e.path}"
            buckets[key].append(e.response_ms)
    rows = [
        (key, round(sum(v) / len(v), 1), len(v), round(max(v), 1))
        for key, v in buckets.items()
    ]
    rows.sort(key=lambda r: r[1], reverse=True)
    return rows[:n]


def top_errors(entries, n=10):
    """Most frequent error responses (status >= 400), grouped by path+status."""
    counter = Counter()
    for e in entries:
        if e.status is not None and e.status >= 400 and e.path:
            counter[(e.status, f"{e.method or '?'} {e.path}")] += 1
    return counter.most_common(n)


def top_ips(entries, n=10):
    """Busiest client IPs — useful for spotting a hammering client."""
    counter = Counter(e.ip for e in entries if e.ip)
    return counter.most_common(n)
