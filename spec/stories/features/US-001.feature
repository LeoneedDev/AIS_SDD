Feature: Schválenie 3D modelu pre zákazku

  @SC-001-01 @R-001 @VAR-1 @BR-003
  Scenario: Zákazník schváli model vytvorený nami
    Given zákazník poslal zaplatenú objednávku s popisom dielu
    And 3D modelár vytvoril model a poslal ho zákazníkovi na schválenie
    When zákazník s modelom súhlasí
    And 3D modelár alebo manažér zaznamená jeho súhlas
    Then stav schválenia modelu je "approved"
    And model sa odovzdá ďalšiemu 3D modelárovi na kontrolu tlačiteľnosti

  @SC-001-05 @R-001 @VAR-1 @BR-002 @BR-007
  Scenario: Zákazník žiada úpravu v rámci bezplatných revízií
    Given zákazníkovi bol poslaný model na schválenie
    And zákazník zatiaľ využil menej ako 2 bezplatné revízie
    When zákazník žiada úpravu modelu
    Then stav schválenia modelu je "rejected"
    And model sa netlačí
    And model upraví náš 3D modelár
    And upravený model sa pošle zákazníkovi ako nová revízia na schválenie

  @SC-001-02 @R-001 @VAR-1 @BR-002
  Scenario: Bezplatné revízie sú vyčerpané
    Given zákazník už využil 2 bezplatné revízie modelu
    When zákazník žiada ďalšiu úpravu modelu
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
