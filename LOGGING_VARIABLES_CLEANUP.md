# Logging Variables Cleanup

## Problem
Es gab drei Log-Level Variablen, was verwirrend war:
- `log_level` - für File Logging  
- `console_level` - für Console Logging
- `file_level` - redundant, gleiche Funktion wie `log_level`

## Lösung
Vereinfachung auf nur zwei Variablen:
- `log_level` - für File Logging (wird über `loglevel` in config.yaml gesetzt)
- `console_level` - für Console Logging (wird über `consolelevel` in config.yaml gesetzt)

## Resultat
✅ Klarere Struktur mit nur zwei globalen Log-Level Variablen
✅ `log_level` wird direkt für das File Logging verwendet 
✅ Keine redundanten Variablen mehr
✅ Alle Tests funktionieren weiterhin
✅ File Logging funktioniert korrekt mit INFO-Level

## Konfiguration
```yaml
loglevel: INFO       # Setzt log_level (File Logging)
consolelevel: INFO   # Setzt console_level (Console Logging)
```
