#!/usr/bin/env python3
"""Generate nexo-shapes.ttl from nexo.ttl plus a curated per-branch allow-list.

Why curated rather than derived: the shapes exist precisely to be NARROWER than
rdfs:domain. Several properties (turnout, winner, majority, office, ...) were
widened to nexo:Event so the ontology would not mis-entail on real corpus data.
That makes them domain-applicable to every class, including Exhibition. A shape
generated from the domain axioms would therefore permit exactly what we want to
forbid, so the allowed sets are stated explicitly here.

Every name is checked against the ontology, so a typo fails loudly.
"""
import sys
from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef, BNode
from rdflib.namespace import XSD

NS = Namespace('http://modultech.eu/nexo/')
g = Graph(); g.parse(sys.argv[1] if len(sys.argv) > 1 else 'nexo.ttl')
def local(u): return str(u).split('/')[-1].split('#')[-1]

# Properties any event may carry, regardless of branch.
CORE = """eventName description eventDate startDate endDate normalizedStartDate
normalizedEndDate duration isOngoing hasLocation hasVenue city country occursIn
hasSpatialExtent hasTemporalExtent hasParticipant hasAgent hasPatient
hasOrganizer hasPerspective hasEventType hasCausality hasImpact hasMagnitude
magnitude partOf hasSubEvent precedes follows triggers causedBy
actualAttendance estimatedParticipants language edition onPlanet""".split()

# Branch-specific additions. The point of the file is what is NOT here.
BRANCH = {
 'CulturalEvent':   "hasArtist hasPerformer hasCurator hasDirector genre medium ticketPrice".split(),
 'SportsEvent':     "homeTeam awayTeam winner loser hasKeyPlayer finalScore competitionName competitionStage sportType".split(),
 'MobilityEvent':   ("hasOperator affectedLine affectedRoute estimatedAffectedPassengers "
                     "disruptionReason numberOfStations fareChangeAmount fleetSize contractValue").split(),
 'LegislativeEvent':("votesInFavour votesAgainst abstentions majority voteOutcome hasKeyPolitician "
                     "hasParty winningParty losingParty policyTopic voteShare turnout office contractValue").split(),
}

kind, rng = {}, {}
for p in g.subjects(RDF.type, OWL.ObjectProperty):   kind[p]='obj'
for p in g.subjects(RDF.type, OWL.DatatypeProperty): kind[p]='data'
for p,o in g.subject_objects(RDFS.range): rng.setdefault(p,o)

missing=[n for n in set(CORE)|{x for v in BRANCH.values() for x in v} if NS[n] not in kind]
assert not missing, f"not declared in the ontology: {sorted(missing)}"
for c in BRANCH:
    assert (NS[c], RDF.type, OWL.Class) in g, f"class missing: {c}"

def constraint(name):
    p = NS[name]; out=[f'        sh:path nexo:{name} ;']
    r = rng.get(p)
    if kind[p]=='obj':
        if isinstance(r, URIRef): out.append(f'        sh:class nexo:{local(r)} ;')
        out.append('        sh:nodeKind sh:BlankNodeOrIRI ;')
    else:
        if isinstance(r, URIRef) and r != RDFS.Literal and str(r).startswith(str(XSD)):
            out.append(f'        sh:datatype xsd:{local(r)} ;')
        elif isinstance(r, BNode):
            members=[]
            for u in g.objects(r, OWL.unionOf): members=[local(x) for x in g.items(u)]
            if members:
                alts=' '.join(f'[ sh:datatype xsd:{m} ]' for m in members)
                out.append(f'        sh:or ( {alts} ) ;')
    return '\n'.join(out)

L=['''@prefix nexo: <http://modultech.eu/nexo/> .
@prefix sh:   <http://www.w3.org/ns/shacl#> .
@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .

# ############################################################################
# NEXO SHACL shapes
#
# OPTIONAL. Constraints, not ontology. Keep this file out of any graph you
# reason over: OWL axioms are inference rules, SHACL shapes are validation
# rules, and conflating them makes a reasoner draw conclusions from what were
# meant to be prohibitions.
#
# These shapes are deliberately NARROWER than nexo.ttl's rdfs:domain axioms.
# Properties such as turnout, winner, majority and office are declared on
# nexo:Event so the ontology does not mis-entail on real data; that makes them
# domain-applicable to every event class, Exhibition included. Domain cannot
# express "an exhibition has no turnout" -- rdfs:domain licenses a property, it
# never forbids one. That prohibition lives here.
#
# Each branch shape is sh:closed, so a property outside its allowed set is a
# violation rather than silently accepted.
#
#   pyshacl -s nexo-shapes.ttl -df turtle mydata.ttl
# ############################################################################

<http://modultech.eu/nexo/shapes> a owl:Ontology ;
    rdfs:label "NEXO SHACL shapes"@en ;
    owl:versionInfo "1.2" .
''']

IGNORED = ('rdf:type rdfs:label rdfs:comment rdfs:seeAlso owl:sameAs')
for cls, extra in BRANCH.items():
    allowed = CORE + extra
    L.append(f'''
# ============================================
# {cls}
# ============================================

nexo:{cls}Shape a sh:NodeShape ;
    sh:targetClass nexo:{cls} ;
    sh:closed true ;
    sh:ignoredProperties ( {IGNORED} ) ;
    sh:name "{cls} shape" ;
    sh:description "Permits the core event properties plus the {cls} branch; anything else is a violation." ;''')
    props = ['    sh:property [\n' + constraint(n) + '\n    ]' for n in allowed]
    L.append(' ;\n'.join(props) + ' .\n')

open(sys.argv[2] if len(sys.argv)>2 else 'nexo-shapes.ttl','w',encoding='utf-8').write('\n'.join(L))
print(f"shapes written: {len(BRANCH)} node shapes")
for c,e in BRANCH.items(): print(f"   {c}Shape: {len(CORE)+len(e)} allowed properties ({len(e)} branch-specific)")
