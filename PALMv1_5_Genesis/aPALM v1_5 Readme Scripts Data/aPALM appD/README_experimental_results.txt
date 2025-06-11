README: Reproducing Experimental Results
========================================

This README provides instructions for reproducing the experimental results for Atlas PALM v1.5, as documented in Appendix D: Experimental Results.

Access Dataset
--------------
- File: data/test_dataset.parquet
- Description: Contains test data for model evaluation, including strain, terpene, and user feedback data.
- Access: Located in the atlas-palm-v1.5/data/ directory of the repository.

Run Evaluation
--------------
- Script: scripts/evaluate_model.py --model v1.5
- Description: Evaluates the Atlas PALM v1.5 model using the test dataset.
- Command: python scripts/evaluate_model.py --model v1.5 --dataset data/test_dataset.parquet

Visualize Metrics
-----------------
- Script: scripts/plot_metrics.py --output charts/
- Description: Generates charts for accuracy, latency, and other metrics.
- Command: python scripts/plot_metrics.py --output charts/

Validate Ontology
-----------------
- Script: scripts/validate_ontology.py
- Description: Validates the Cannabis Knowledge Graph structure.
- Command: python scripts/validate_ontology.py

Troubleshooting
---------------
- Logs: logs/evaluation_errors.log
- Instructions: Check logs/evaluation_errors.log for errors. If metrics differ, verify dataset integrity using parquet-tools.

Version Control
---------------
- Branch: feature/evaluation-update
- Instructions: Commit evaluation scripts to scripts/ on feature/evaluation-update.
- Command:
  git checkout feature/evaluation-update
  git add scripts/*
  git commit -m "Update evaluation scripts for v1.5"
  git push origin feature/evaluation-update