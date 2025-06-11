README: Cannabis Knowledge Graph Setup
======================================

This README provides instructions for setting up and querying the Neo4j-based Cannabis Knowledge Graph for Atlas PALM v1.5, as documented in Appendix F: Domain Ontology.

Setup
-----
- Install Neo4j: Follow instructions at https://neo4j.com/docs/
- Load Data: Import strain, terpene, and regulatory data into Neo4j.
- Configuration: Set up connection credentials in scripts/validate_ontology.py.

Query Example
-------------
MATCH (s:Strain)-[:LEGAL_IN]->(r:Region {name: "EU"})
WHERE s.cbd > 0.05
RETURN s.name, s.cbd, s.terpenes

Validation
----------
- Script: scripts/validate_ontology.py
- Command: python scripts/validate_ontology.py