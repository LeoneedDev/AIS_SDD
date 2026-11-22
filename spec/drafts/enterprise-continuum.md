# Enterprise Continuum – PrintOnDemand (DRAFT)

Stav: návrh na kontrolu. Zdroj údajov: `spec/architecture/continuum/reuse-catalog.yaml`.

## 1. Architecture a Solutions Continuum

| Úroveň | Architecture Continuum (ABB) | Solutions Continuum (SBB) | Rozhodnutie |
|---|---|---|---|
| **Foundation** | ABB-01 Jednotný formát 3D modelov | SBB-01 STL + konverzia z iných formátov | upraviť |
| **Foundation** | ABB-02 Jeden zdroj pravdy o objednávke | SBB-02 Databáza objednávok | použiť |
| **Common Systems** | ABB-03 Ukladanie objednávok a údajov | SBB-03 PostgreSQL | použiť |
| **Common Systems** | ABB-04 Online platba | SBB-04 Platobná brána podľa regiónu | použiť |
| **Common Systems** | ABB-05 Prihlásenie zákazníka | SBB-05 Login + heslo, voliteľne 2FA (kód / TOTP) | použiť |
| **Common Systems** | ABB-06 Notifikácie zákazníka | SBB-06 Notifier + e-mail / SMS služba | použiť |
| **Industry** | ABB-07 Tvorba a úprava 3D modelu | SBB-07 FreeCAD | použiť |
| **Industry** | ABB-08 Príprava modelu na tlač | SBB-08 Slicer od výrobcu tlačiarne | použiť |
| **Industry** | ABB-09 Riadenie tlače | SBB-09 Univerzálne rozhranie tlačiarní + Print Scheduler | použiť |
| **Organization-Specific** | ABB-10 Ukladanie a opätovné použitie modelov | SBB-10 Model Repository nad PostgreSQL (súbory na serveri) | použiť |
| **Organization-Specific** | ABB-11 Overenie tlačiteľnosti modelu | SBB-11 Open-source validátory + vlastné pre naše tlačiarne | upraviť |
| **Organization-Specific** | ABB-12 Spoločná práca modelárov | SBB-12 GitLab – repozitár na každý model | upraviť |

**Vlastník:** manažér nad 3D modelármi (SH-Manager); ak nie je k dispozícii, CEO (SH-ManagementCEO).

**Zrelosť:** všetky SBB sú už v prevádzke (AS-IS). TO-BE môže priniesť vlastnú aplikáciu alebo rozhranie namiesto open-source riešenia, ak bude treba niečo pokročilejšie.

## 2. Páry ABB → SBB s odôvodnením

**ABB-11 Overenie tlačiteľnosti modelu → SBB-11 Open-source validátory + vlastné validátory**
Potrebujeme overiť, že model od zákazníka sa dá vytlačiť (rozmery, chyby geometrie).
Základnú kontrolu robia hotové open-source validátory, ktoré netreba vyvíjať. Každý typ
tlače (plast, kov, živica, …) a každá naša tlačiareň má však vlastné limity (C-001), preto
open-source riešenie **upravíme** vlastnými validátormi.

**ABB-12 Spoločná práca modelárov → SBB-12 GitLab – repozitár na každý model**
Modelári potrebujú spolupracovať na modeli, sledovať jeho revízie a stav. Model ako
samostatný repozitár s pull requestmi a issues dáva históriu zmien a kontrolu kvality
(ďalší modelár schvaľuje zmenu). Model je zároveň úloha (ticket), takže manažér vidí stav
všetkých modelov. Hotová platforma GitLab sa **upraví** pre prácu s 3D modelmi.

**ABB-10 Ukladanie a opätovné použitie modelov → SBB-10 Model Repository nad PostgreSQL**
Ak už model raz existuje, nemusíme ho vytvárať znova. Model Repository si pamätá, ku ktorej
objednávke model patril, a ponúkne ho ďalšiemu zákazníkovi, iba ak to pôvodný vlastník
povolil (BR-006). V PostgreSQL (SBB-03) sú údaje o modeli a cesta k súboru, samotné súbory sú uložené na serveri.

**ABB-01 Jednotný formát 3D modelov → SBB-01 STL + konverzia**
STL je rozšírený otvorený štandard, ktorý podporujú slicery aj validátory. Aby sme
neodmietali zákazníkov s inými formátmi, model do STL **skonvertujeme**.

## 3. Záznam o práci s AI

| Položka | Obsah |
|---|---|
| Nástroj | Claude Code (Opus 5.5) |
| Dátum | 2026-11-22 |
| Vstupy | model `EANEWExample.qea` (prvky a väzby), `spec/` súbory, odpovede autora v konverzácii |
| Postup | AI navrhlo zoznam ABB/SBB kandidátov z prvkov modelu (Postgresql, CAD, Slicer, Payment API, Model Repository, …). Autor ku každému uviedol zdroj, štandard a rozhodnutie. |
| Odpovede AI | návrh tabuľky, klasifikácia do úrovní, otvorené otázky; neznáme údaje označené UNKNOWN |
| Rozhodnutia človeka | zdroj a rozhodnutie (použiť / upraviť) pri všetkých 12 SBB |
| Rozhodnutia človeka (doplnené) | CAD = FreeCAD; Modeling Workspace = GitLab; súbory modelov na serveri, v PostgreSQL cesta k nim; všetky SBB AS-IS |
| Rozhodnutia človeka (vlastník) | vlastník SBB je manažér nad 3D modelármi; ak nie je k dispozícii, CEO |
| Ponechané ako UNKNOWN | verzie produktov; poskytovatelia platieb, e-mailu a SMS – líšia sa podľa krajiny (agregátory) |
