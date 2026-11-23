# ADR-001 Implementačná technológia pre R-001

- Stav: Proposed
- Dátum: 2026-11-23
- Requirement: R-001
- Contract: model-approval-api, model-validation-api, model-repository-api v0.2.0 (approved)

## Kontext

Approved contract určuje HTTP REST a OpenAPI 3.1, ale nie jazyk, framework ani
databázu. Reuse catalog uvádza PostgreSQL pre Model Repository (súbory na
serveri, v DB iba cesty). Reálne tlačiarne a slicer nie sú k dispozícii.

## Rozhodnutie (výber autora, 2026-11-23)

- Backend: Python 3.12, FastAPI, SQLAlchemy 2.
- Databáza: PostgreSQL (aj pre testy), lokálne cez `docker-compose.yml`.
- Testy: pytest, pytest-bdd (spúšťa priamo `spec/stories/features/US-001.feature`),
  overenie odpovedí voči approved contractu (jsonschema).
- Model Validator: zástupný validátor (stub); výsledok určujú značky v súbore.
- Customer portal a chat (INT-010): statické mockupy, chat bez backendu.
- Každý component je samostatný Python balík; závislosti kontroluje test
  `tests/test_architecture.py` podľa `allowed_dependencies`.

## Dôsledky

- Zmena technológie neovplyvní contract.
- Validátor a slicer bude treba nahradiť skutočnými službami (TO-BE).

Rozhodnutie Accepted / Rejected zapisuje človek.
