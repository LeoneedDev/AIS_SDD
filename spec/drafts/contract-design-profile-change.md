# Návrh zmeny contract-design-profile.yaml (QR-002)

Profil je approved, AI ho nemení. Ak s návrhom súhlasíš, nahraď v
`spec/policies/contract-design-profile.yaml` celú sekciu `security` týmto textom:

```yaml
  security:
    authentication: >
      Prehliadač: relácia v HttpOnly cookie pod_session (SameSite=Strict, 8 h),
      ktorú vytvorí prihlásenie loginom a heslom (auth-api). Ostatní klienti:
      rovnaký token v hlavičke Authorization: Bearer. 2FA neskôr (QR-001).
    authorization: "explicitne pre každú operáciu"
    csrf: "SameSite=Strict cookie"
```

Ostatné časti profilu sa nemenia.
