# Event Slot-Filling Dataset Generator (v3)

Generates EN/DE news-style passages annotated for **NER + event slot-filling**
across four domains: cultural, mobility, sports, politics.

Each example carries:
- `entities` — typed spans with offsets (PER, ORG, LOC, FAC, DATE, MONEY, NUM, EVENT, MISC)
- `domain_labels` — `cultural` / `mobility` / `sports` / `politics`
- `events` — one or more, each with `event_subtype`, `trigger`, and `slots`

Slot values are grounded: every string slot value matches an extracted entity
surface form, so NER F1 and slot F1 are independently scorable.

## Design

The prompt does NOT enumerate cities, scales, styles, or twists. The model
picks the place, register, sentence count (1-6), people, venue, angle.
Real entities are used (cities, parties, transit operators, competitions —
SPD, Conservatives, BVG, TfL, Bundesliga, Eurovision, Frankfurter Buchmesse,
etc.). For named people, invented names are preferred so we don't put
fictional words in real public figures' mouths.

Python controls only two balance knobs:
- language (EN/DE, ~70/30)
- target domain (cultural / mobility / sports / politics / multi / negative)

A per-spec random entropy seed (a few unrelated words) is included purely
to nudge the model away from default attractors.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
```

## How to run — three steps

**1. Dry run — see the cost estimate before spending anything.**

```bash
python generate_dataset.py --n 1000 --dry_run
```

Prints something like `Estimated cost: ~$13.85 with prompt caching (would
be ~$17.00 without).` Exits before any API calls. Use this any time you
change the prompt, the model, or `--n` so you don't get surprised.

**2. Smoke test — generate a small batch first (~$0.30, ~1 minute).**

```bash
python generate_dataset.py --n 20 --out smoke
```

Produces `smoke.jsonl`, `smoke_annotated.jsonl`, and `smoke_failures.jsonl`.
Inspect a few examples by eye. Check the final diversity report and pass
rate (should be ≥95% on Sonnet). If it looks wrong, fix before scaling up.

**3. Full run (~$14, ~25 minutes for n=1000).**

```bash
python generate_dataset.py --n 1000 --out events_dataset
```

Streams writes to disk as records complete, so a crash doesn't lose data.
Final report prints: domain distribution, drop reasons (if any), diversity
report (top recurring entity surfaces per type), and actual token cost from
the API's reported usage.

## Cost notes

| n     | Model        | Estimated cost |
| ----- | ------------ | -------------- |
| 20    | Sonnet 4.6   | ~$0.22         |
| 100   | Sonnet 4.6   | ~$1.10         |
| 1,000 | Sonnet 4.6   | ~$11           |
| 5,000 | Sonnet 4.6   | ~$55           |

Costs scale roughly linearly with `--n` and depend on the average number
of API calls per spec (the validator may retry the model on hard failures).
The validator drops ungrounded slot values rather than retrying, so most
specs succeed on the first try. Expect ~1.15 calls/spec on Sonnet 4.6.

Prompt caching is on by default. The first call writes the system prompt
to a 5-minute ephemeral cache; subsequent calls within that window pay 10%
of full input price for the cached portion.

The actual cost is printed at the end of every run from the API's
reported token usage, alongside a `Retry stats: N total API calls for M
specs (avg X attempts/spec)` line so you can verify the estimate.

To go cheaper, switch to Haiku:

```bash
python generate_dataset.py --n 1000 --model claude-haiku-4-5 --out events_dataset
```

That's roughly 3× cheaper (~$5 for 1k), but quality and pass rate on this
task should be smoke-tested first — Sonnet is the safer default.

To trade quality for cost, lower `--max_retries` (default 3):

```bash
python generate_dataset.py --n 1000 --max_retries 2 --out events_dataset
```

## Outputs

| File                             | Contents                                                |
| -------------------------------- | ------------------------------------------------------- |
| `<out>.jsonl`                    | Plain: `{id, language, text}` per record (model input)  |
| `<out>_annotated.jsonl`          | Gold: entities, domain_labels, events, slots            |
| `<out>_failures.jsonl`           | Dropped specs with the validator's per-attempt reasons  |

## Flags

| Flag             | Default              | What                                                |
| ---------------- | -------------------- | --------------------------------------------------- |
| `--n`            | 1000                 | Number of examples to attempt                       |
| `--out`          | `events_dataset`     | Output stem (writes `<stem>.jsonl` etc.)            |
| `--model`        | `claude-sonnet-4-6`  | Model name                                          |
| `--concurrency`  | 8                    | Parallel API calls                                  |
| `--seed`         | 42                   | RNG seed for spec sampling (reproducible)           |
| `--max_retries`  | 3                    | Max attempts per spec — lower = cheaper             |
| `--dry_run`      | off                  | Print cost estimate and exit before any API calls   |

## Files

| File                     | What                                                  |
| ------------------------ | ----------------------------------------------------- |
| `generate_dataset.py`    | Async generator, forced tool use, streaming writes    |
| `build_samples.py`       | 20 hand-built reference samples (gold)                |
| `sample_annotated.jsonl` | The 20 samples, fully annotated                       |
| `sample_plain.jsonl`     | The 20 samples, plain (id/language/text only)         |
| `requirements.txt`       | `anthropic>=0.40.0`                                   |
