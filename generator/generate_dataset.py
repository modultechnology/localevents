"""
Event Slot-Filling Dataset Generator (v3 — simplified)
=======================================================

Generates news-style passages in the spirit of NYT / Guardian / FAZ /
Der Standard, covering local-to-international cultural, mobility, sports,
and politics events. Each example carries an entity layer + event
slot-filling layer; slot values are grounded against the entity surfaces.

Design choice: the prompt does NOT enumerate cities, scales, styles, or
"twists". The model picks the place, the people, the angle, the register,
the sentence count, all freely. The Python layer only controls two things
to avoid corpus-level skew:

  * language balance (EN vs DE)
  * domain balance (cultural / mobility / sports / politics / multi / negative)

A small random "entropy seed" (a few unrelated English words) is included
in each prompt purely to nudge the model out of its default attractors.

Usage
-----
    # See the cost estimate before spending anything:
    python generate_dataset.py --n 1000 --dry_run

    # Quick smoke test (~$0.30, ~1 minute) — verify everything works:
    python generate_dataset.py --n 20 --out smoke

    # Full 1k run (~$14, ~25 minutes) on Sonnet 4.6 with prompt caching:
    python generate_dataset.py --n 1000 --out events_dataset

Cost notes
----------
Costs scale roughly linearly with --n. Default model is Sonnet 4.6
($3 / $15 per M input/output tokens). Prompt caching is enabled and saves
~20%. To go cheaper, pass --model claude-haiku-4-5 (~3× cheaper, quality
trade-off to verify on a smoke run first). The actual cost is printed at
the end of every run from the API's reported token usage.

Requires:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=...
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import sys
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

try:
    from anthropic import AsyncAnthropic
except ImportError:
    print("Install: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)


SCHEMA_VERSION = "3.0"
DEFAULT_MODEL = "claude-sonnet-4-6"


# =============================================================================
# Two balance knobs: language and domain. Everything else is the model's call.
# =============================================================================

LANG_RATIO = {"en": 0.70, "de": 0.30}

# Domain weights — cultural/mobility/sports/politics roughly balanced,
# small share of multi (two events) and a few negatives.
DOMAIN_WEIGHTS: dict[str, float] = {
    "cultural": 0.21,
    "mobility": 0.21,
    "sports":   0.21,
    "politics": 0.21,
    "multi":    0.13,
    "negative": 0.03,
}


# =============================================================================
# Entity types & domain slot vocabularies
# =============================================================================

ENTITY_TYPES: dict[str, str] = {
    "PER":   "Named individuals.",
    "ORG":   "Organisations: parties, teams, operators, agencies, companies, schools.",
    "LOC":   "Geographic places: cities, countries, regions, neighbourhoods, streets.",
    "FAC":   "Built facilities: venues, stadiums, museums, theatres, stations, bridges, parks.",
    "DATE":  "Dates, times, durations, ranges, named periods.",
    "MONEY": "Currency amounts.",
    "NUM":   "Cardinal counts: attendance, distances, vote tallies, fleet sizes, edition numbers.",
    "EVENT": "Named events referenced in the passage.",
    "MISC":  "Scores, percentages, genres, sport types, languages, named programmes/plans.",
}

DOMAINS: dict[str, dict] = {
    "cultural": {
        "examples": "concerts, exhibitions, festivals, premieres, book launches, "
                    "film screenings, lectures, workshops, art fairs. Local, regional, "
                    "national, or international scale all fine — a parish-hall concert "
                    "or the Frankfurter Buchmesse are equally valid.",
        "slot_keys": [
            "event_name", "venue", "city", "country", "start_date", "end_date", "duration",
            "performers", "artists", "directors", "organizers", "curators",
            "actual_attendance", "ticket_price", "genre", "medium", "language", "edition",
        ],
    },
    "mobility": {
        "examples": "transit disruptions, line openings, strikes, fare changes, "
                    "bike-share launches, road closures, infrastructure projects. "
                    "Local to international (e.g., cross-border rail).",
        "slot_keys": [
            "event_name", "city", "country", "start_date", "end_date", "duration",
            "operator", "affected_lines", "affected_routes",
            "estimated_affected_passengers", "reason", "ongoing",
            "fare_change_amount", "fleet_size", "n_stations", "contract_value",
        ],
    },
    "sports": {
        "examples": "matches, tournaments, derbies, marathons, regattas, championships. "
                    "Amateur leagues, national divisions, international competitions all fine.",
        "slot_keys": [
            "event_name", "venue", "city", "country", "event_date",
            "home_team", "away_team", "winner", "loser",
            "final_score", "attendance", "competition_name",
            "sport_type", "key_players", "duration", "organizers",
        ],
    },
    "politics": {
        "examples": "elections, council votes, referendums, party conferences, "
                    "policy announcements, parliamentary debates, mayor inaugurations, "
                    "resignations, coalition agreements. Local council level up to "
                    "national or EU-level politics.",
        "slot_keys": [
            "event_name", "venue", "city", "country", "event_date",
            "office", "winning_party", "losing_party", "vote_share", "turnout",
            "key_politicians", "key_parties", "policy_topic",
            "majority", "n_votes_for", "n_votes_against", "n_abstentions",
            "organizers", "duration",
        ],
    },
}


# =============================================================================
# Entropy seed: short list of unrelated English words drawn fresh per spec.
# Pure noise — the prompt says "use as a creative nudge, do NOT quote in the
# passage". Purpose: break the model out of its attractor states without
# imposing any categorical structure.
# =============================================================================

_WORD_POOL = """
abide alabaster amber anchor archway barley bramble brindle brittle canyon
cellar churn cobalt coda coil cypress dappled drift dusk ember fathom feldspar
flint fluent forge frostwork furrow gable garnet gild glade granite gull
hawthorn hearth heron hollow ivy juniper keep lantern lattice lichen linden
loam loft marrow marsh moss myrtle nettle ochre opal orchard oxbow petal
pewter pine pivot quarry querulous quince ravine reed rivulet rookery rust
saffron sage shale shoal sienna silt skein slate sloop sluice sorrel spar
spire stoat sumac tallow tannin thicket thrush tinder tundra umber vellum
verge vetiver wadi warren wax willow wisp wreath yarrow yew zinc
""".split()


def _entropy_seed(rng: random.Random, k: int = 6) -> str:
    """Return k unrelated words + a 5-digit number, comma-joined."""
    words = rng.sample(_WORD_POOL, k)
    n = rng.randint(10000, 99999)
    return ", ".join(words) + f" / {n}"


# =============================================================================
# Spec dataclass — just language + target + entropy seed + id.
# =============================================================================

@dataclass
class ExampleSpec:
    spec_id: int
    language: str
    target: str           # cultural | mobility | sports | politics | multi | negative
    entropy: str
    multi_domains: list[str] | None = None


def make_specs(n: int, seed: int = 42) -> list[ExampleSpec]:
    rng = random.Random(seed)
    targets, weights = zip(*DOMAIN_WEIGHTS.items())
    specs: list[ExampleSpec] = []
    for i in range(n):
        lang = "en" if rng.random() < LANG_RATIO["en"] else "de"
        target = rng.choices(targets, weights=weights)[0]
        ent = _entropy_seed(rng)
        multi = None
        if target == "multi":
            pair_choices = [
                ("sports", "mobility"),
                ("cultural", "mobility"),
                ("cultural", "sports"),
                ("politics", "mobility"),
                ("politics", "cultural"),
            ]
            multi = list(rng.choice(pair_choices))
        specs.append(ExampleSpec(spec_id=i, language=lang, target=target,
                                 entropy=ent, multi_domains=multi))
    return specs


# =============================================================================
# Tool schema for forced structured output. The Anthropic API guarantees
# `block.input` matches this schema — no JSON parse errors possible.
# =============================================================================

EXAMPLE_TOOL = {
    "name": "produce_example",
    "description": "Submit one validated training example for the dataset.",
    "input_schema": {
        "type": "object",
        "required": ["text", "entities", "domain_labels", "events"],
        "properties": {
            "text": {"type": "string"},
            "entities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["type", "text"],
                    "properties": {
                        "type": {"type": "string",
                                 "enum": list(ENTITY_TYPES.keys())},
                        "text": {"type": "string"},
                    },
                },
            },
            "domain_labels": {
                "type": "array",
                "items": {"type": "string",
                          "enum": ["cultural", "mobility", "sports", "politics"]},
            },
            "events": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["event_type", "event_subtype", "trigger", "slots"],
                    "properties": {
                        "event_type": {"type": "string",
                                       "enum": ["cultural", "mobility", "sports", "politics"]},
                        "event_subtype": {"type": "string"},
                        "trigger": {"type": "string"},
                        "slots": {"type": "object", "additionalProperties": True},
                    },
                },
            },
        },
    },
}


# =============================================================================
# Prompt
# =============================================================================

PROMPT_SYSTEM = """You are generating ONE training example for a joint named-\
entity-recognition + event slot-filling dataset.

