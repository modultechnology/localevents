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
| `nexo-shapes.ttl` | *Optional.* SHACL constraints for the four domain branches |
| `gen_props_table.py` | Appends the per-class property reference to the generated docs |
| `gen_shapes.py` | Regenerates the SHACL shapes from the ontology |
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
python3 gen_props_table.py nexo.ttl nexo-documentation.html nexo-documentation.html
```

Both steps are needed. pyLODE lists only the axioms asserted *directly* on each
class, which makes leaf classes look as though they have no properties —
`nexo:Exhibition` declares none of its own but inherits 58. The second step
appends a **Properties per Class** section resolving each class to its full
inherited set. It is derived entirely from the `rdfs:domain` axioms in
`nexo.ttl` and asserts nothing new; running pyLODE alone will silently drop it.

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

## Validating data

`nexo.ttl` cannot express "an exhibition has no turnout". `rdfs:domain` is an
inference rule — it licenses a property on a class, it never forbids one — and
several properties (`turnout`, `winner`, `majority`, `office`) are declared on
`nexo:Event` so the ontology does not mis-entail on real data. That makes them
domain-applicable to every event class.

`nexo-shapes.ttl` supplies the prohibition. Four `sh:closed` node shapes, one
per domain branch, permitting the core event properties plus that branch's own:

```bash
pip install pyshacl
pyshacl -s nexo-shapes.ttl -e nexo.ttl -df turtle mydata.ttl
```

**`-e nexo.ttl` is required.** `sh:targetClass` matches instances through
`rdfs:subClassOf*`, so the validator needs the class hierarchy to know an
`Exhibition` is a `CulturalEvent`. Without it no shape matches, every check is
skipped, and the report reads `Conforms: True` for data that plainly is not —
a silent failure.

Keep the shapes out of any graph you reason over. OWL axioms are inference
rules and SHACL shapes are validation rules; conflating them lets a reasoner
draw conclusions from what were meant to be prohibitions.