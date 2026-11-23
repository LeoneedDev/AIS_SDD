# ADR-002 Overenie bearer tokenu bez prihlasovacej služby

- Stav: Proposed
- Dátum: 2026-11-23
- Requirement: R-001, QR-001
- Policy: contract-design-profile.yaml (security.authentication)

## Kontext

Profil určuje bearer token, ktorý frontend získa pri prihlásení. Prihlásenie
(login, heslo, 2FA) nie je súčasťou contractu R-001.

## Rozhodnutie (návrh AI)

- API overuje JWT podpísaný HS256 tajomstvom `POD_JWT_SECRET`.
- Token nesie `sub` (ID zákazníka alebo zamestnanca), `role`
  (customer / modeler / manager) a pri zamestnancovi `nickname` (QR-001).
- Na vývoj a ukážku tokeny vydáva `python -m pod.dev_seed`; prihlasovacia
  služba sa doplní samostatnou zmenou.

## Dôsledky

- Autorizácia každej operation je explicitná (`allowed_roles` v contracte).
- Pred nasadením treba prihlasovaciu službu a bezpečné tajomstvo.

Rozhodnutie Accepted / Rejected zapisuje človek.