The dataset is news-style text in the spirit of The New York Times, The \
Guardian, FAZ, Der Standard, and similar outlets, covering LOCAL TO \
INTERNATIONAL events in four domains:

  cultural   — concerts, exhibitions, festivals, premieres, book launches,
               film screenings, lectures, workshops, art fairs.
  mobility   — transit disruptions, line openings, strikes, fare changes,
               road closures, infrastructure projects.
  sports     — matches, tournaments, derbies, marathons, regattas,
               championships, school sports days.
  politics   — elections, council votes, referendums, party conferences,
               policy announcements, parliamentary debates, resignations.

USE REAL ENTITIES where possible. Real cities, real venues (Royal Albert \
Hall, Stadtsaal Wien, Camp Nou), real parties (SPD, Conservatives, Labour, \
ÖVP, Grüne, Sinn Féin), real transit operators (MTA, TfL, BVG, ÖBB, RMV), \
real competitions (Bundesliga, Eurovision, Champions League, Frankfurter \
Buchmesse), real organisations. Cover both the Anglo-Saxon and the \
Germanic spheres, but other places (France, Italy, Scandinavia, etc.) are \
welcome where relevant. Scale can be parish-council-vote local or \
Eurovision-international — vary it.

For named PEOPLE, prefer plausible INVENTED names so we don't put fictional \
words in real public figures' mouths. Real public figures may be MENTIONED \
where natural (a real Chancellor, a real Bürgermeister), but quoted speech \
and detailed personal actions should be attributed to invented people. \
Invent names freely across all naming traditions realistic for the place — \
do not collapse onto a small handful of "diverse-sounding" favourites.

