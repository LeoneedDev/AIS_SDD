# DESIGN_CONTRACT – R-001, contract 0.2.0 (proposed)

## Pochopenie úlohy

HTTP contract pre schválenie 3D modelu zákazníkom pred tlačou (R-001), pokrytie
scenárov SC-001-01 … SC-001-11 a mapping každej operation. Verzia 0.2.0
zapracúva rozhodnutia človeka k DR-1 … DR-6 z verzie 0.1.0. Návrh sa neschvaľuje.

## Režim a specification baseline

- Režim: DESIGN_CONTRACT
- Specification baseline: 0.1.0 (`spec/manifest.yaml`)
- Typ rozhrania: HTTP REST, OpenAPI 3.1 podľa approved `contract-design-profile.yaml`.

## Použité autoritatívne vstupy

- requirements.yaml (R-001, C-001), business-rules.yaml (BR-001 … BR-009),
  quality-requirements.yaml (QR-001, draft)
- actors-processes.yaml, components.yaml, data-objects.yaml, lifecycles.yaml,
  interactions.yaml, service-realization.yaml
- US-001.md, US-001.feature, glossary.md
- contract-design-profile.yaml (approved, Leonid)
- views: `spec/architecture/views/*.png`
- ADR: žiadne

## Rozhodnutia človeka (2026-11-23) a kam sa zapísali

| DR | Rozhodnutie | Zapísané |
|---|---|---|
| DR-1 | Zákazník nemá tlačidlo „chcem úpravu“. O modeli rozhoduje iba sám v portáli: súhlasí, alebo nesúhlasí s komentárom. Súhlas s opravou a rozdelením zadáva tiež sám; modelár ani manažér za neho nerozhodujú. | BR-002, BR-003, BR-005, BR-009, R-001, lifecycle, SC-001-01/02/05, glossary |
| DR-2 | in_review ostáva: znamená, že zákazník model otvoril; stav vidia obe strany. | lifecycles.yaml |
| DR-3 | Celá história schvaľovania, zmien, súhlasov a nesúhlasov patrí k objednávke; jedna objednávka = jeden model. | data-objects.yaml (DO-Order, DO-ModelApproval part_of DO-Order); G5 v gap-analysis.md (mimo EA) |
| DR-4 | Platí prvá požiadavka; ďalšia dostane 409. | contract (`x-sdd.concurrency`) |
| DR-5 | Zákazník vidí ID a prezývku zamestnanca, nie celé meno. | QR-001, schema `employee_ref` |
| DR-6 | Owner DO-3DModel je Model Repository; Validator je iba medzistav počas overenia. | data-objects.yaml, components.yaml |
| — | Limit 10 vlastných nahraní sa uplatní automaticky; potom je overenie za doplatok. | BR-004, nový SC-001-11 |
| — | Vrátenie peňazí, notifikácie, chat, pridelenie úloh a tlač sú mimo contractu. | tento report |

## Chýbajúce informácie alebo rozpory (neblokujúce)

| Položka | Stav |
|---|---|
| Dĺžka obdobia limitu nahraní (BR-004) | UNKNOWN; contract ju neobsahuje ako konštantu, vracia iba `period_ends_at`. |
| Interakcie Validator → Repository (uloženie overeného modelu) a Portal → Repository (nahranie zákazníkom) | V modeli EA nie sú; autor nechce ďalšie zmeny v EA. Contract sa riadi rozhodnutím DR-6. |
| Pripomienka zákazníkovi, ktorý dlho nereaguje | Spomenutá autorom, nie je rozhodnutá; nie je v contracte. |
| Mockup chatu (INT-010) | Prípadne v IMPLEMENT_CHANGE, nie je súčasťou contractu. |
| Overenie modelu | Synchrónne (odpoveď 201 s výsledkom). |
| R-001, C-001 majú stav approved, ale ich text sa po rozhodnutiach zmenil | Človek ich má znova skontrolovať. |

## Impact analysis

```yaml
change:
  mode: "DESIGN_CONTRACT"
  requirement: "R-001"
  specification_baseline: "0.1.0"
  reason: "Contract 0.2.0 po rozhodnutiach DR-1 … DR-6."
affected:
  goals: ["G-001"]
  actors_roles: ["ACT-Clients", "ACT-3DModeler", "ACT-Manager"]
  business_processes: ["BP-ModelThePart", "BP-ApproveTheModel"]
  business_services: ["BS-3DModelingApproval"]
  application_services: ["AS-ModellingOfComponent", "AS-ApprovingModel", "AS-ModelStorage"]
  application_components: ["AC-ModelingWorkspace", "AC-ModelValidator", "AC-ModelRepository"]
  interfaces_contracts:
    - "spec/contracts/proposed/model-approval-api.v0.2.0.yaml"
    - "spec/contracts/proposed/model-validation-api.v0.2.0.yaml"
    - "spec/contracts/proposed/model-repository-api.v0.2.0.yaml"
  data_objects: ["DO-Order", "DO-ModelOrder", "DO-ModelApproval", "DO-3DModel", "DO-Notification", "DO-ModelingTask"]
  technology_elements: []
  work_packages_deliverables: []
  decisions: []
  scenarios: ["SC-001-01", "SC-001-02", "SC-001-03", "SC-001-04", "SC-001-05", "SC-001-06",
              "SC-001-07", "SC-001-08", "SC-001-09", "SC-001-10", "SC-001-11"]
  tests: []
open_questions: []
```

