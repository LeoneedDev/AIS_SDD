Feature: Prihlásenie do portálu

  @SC-002-01 @QR-002
  Scenario: Zákazník sa prihlási správnym loginom a heslom
    Given zákazník má účet s loginom "anna" a heslom "Anna-heslo-1"
    When zákazník sa prihlási loginom "anna" a heslom "Anna-heslo-1"
    Then prehliadač dostane reláciu v HttpOnly cookie
    And zákazník vidí stav svojej objednávky bez zadávania tokenu

  @SC-002-02 @QR-002
  Scenario: Nesprávne heslo
    Given zákazník má účet s loginom "anna" a heslom "Anna-heslo-1"
    When zákazník sa prihlási loginom "anna" a heslom "zle-heslo"
    Then prihlásenie sa nepodarí so všeobecnou chybou
    And prehliadač nedostane reláciu

  @SC-002-03 @QR-002
  Scenario: Odhlásenie ukončí reláciu
    Given zákazník je prihlásený
    When zákazník sa odhlási
    Then jeho ďalšia požiadavka na objednávku je odmietnutá ako neprihlásená

  @SC-002-04 @QR-002
  Scenario: Relácia vyprší po 8 hodinách
    Given zákazník je prihlásený
    When uplynie viac ako 8 hodín od prihlásenia
    Then jeho ďalšia požiadavka na objednávku je odmietnutá ako neprihlásená

  @SC-002-05 @QR-002 @QR-001
  Scenario: Zamestnanec sa prihlási a pracuje podľa svojej roly
    Given 3D modelár má účet s loginom "jan.m" a heslom "Jan-heslo-1"
    When 3D modelár sa prihlási loginom "jan.m" a heslom "Jan-heslo-1"
    Then relácia patrí roli "modeler" s prezývkou "jan.m"