REGISTER & LENGTH — vary widely:
  - Length: 1 to 6 sentences. Pick fresh each time, don't default to 3.
  - Register: from terse wire-style brief to long, novelistic, sub-claused
    journalistic prose. Pick fresh each time, don't default to medium.
  - Outlet style: NYT, Guardian, FAZ, Der Standard, or a similar paper's
    voice. You decide which one fits this passage.

OUTPUT — call the produce_example tool with:

  text           — the passage itself.
  entities       — every named entity, typed as one of:
                     PER, ORG, LOC, FAC, DATE, MONEY, NUM, EVENT, MISC.
                   Each `text` must be a verbatim substring of the passage.
                   Spans must be non-overlapping — if "London" appears only
                   inside "London Symphony Orchestra", don't extract it
                   separately.
  domain_labels  — one or more of cultural / mobility / sports / politics.
                   Empty list [] for negatives.
  events         — one event per domain the passage actually narrates. Each
                   has event_type, event_subtype (open vocabulary — invent
                   the most specific fitting label), a short trigger phrase
                   (≤ 8 words, verbatim from text), and a slots dict.

GROUNDING RULE — fill slots AFTER you finalize entities, and ONLY from
the entity list you just produced. Every string slot value (and every
element of a list-of-strings slot) must literally appear as one of your
extracted entities' text. If a slot key would need a value not in your
entity list, OMIT that slot rather than inventing one.

Concrete example of the discipline:

  text = "Vienna's city council voted Tuesday to fund the Konzerthaus
          renovation."
  entities = [
    {LOC: "Vienna"}, {ORG: "city council"}, {DATE: "Tuesday"},
    {FAC: "Konzerthaus"}
  ]
  slots OK:    {"city": "Vienna", "event_date": "Tuesday",
                "venue": "Konzerthaus", "organizers": ["city council"]}
  slots WRONG: {"city": "Vienna", "country": "Austria", ...}  ← "Austria"
                is not in the entity list, so OMIT the country slot.

Numeric slot values (attendance, vote counts, money amounts) should be
the cleaned integer/decimal corresponding to a NUM or MONEY entity in
the text (e.g. NUM "9,800" → slot value 9800).