## Navrhovaný výstup

| API (component, service) | Operation | Endpoint | Roly | Scenáre |
|---|---|---|---|---|
| Model Approval (AC-ModelingWorkspace, AS-ModellingOfComponent) | create_model_approval | POST /orders/{order_id}/model_approvals | modeler, manager | 01, 02, 05, 06 |
| | list_model_approvals | GET /orders/{order_id}/model_approvals | zákazník, modeler, manager | 01, 02, 05 |
| | get_model_approval | GET …/model_approvals/{id} | zákazník, modeler, manager | 01, 02, 05 |
| | start_review | POST …/review_starts | zákazník | 01, 05 |
| | approve_model | POST …/approvals | zákazník (BR-003) | 01 |
| | reject_model | POST …/rejections (komentár povinný) | zákazník (BR-003) | 05, 02 |
| | submit_revision | POST …/revisions | modeler (BR-007) | 05 |
| | record_customer_consent | POST /orders/{order_id}/customer_consents | zákazník | 04, 08, 09, 10 |
| | list_customer_consents | GET /orders/{order_id}/customer_consents | zákazník, modeler, manager | 04, 09, 10 |
| Model Validation (AC-ModelValidator, AS-ApprovingModel) | create_model_validation | POST /model_validations | modeler, manager | 03, 04, 08, 09, 10 |
| | get_model_validation | GET /model_validations/{id} | modeler, manager | 03, 04, 08 |
| Model Repository (AC-ModelRepository, AS-ModelStorage) | upload_model_version | POST /orders/{order_id}/model_versions | zákazník (limit BR-004), modeler | 03, 05, 11 |
| | search_reusable_models | GET /reusable_models?query= | modeler, manager | 06, 07 |
| | get_model | GET /models/{id} | zákazník (vlastný), modeler, manager | 01, 06 |

Lifecycle DO-ModelApproval → operations:

| Prechod | Operation | Guard |
|---|---|---|
| → waiting_for_review | create_model_approval | 409 ak existuje aktívny záznam |
| waiting_for_review → in_review | start_review | zákazník otvoril model |
| in_review → approved | approve_model | iba zákazník (BR-003) |
| in_review → rejected | reject_model | revision_count < 2, komentár |
| rejected → closed_new_development | reject_model | revision_count = 2 |
| rejected → waiting_for_review | submit_revision | revision_count < 2, potom +1 |

## Validation results

| Kontrola | Výsledok |
|---|---|
| OpenAPI 3.1 syntax (openapi-spec-validator), 3 súbory | PASS |
| operationId a paths v snake_case | PASS |
| Každá operation má Requirement, Application Service, Component, roly, rules, data objects, scenarios (`x-sdd`) | PASS |
| Všetky SC-ID existujú v US-001.feature | PASS |
| Každý scenár SC-001-01 … 11 je pokrytý | PASS |
| Každý prechod lifecycle má operation | PASS |
| Otvorené DECISION REQUIRED | žiadne |
| Všetky YAML v spec/ sa dajú načítať | PASS |

## Approval checklist (kapitola 9 pravidiel)

| Podmienka | Stav |
|---|---|
| Každá operation má business dôvod a Requirement ID | áno |
| Mapping na Application Service a Component | áno |
| Názvy podľa glossary | áno (model approval, revision, order, 3D model) |
| Pozitívne aj negatívne scenáre majú pozorovateľný výsledok | áno (stav, 409/429, order_can_be_fulfilled) |
| Rules, invariants a lifecycle sú vynútiteľné | áno (guards, roly) |
| Authentication, authorization, citlivé údaje explicitné | áno (bearer, allowed_roles, employee_ref) |
| Error behavior a súbeh | áno (problem-details, 409 – prvá požiadavka vyhráva) |
| Project policy dodržaná | áno |
| Breaking changes | n/a (prvá verzia) |
| Uzavreté DECISION REQUIRED | áno |

## Traceability summary

R-001 → SC-001-01 … 11 → operations (tabuľka vyššie) → AS / AC podľa `x-sdd`.
Záznamy operation → scenario sa doplnia do `traceability.yaml` po schválení (#15).

## Decision required / ADR

Žiadne otvorené DECISION REQUIRED. ADR netreba: contract nemení component boundary
ani technológiu; presun ownera DO-3DModel rozhodol človek priamo v spec.
