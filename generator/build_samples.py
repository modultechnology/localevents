"""Build 20 hand-crafted reference samples that pass the v3 validator.

Each sample is constructed as a Python dict matching the LLM-output schema,
then run through the same `add_offsets` + `validate_example` pipeline the
real generator uses. Guarantees the samples are exactly what the generator
should produce.

Sample distribution: 14 EN / 6 DE; 4 cultural, 4 mobility, 4 sports, 4
politics, 3 multi, 1 negative.

Real entities used where natural: real cities, real venues, real parties,
real transit operators. People are invented (no real public figures named
in quoted/active roles).

Run: python build_samples.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from generate_dataset import (
    ExampleSpec, SCHEMA_VERSION, add_offsets, validate_example, _entropy_seed,
)
import random

_RNG = random.Random(0)
_E = lambda: _entropy_seed(_RNG)


SAMPLES = []

# ============================================================================
# CULTURAL (4)
# ============================================================================

# 0 — EN cultural, simple, Brooklyn poetry slam
SAMPLES.append((
    ExampleSpec(0, "en", "cultural", _E()),
    {
        "text": "The Brooklyn Poets collective opened its eighth annual Borough Slam at the Old Stone House in Park Slope on Saturday night, drawing about 140 attendees for what organizers called their largest local turnout to date.",
        "entities": [
            {"type": "ORG",   "text": "Brooklyn Poets"},
            {"type": "EVENT", "text": "Borough Slam"},
            {"type": "FAC",   "text": "Old Stone House"},
            {"type": "LOC",   "text": "Park Slope"},
            {"type": "DATE",  "text": "Saturday night"},
            {"type": "NUM",   "text": "140"},
        ],
        "domain_labels": ["cultural"],
        "events": [{
            "event_type": "cultural",
            "event_subtype": "PoetrySlam",
            "trigger": "opened",
            "slots": {
                "event_name": "Borough Slam",
                "venue": "Old Stone House",
                "city": "Park Slope",
                "organizers": ["Brooklyn Poets"],
                "actual_attendance": 140,
                "start_date": "Saturday night",
            },
        }],
    },
))

# 1 — EN cultural, medium, Sheffield premiere
SAMPLES.append((
    ExampleSpec(1, "en", "cultural", _E()),
    {
        "text": "A new ensemble play tracing four generations of steelworkers' families opens at the Crucible Studio in Sheffield on Thursday, marking the venue's first commission from local writer Imogen Hawkridge. The 95-minute piece, titled Forge, features a six-strong cast drawn from amateur dramatic societies across South Yorkshire and runs until 24 May. Director Niamh Caulfield said rehearsals had been built around the cast's day jobs. Tickets are priced at £14, with a pay-what-you-can policy on the final Wednesday.",
        "entities": [
            {"type": "FAC",   "text": "Crucible Studio"},
            {"type": "LOC",   "text": "Sheffield"},
            {"type": "DATE",  "text": "Thursday"},
            {"type": "PER",   "text": "Imogen Hawkridge"},
            {"type": "DATE",  "text": "95-minute"},
            {"type": "EVENT", "text": "Forge"},
            {"type": "LOC",   "text": "South Yorkshire"},
            {"type": "DATE",  "text": "24 May"},
            {"type": "PER",   "text": "Niamh Caulfield"},
            {"type": "MONEY", "text": "£14"},
            {"type": "DATE",  "text": "final Wednesday"},
        ],
        "domain_labels": ["cultural"],
        "events": [{
            "event_type": "cultural",
            "event_subtype": "Premiere",
            "trigger": "opens",
            "slots": {
                "event_name": "Forge",
                "venue": "Crucible Studio",
                "city": "Sheffield",
                "artists": ["Imogen Hawkridge"],
                "directors": ["Niamh Caulfield"],
                "start_date": "Thursday",
                "end_date": "24 May",
                "duration": "95-minute",
                "ticket_price": "£14",
            },
        }],
    },
))

# 2 — DE cultural, medium, Frankfurt exhibition
SAMPLES.append((
    ExampleSpec(2, "de", "cultural", _E()),
    {
        "text": "Mit der Eröffnung der Ausstellung „Eisenbahn und Erinnerung“ hat das Historische Museum Frankfurt am Donnerstagabend seine neue Sonderschau gestartet. Im Mittelpunkt stehen rund 180 Objekte aus den Beständen des Deutschen Bahnmuseums sowie zwölf Leihgaben aus Privatsammlungen, die der Kurator Hans-Jürgen Reibl gemeinsam mit der Düsseldorfer Historikerin Eva Kropp zusammengetragen hat. Die Schau, zu der etwa 320 geladene Gäste erschienen, läuft bis zum 14. September.",
        "entities": [
            {"type": "EVENT", "text": "Eisenbahn und Erinnerung"},
            {"type": "FAC",   "text": "Historische Museum Frankfurt"},
            {"type": "DATE",  "text": "Donnerstagabend"},
            {"type": "NUM",   "text": "180"},
            {"type": "ORG",   "text": "Deutschen Bahnmuseums"},
            {"type": "NUM",   "text": "zwölf"},
            {"type": "PER",   "text": "Hans-Jürgen Reibl"},
            {"type": "LOC",   "text": "Düsseldorfer"},
            {"type": "PER",   "text": "Eva Kropp"},
            {"type": "NUM",   "text": "320"},
            {"type": "DATE",  "text": "14. September"},
        ],
        "domain_labels": ["cultural"],
        "events": [{
            "event_type": "cultural",
            "event_subtype": "Exhibition",
            "trigger": "Eröffnung",
            "slots": {
                "event_name": "Eisenbahn und Erinnerung",
                "venue": "Historische Museum Frankfurt",
                "curators": ["Hans-Jürgen Reibl", "Eva Kropp"],
                "actual_attendance": 320,
                "start_date": "Donnerstagabend",
                "end_date": "14. September",
            },
        }],
    },
))

# 3 — EN cultural, simple, international (Eurovision-style)
SAMPLES.append((
    ExampleSpec(3, "en", "cultural", _E()),
    {
        "text": "Eurovision 2026 organizers announced on Tuesday that the 70th edition of the song contest will be staged at the Wiener Stadthalle in Vienna from 12 to 16 May, with around 9,000 ticketed spectators expected at each of the two semi-finals.",
        "entities": [
            {"type": "EVENT", "text": "Eurovision 2026"},
            {"type": "DATE",  "text": "Tuesday"},
            {"type": "NUM",   "text": "70th"},
            {"type": "FAC",   "text": "Wiener Stadthalle"},
            {"type": "LOC",   "text": "Vienna"},
            {"type": "DATE",  "text": "12 to 16 May"},
            {"type": "NUM",   "text": "9,000"},
            {"type": "NUM",   "text": "two"},
        ],
        "domain_labels": ["cultural"],
        "events": [{
            "event_type": "cultural",
            "event_subtype": "MusicCompetition",
            "trigger": "will be staged",
            "slots": {
                "event_name": "Eurovision 2026",
                "venue": "Wiener Stadthalle",
                "city": "Vienna",
                "start_date": "12 to 16 May",
                "edition": "70th",
                "actual_attendance": 9000,
            },
        }],
    },
))

# ============================================================================
# MOBILITY (4)
# ============================================================================

# 4 — EN mobility, medium, Manchester Metrolink strike
SAMPLES.append((
    ExampleSpec(4, "en", "mobility", _E()),
    {
        "text": "Metrolink trams across Greater Manchester will come to a standstill on Thursday and Friday after drivers voted to walk out over rota changes. Operator KeolisAmey said all eight tram lines would be suspended from 04:00 on Thursday until early Saturday morning, with around 240,000 daily journeys expected to be affected. Talks between the operator and the RMT broke down on Tuesday evening.",
        "entities": [
            {"type": "ORG",  "text": "Metrolink"},
            {"type": "LOC",  "text": "Greater Manchester"},
            {"type": "DATE", "text": "Thursday and Friday"},
            {"type": "ORG",  "text": "KeolisAmey"},
            {"type": "MISC", "text": "all eight tram lines"},
            {"type": "DATE", "text": "04:00 on Thursday"},
            {"type": "DATE", "text": "early Saturday morning"},
            {"type": "NUM",  "text": "240,000"},
            {"type": "ORG",  "text": "RMT"},
            {"type": "DATE", "text": "Tuesday evening"},
            {"type": "MISC", "text": "rota changes"},
        ],
        "domain_labels": ["mobility"],
        "events": [{
            "event_type": "mobility",
            "event_subtype": "TransportStrike",
            "trigger": "walk out",
            "slots": {
                "city": "Greater Manchester",
                "operator": "KeolisAmey",
                "affected_lines": ["all eight tram lines"],
                "start_date": "04:00 on Thursday",
                "end_date": "early Saturday morning",
                "estimated_affected_passengers": 240000,
                "reason": "rota changes",
                "ongoing": False,
            },
        }],
    },
))

# 5 — DE mobility, complex, Wien U2 disruption
SAMPLES.append((
    ExampleSpec(5, "de", "mobility", _E()),
    {
        "text": "Die U2 wird in Wien zwischen Schottentor und Karlsplatz von Freitagabend bis Montag früh komplett gesperrt, um den letzten Streckenabschnitt für die Verlängerung Richtung Matzleinsdorfer Platz an das bestehende Netz anzuschließen. Wie die Wiener Linien am Mittwoch mitteilten, sind insgesamt 71 Stunden Sperre vorgesehen, in denen rund 134.000 tägliche Fahrgäste auf einen Schienenersatzverkehr mit zwölf Bussen sowie auf die Straßenbahnlinien D, 71 und 1 ausweichen müssen. Die Verlängerung der U2 soll planmäßig im Herbst 2027 in Betrieb gehen.",
        "entities": [
            {"type": "MISC",  "text": "U2"},
            {"type": "LOC",   "text": "Wien"},
            {"type": "FAC",   "text": "Schottentor"},
            {"type": "FAC",   "text": "Karlsplatz"},
            {"type": "DATE",  "text": "Freitagabend"},
            {"type": "DATE",  "text": "Montag früh"},
            {"type": "FAC",   "text": "Matzleinsdorfer Platz"},
            {"type": "ORG",   "text": "Wiener Linien"},
            {"type": "DATE",  "text": "Mittwoch"},
            {"type": "DATE",  "text": "71 Stunden"},
            {"type": "NUM",   "text": "134.000"},
            {"type": "NUM",   "text": "zwölf"},
            {"type": "MISC",  "text": "Straßenbahnlinien D, 71 und 1"},
            {"type": "DATE",  "text": "Herbst 2027"},
        ],
        "domain_labels": ["mobility"],
        "events": [{
            "event_type": "mobility",
            "event_subtype": "TransitDisruption",
            "trigger": "komplett gesperrt",
            "slots": {
                "city": "Wien",
                "operator": "Wiener Linien",
                "affected_lines": ["U2"],
                "start_date": "Freitagabend",
                "end_date": "Montag früh",
                "duration": "71 Stunden",
                "estimated_affected_passengers": 134000,
                "ongoing": False,
            },
        }],
    },
))

# 6 — EN mobility, complex, Bristol bike share
SAMPLES.append((
    ExampleSpec(6, "en", "mobility", _E()),
    {
        "text": "Bristol's long-delayed e-bike scheme finally launched on Monday morning, with 600 vehicles distributed across 80 stations from Bedminster to Stoke Bishop. The £4.2 million programme, run by Beryl on a five-year contract with Bristol City Council, will cost users £1 to unlock plus 12p per minute. Council transport lead Aamir Khan-Rashid said the rollout had taken eighteen months longer than planned.",
        "entities": [
            {"type": "LOC",   "text": "Bristol"},
            {"type": "DATE",  "text": "Monday morning"},
            {"type": "NUM",   "text": "600"},
            {"type": "NUM",   "text": "80"},
            {"type": "LOC",   "text": "Bedminster"},
            {"type": "LOC",   "text": "Stoke Bishop"},
            {"type": "MONEY", "text": "£4.2 million"},
            {"type": "ORG",   "text": "Beryl"},
            {"type": "DATE",  "text": "five-year"},
            {"type": "ORG",   "text": "Bristol City Council"},
            {"type": "MONEY", "text": "£1"},
            {"type": "MONEY", "text": "12p"},
            {"type": "PER",   "text": "Aamir Khan-Rashid"},
            {"type": "DATE",  "text": "eighteen months"},
        ],
        "domain_labels": ["mobility"],
        "events": [{
            "event_type": "mobility",
            "event_subtype": "BikeShareLaunch",
            "trigger": "launched",
            "slots": {
                "city": "Bristol",
                "operator": "Beryl",
                "start_date": "Monday morning",
                "fleet_size": 600,
                "n_stations": 80,
                "contract_value": "£4.2 million",
                "duration": "five-year",
            },
        }],
    },
))

# 7 — EN mobility, simple, Heathrow flight cancellations
SAMPLES.append((
    ExampleSpec(7, "en", "mobility", _E()),
    {
        "text": "British Airways cancelled 47 short-haul flights from Heathrow on Wednesday after a baggage-system outage at Terminal 5, affecting roughly 9,300 passengers.",
        "entities": [
            {"type": "ORG",  "text": "British Airways"},
            {"type": "NUM",  "text": "47"},
            {"type": "FAC",  "text": "Heathrow"},
            {"type": "DATE", "text": "Wednesday"},
            {"type": "FAC",  "text": "Terminal 5"},
            {"type": "NUM",  "text": "9,300"},
            {"type": "MISC", "text": "baggage-system outage"},
        ],
        "domain_labels": ["mobility"],
        "events": [{
            "event_type": "mobility",
            "event_subtype": "FlightCancellation",
            "trigger": "cancelled",
            "slots": {
                "operator": "British Airways",
                "start_date": "Wednesday",
                "estimated_affected_passengers": 9300,
                "reason": "baggage-system outage",
            },
        }],
    },
))

# ============================================================================
# SPORTS (4)
# ============================================================================

# 8 — EN sports, simple, Bronx HS basketball
SAMPLES.append((
    ExampleSpec(8, "en", "sports", _E()),
    {
        "text": "Cardinal Hayes High School in the Bronx defeated rival Mount St. Michael Academy 71-58 on Friday night before a near-capacity crowd of 1,200, securing a top seed in the CHSAA playoffs.",
        "entities": [
            {"type": "ORG",   "text": "Cardinal Hayes High School"},
            {"type": "LOC",   "text": "the Bronx"},
            {"type": "ORG",   "text": "Mount St. Michael Academy"},
            {"type": "MISC",  "text": "71-58"},
            {"type": "DATE",  "text": "Friday night"},
            {"type": "NUM",   "text": "1,200"},
            {"type": "EVENT", "text": "CHSAA playoffs"},
        ],
        "domain_labels": ["sports"],
        "events": [{
            "event_type": "sports",
            "event_subtype": "TeamMatch",
            "trigger": "defeated",
            "slots": {
                "home_team": "Cardinal Hayes High School",
                "away_team": "Mount St. Michael Academy",
                "winner": "Cardinal Hayes High School",
                "loser": "Mount St. Michael Academy",
                "final_score": "71-58",
                "city": "the Bronx",
                "attendance": 1200,
                "competition_name": "CHSAA playoffs",
                "event_date": "Friday night",
            },
        }],
    },
))

# 9 — EN sports, simple, cricket
SAMPLES.append((
    ExampleSpec(9, "en", "sports", _E()),
    {
        "text": "Glamorgan eased to a six-wicket victory over Worcestershire in their County Championship Division Two opener at Sophia Gardens in Cardiff on Saturday, with overseas signing Marnus Steyn top-scoring with 87 not out.",
        "entities": [
            {"type": "ORG",   "text": "Glamorgan"},
            {"type": "MISC",  "text": "six-wicket victory"},
            {"type": "ORG",   "text": "Worcestershire"},
            {"type": "EVENT", "text": "County Championship Division Two"},
            {"type": "FAC",   "text": "Sophia Gardens"},
            {"type": "LOC",   "text": "Cardiff"},
            {"type": "DATE",  "text": "Saturday"},
            {"type": "PER",   "text": "Marnus Steyn"},
            {"type": "MISC",  "text": "87 not out"},
        ],
        "domain_labels": ["sports"],
        "events": [{
            "event_type": "sports",
            "event_subtype": "TeamMatch",
            "trigger": "eased to",
            "slots": {
                "home_team": "Glamorgan",
                "away_team": "Worcestershire",
                "winner": "Glamorgan",
                "final_score": "six-wicket victory",
                "venue": "Sophia Gardens",
                "city": "Cardiff",
                "competition_name": "County Championship Division Two",
                "key_players": ["Marnus Steyn"],
                "event_date": "Saturday",
            },
        }],
    },
))

# 10 — DE sports, simple, Regionalliga
SAMPLES.append((
    ExampleSpec(10, "de", "sports", _E()),
    {
        "text": "Die SV Elversberg setzte sich am Samstag im Heimspiel der Regionalliga Südwest mit 2:1 gegen Eintracht Trier durch; das Tor zum Sieg fiel in der 87. Minute durch Linus Vorbach vor 4.380 Zuschauern.",
        "entities": [
            {"type": "ORG",   "text": "SV Elversberg"},
            {"type": "DATE",  "text": "Samstag"},
            {"type": "EVENT", "text": "Regionalliga Südwest"},
            {"type": "MISC",  "text": "2:1"},
            {"type": "ORG",   "text": "Eintracht Trier"},
            {"type": "DATE",  "text": "87. Minute"},
            {"type": "PER",   "text": "Linus Vorbach"},
            {"type": "NUM",   "text": "4.380"},
        ],
        "domain_labels": ["sports"],
        "events": [{
            "event_type": "sports",
            "event_subtype": "TeamMatch",
            "trigger": "setzte sich",
            "slots": {
                "home_team": "SV Elversberg",
                "away_team": "Eintracht Trier",
                "winner": "SV Elversberg",
                "loser": "Eintracht Trier",
                "final_score": "2:1",
                "competition_name": "Regionalliga Südwest",
                "attendance": 4380,
                "key_players": ["Linus Vorbach"],
                "event_date": "Samstag",
            },
        }],
    },
))

# 11 — EN sports, international, Champions League
SAMPLES.append((
    ExampleSpec(11, "en", "sports", _E()),
    {
        "text": "Manchester City booked their place in the Champions League quarter-finals on Tuesday with a 3-1 home win over Real Madrid at the Etihad Stadium, taking the tie 4-2 on aggregate; Kasper Vinterberg netted twice for the hosts before 53,400 fans.",
        "entities": [
            {"type": "ORG",   "text": "Manchester City"},
            {"type": "EVENT", "text": "Champions League"},
            {"type": "DATE",  "text": "Tuesday"},
            {"type": "MISC",  "text": "3-1"},
            {"type": "ORG",   "text": "Real Madrid"},
            {"type": "FAC",   "text": "Etihad Stadium"},
            {"type": "MISC",  "text": "4-2 on aggregate"},
            {"type": "PER",   "text": "Kasper Vinterberg"},
            {"type": "NUM",   "text": "53,400"},
        ],
        "domain_labels": ["sports"],
        "events": [{
            "event_type": "sports",
            "event_subtype": "ChampionshipMatch",
            "trigger": "booked their place",
            "slots": {
                "home_team": "Manchester City",
                "away_team": "Real Madrid",
                "winner": "Manchester City",
                "final_score": "3-1",
                "venue": "Etihad Stadium",
                "competition_name": "Champions League",
                "key_players": ["Kasper Vinterberg"],
                "attendance": 53400,
                "event_date": "Tuesday",
            },
        }],
    },
))

# ============================================================================
# POLITICS (4)
# ============================================================================

# 12 — EN politics, simple, US state-level vote
SAMPLES.append((
    ExampleSpec(12, "en", "politics", _E()),
    {
        "text": "The Pennsylvania Senate passed a closely watched school-funding bill 28-21 on Wednesday, with three Republicans crossing party lines to back the Democratic-sponsored measure.",
        "entities": [
            {"type": "ORG",  "text": "Pennsylvania Senate"},
            {"type": "MISC", "text": "school-funding bill"},
            {"type": "MISC", "text": "28-21"},
            {"type": "DATE", "text": "Wednesday"},
            {"type": "NUM",  "text": "three"},
            {"type": "ORG",  "text": "Republicans"},
            {"type": "ORG",  "text": "Democratic"},
        ],
        "domain_labels": ["politics"],
        "events": [{
            "event_type": "politics",
            "event_subtype": "ParliamentaryVote",
            "trigger": "passed",
            "slots": {
                "event_date": "Wednesday",
                "policy_topic": "school-funding bill",
                "key_parties": ["Republicans", "Democratic"],
                "majority": "28-21",
                "organizers": ["Pennsylvania Senate"],
            },
        }],
    },
))

# 13 — DE politics, medium, council vote
SAMPLES.append((
    ExampleSpec(13, "de", "politics", _E()),
    {
        "text": "Der Wiener Gemeinderat hat am Donnerstag mit 61 zu 39 Stimmen die Erhöhung der Parkgebühren in den Innenbezirken beschlossen. Für den Antrag der Koalition aus SPÖ und Neos stimmten neben den 65 Mandataren der beiden Fraktionen auch zwei Abgeordnete der Grünen. Die ÖVP und die FPÖ kündigten in der Debatte Verfassungsbeschwerden an.",
        "entities": [
            {"type": "ORG",  "text": "Wiener Gemeinderat"},
            {"type": "DATE", "text": "Donnerstag"},
            {"type": "MISC", "text": "61 zu 39"},
            {"type": "MISC", "text": "Parkgebühren in den Innenbezirken"},
            {"type": "ORG",  "text": "SPÖ"},
            {"type": "ORG",  "text": "Neos"},
            {"type": "NUM",  "text": "65"},
            {"type": "NUM",  "text": "zwei"},
            {"type": "ORG",  "text": "Grünen"},
            {"type": "ORG",  "text": "ÖVP"},
            {"type": "ORG",  "text": "FPÖ"},
        ],
        "domain_labels": ["politics"],
        "events": [{
            "event_type": "politics",
            "event_subtype": "CouncilVote",
            "trigger": "beschlossen",
            "slots": {
                "event_date": "Donnerstag",
                "policy_topic": "Parkgebühren in den Innenbezirken",
                "key_parties": ["SPÖ", "Neos", "Grünen", "ÖVP", "FPÖ"],
                "majority": "61 zu 39",
                "organizers": ["Wiener Gemeinderat"],
            },
        }],
    },
))

# 14 — EN politics, complex, UK by-election
SAMPLES.append((
    ExampleSpec(14, "en", "politics", _E()),
    {
        "text": "Labour comfortably held the Rochdale parliamentary seat in Thursday's by-election, with candidate Sarah Wainwright taking 47.3% of the vote on a 38% turnout. The Conservatives slipped to fourth place behind Reform UK and the Liberal Democrats, polling just 9.1%. Returning officer Margaret Chen-Doherty announced the result shortly after 02:00 on Friday.",
        "entities": [
            {"type": "ORG",   "text": "Labour"},
            {"type": "LOC",   "text": "Rochdale"},
            {"type": "DATE",  "text": "Thursday"},
            {"type": "EVENT", "text": "by-election"},
            {"type": "PER",   "text": "Sarah Wainwright"},
            {"type": "MISC",  "text": "47.3%"},
            {"type": "MISC",  "text": "38%"},
            {"type": "ORG",   "text": "Conservatives"},
            {"type": "ORG",   "text": "Reform UK"},
            {"type": "ORG",   "text": "Liberal Democrats"},
            {"type": "MISC",  "text": "9.1%"},
            {"type": "PER",   "text": "Margaret Chen-Doherty"},
            {"type": "DATE",  "text": "02:00 on Friday"},
        ],
        "domain_labels": ["politics"],
        "events": [{
            "event_type": "politics",
            "event_subtype": "Election",
            "trigger": "held",
            "slots": {
                "event_name": "by-election",
                "city": "Rochdale",
                "event_date": "Thursday",
                "winning_party": "Labour",
                "losing_party": "Conservatives",
                "vote_share": "47.3%",
                "turnout": "38%",
                "key_politicians": ["Sarah Wainwright", "Margaret Chen-Doherty"],
                "key_parties": ["Labour", "Conservatives", "Reform UK", "Liberal Democrats"],
            },
        }],
    },
))

# 15 — DE politics, complex, Bundestag debate
SAMPLES.append((
    ExampleSpec(15, "de", "politics", _E()),
    {
        "text": "Der Bundestag hat am Freitag das Gesetz zur Reform der Pflegeversicherung in dritter Lesung verabschiedet. Mit 412 Ja-Stimmen bei 198 Gegenstimmen und 14 Enthaltungen passierte die Vorlage der Ampel-Koalition aus SPD, Grünen und FDP das Parlament, während CDU/CSU und AfD geschlossen dagegen votierten. Gesundheitsminister Friedrich Heimann sprach von einem Generationenwerk.",
        "entities": [
            {"type": "ORG",  "text": "Bundestag"},
            {"type": "DATE", "text": "Freitag"},
            {"type": "MISC", "text": "Reform der Pflegeversicherung"},
            {"type": "MISC", "text": "dritter Lesung"},
            {"type": "NUM",  "text": "412"},
            {"type": "NUM",  "text": "198"},
            {"type": "NUM",  "text": "14"},
            {"type": "ORG",  "text": "SPD"},
            {"type": "ORG",  "text": "Grünen"},
            {"type": "ORG",  "text": "FDP"},
            {"type": "ORG",  "text": "CDU/CSU"},
            {"type": "ORG",  "text": "AfD"},
            {"type": "PER",  "text": "Friedrich Heimann"},
        ],
        "domain_labels": ["politics"],
        "events": [{
            "event_type": "politics",
            "event_subtype": "ParliamentaryVote",
            "trigger": "verabschiedet",
            "slots": {
                "event_date": "Freitag",
                "policy_topic": "Reform der Pflegeversicherung",
                "key_parties": ["SPD", "Grünen", "FDP", "CDU/CSU", "AfD"],
                "key_politicians": ["Friedrich Heimann"],
                "n_votes_for": 412,
                "n_votes_against": 198,
                "n_abstentions": 14,
                "organizers": ["Bundestag"],
            },
        }],
    },
))

# ============================================================================
# MULTI (3)
# ============================================================================

# 16 — EN multi sports+mobility, Pittsburgh marathon
SAMPLES.append((
    ExampleSpec(16, "en", "multi", _E(), multi_domains=["sports", "mobility"]),
    {
        "text": "The 31st Three Rivers Half Marathon set off from Point State Park in Pittsburgh on Sunday morning, with about 9,800 registered runners. Race officials said Wesley Akinwale took the men's title in 1:04:12, while Sara Malone won the women's race in 1:13:48. The Port Authority diverted four bus routes and closed the Boulevard of the Allies between 6 a.m. and noon.",
        "entities": [
            {"type": "EVENT", "text": "Three Rivers Half Marathon"},
            {"type": "FAC",   "text": "Point State Park"},
            {"type": "LOC",   "text": "Pittsburgh"},
            {"type": "DATE",  "text": "Sunday morning"},
            {"type": "NUM",   "text": "9,800"},
            {"type": "PER",   "text": "Wesley Akinwale"},
            {"type": "MISC",  "text": "1:04:12"},
            {"type": "PER",   "text": "Sara Malone"},
            {"type": "MISC",  "text": "1:13:48"},
            {"type": "ORG",   "text": "Port Authority"},
            {"type": "NUM",   "text": "four"},
            {"type": "FAC",   "text": "Boulevard of the Allies"},
            {"type": "DATE",  "text": "6 a.m. and noon"},
        ],
        "domain_labels": ["sports", "mobility"],
        "events": [
            {
                "event_type": "sports",
                "event_subtype": "MarathonRace",
                "trigger": "set off",
                "slots": {
                    "event_name": "Three Rivers Half Marathon",
                    "venue": "Point State Park",
                    "city": "Pittsburgh",
                    "event_date": "Sunday morning",
                    "winner": "Wesley Akinwale",
                    "key_players": ["Wesley Akinwale", "Sara Malone"],
                    "attendance": 9800,
                },
            },
            {
                "event_type": "mobility",
                "event_subtype": "RoadClosure",
                "trigger": "closed",
                "slots": {
                    "city": "Pittsburgh",
                    "operator": "Port Authority",
                    "affected_routes": ["Boulevard of the Allies"],
                    "duration": "6 a.m. and noon",
                    "reason": "Three Rivers Half Marathon",
                },
            },
        ],
    },
))

# 17 — DE multi politics+mobility, Berlin tax + bus reroute
SAMPLES.append((
    ExampleSpec(17, "de", "multi", _E(), multi_domains=["politics", "mobility"]),
    {
        "text": "Das Berliner Abgeordnetenhaus hat am Donnerstag mit 87 zu 73 Stimmen die Einführung einer Citymaut für die Innenstadt beschlossen. Im Zuge der Vorbereitungen werden die BVG-Buslinien 100 und 200 ab 1. Juli vorübergehend über den Spittelmarkt umgeleitet. Stadtentwicklungssenatorin Linda Wessel sagte, mit der Maßnahme würden täglich rund 60.000 Fahrzeuge aus der Mitte ferngehalten.",
        "entities": [
            {"type": "ORG",  "text": "Berliner Abgeordnetenhaus"},
            {"type": "DATE", "text": "Donnerstag"},
            {"type": "MISC", "text": "87 zu 73"},
            {"type": "MISC", "text": "Citymaut"},
            {"type": "LOC",  "text": "Innenstadt"},
            {"type": "ORG",  "text": "BVG"},
            {"type": "MISC", "text": "Buslinien 100 und 200"},
            {"type": "DATE", "text": "1. Juli"},
            {"type": "FAC",  "text": "Spittelmarkt"},
            {"type": "PER",  "text": "Linda Wessel"},
            {"type": "NUM",  "text": "60.000"},
            {"type": "LOC",  "text": "Mitte"},
        ],
        "domain_labels": ["politics", "mobility"],
        "events": [
            {
                "event_type": "politics",
                "event_subtype": "CouncilVote",
                "trigger": "beschlossen",
                "slots": {
                    "event_date": "Donnerstag",
                    "policy_topic": "Citymaut",
                    "majority": "87 zu 73",
                    "organizers": ["Berliner Abgeordnetenhaus"],
                    "key_politicians": ["Linda Wessel"],
                },
            },
            {
                "event_type": "mobility",
                "event_subtype": "BusRerouting",
                "trigger": "umgeleitet",
                "slots": {
                    "operator": "BVG",
                    "affected_lines": ["Buslinien 100 und 200"],
                    "start_date": "1. Juli",
                    "reason": "Citymaut",
                },
            },
        ],
    },
))

# 18 — EN multi cultural+mobility, Austin block festival
SAMPLES.append((
    ExampleSpec(18, "en", "multi", _E(), multi_domains=["cultural", "mobility"]),
    {
        "text": "Austin's annual East Side Block Festival kicked off on Saturday afternoon, with five city blocks along East 11th Street closed to traffic until late Sunday evening. Capital Metro rerouted the 17 and 30 bus lines through East 12th Street. By 10 p.m., police estimated the crowd at roughly 14,500, the festival's largest opening night since its 2017 debut.",
        "entities": [
            {"type": "LOC",   "text": "Austin"},
            {"type": "EVENT", "text": "East Side Block Festival"},
            {"type": "DATE",  "text": "Saturday afternoon"},
            {"type": "NUM",   "text": "five"},
            {"type": "FAC",   "text": "East 11th Street"},
            {"type": "DATE",  "text": "late Sunday evening"},
            {"type": "ORG",   "text": "Capital Metro"},
            {"type": "MISC",  "text": "17 and 30 bus lines"},
            {"type": "FAC",   "text": "East 12th Street"},
            {"type": "DATE",  "text": "10 p.m."},
            {"type": "NUM",   "text": "14,500"},
            {"type": "DATE",  "text": "2017"},
        ],
        "domain_labels": ["cultural", "mobility"],
        "events": [
            {
                "event_type": "cultural",
                "event_subtype": "Festival",
                "trigger": "kicked off",
                "slots": {
                    "event_name": "East Side Block Festival",
                    "city": "Austin",
                    "actual_attendance": 14500,
                    "start_date": "Saturday afternoon",
                    "end_date": "late Sunday evening",
                },
            },
            {
                "event_type": "mobility",
                "event_subtype": "TransitRerouting",
                "trigger": "rerouted",
                "slots": {
                    "city": "Austin",
                    "operator": "Capital Metro",
                    "affected_lines": ["17 and 30 bus lines"],
                    "start_date": "Saturday afternoon",
                    "end_date": "late Sunday evening",
                    "reason": "East Side Block Festival",
                },
            },
        ],
    },
))

# ============================================================================
# NEGATIVE (1)
# ============================================================================

# 19 — EN negative, Glasgow Subway debate
SAMPLES.append((
    ExampleSpec(19, "en", "negative", _E()),
    {
        "text": "Plans to extend the Glasgow Subway out to Drumchapel are facing renewed opposition from residents in the Anniesland area, who say the proposed alignment cuts too close to existing housing. Strathclyde Partnership for Transport published an updated feasibility study last week putting the cost of the eight-station extension at £640 million, well above the £450 million estimate from 2019. A public consultation closed in March without a clear preferred route.",
        "entities": [
            {"type": "ORG",   "text": "Glasgow Subway"},
            {"type": "LOC",   "text": "Drumchapel"},
            {"type": "LOC",   "text": "Anniesland"},
            {"type": "ORG",   "text": "Strathclyde Partnership for Transport"},
            {"type": "DATE",  "text": "last week"},
            {"type": "NUM",   "text": "eight-station"},
            {"type": "MONEY", "text": "£640 million"},
            {"type": "MONEY", "text": "£450 million"},
            {"type": "DATE",  "text": "2019"},
            {"type": "DATE",  "text": "March"},
        ],
        "domain_labels": [],
        "events": [],
    },
))


# ============================================================================
# Run validation + write
# ============================================================================

def main():
    out_dir = Path(__file__).parent
    plain_path = out_dir / "sample_plain.jsonl"
    annot_path = out_dir / "sample_annotated.jsonl"

    failures: list[tuple[int, str]] = []
    valid: list[tuple[ExampleSpec, dict]] = []

    for spec, raw in SAMPLES:
        validated, reason = validate_example(raw, spec)
        if validated is None:
            failures.append((spec.spec_id, reason))
        else:
            valid.append((spec, validated))

    if failures:
        print("VALIDATION FAILURES:")
        for sid, msg in failures:
            print(f"  id={sid}: {msg}")
        print(f"\n{len(failures)} of {len(SAMPLES)} samples failed.")
        sys.exit(1)

    with plain_path.open("w", encoding="utf-8") as fp, \
         annot_path.open("w", encoding="utf-8") as fa:
        for spec, rec in valid:
            plain = {"id": spec.spec_id, "language": spec.language, "text": rec["text"]}
            annotated = {
                "id": spec.spec_id,
                "schema_version": SCHEMA_VERSION,
                "language": spec.language,
                "target": spec.target,
                "text": rec["text"],
                "entities": rec["entities"],
                "domain_labels": rec["domain_labels"],
                "events": rec["events"],
            }
            fp.write(json.dumps(plain, ensure_ascii=False) + "\n")
            fa.write(json.dumps(annotated, ensure_ascii=False) + "\n")

    print(f"All {len(valid)} samples passed validation.")
    print(f"Wrote {plain_path}")
    print(f"Wrote {annot_path}")

    # Summary
    from collections import Counter
    print("\n--- Distribution ---")
    print(f"Language:  {dict(Counter(s.language for s, _ in valid))}")
    print(f"Target:    {dict(Counter(s.target for s, _ in valid))}")
    n_ents = [len(r['entities']) for _, r in valid]
    n_events = [len(r['events']) for _, r in valid]
    print(f"Entities:  range {min(n_ents)}-{max(n_ents)}, mean {sum(n_ents)/len(n_ents):.1f}")
    print(f"Events:    range {min(n_events)}-{max(n_events)}, mean {sum(n_events)/len(n_events):.1f}")
    types = Counter()
    for _, r in valid:
        for e in r["entities"]:
            types[e["type"]] += 1
    print(f"\nEntity types: {dict(types.most_common())}")


if __name__ == "__main__":
    main()
