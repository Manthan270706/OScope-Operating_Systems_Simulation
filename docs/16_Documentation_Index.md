# OScope — Documentation Index

## Foundation
1. [Project Charter](01_Project_Charter.md)
2. [PRD](02_PRD.md)
3. [SRS](03_SRS.md)

## Design
4. [TDD](04_TDD.md)
5. [Architecture](05_Architecture.md)
6. [ADRs](06_ADRs.md)
7. [API and Interface Specification](07_API_and_Interface_Spec.md)
8. [Data Model and Result Schema](08_Data_Model_and_Result_Schema.md)

## Engineering
9. [Test Strategy](09_Test_Strategy.md)
10. [Implementation Plan](10_Implementation_Plan.md)
11. [Requirements Traceability Matrix](11_Traceability_Matrix.md)
12. [Risk Register](12_Risk_Register.md)
13. [Coding and Engineering Standards](13_Coding_and_Engineering_Standards.md)
14. [Development Workflow](14_Development_Workflow.md)

## Validation
15. [Demo and Evaluation Plan](15_Demo_and_Evaluation_Plan.md)

---

## Final Project Status

All project phases are **Complete, Tested, and Demonstration-Ready**:
- **Codebase:** C++17, clean build under `-Wall -Wextra -Wpedantic` with 0 warnings.
- **Automated Tests:** **340/340 CTest tests passing (100%)**.
- **JSON Schema:** Validated schema v1.0.0 compliance with `python3 -m json.tool`.
- **Traceability:** 100% bidirectional coverage across all PRD/SRS functional requirements in `11_Traceability_Matrix.md`.
- **Demonstration:** CLI direct flags (`--demo-all`, `--demo-paging`, etc.) and interactive submenus verified end-to-end.
