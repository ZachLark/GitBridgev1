README: Simulation Test Suite
=============================

This README provides instructions for running the simulation test suite for Atlas PALM v1.5, as documented in Appendix D: Simulation Tests.

File
----
- Script: scripts/simulation_test_suite.py
- Description: Contains 1,000+ test cases for the Simulation Framework (Section VIII).

Structure
---------
- 300 edge case tests
- 200 cultural mismatch tests
- 150 high-volume load tests
- 200 compliance and ethics tests
- 150 user journey tests

Execution
---------
- Command: pytest -v simulation_test_suite.py --log-cli-level=INFO
- Dependencies: pytest, pytest-asyncio, Atlas PALM codebase

Sample Output
-------------
- Total tests: 1,000
- Passed: 997
- Failed: 3 (logged for debugging)
- Duration: 120 seconds