NEGATIVES — if the spec says target=negative, produce a plausible news
passage that mentions cultural/mobility/sports/politics topics but does
NOT narrate an event of those types (a debate about a future tram line,
an artist profile, an architectural piece on a stadium, a polling
retrospective). Set domain_labels=[] and events=[]. Still extract entities."""


def build_user_prompt(spec: ExampleSpec) -> str:
    lang_full = "English" if spec.language == "en" else "German"

    if spec.target == "negative":
        target_block = """TARGET: NEGATIVE — no event narrated, but the passage touches
on cultural/mobility/sports/politics topics. Set domain_labels=[] and events=[]."""
    elif spec.target == "multi":
        d1, d2 = spec.multi_domains
        target_block = f"""TARGET: MULTI-DOMAIN — narrate TWO related events spanning
{d1!r} and {d2!r}. Each gets its own entry in `events`. domain_labels should
contain both: {[d1, d2]}.

  {d1!r} — typical content: {DOMAINS[d1]['examples']}
  Slot keys available: {', '.join(DOMAINS[d1]['slot_keys'])}

  {d2!r} — typical content: {DOMAINS[d2]['examples']}
  Slot keys available: {', '.join(DOMAINS[d2]['slot_keys'])}"""
    else:
        d = spec.target
        info = DOMAINS[d]
        target_block = f"""TARGET DOMAIN: {d}

Typical content: {info['examples']}

Slot keys available — include the ones the text supports:
  {', '.join(info['slot_keys'])}

domain_labels = [{d!r}]. events has ONE entry."""

    return f"""Language: {lang_full}

{target_block}

Entropy seed for this turn (use as a creative nudge — do NOT include these
words in the passage):
  {spec.entropy}

