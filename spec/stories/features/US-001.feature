Feature: Schválenie 3D modelu pre zákazku

  @SC-001-01 @R-001 @VAR-1 @BR-003
  Scenario: Zákazník schváli model vytvorený nami
    Given zákazník poslal zaplatenú objednávku s popisom dielu
    And 3D modelár vytvoril model a poslal ho zákazníkovi na schválenie
    When zákazník model otvorí v portáli
    And zákazník v portáli potvrdí, že s modelom súhlasí
    Then stav schválenia modelu je "approved"
    And model sa odovzdá ďalšiemu 3D modelárovi na kontrolu tlačiteľnosti

  @SC-001-05 @R-001 @VAR-1 @BR-002 @BR-003 @BR-007
  Scenario: Zákazník nesúhlasí s modelom v rámci bezplatných revízií
    Given zákazníkovi bol poslaný model na schválenie
    And zákazník zatiaľ využil menej ako 2 bezplatné revízie
    When zákazník v portáli nesúhlasí s modelom a uvedie komentár
    Then stav schválenia modelu je "rejected"
    And model sa netlačí
    And model upraví náš 3D modelár
    And upravený model sa pošle zákazníkovi ako nová revízia na schválenie

  @SC-001-02 @R-001 @VAR-1 @BR-002 @BR-003
  Scenario: Bezplatné revízie sú vyčerpané
    Given zákazník už využil 2 bezplatné revízie modelu
    When zákazník s modelom znova nesúhlasí
    Then stav schválenia modelu je "closed_new_development"
    And zákazník dostane informáciu, že ďalšia úprava je nový platený vývoj modelu
    And pre nový model sa vytvorí nový záznam schválenia

  @SC-001-06 @R-001 @VAR-1 @BR-006
  Scenario: Použije sa existujúci model, ktorý vlastník povolil zdieľať
    Given v repozitári existuje overený model zodpovedajúci popisu zákazníka
    And pôvodný zákazník povolil zdieľanie tohto modelu
    When 3D modelár spracúva novú objednávku s popisom
    Then existujúci model sa pošle zákazníkovi na schválenie bez nového modelovania

  @SC-001-07 @R-001 @VAR-1 @BR-006
  Scenario: Existujúci model bez súhlasu so zdieľaním sa nepoužije
    Given v repozitári existuje overený model zodpovedajúci popisu zákazníka
    And pôvodný zákazník nepovolil zdieľanie tohto modelu
    When 3D modelár spracúva novú objednávku s popisom
    Then existujúci model sa novému zákazníkovi neponúkne
    And 3D modelár vytvorí nový model

  @SC-001-08 @R-001 @VAR-1 @BR-005
  Scenario: Schválený model neprejde kontrolou tlačiteľnosti
    Given zákazník schválil model vytvorený nami
    When kontrola tlačiteľnosti nájde v modeli chybu
    Then model sa netlačí
    And model sa vráti 3D modelárovi na prepracovanie

  @SC-001-03 @R-001 @VAR-2 @BR-008
  Scenario: Model od zákazníka je možné vytlačiť
    Given zákazník poslal zaplatenú objednávku s vlastným 3D modelom
    When validátor pre zvolený typ tlače overí model
    And model nemá žiadne chyby
    Then zákazník dostane notifikáciu, že model je v poriadku
    And model sa odovzdá do tlače bez ďalšieho potvrdenia zákazníkom

  @SC-001-04 @R-001 @VAR-2 @BR-005
  Scenario: Model od zákazníka obsahuje chyby
    Given zákazník poslal zaplatenú objednávku s vlastným 3D modelom
    When validátor pre zvolený typ tlače nájde v modeli chyby
    Then model sa netlačí
    And zákazník dostane notifikáciu so zoznamom chýb
    And zákazník je opýtaný, či chce, aby sme model opravili
    And bez súhlasu zákazníka sa model neupravuje

  @SC-001-09 @R-001 @C-001 @BR-009
  Scenario: Príliš veľký model sa rozdelí na časti so súhlasom zákazníka
    Given model je schválený a je príliš veľký na tlač v celku
    And slicer ho dokáže rozdeliť na časti
    When zákazníka sa opýtame, či súhlasí s rozdelením modelu
    And zákazník s rozdelením súhlasí
    Then model sa rozdelí na časti a časti sa vytlačia samostatne

  @SC-001-10 @R-001 @C-001 @BR-009
  Scenario: Zákazník nesúhlasí s rozdelením príliš veľkého modelu
    Given model je schválený a je príliš veľký na tlač v celku
    When zákazníka sa opýtame, či súhlasí s rozdelením modelu
    And zákazník s rozdelením nesúhlasí
    Then model sa nerozdelí ani nevytlačí
    And zákazník dostane informáciu, že model v celku nevieme vytlačiť a objednávku nevieme vykonať

  @SC-001-11 @R-001 @VAR-2 @BR-004
  Scenario: Zákazník prekročí limit vlastných nahraní modelu
    Given zákazník v sledovanom období už 10-krát nahral nový vlastný model
    When zákazník nahrá ďalší model
    Then model sa neoverí
    And zákazník dostane informáciu, že ďalšie overenie je za doplatok
