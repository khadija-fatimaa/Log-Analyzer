# ANSWERS

## 1. How to run

Requires **Python 3.8+** only — no third-party packages, no `pip install`.

From the repository root:

```bash
python3 loglens.py path/to/logfile.log
```

That prints the full report. To generate a test log first:

```bash
python3 scripts/generate_logs.py --lines 3000 --seed 42 > sample.log
python3 loglens.py sample.log
```

Additional views: `--slowest N`, `--errors`, `--ips`.

## 2. Stack choice

I chose **Python with the standard library only**, and a **CLI** rather than a
web app.

- **Why Python:** the task is text parsing — regex, string splitting,
  normalizing formats. Python does this concisely, and shipping with zero
  dependencies means it runs on any machine with Python 3 via a single command.
  Since "run it on a fresh machine" is explicitly graded, removing the install
  step is a direct win.
- **Why a CLI:** the assignment frames the user as "someone on call." On-call
  engineers work in a terminal, often over SSH, and want fast answers. A CLI
  fits that workflow with far less surface area to break.
- **What would have been worse:** a **web dashboard**. It would add a server, a
  frontend, and a build step — more things to fail and more to install — for a
  task whose hardest requirement is robust parsing, not visualization. A
  heavier choice like a pandas/Spark pipeline would also be worse here: it adds
  a big dependency and startup cost for input sizes (up to a few hundred
  thousand lines) that plain Python streams through in a few seconds.

## 3. One real edge case

**Lines where the status code is missing entirely**, e.g.:

```
2024-03-15T14:23:01Z 10.0.0.7 POST /api/orders 142ms
```

Here the response time (`142ms`) sits in the position a status code would
normally occupy. A naive parser reads `142ms` as the status, fails, and — worse
— never looks further, so the **response time is lost**, silently corrupting
every latency statistic.

This is handled in **`parser.py`, lines 284–288** (the
`elif parse_response_time(first) is not None:` branch). Before consuming a
token as the status, the parser checks whether it actually looks like a status
(a 3-digit number or `-`). If instead it looks like a response time, the parser
concludes the status was omitted, records a `missing_status` anomaly, and
leaves that token for the response-time scanner to pick up.

**Without this handling:** those lines would either be skipped (losing real
request data) or, worse, parsed with a garbage status and a `None` response
time — quietly skewing the averages. The "never silently drop data" property
would be violated.

## 4. AI usage

I built this with **Claude (Anthropic's AI assistant)**. To be specific:

- I gave Claude the assessment document and asked it to plan the project,
  choose a stack, and write the parser, analyzer, CLI, test-data generator, and
  documentation.
- Claude wrote the initial versions of `parser.py`, `analyze.py`,
  `loglens.py`, and `scripts/generate_logs.py`.

**Something I changed about the AI output and why:** the first version of the
parser consumed the token right after the path as the status code
unconditionally. When I tested it against generated data, I saw a
`unsparseable_status` anomaly count that didn't make sense, and traced it to
lines where the status was _missing_ — the response time was being read as a
status and then thrown away, losing the timing data. I changed the logic to
inspect that token first and only treat it as a status if it looks like one,
otherwise fall back to treating the status as absent (see Q3). This turned a
silent data-loss bug into correctly parsed lines with an honest
`missing_status` anomaly.

I took a little help from chat gpt as welll just asking for some alterations in a file. I ran it against my own log file and checked the slowest-endpoint numbers by hand.

## 5. Honest gap

The **timestamp parsing is not timezone-aware for non-UTC inputs.** Every
parsed timestamp is coerced to UTC, and formats without an explicit zone (the
slash and `15-Mar-2024` formats, and Unix epoch) are _assumed_ to be UTC. If a
real log mixed local-time and UTC entries, the ordering and any time-bucketed
analysis would be subtly wrong, with no warning to the user.

**With another day**, I would: (a) detect and preserve explicit timezone
offsets where present, (b) add a `--assume-tz` flag so the operator can declare
the zone of zone-less timestamps, and (c) surface a "mixed timezone" anomaly
when both zoned and zone-less timestamps appear in the same file, so the
ambiguity is visible rather than hidden. I'd also add a proper unit-test file —
right now correctness is verified by running the generator and inspecting
output, which is fine for a take-home but wouldn't catch regressions
automatically.

> **[My part]**, I tested it on data and validated all the results and fixed any bugs i saw.
