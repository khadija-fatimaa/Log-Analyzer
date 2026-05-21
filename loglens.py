#!/usr/bin/env python3
"""
loglens — a small, dependency-free log analyzer for on-call engineers.

Usage:
    python3 loglens.py <logfile>                 # full summary report
    python3 loglens.py <logfile> --slowest 10    # 10 slowest endpoints
    python3 loglens.py <logfile> --errors        # top error responses
    python3 loglens.py <logfile> --ips           # busiest client IPs

Always prints a "data quality" section: how many lines parsed, how many were
skipped and why, and what format anomalies were seen. Nothing is silently
dropped — that's the whole point.
"""

import argparse
import sys

import analyze
from parser import parse_file


def _print_quality(result):
    parsed = len(result.entries)
    print("=" * 60)
    print("DATA QUALITY")
    print("=" * 60)
    print(f"  Total lines read : {result.total_lines}")
    print(f"  Parsed OK        : {parsed}")
    print(f"  Skipped          : {result.skipped}", end="")
    if result.total_lines:
        pct = 100.0 * result.skipped / result.total_lines
        print(f"  ({pct:.1f}%)")
    else:
        print()
    if result.skip_reasons:
        print("  Skip reasons:")
        for reason, count in sorted(result.skip_reasons.items(), key=lambda x: -x[1]):
            print(f"    - {reason}: {count}")
    if result.anomalies:
        print("  Format anomalies (parsed, but with a quirk):")
        for kind, count in sorted(result.anomalies.items(), key=lambda x: -x[1]):
            print(f"    - {kind}: {count}")
    print()


def _print_summary(result):
    s = analyze.summary(result.entries)
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Requests parsed  : {s['total_parsed']}")
    print(f"  4xx errors       : {s['errors_4xx']}")
    print(f"  5xx errors       : {s['errors_5xx']}")
    if s["response_ms_avg"] is not None:
        print(f"  Response time    : avg {s['response_ms_avg']}ms / "
              f"median {s['response_ms_median']}ms / max {s['response_ms_max']}ms")
    print(f"  Methods          : "
          + ", ".join(f"{m}={c}" for m, c in s["method_counts"].items()))
    print("  Status codes     : "
          + ", ".join(f"{code}={c}" for code, c in s["status_counts"].items()))
    print()


def _print_slowest(result, n):
    rows = analyze.slowest_endpoints(result.entries, n)
    print("=" * 60)
    print(f"TOP {n} SLOWEST ENDPOINTS (by average response time)")
    print("=" * 60)
    if not rows:
        print("  (no timing data available)")
    for key, avg, count, mx in rows:
        print(f"  {avg:>8.1f}ms avg  | {count:>6} reqs | max {mx:>8.1f}ms | {key}")
    print()


def _print_errors(result, n):
    rows = analyze.top_errors(result.entries, n)
    print("=" * 60)
    print(f"TOP {n} ERROR RESPONSES")
    print("=" * 60)
    if not rows:
        print("  (no errors found)")
    for (status, key), count in rows:
        print(f"  {count:>6}x  {status}  {key}")
    print()


def _print_ips(result, n):
    rows = analyze.top_ips(result.entries, n)
    print("=" * 60)
    print(f"TOP {n} BUSIEST CLIENT IPs")
    print("=" * 60)
    for ip, count in rows:
        print(f"  {count:>6} reqs  {ip}")
    print()


def main(argv=None):
    ap = argparse.ArgumentParser(description="Analyze a server log file.")
    ap.add_argument("logfile", help="path to the log file")
    ap.add_argument("--slowest", type=int, metavar="N", nargs="?", const=10,
                    help="show N slowest endpoints (default 10)")
    ap.add_argument("--errors", action="store_true", help="show top error responses")
    ap.add_argument("--ips", action="store_true", help="show busiest client IPs")
    args = ap.parse_args(argv)

    try:
        result = parse_file(args.logfile)
    except FileNotFoundError:
        print(f"error: file not found: {args.logfile}", file=sys.stderr)
        return 2
    except PermissionError:
        print(f"error: cannot read file (permission denied): {args.logfile}", file=sys.stderr)
        return 2

    _print_quality(result)

    # If no specific view was requested, show the full summary.
    specific = args.slowest is not None or args.errors or args.ips
    if not specific:
        _print_summary(result)
        _print_slowest(result, 10)
        _print_errors(result, 10)
        return 0

    if args.slowest is not None:
        _print_slowest(result, args.slowest)
    if args.errors:
        _print_errors(result, 10)
    if args.ips:
        _print_ips(result, 10)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        # Happens when output is piped to a command that closes early (e.g. head).
        # Suppress the noisy traceback and exit cleanly.
        try:
            sys.stdout.close()
        except Exception:
            pass
        sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(130)
