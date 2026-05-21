# loglens

A small, dependency-free command-line tool that reads a messy server log file
and produces useful output for someone on call: a summary report, the slowest
endpoints, the most common errors, and the busiest client IPs.

Its main job is **robustness**. Real logs contain malformed lines, multiple
timestamp formats, mixed response-time units, missing fields, and even
JSON-formatted lines bolted on by a different logger. loglens parses what it
can, skips what it can't, and **always reports exactly what it skipped and
why** it never silently drops data.

## Requirements

- Python 3.8 or newer. That's it only the standard library is used. No `pip install`.

## How to run

From the repository root:

```bash
# Full report (summary + slowest endpoints + top errors)
python3 loglens.py path/to/logfile.log
```

Other views:

```bash
python3 loglens.py path/to/logfile.log --slowest 10   # 10 slowest endpoints
python3 loglens.py path/to/logfile.log --errors       # top error responses
python3 loglens.py path/to/logfile.log --ips          # busiest client IPs
```

## Generating a test log

There's no sample file shipped, so a generator is included. It produces a
representative log including all the documented deviations (alternate
timestamps, mixed units, missing statuses, appended fields, JSON lines, and
fully malformed lines).

```bash
python3 scripts/generate_logs.py --lines 3000 --seed 42 > sample.log
python3 loglens.py sample.log
```

Flags: `--lines N` (default 2000), `--seed N` (reproducible output),
`--deviation-rate 0.08` (fraction of deviant lines).

## Project layout

```
loglens.py              CLI entry point (argument parsing + printing)
parser.py               Turns raw lines into structured records (the robust core)
analyze.py              Computes summary stats from parsed records
scripts/generate_logs.py  Test-data generator
ANSWERS.md              Answers to the assessment questions
```
