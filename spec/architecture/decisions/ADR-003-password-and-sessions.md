# ADR-003 Ukladanie hesiel a relácie

- Stav: Proposed
- Dátum: 2026-11-23
- Requirement: R-001, QR-001, QR-002
- Contract: auth-api 0.1.0, model-*-api 0.3.0 (approved)

## Kontext

QR-002 vyžaduje prihlásenie loginom a heslom, reláciu v HttpOnly cookie na 8 hodín
a odhlásenie. Heslo sa ukladá iba ako hash.

## Rozhodnutie (návrh AI)

- Hash hesla: `hashlib.scrypt` zo štandardnej knižnice Pythonu (n=2^14, r=8, p=1,
  16 B náhodná soľ) – bez novej závislosti; porovnanie v konštantnom čase.
- Relácia: záznam na serveri (`login_sessions`) + podpísaný JWT s `sid` a `exp`
  v cookie `pod_session` (HttpOnly, SameSite=Strict, Max-Age 8 h).
  Odhlásenie zruší záznam na serveri, takže skopírovaný token už neplatí.
- Bearer token bez relácie (`pod.dev_seed`, testy) zostáva iba na vývoj.

## Dôsledky

- 2FA a obmedzenie nesprávnych pokusov sa doplnia neskôr (QR-002).
- Pri nasadení cez HTTPS treba zapnúť `POD_COOKIE_SECURE=true`.

Rozhodnutie Accepted / Rejected zapisuje človek.
