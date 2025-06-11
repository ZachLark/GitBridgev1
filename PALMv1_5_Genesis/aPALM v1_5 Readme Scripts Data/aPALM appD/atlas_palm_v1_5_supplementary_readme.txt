# Atlas PALM v1.5 Supplementary Package README

## Overview
This README provides an overview of the Atlas PALM v1.5 Supplementary Package, delivered on May 6, 2025, 23:59 PDT. The package includes Sections I–XI, Table of Contents, Table of Appendices, Appendices A–N, diagrams, code files, and metadata.

## Setup Instructions
- **Repository**: Clone the atlas-palm-v1.5 repository:
  ```
  git clone https://github.com/your-org/atlas-palm-v1.5.git
  ```
- **Dependencies**: Install Python dependencies:
  ```
  pip install -r requirements.txt
  ```
- **Neo4j Setup**: Configure the Cannabis Knowledge Graph (see data/knowledge_graph_readme.txt).

## File Structure
- `data/`: Datasets (e.g., test_dataset.parquet, terpene_dataset.parquet)
- `scripts/`: Evaluation and test scripts (e.g., evaluate_model.py, simulation_test_suite.py)
- `logs/`: Log files (e.g., evaluation_errors.log)
- `charts/`: Generated metrics charts
- `docs/`: Supplementary Package documents (e.g., Appendices A–N)

## Usage
- Run simulation tests: See scripts/simulation_test_suite_readme.txt.
- Reproduce experimental results: See README_experimental_results.txt.
- Query the knowledge graph: See data/knowledge_graph_readme.txt.

## Timestamp
- NIST Timestamp: `{"timestamp": "202505062359"}`