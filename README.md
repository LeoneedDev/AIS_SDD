# AIS SDD – 3D model pre zákazku

Specification-Driven Development balík pre jednu end-to-end funkcionalitu:
**3D model pre zákazku – vytvorenie alebo schválenie modelu** (Requirement `R-001`).

Architektúra bola spracovaná po Layered Viewpoint v Sparx EA (model zostáva u tímu).
Tento repozitár obsahuje iba vybraný specification package, nie celý model.

## Štruktúra

| Cesta | Obsah |
|---|---|
| `AGENTS.md` | vstupný bod pre AI, pravidlá sú v `.agents/rules.md` |
| `spec/manifest.yaml` | obsah balíka: verzia, baseline, ktoré súbory sú autoritatívne |
| `spec/glossary.md` | jedna definícia pre každý business pojem |
| `spec/requirements/` | requirements, constraints, business rules, quality requirements |
| `spec/business/` | actors, processes, business scenarios |
| `spec/application/` | components, service realization, interactions, data objects, lifecycles |
| `spec/technology/` | technology a deployment context (ak je relevantný) |
| `spec/stories/` | user stories a Gherkin `features/` |
| `spec/architecture/` | obrázky views zo Sparx EA, ADR, continuum, migration, GAP |
| `spec/policies/` | contract design profile |
| `spec/contracts/` | `proposed/` (AI) a `approved/` (iba človek) |
| `spec/prompts/` | prompty pre režimy PREPARE_SPEC až VERIFY_CHANGE |
| `spec/traceability/` | trace väzby Goal, Requirement, ..., contract |
| `spec/drafts/` | pracovné návrhy AI, nie sú schválené |
| `src/pod/` | backend (FastAPI), jeden balík na Application Component |
| `src/portal_mock/` | mockup zákazníckeho portálu a chatu |
| `config/`, `docker-compose.yml` | konfigurácia a lokálny PostgreSQL |
| `tests/` | contract, architecture a acceptance tests (US-001.feature) |
| `reports/` | reporty DESIGN_CONTRACT, IMPLEMENT_CHANGE, VERIFY_CHANGE |

**Ukážka (demo mockupu): [docs/demo/README.md](docs/demo/README.md)**

## Spustenie

```bash
docker compose up -d                                  # PostgreSQL (pod + pod_test)
python -m venv .venv && .venv/Scripts/pip install -e ".[test]"
.venv/Scripts/python -m pytest                        # všetky testy
PYTHONPATH=src .venv/Scripts/python -m pod.dev_seed   # ukážkové objednávky + tokeny
PYTHONPATH=src .venv/Scripts/uvicorn pod.main:create_app --factory --reload
```

- Portál (mockup): http://127.0.0.1:8000/portal/ – vlož token a ID objednávky z `dev_seed`.
- OpenAPI jednotlivých API: `/api/modeling_workspace/docs`, `/api/model_validator/docs`,
  `/api/model_repository/docs`.
- Zástupný validátor: súbor so značkou `STUB:ERROR` neprejde, `STUB:TOO_LARGE` sa nezmestí
  (dá sa rozdeliť), `STUB:TOO_LARGE_UNSPLITTABLE` sa nezmestí ani po rozdelení.

## Postup

1. Doplniť miesta označené `✍️` v `spec/` a priložiť obrázky views do `spec/architecture/views/`.
2. `PREPARE_SPEC` – vyriešiť otázky a DECISION REQUIRED.
3. `DESIGN_CONTRACT` – človek schváli konkrétnu verziu contractu.
4. `IMPLEMENT_CHANGE` – candidate code a tests.
5. `VERIFY_CHANGE` – report a jeden pull request.

Harmonogram, effort, ocenenie a finančná analýza nie sú súčasťou tohto balíka.
