# Glossary

Každý dôležitý business pojem má jednu definíciu. Bez názvov tried a tabuliek.
Riadky „z modelu“ citujú prvok zo Sparx EA; definíciu vlastnými slovami potvrdí človek.

## Order (zákazka)

Objednávka (požiadavka) zákazníka na jeden diel na mieru; patrí k nej model, kontaktné údaje zákazníka a informácie o platbe.

- z modelu: Meaning „Customer commitment to buy one custom part“ (EA #1019) —Association→ BO-Order
- z modelu: Representation „Order confirmation (PDF / e-mail)“ (EA #1020) —Realization→ BO-Order
- IDs: BO-Order, DO-Order

## Prompt order

Objednávka, v ktorej zákazník dodá iba popis alebo schémy dielu; model vytvoríme my (VAR-1).

- z modelu: Junction „Who provides model?“ (EA #1093), Notes: „user also can ask us to create model for him based on description or schemas“
- z modelu: DO-PromptOrder —Specialization→ DO-Order
- IDs: DO-PromptOrder (cesta VAR-1)

## Model order

Objednávka, v ktorej zákazník dodá hotový 3D model; model iba overíme (VAR-2).

- z modelu: Junction „Who provides model?“, Notes: „If model is user provided we dont need create it or recreate it, only approve that this model is ok“
- z modelu: DO-ModelOrder —Specialization→ DO-Order, —Aggregation→ DO-3DModel
- IDs: DO-ModelOrder (cesta VAR-2)

## 3D model

Súbor 3D modelu dielu spolu s informáciami potrebnými pre 3D tlač (metadáta, rozmery).

- z modelu: Value „Part matches the approved model“ (EA #822)
- z modelu: ART-PartModelFile „Part model file (.stl)“ —Realization→ DO-3DModel
- IDs: BO-3DModel, DO-3DModel

## Model approval (schválenie modelu)

Súhlas zákazníka s konkrétnou revíziou modelu; v systéme ho reprezentuje aktuálny stav schválenia a história revízií.

- z modelu: Principle „Nothing is printed without customer approval“ (EA #667)
- z modelu: Value Stream stage „Approve the model“ (VS-01.4, EA #100)
- z modelu: Data Object „Model approval“ (EA #1113) —Association→ DO-3DModel
- z modelu: Business Process „Approve the model“ (EA #1115) – Clients, 3D modeler, Manager (Assignment)
- IDs: PRIN-001, BP-ApproveTheModel, AS-ApprovingModel, DO-ModelApproval
- Nezamieňať: technická kontrola modelu (AS-ApprovingModel, Model Validator) ≠ súhlas zákazníka

## Revision (revízia modelu)

Úprava modelu, ktorú na žiadosť zákazníka urobia naši 3D modelári (aj oprava chýb v modeli zákazníka). Prvé 2 revízie sú bezplatné; ďalšia úprava je vývoj nového modelu (BR-002). Ak zákazník sám nahrá nový model, nejde o revíziu (BR-004).

- z modelu: Contract „General terms (2 free model revisions, 14-day complaint)“ (EA #823)
- IDs: R-001
