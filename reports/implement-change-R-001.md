# IMPLEMENT_CHANGE – R-001 (candidate code)

## Pochopenie úlohy

Candidate code a testy pre R-001 podľa approved contractov 0.2.0
(Model Approval, Model Validation, Model Repository API), plus mockup
zákazníckeho portálu a chatu.

## Režim a specification baseline

- Režim: IMPLEMENT_CHANGE
- Specification baseline: 0.1.0; contracts 0.2.0 (approved, Leonid)
- Technológia podľa výberu autora (2026-11-23): Python + FastAPI, PostgreSQL,
  stub validátor, mockup portálu a chatu – ADR-001 (Proposed)

## Použité autoritatívne vstupy

- `spec/contracts/approved/*.v0.2.0.yaml`
- `spec/requirements/*`, `spec/application/*`, `spec/stories/features/US-001.feature`
- `spec/policies/contract-design-profile.yaml`

## Generation plan (súbory)

| Súbor / balík | Component | Obsah |
|---|---|---|
| `src/pod/modeling_workspace/` | AC-ModelingWorkspace | Model Approval API, lifecycle DO-ModelApproval, súhlasy, BR-001 (`reevaluate_print`) |
| `src/pod/model_validator/` | AC-ModelValidator | Model Validation API, stub validátor |
| `src/pod/model_repository/` | AC-ModelRepository | Model Repository API, limit BR-004, BR-006 |
| `src/pod/order_orchestrator/` | AC-OrderOrchestrator | interné: DO-Order, DO-ModelingTask, stav tlače (bez API) |
| `src/pod/notifier/` | AC-Notifier | interné: DO-Notification do účtu (bez API) |
| `src/pod/core/` | – | settings, DB, bearer token (ADR-002), problem-details |
| `src/portal_mock/` | AC-CustomerPortal | statický mockup portálu a chatu (INT-010) |
| `tests/` | – | contract, architecture, acceptance, rules |

## Quality gates

| Kontrola | Výsledok |
|---|---|
| Implementácia vystavuje presne 14 operations z approved contractov (cesty, metódy, operationId) | PASS |
| Každá odpoveď API v testoch zodpovedá schéme a status kódu z contractu | PASS |
| Každá operation vyžaduje bearer token | PASS |
| Importy medzi komponentmi rešpektujú allowed_dependencies | PASS (s výnimkou nižšie) |
| Acceptance: SC-001-01 … SC-001-11 z US-001.feature | PASS (11/11) |
| Negatívne prípady (401, 403, 409, súbeh „prvý vyhráva“, BR-003, BR-005) | PASS (12/12) |
| Spolu | 27 passed (PostgreSQL 16) |

## Rozhodnutia a otvorené body pre človeka

| # | Bod | Návrh |
|---|---|---|
| 1 | `components.yaml` neurčuje `allowed_dependencies` pre AC-ModelRepository. Kód potrebuje Repository → OrderOrchestrator (vlastník objednávky, začatá tlač) a Repository → ModelingWorkspace (súhlas s opravou, BR-005). | Doplniť do components.yaml, alebo rozhodnúť inak. Výnimka je zapísaná v `tests/test_architecture.py` (`NOT_IN_SPEC`). |
| 2 | Validator má v spec iba závislosť na Workspace, ale INT-007/008/009 vedú z Validatora k Notifier, Orchestrator a Slicer. | Implementované cez Workspace (Validator → Workspace → ostatné); hranice ostali dodržané. Slicer je súčasť stubu. |
| 3 | `get_model`: contract hovorí „model iného zákazníka vidí iba zamestnanec a iba ak je zdieľanie povolené“. | Implementované: zákazník vidí iba svoj model; zamestnanec vidí modely objednávok, na ktorých pracuje; zdieľanie sa vynucuje pri ponuke na opätovné použitie (`search_reusable_models`). Potvrdiť výklad. |
| 4 | Dĺžka obdobia limitu nahraní (BR-004) je UNKNOWN. | Konfigurácia `POD_UPLOAD_LIMIT_PERIOD_DAYS`; prázdne = celá doba objednávky. |
| 5 | Prihlásenie (vydanie tokenu) nie je v contracte. | ADR-002 (Proposed); na vývoj tokeny z `python -m pod.dev_seed`. |
| 6 | Statické cesty `/portal` a `/model_files` nie sú v contracte. | Nie sú to API operations (mockup a súbory modelov – `file_url`). |
| 7 | ADR-001 a ADR-002 majú stav Proposed. | Človek ich má prijať alebo zamietnuť. |

## Traceability summary

R-001 → SC-001-01 … 11 → operations (traceability.yaml, 38 záznamov) →
`tests/acceptance/test_us001.py` (11 záznamov scenario → test).
