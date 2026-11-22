# Otvorené otázky (pracovný zoznam)

Tento súbor nahrádza komentáre `✍️` v spec/. Po zodpovedaní otázku zmaž a odpoveď
zapíš do príslušného súboru.

## Pred DESIGN_CONTRACT (blokujú contract)

| # | Súbor | Otázka |
|---|---|---|
| 1 | stories/features/US-001.feature | Skontrolovať draft 8 scenárov. |
| 2 | stories/US-001.md | Skontrolovať draft user story. |
| 3 | requirements/business-rules.yaml – BR-001, BR-008 | Potvrdiť znenie (VAR-1: approved; VAR-2: nezmenený model = súhlas). |
| 4 | requirements/requirements.yaml – R-001 | Platia 2 bezplatné revízie iba pre VAR-1, alebo aj pre VAR-2? Ak iba pre jednu cestu, odstrániť nadbytočný AS z `realized_by`. |
| 6 | policies/contract-design-profile.yaml | Formát API: napr. OpenAPI 3.1 (REST), formát chýb, autentifikácia; events (AsyncAPI) áno/nie. |

## Potvrdiť drafty

| # | Súbor | Otázka |
|---|---|---|
| 7 | requirements/business-rules.yaml – BR-003 | Potvrdiť znenie (súhlas dáva zákazník, zaznamená modelár alebo manažér). |
| 8 | requirements/business-rules.yaml – BR-004 | Počíta sa zmena modelu pred tlačou ako jedna z 2 revízií? |
| 9 | requirements/requirements.yaml – C-001 | Potvrdiť znenie (tlačíme iba modely v rámci parametrov našich tlačiarní). |
| 10 | requirements/quality-requirements.yaml – QR-001 | Vlastník? Návrh: SH-ManagementCEO. |
| 11 | architecture/migration/gap-analysis.md | Potvrdiť, že R-001 nie je dotknutý žiadnym gapom. |

## Menšie

| # | Súbor | Otázka |
|---|---|---|
| 12 | application/components.yaml – AC-ModelingWorkspace | `allowed_dependencies`: podľa interactions AC-ModelRepository, AC-CustomerPortal, AC-ModelValidator – zapísať? |
| 13 | glossary.md | Synonymá, ktoré nepoužívať (Order, 3D model). Možno vynechať. |
| 14 | manifest.yaml – supporting.architecture_views | Exportovať z EA ako PNG do `spec/architecture/views/`: D52 Layered, D64 Service Realization, D51 Application Usage, D50 Application Cooperation, D54 Application Structure, D47 Business Process Cooperation, D60 Information Structure, D48 Requirements Realization. Status „approved“ až po porovnaní s modelom. |
| 15 | traceability/traceability.yaml | Po contracte pridať operation → scenario (urobí AI). Väzby R-001 → SC-001-01…08 sú doplnené. |
