# PREPARE_SPEC + DESIGN_CONTRACT – prihlásenie (QR-002)

## Pochopenie úlohy

Portál má mať prihlasovaciu stránku; relácia sa ukladá v HttpOnly cookie
namiesto ručného zadávania tokenu.

## Režim a specification baseline

- PREPARE_SPEC (rozhodnutia autora 2026-11-23 zapísané ako draft), potom DESIGN_CONTRACT
- Baseline 0.1.0; nadväzuje na approved contracts 0.2.0

## Rozhodnutia autora (2026-11-23)

| Otázka | Rozhodnutie |
|---|---|
| Kde uložiť token | HttpOnly cookie |
| Ktorý component | AC-CustomerPortal (zákazníci aj zamestnanci) |
| 2FA | neskôr, samostatnou zmenou |
| Dĺžka relácie | 8 hodín + odhlásenie |
| Ochrana pred hádaním hesla | zatiaľ nie |

## Zapísané do spec (draft)

| Súbor | Zmena |
|---|---|
| quality-requirements.yaml | nový QR-002 (status draft) |
| data-objects.yaml | nový DO-UserAccount (owner AC-CustomerPortal; v EA zatiaľ nie je) |
| components.yaml | AC-CustomerPortal: AS-Authentication, DO-UserAccount |
| glossary.md | Account, Session |
| stories/US-002.md, features/US-002.feature | SC-002-01 … 05 |
| drafts/contract-design-profile-change.md | návrh novej sekcie `security` (profil mení iba človek) |

## Navrhovaný výstup (spec/contracts/proposed/)

| Contract | Zmena |
|---|---|
| auth-api.v0.1.0.yaml (nový) | POST /sessions (create_session), GET /sessions/current (get_current_session), DELETE /sessions/current (delete_current_session) |
| model-approval-api.v0.3.0.yaml | iba pridaný alternatívny `cookie_auth` |
| model-repository-api.v0.3.0.yaml | iba pridaný alternatívny `cookie_auth` |
| model-validation-api.v0.3.0.yaml | iba pridaný alternatívny `cookie_auth` |

Zmena v 0.3.0 je spätne kompatibilná: Bearer ostáva, cookie je druhá možnosť.

## Validation results

| Kontrola | Výsledok |
|---|---|
| OpenAPI 3.1 syntax (4 súbory) | PASS |
| snake_case paths a operationId | PASS |
| Každá operation má mapping (QR, component, service, data object, scenáre) | PASS |
| Scenáre SC-002-01 … 05 pokryté | PASS |

## Decision required / ADR

- Ľudské schválenie: QR-002, zmena profilu, auth-api 0.1.0, contracts 0.3.0.
- Hash hesla: navrhujem `hashlib.scrypt` zo štandardnej knižnice Pythonu (bez novej
  závislosti) – zapíše sa do ADR-003 pri implementácii.
- Účty sa zakladajú vopred (`pod.dev_seed`), registrácia nie je v rozsahu.
