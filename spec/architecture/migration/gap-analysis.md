# GAP Analysis

Status: MODELED IN EA (diagram "Gap Analysis" D62); prvky majú v EA status Proposed.

Porovnávané Plateaus:
- AS-IS: PL-ASIS (EA #1078)
- Transition: PL-TRANSITION (EA #1079)
- TO-BE: PL-TOBE (EA #1080)

## Gaps z modelu

| ID | Gap (EA #) | Súvisiaci Requirement (Association) | Plateaus (Association) |
|---|---|---|---|
| G1 | Missing company accounts and invoicing for business customers (#1063) | Company account with invoicing (#677) | AS-IS, Transition |
| G2 | Missing automatic price calculations for quoting (#1064) | Online ordering and quoting (#674) | AS-IS, Transition |
| G3 | Missing support for complaint handling and reprinting (#1067) | Complaint handling and reprint (14 days) (#673) | Transition, TO-BE |
| G4 | Missing tracking of material stock and its consumption (#1065) | Choosing materials for the print (#1070) | Transition, TO-BE |

## Návrh autora (mimo EA)

| ID | Gap | Stav |
|---|---|---|
| G5 | Objednávka s viacerými modelmi: odporúča sa rozdeliť ju na samostatné objednávky (jeden model = jedna objednávka), ak nejde o jeden spoločný diel. | návrh autora, v EA sa nemodeluje |

## Vzťah k tejto funkcionalite

Žiadny gap v modeli sa neviaže na R-001 (EA #671). Podľa šablóny teda GAP Analysis
túto zmenu neblokuje.

AI nesmie gaps ani z nich odvodené requirements vymyslieť.
