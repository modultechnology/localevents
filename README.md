# LocalEvents

A benchmark for **multi-event extraction from local news**, with the ontology
that backs its schema and the notebooks used to evaluate open-weight models
against it.

Local reporting is where events cluster: a road closure, a football match and a
council vote often appear in the same short passage, each carrying its own
participants, dates and numbers. LocalEvents targets that setting — bilingual,
multi-domain, and annotated so that **every extracted value is a verbatim span
of the source text**.

Modul University Vienna · [Modul Technology GmbH](https://www.modultech.eu/) · CC BY 4.0

## Paper

> **The LocalEvents Benchmark: Event Extraction and Slot Filling with Small LLMs**
> Uladzislau Smirnou, Adrian M.P. Brașoveanu, Lyndon J. B. Nixon
>
> *ELMKE 2026* — 4th Workshop on Evaluation of Language Models in Knowledge
> Engineering, co-located with the 25th International Semantic Web Conference
> (ISWC 2026), Bari, Italy, 25–26 October 2026. CEUR Workshop Proceedings.

The paper introduces the benchmark, the schema-guided generation pipeline, and
the layered evaluation protocol. Three findings drive the design of everything
in this repository:

- **Detection and slot filling are close to anti-correlated.** The strongest
  event detector (Gemma-2 9B, 0.83 event F₁) is not the strongest slot filler
  (Llama 3.1 8B, 0.78 slot F₁ on matched events). A single fused score hides
  this, which is why the protocol reports the two halves separately.
- **Every model loses ground on German** — 0.21 F₁ on average, almost entirely
  recall.
- **The slots that fail are the inferred, categorical ones** (`country`,
  `genre`, `sport_type`). The groundedness invariant isolates them by
  construction: a model writing `country: Austria` when the passage says only
  *Vienna* has left the text, and that is mechanically detectable.

---

## Contents

| Folder | What's in it |
|---|---|
| [`dataset/`](dataset/) | 1,983 annotated passages · 2,180 events · English + German |
| [`ontology/`](ontology/) | NEXO v1.2 — the event ontology, plus generated HTML documentation |
| [`models/`](models/) | Four evaluation notebooks, one per open-weight model |

---

## Dataset

`dataset/events_2k_dataset_annotated.jsonl` — one JSON object per line,
`schema_version` 3.0.

**1,983 passages** (1,400 en / 583 de) carrying **2,180 events** across four
domains:

| Domain | Events | Distinct subtypes |
|---|---:|---:|
| sports | 556 | 100 |
| mobility | 556 | 152 |
| cultural | 545 | 100 |
| politics | 523 | 47 |

Passages are drawn against six generation targets: the four domains
(1,656 single-domain records), `multi` (**262 records carrying two domains at
once**), and `negative` (65 records with entities but deliberately no events).
The multi-domain and negative slices are the point — they test whether a model
over-extracts when domains collide, and whether it can decline to extract at
all.

**19,238 entity mentions** over nine types: ORG (4,062), NUM (3,599), DATE
(2,728), PER (2,411), FAC (1,927), LOC (1,748), MISC (1,393), EVENT (944),
MONEY (426). **50 distinct slot keys** across the four domains.

### Record shape

```json
{
  "id": 1,
  "schema_version": "3.0",
  "language": "en",
  "target": "cultural",
  "text": "The Städel Museum in Frankfurt am Main opens its long-awaited …",
  "entities": [
    {"type": "FAC", "text": "Städel Museum", "offset": [4, 17]}
  ],
  "domain_labels": ["cultural"],
  "events": [
    {
      "event_type": "cultural",
      "event_subtype": "exhibition_opening",
      "trigger": "opens its long-awaited retrospective",
      "trigger_offset": [39, 75],
      "slots": {
        "venue": "Städel Museum",
        "city": "Frankfurt am Main",
        "start_date": "this Saturday",
        "curators": ["Dr. Lena Vorsbach"],
        "ticket_price": 14
      }
    }
  ]
}
```

Note `"start_date": "this Saturday"` — dates are **surface forms as written**,
not normalised. That is deliberate, and it is what the groundedness invariant
below guarantees.

### Groundedness invariant

Every string value is a verbatim substring of `text`, and every offset resolves
exactly. Verified over the full corpus:

| Property | Result |
|---|---|
| Entity offsets resolve to the annotated string | **19,238 / 19,238** |
| Trigger offsets resolve to the annotated string | **2,180 / 2,180** |
| String slot values are verbatim substrings of `text` | **14,701 / 14,701** (100.00%) |
| Overlapping entity spans | 0 |
| Nulls, empty strings, untrimmed whitespace in slots | 0 |
| Duplicate texts, duplicate IDs, duplicate events | 0 |

This is what makes the corpus checkable: a claimed extraction can be verified
against the source text mechanically, with no judgement call about paraphrase.

### Other files

`events_2k_dataset.jsonl` — the same 1,983 passages with `id`, `language` and
`text` only. Identical IDs and identical texts; use it as the model input so no
annotation leaks into the prompt.

`events_2k_dataset_failures.jsonl` — 17 passages the generator abandoned after
three attempts each, with the validator's reason for every attempt. All 51
failures are validator rejections rather than model refusals:

| Reason | Count |
|---|---:|
| `trigger_not_in_text` | 20 |
| `trigger_too_long` | 13 |
| `events_not_list` | 11 |
| `entities_not_list` | 7 |

The top two are the groundedness constraint doing its job. German accounts for
10 of the 17 abandoned passages despite being under a third of the corpus.

---

## Ontology

[`ontology/`](ontology/) holds **NEXO v1.2** — namespace
`http://modultech.eu/nexo/`, 123 classes, 38 object properties, 47 datatype
properties, OWL 2.

NEXO models events **as reported in narrative text** rather than as they
occurred, across eighteen domain families sharing one spine for temporality,
spatiality, participation, causality, composition and perspective. Version 1.2
adds the Mobility and Legislative branches this corpus needs — neither has a
counterpart in schema.org, SEM or LODE, which model transport as journeys
rather than as events in the operation of a network, and have no
deliberative-vote vocabulary at all.

Ranges are permissive by design, for the same reason the dataset is:
`nexo:startDate` accepts `"this Saturday"` as readily as an `xsd:dateTime`,
with `nexo:normalizedStartDate` for the resolved value.

Open `ontology/nexo-documentation.html` in a browser for the full reference, or
see [`ontology/README.md`](ontology/README.md) for the design rationale and the
v1.2 changelog.

The dataset's flat slot keys are a projection of a NEXO subset; the JSONL is
self-contained and needs no RDF tooling to use.

---

## Models

[`models/`](models/) holds one notebook per model, all zero-shot:

| Notebook | Model |
|---|---|
| `Gemma2_9B_events_2k_clean.ipynb` | `google/gemma-2-9b-it` |
| `Llama31_8B_events_2k_clean.ipynb` | `meta-llama/Meta-Llama-3.1-8B-Instruct` |
| `Mistral_7B_events_2k_clean.ipynb` | `mistralai/Mistral-7B-Instruct-v0.3` |
| `Qwen25_7B_events_2k_clean.ipynb` | `Qwen/Qwen2.5-7B-Instruct` |

**The prompt is held constant across all four.** Only three of twenty-four
cells differ between notebooks: the title, the model identifier, and the chat
template — Gemma exposes no system role, so the system message is prepended to
the user turn instead. The `RULES` and `FEW_SHOT` blocks are byte-identical, so
parity can be confirmed by hashing rather than taken on trust.

Decoding is pinned: `TEMPERATURE = 0.0`, `TOP_P = 1.0`,
`REPETITION_PENALTY = 1.05`, `MAX_NEW_TOKENS = 1200`, `BATCH_SIZE = 64`, 4-bit
quantization, seeds `[42, 1, 2]` applied across `random`, `numpy` and `torch`.

### Running them

Gated models need a Hugging Face token, read from the environment — never
hardcode it:

```bash
export HF_TOKEN="hf_..."        # Linux / macOS
$env:HF_TOKEN = "hf_..."        # PowerShell
```

The notebooks raise immediately if it isn't set. They ship with outputs
stripped, so run order is top to bottom.

> Library versions are not pinned. `transformers`, `torch` and `bitsandbytes`
> all move quickly, and quantization behaviour in particular has changed
> between releases — expect to adjust versions to reproduce exactly.

---

## Citation

If you use LocalEvents, please cite the paper:

```bibtex
@inproceedings{localevents2026,
  author    = {Smirnou, Uladzislau and
               Bra{\c s}oveanu, Adrian M.P. and
               Nixon, Lyndon J. B.},
  title     = {The {LocalEvents} Benchmark: Event Extraction and Slot
               Filling with Small {LLMs}},
  booktitle = {Proceedings of the 4th Workshop on Evaluation of Language
               Models in Knowledge Engineering (ELMKE 2026), co-located with
               the 25th International Semantic Web Conference (ISWC 2026)},
  series    = {CEUR Workshop Proceedings},
  publisher = {CEUR-WS.org},
  address   = {Bari, Italy},
  year      = {2026}
}
```

<!-- TODO: add the CEUR-WS volume/paper URL once the proceedings are online. -->

The ontology can be cited on its own — see [`ontology/README.md`](ontology/README.md).

## License

CC BY 4.0 for the dataset and the ontology. Share and adapt with attribution.
