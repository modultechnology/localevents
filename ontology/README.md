# NEXO — Narrative Event eXtraction Ontology

**Version 1.2** · OWL 2 · CC BY 4.0 · `http://modultech.eu/nexo/`

Published by MODUL Technology GmbH

NEXO models events as they are **reported in narrative text**, rather than as
they occurred. It covers eighteen domain families under a single event model,
with a shared spine for temporality, spatiality, participation, causality,
composition and perspective — so domain branches specialise one model instead of
each inventing their own.

The commitment that shapes the rest: NEXO is built for **extraction output**,
not curated records. Extracted values are verbatim surface forms, often
underspecified and sometimes contradictory across sources, so ranges are
permissive by intent — `nexo:startDate` accepts `"this Saturday"` as readily as
an `xsd:dateTime`.

## Files

| File | Contents |
|---|---|
| `nexo.ttl` | The ontology. OWL 2, Turtle. Imports nothing. |
| `nexo-documentation.html` | Generated reference documentation — open in a browser |
| `README.md` | This file |

## Structure

```
Event
├── SimpleEvent        clear boundaries, single location, direct participants
├── ComplexEvent       fuzzy boundaries, distributed, composed of sub-events
├── EnvironmentalEvent
├── FinancialEvent
├── MobilityEvent      transport network operations       [new in 1.2]
└── LegislativeEvent   assembly votes and proceedings     [new in 1.2]
```

123 classes · 38 object properties · 47 datatype properties.

Cross-cutting: `Causality` (natural / anthropogenic / mixed), `Perspective`
(competing accounts of one event), `Phase`, `Trigger`, `Impact`, `Role`.

## Example

```turtle
@prefix nexo: <http://modultech.eu/nexo/> .

:tramClosure a nexo:LineClosure ;
    nexo:eventName        "Tram 3 weekend closure"@en ;
    nexo:hasOperator      :cityTransit ;
    nexo:affectedLine     "3" , "3B" ;
    nexo:disruptionReason "track renewal" ;
    nexo:startDate        "this Saturday" ;    # surface form, as extracted
    nexo:isOngoing        false .

:cityTransit a nexo:Agent ; rdfs:label "City Transit" .
```

Use `nexo:normalizedStartDate` once a date has been resolved to `xsd:dateTime`.

## Changes in 1.2

**New branches.** `MobilityEvent` (14 classes) covers service disruptions,
closures, transit strikes, infrastructure projects and fare changes.
`LegislativeEvent` (6 classes) covers votes taken by assemblies — distinct from
elections, in which an electorate rather than an assembly votes.

**Refined branches.** Cultural gained `Exhibition`, `Concert`,
`StagePerformance`, `FestivalEdition`, `BookEvent`, `ArtistResidency`,
`ProgrammeAnnouncement`. Sports gained `TeamSportsMatch`,
`IndividualSportsMatch` and `SportsRace` — the first two resolving a defect in
which the extraction templates referenced classes the ontology never declared.
Competition round is a property (`competitionStage`), not a subclass axis, since
stage varies independently of sport.

**Repairs.** `Trigger`, `Role`, `EventType`, `Perspective` and `Magnitude` were
declared in 1.1 but no property had them in range, so nothing could ever be
attached to one; `hasTrigger`, `hasRole`, `hasEventType`, `hasPerspective` and
`hasMagnitude` fix that. `SubEvent` is deprecated — `hasSubEvent` already ranges
over `Event`, so it was never usable.

**Ranges widened for extracted text.** `startDate` / `endDate` ranged over
`xsd:dateTime`, which is unusable for extraction under a groundedness
constraint; both now accept `xsd:string` too, with `normalizedStartDate` /
`normalizedEndDate` for resolved values. `description` and `eventName` were
fixed to `xsd:string`, which forbids a language tag — untenable for an ontology
about text — and now range over `rdfs:Literal`.

**Domain fix.** `startDate` / `endDate` were restricted to `TemporalExtent`,
contradicting the ontology's own examples. Now `Event ⊔ TemporalExtent`.

> `rdfs:domain` is **conjunctive** — two domain axioms on one property
> intersect, they do not union. Adding a wider domain beside a narrow one
> widens nothing.

Every change is a widening: nothing valid under 1.1 is invalid under 1.2.

## Regenerating the documentation

```bash
pip install pylode
python3 -m pylode -p ontpub -o nexo-documentation.html nexo.ttl
```

pyLODE 3.6 crashes on `rdfs:Datatype` blank nodes that are unions rather than
restrictions (it routes them to the restriction renderer, which returns `None`).
`nexo.ttl` uses such unions for the mixed-type ranges above. The one-line fix is
in `pylode/utils.py`, in `_bn_html` — send datatype nodes carrying
`owl:unionOf` to `_setclass_html` instead.

## Citation

```bibtex
@software{nexo,
  author       = {{MODUL Technology GmbH}},
  title        = {{NEXO}: Narrative Event eXtraction Ontology},
  version      = {1.2},
  year         = {2026},
  license      = {CC-BY-4.0}
}
```
