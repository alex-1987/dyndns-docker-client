# File Logging Fix

## Problem

Trotz der Konfiguration `loglevel: INFO` wurden INFO-Nachrichten (wie IP-Updates) nicht in die Log-Datei geschrieben. Nur WARNING, ERROR und CRITICAL Nachrichten erschienen im Log.

Das betraf wichtige Ereignisse wie:
```
[INFO] MAIN --> Current public IP: 124.120.46.43
[INFO] MAIN --> New IP detected: 124.120.46.43 (previous: 124.120.45.154)
[INFO] CLOUDFLARE --> Provider 'cloudflare' updated successfully. New IP: 124.120.46.43
```

## Ursache

Die globale Variable `file_level` wurde nie korrekt gesetzt und hatte immer den Standardwert 'WARNING'. Dadurch wurden nur WARNING und höhere Level in die Log-Datei geschrieben, obwohl der Benutzer `loglevel: INFO` konfiguriert hatte.

**Problematischer Code:**
```python
# file_level wurde nie gesetzt
file_level = globals().get('file_level', 'WARNING')  # Immer 'WARNING'!
```

## Lösung

1. **Globale Variable hinzugefügt**: `file_level` als separate globale Variable
2. **Initialisierung korrigiert**: `file_level` wird jetzt korrekt aus der Konfiguration gesetzt
3. **Setup-Funktionen aktualisiert**: Sowohl `setup_logging()` als auch die Hot-Reload-Logik setzen `file_level`
4. **Standardwert geändert**: Von 'WARNING' auf 'INFO' für bessere Benutzerfreundlichkeit

**Korrigierter Code:**
```python
# Global variables
file_level = "INFO"  # Neuer Standardwert

def setup_logging(loglevel, config=None):
    global log_level, file_level, file_logger_instance
    log_level = loglevel
    file_level = loglevel  # Korrekte Zuweisung

# In main()
loglevel = config.get("loglevel", "INFO")
file_level = loglevel  # Explizite Zuweisung

# In Hot-Reload
new_loglevel = config.get("loglevel", "INFO")
file_level = new_loglevel  # Update bei Konfigurationsänderungen
```

## Verifikation

Ein Testskript bestätigt, dass die Korrektur funktioniert:
```
✅ Found expected message: Test INFO message
✅ Found expected message: Test WARNING message  
✅ Found expected message: Test ERROR message
✅ Correctly excluded message: Test DEBUG message
🎉 File logging test PASSED!
```

## Ergebnis

✅ **INFO-Nachrichten werden jetzt korrekt in die Log-Datei geschrieben**  
✅ **IP-Updates und Provider-Updates erscheinen im Log**  
✅ **Konfiguration `loglevel: INFO` funktioniert wie erwartet**  
✅ **Hot-Reload von Log-Level-Änderungen funktioniert**  
✅ **Alle bestehenden Tests (22/22) funktionieren weiterhin**

Ihre IP-Änderungs-Events werden jetzt ordnungsgemäß in `/app/config/dyndns.log` protokolliert!
