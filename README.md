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
| `src/`, `config/`, `tests/` | realizácia – vznikne až v IMPLEMENT_CHANGE |
| `reports/` | validation reporty z VERIFY_CHANGE |

## Postup

1. Doplniť miesta označené `✍️` v `spec/` a priložiť obrázky views do `spec/architecture/views/`.
2. `PREPARE_SPEC` – vyriešiť otázky a DECISION REQUIRED.
3. `DESIGN_CONTRACT` – človek schváli konkrétnu verziu contractu.
4. `IMPLEMENT_CHANGE` – candidate code a tests.
5. `VERIFY_CHANGE` – report a jeden pull request.

Harmonogram, effort, ocenenie a finančná analýza nie sú súčasťou tohto balíka.