Now call produce_example."""


# =============================================================================
# Post-processing: char offsets via first non-overlapping occurrence
# =============================================================================

def add_offsets(obj: dict) -> dict:
    text = obj["text"]
    occupied: list[tuple[int, int]] = []
    for ent in obj["entities"]:
        s = ent["text"]
        cursor = 0
        ent["offset"] = None
        while True:
            idx = text.find(s, cursor)
            if idx == -1:
                break
            end = idx + len(s)
            if not any(not (end <= a or idx >= b) for a, b in occupied):
                ent["offset"] = [idx, end]
                occupied.append((idx, end))
                break
            cursor = idx + 1
    for ev in obj.get("events", []):
        idx = text.find(ev["trigger"])
        ev["trigger_offset"] = [idx, idx + len(ev["trigger"])] if idx >= 0 else None
    return obj


# =============================================================================
# Validation
# =============================================================================

_QUOTE_NORM = str.maketrans({
    "\u201c": '"', "\u201d": '"', "\u201e": '"', "\u201f": '"',
    "\u2018": "'", "\u2019": "'", "\u2032": "'",
    "\u00ab": '"', "\u00bb": '"',
})


def validate_example(obj: dict, spec: ExampleSpec) -> tuple[dict | None, str]:
    if not isinstance(obj, dict): return None, "not_dict"
    for k in ("text", "entities", "domain_labels", "events"):
        if k not in obj: return None, f"missing:{k}"
    text = obj["text"]
    if not isinstance(text, str) or not text.strip(): return None, "bad_text"
    if not isinstance(obj["entities"], list): return None, "entities_not_list"
    if not isinstance(obj["events"], list): return None, "events_not_list"
    if not isinstance(obj["domain_labels"], list): return None, "domain_labels_not_list"

    norm_text = text.translate(_QUOTE_NORM)
    for ent in obj["entities"]:
        if not isinstance(ent, dict): return None, "entity_not_dict"
        if ent.get("type") not in ENTITY_TYPES:
            return None, f"bad_entity_type:{ent.get('type')!r}"
        if not isinstance(ent.get("text"), str):
            return None, "entity_text_not_str"
        s = ent["text"]
        if s in text:
            continue
        idx = norm_text.find(s.translate(_QUOTE_NORM))
        if idx >= 0:
            ent["text"] = text[idx:idx + len(s)]
            continue
        return None, f"entity_not_in_text:{s!r}"

    obj = add_offsets(obj)
    # Unplaceable entities (couldn't find non-overlapping position) — drop
    # them rather than rejecting the whole example. They were probably
    # sub-spans already covered by a longer entity.
    obj["entities"] = [e for e in obj["entities"] if e.get("offset") is not None]

    surfaces = {e["text"] for e in obj["entities"]}

    def _ground_slot(slot_value: str) -> str | None:
        """Find an entity surface that grounds this slot value.

        Match priority: exact, quote-normalized, article-stripped, case-
        insensitive substring (slot is substring of entity OR vice versa).
        Returns the entity surface to align the slot value to, or None if
        no acceptable match.
        """
        # 1. Exact match — fastest, most common when prompt grounds well.
        if slot_value in surfaces:
            return slot_value
        # 2. Quote normalization (handles curly vs ASCII quotes).
        norm_value = slot_value.translate(_QUOTE_NORM)
        for s in surfaces:
            if s.translate(_QUOTE_NORM) == norm_value:
                return s
        # 3. Article-stripping (English & German): "the Vienna State Opera"
        # vs entity "Vienna State Opera". Strip leading article from slot.
        lower_value = slot_value.lower().strip()
        for article in ("the ", "a ", "an ", "der ", "die ", "das ",
                        "den ", "dem ", "des "):
            if lower_value.startswith(article):
                stripped = slot_value[len(article):]
                if stripped in surfaces:
                    return stripped
                # And the reverse: entity is "the X", slot is "X".
                for s in surfaces:
                    if s.lower().startswith(article) and s[len(article):] == slot_value:
                        return s
        # 4. Case-insensitive exact.
        for s in surfaces:
            if s.lower() == slot_value.lower():
                return s
        return None

    for ev in obj["events"]:
        if not isinstance(ev, dict): return None, "event_not_dict"
        for k in ("event_type", "event_subtype", "trigger", "slots"):
            if k not in ev: return None, f"event_missing:{k}"
        if ev["event_type"] not in ("cultural", "mobility", "sports", "politics"):
            return None, f"bad_event_type:{ev['event_type']!r}"
        # Trigger grounding — try exact, then case-insensitive, then drop
        # leading article. Reject only if no recovery possible.
        if not isinstance(ev["trigger"], str):
            return None, "trigger_not_str"
        if ev["trigger"] not in text:
            t = ev["trigger"]
            recovered = None
            # case-insensitive
            tl = t.lower()
            text_l = text.lower()
            idx = text_l.find(tl)
            if idx >= 0:
                recovered = text[idx:idx + len(t)]
            else:
                # try stripping leading article
                for article in ("the ", "a ", "an ", "der ", "die ", "das "):
                    if tl.startswith(article):
                        stripped = t[len(article):]
                        if stripped in text:
                            recovered = stripped
                            break
            if recovered is None:
                return None, f"trigger_not_in_text:{ev.get('trigger')!r}"
            ev["trigger"] = recovered
        if len(ev["trigger"].split()) > 8:
            return None, f"trigger_too_long:{ev['trigger']!r}"
        # Slot grounding — align where possible, DROP ungrounded slots.
        # The audit property is preserved (every retained slot value is
        # grounded to an entity surface) while saving costly retries.
        for k, v in list(ev["slots"].items()):
            if isinstance(v, list):
                aligned = []
                for vv in v:
                    if isinstance(vv, bool) or vv is None:
                        aligned.append(vv)
                    elif isinstance(vv, str):
                        match = _ground_slot(vv)
                        if match is not None:
                            aligned.append(match)
                        # else: silently drop this list element
                    elif isinstance(vv, (int, float)):
                        aligned.append(vv)
                    # else: silently drop unexpected type
                if aligned:
                    ev["slots"][k] = aligned
                else:
                    del ev["slots"][k]  # all values dropped → drop whole slot
            else:
                if isinstance(v, bool) or v is None:
                    continue
                if isinstance(v, str):
                    match = _ground_slot(v)
                    if match is not None:
                        ev["slots"][k] = match
                    else:
                        del ev["slots"][k]  # drop ungrounded slot
                elif isinstance(v, (int, float)):
                    continue
                else:
                    del ev["slots"][k]  # drop unexpected type

    if {ev["event_type"] for ev in obj["events"]} != set(obj["domain_labels"]):
        return None, "domain_mismatch"
    if spec.target == "negative" and obj["events"]:
        return None, "negative_with_events"
    return obj, "ok"


# =============================================================================
# Usage tracking
# =============================================================================

@dataclass
class UsageStats:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0

    def add(self, usage) -> None:
        def g(name):
            if usage is None: return 0
            if hasattr(usage, name):
                v = getattr(usage, name)
                return v if v is not None else 0
            if isinstance(usage, dict):
                return usage.get(name, 0) or 0
            return 0
        self.input_tokens += g("input_tokens")
        self.output_tokens += g("output_tokens")
        self.cache_creation_tokens += g("cache_creation_input_tokens")
        self.cache_read_tokens += g("cache_read_input_tokens")


# =============================================================================
# Async generation — forced tool use, targeted feedback retries, caching
# =============================================================================

async def generate_one(
    client: AsyncAnthropic,
    spec: ExampleSpec,
    model: str,
    sem: asyncio.Semaphore,
    usage: UsageStats,
    max_retries: int = 4,
) -> tuple[dict | None, list[str]]:
    reasons: list[str] = []
    last_obj: dict | None = None
    last_reason: str | None = None
    last_tool_id: str | None = None
    user_msg = build_user_prompt(spec)

    async with sem:
        for _ in range(max_retries):
            messages: list[dict] = [{"role": "user", "content": user_msg}]
            if last_obj is not None and last_reason is not None and last_tool_id is not None:
                messages.append({
                    "role": "assistant",
                    "content": [{"type": "tool_use", "id": last_tool_id,
                                 "name": "produce_example", "input": last_obj}],
                })
                messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": last_tool_id,
                        "content": (f"Validation failed: {last_reason}\n\n"
                                    f"Please call produce_example again with the corrected "
                                    f"fields. KEEP the `text` field exactly the same — only "
                                    f"fix the specific issue above. Every entity must be a "
                                    f"verbatim substring of `text`, every string slot value "
                                    f"must match an extracted entity surface."),
                        "is_error": True,
                    }],
                })
            try:
                resp = await client.messages.create(
                    model=model,
                    max_tokens=2500,
                    system=[{
                        "type": "text",
                        "text": PROMPT_SYSTEM,
                        "cache_control": {"type": "ephemeral"},
                    }],
                    tools=[{**EXAMPLE_TOOL, "cache_control": {"type": "ephemeral"}}],
                    tool_choice={"type": "tool", "name": "produce_example"},
                    messages=messages,
                )
                usage.add(getattr(resp, "usage", None))
                tool_block = next((b for b in resp.content
                                   if getattr(b, "type", None) == "tool_use"), None)
                if tool_block is None:
                    reasons.append("no_tool_use_block")
                    last_obj, last_reason, last_tool_id = None, None, None
                    continue
                obj = tool_block.input
                validated, reason = validate_example(obj, spec)
                if validated is not None:
                    return validated, reasons + ["ok"]
                reasons.append(reason)
                last_obj, last_reason, last_tool_id = obj, reason, tool_block.id
            except Exception as e:
                reasons.append(f"api_error:{type(e).__name__}:{e!s}")
                await asyncio.sleep(1.5)
        return None, reasons


# =============================================================================
# Main loop with streaming writes
# =============================================================================

async def main_async(args) -> None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    specs = make_specs(args.n, seed=args.seed)
    print(f"Built {len(specs)} specs. Generating with {args.model} "
          f"(concurrency={args.concurrency})...")

    # Cost estimate — calibrated against measured run telemetry plus the
    # validator policy of dropping ungrounded slots/entities rather than
    # retrying. Most rejection causes (slot_ungrounded, unplaceable,
    # trigger_not_in_text via case-insensitive recovery) are now handled
    # inline. Remaining retries are only for hard failures (entity invented
    # outside text, domain mismatch). Expected ~1.15 attempts/spec.
    sys_tok = len(PROMPT_SYSTEM) // 4
    user_tok_avg = 320     # observed ~323
    out_tok_avg = 550      # observed ~515
    if "sonnet" in args.model.lower():
        in_price, out_price = 3.0, 15.0
    elif "haiku" in args.model.lower():
        in_price, out_price = 1.0, 5.0
    elif "opus" in args.model.lower():
        in_price, out_price = 15.0, 75.0
    else:
        in_price, out_price = 3.0, 15.0
    avg_attempts_per_spec = 1.15
    n_calls = int(len(specs) * avg_attempts_per_spec)
    write_cost = sys_tok * in_price * 1.25 / 1_000_000
    read_cost = sys_tok * in_price * 0.10 / 1_000_000 * (n_calls - 1)
    user_cost = user_tok_avg * in_price / 1_000_000 * n_calls
    out_cost = out_tok_avg * out_price / 1_000_000 * n_calls
    est_total = write_cost + read_cost + user_cost + out_cost
    est_no_cache = (sys_tok + user_tok_avg) * in_price / 1_000_000 * n_calls + out_cost
    print(f"Estimated cost: ~${est_total:.2f} with prompt caching "
          f"(would be ~${est_no_cache:.2f} without). "
          f"Assumes ~{avg_attempts_per_spec} API calls per spec.")
    if args.dry_run:
        print("Dry run — exiting before any API calls.")
        return

    client = AsyncAnthropic(api_key=api_key)
    sem = asyncio.Semaphore(args.concurrency)
    usage = UsageStats()

    out_stem = Path(args.out)
    plain_path = out_stem.with_suffix(".jsonl")
    annot_path = out_stem.parent / f"{out_stem.name}_annotated.jsonl"
    fail_path = out_stem.parent / f"{out_stem.name}_failures.jsonl"
    for p in (plain_path, annot_path, fail_path):
        p.write_text("", encoding="utf-8")

    t0 = time.time()
    total = len(specs)
    progress = {"done": 0, "ok": 0}
    every = max(1, total // 40)
    write_lock = asyncio.Lock()

    def _eta(s: float) -> str:
        return f"{s:.0f}s" if s < 90 else f"~{s/60:.1f}m"

    async def _write_result(spec: ExampleSpec, rec: dict | None,
                            reasons: list[str]) -> None:
        async with write_lock:
            if rec is None:
                with fail_path.open("a", encoding="utf-8") as ff:
                    ff.write(json.dumps({
                        "id": spec.spec_id, "language": spec.language,
                        "target": spec.target, "multi_domains": spec.multi_domains,
                        "entropy": spec.entropy, "attempt_reasons": reasons,
                    }, ensure_ascii=False) + "\n")
                return
            plain = {"id": spec.spec_id, "language": spec.language, "text": rec["text"]}
            annotated = {
                "id": spec.spec_id, "schema_version": SCHEMA_VERSION,
                "language": spec.language, "target": spec.target,
                "text": rec["text"], "entities": rec["entities"],
                "domain_labels": rec["domain_labels"], "events": rec["events"],
            }
            with plain_path.open("a", encoding="utf-8") as fp:
                fp.write(json.dumps(plain, ensure_ascii=False) + "\n")
            with annot_path.open("a", encoding="utf-8") as fa:
                fa.write(json.dumps(annotated, ensure_ascii=False) + "\n")

    async def _track(spec):
        result = await generate_one(client, spec, args.model, sem, usage,
                                    max_retries=args.max_retries)
        rec, reasons = result
        await _write_result(spec, rec, reasons)
        progress["done"] += 1
        if rec is not None:
            progress["ok"] += 1
        d, ok = progress["done"], progress["ok"]
        if d % every == 0 or d == total:
            elapsed = time.time() - t0
            eta = elapsed * (total - d) / d if d else 0
            print(f"  [{d}/{total}] {d/total*100:5.1f}% — "
                  f"{elapsed:.0f}s elapsed, {_eta(eta)} left — "
                  f"{ok} ok, {d-ok} dropped", flush=True)
        return result

    results = await asyncio.gather(*(_track(sp) for sp in specs))
    n_ok = sum(1 for r, _ in results if r is not None)
    n_fail = sum(1 for r, _ in results if r is None)

    print(f"\n  wrote {plain_path} ({n_ok} records)")
    print(f"  wrote {annot_path} ({n_ok} records)")
    if n_fail:
        print(f"  wrote {fail_path} ({n_fail} dropped)")
    print(f"\nFinal: {n_ok}/{len(results)} valid examples generated.")

    if n_fail:
        rows = [(s.language, r[-1].split(":")[0] if r else "no_attempts")
                for (rec, r), s in zip(results, specs) if rec is None]
        print("Drops by language:")
        for lang, count in Counter(r[0] for r in rows).most_common():
            n_total = sum(1 for s in specs if s.language == lang)
            print(f"  {lang}: {count}/{n_total} dropped "
                  f"({(n_total-count)/n_total*100:.0f}% pass)")
        print("Drop reasons:")
        for reason, count in Counter(r[1] for r in rows).most_common():
            print(f"  {count:4d}  {reason}")

    # Diversity report
    surfaces_by_type: dict[str, Counter] = {}
    subtype_counter: Counter = Counter()
    target_counter: Counter = Counter()
    # Retry-reason histogram across ALL specs (successful + failed). Each spec
    # may have had multiple validation rejections before finally succeeding;
    # this surfaces what the validator is rejecting most often so we can fix it.
    retry_reasons: Counter = Counter()
    total_attempts = 0
    for (rec, reasons), spec in zip(results, specs):
        # `reasons` ends with "ok" on success, or with the final-attempt
        # rejection reason on failure. Everything BEFORE the last entry is a
        # retry-rejection (the rejection that triggered a retry).
        total_attempts += len(reasons)
        rejection_reasons = reasons[:-1] if reasons and reasons[-1] == "ok" else reasons
        for r in rejection_reasons:
            retry_reasons[r.split(":")[0]] += 1
        if rec is None:
            continue
        target_counter[spec.target] += 1
        for ent in rec["entities"]:
            surfaces_by_type.setdefault(ent["type"], Counter())[ent["text"]] += 1
        for ev in rec["events"]:
            subtype_counter[ev["event_subtype"]] += 1

    print(f"\nDomain distribution: "
          f"{', '.join(f'{t}×{n}' for t, n in target_counter.most_common())}")
    print("\nDiversity report — top recurring entity surface forms:")
    for t in ("LOC", "FAC", "ORG", "PER", "EVENT"):
        c = surfaces_by_type.get(t)
        if not c: continue
        unique, total_e = len(c), sum(c.values())
        top = c.most_common(5)
        print(f"  {t}: {unique}/{total_e} unique — "
              f"top5: {', '.join(f'{s}×{n}' for s, n in top)}")
    if subtype_counter:
        print(f"\n  event_subtypes: {len(subtype_counter)} unique — "
              f"top5: {', '.join(f'{s}×{n}' for s, n in subtype_counter.most_common(5))}")

    # Retry-cost report: how many attempts per spec, and what the validator
    # rejected. If avg > 1.5, retries are dominating cost — fix the prompt
    # or the validator to reduce them.
    avg_attempts = total_attempts / len(results) if results else 0
    print(f"\nRetry stats: {total_attempts} total API calls for {len(results)} specs "
          f"(avg {avg_attempts:.2f} attempts/spec).")
    if retry_reasons:
        print("Validator rejection reasons (across all specs incl. retries):")
        for reason, count in retry_reasons.most_common(10):
            print(f"  {count:4d}  {reason}")

    # Cost report
    print(f"\nToken usage:")
    print(f"  input (uncached):    {usage.input_tokens:>10,}")
    print(f"  cache writes:        {usage.cache_creation_tokens:>10,}")
    print(f"  cache reads:         {usage.cache_read_tokens:>10,}")
    print(f"  output:              {usage.output_tokens:>10,}")
    actual = (usage.input_tokens * in_price / 1_000_000
              + usage.cache_creation_tokens * in_price * 1.25 / 1_000_000
              + usage.cache_read_tokens * in_price * 0.10 / 1_000_000
              + usage.output_tokens * out_price / 1_000_000)
    nocache = ((usage.input_tokens + usage.cache_creation_tokens + usage.cache_read_tokens)
               * in_price / 1_000_000 + usage.output_tokens * out_price / 1_000_000)
    print(f"\nActual cost: ${actual:.2f}", end="")
    if usage.cache_read_tokens > 0:
        print(f" (saved ~${nocache-actual:.2f} = {(nocache-actual)/nocache*100:.0f}% via caching)")
    else:
        print()

    # Sort output files by id
    def _sort(p):
        if not p.exists() or p.stat().st_size == 0: return
        recs = [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]
        recs.sort(key=lambda r: r.get("id", 0))
        with p.open("w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    for p in (plain_path, annot_path, fail_path):
        _sort(p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--out", type=str, default="events_dataset")
    ap.add_argument("--model", type=str, default=DEFAULT_MODEL)
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--max_retries", type=int, default=3,
                    help="Max API calls per spec (1 initial + N-1 retries). "
                         "Lower = cheaper, higher = better pass rate.")
    ap.add_argument("--dry_run", action="store_true",
                    help="Print cost estimate and exit before any API calls.")
    args = ap.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
