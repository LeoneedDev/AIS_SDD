# Glossary

Každý dôležitý business pojem má jednu definíciu. Bez názvov tried a tabuliek.
Riadky „z modelu“ citujú prvok zo Sparx EA; definíciu vlastnými slovami potvrdí človek.

## Order (zákazka)

✍️ definícia (1–2 vety)

- z modelu: Meaning „Customer commitment to buy one custom part“ (EA #1019) —Association→ BO-Order
- z modelu: Representation „Order confirmation (PDF / e-mail)“ (EA #1020) —Realization→ BO-Order
- IDs: BO-Order, DO-Order
- Nepoužívať ako synonymum: ✍️

## Prompt order

✍️ definícia

- z modelu: Junction „Who provides model?“ (EA #1093), Notes: „user also can ask us to create model for him based on description or schemas“
- z modelu: DO-PromptOrder —Specialization→ DO-Order
- IDs: DO-PromptOrder (cesta VAR-1)

## Model order

✍️ definícia

- z modelu: Junction „Who provides model?“, Notes: „If model is user provided we dont need create it or recreate it, only approve that this model is ok“
- z modelu: DO-ModelOrder —Specialization→ DO-Order, —Aggregation→ DO-3DModel
- IDs: DO-ModelOrder (cesta VAR-2)

## 3D model

✍️ definícia

- z modelu: Value „Part matches the approved model“ (EA #822)
- z modelu: ART-PartModelFile „Part model file (.stl)“ —Realization→ DO-3DModel
- IDs: BO-3DModel, DO-3DModel
- Nepoužívať ako synonymum: ✍️ (napr. „súbor“, „G-code“ – G-code je samostatný DO, EA #967)

## Model approval (schválenie modelu)

✍️ definícia

- z modelu: Principle „Nothing is printed without customer approval“ (EA #667)
- z modelu: Value Stream stage „Approve the model“ (VS-01.4, EA #100)
- IDs: PRIN-001, AS-ApprovingModel

## Revision (revízia modelu)

✍️ Čo sa počíta ako revízia a kedy sa bezplatná revízia minie.

- z modelu: Contract „General terms (2 free model revisions, 14-day complaint)“ (EA #823)
- IDs: R-001
