# Provider Test Suite Documentation

Diese Dokumentation beschreibt das umfassende Test-Framework für die vereinheitlichte Provider-Architektur im DynDNS Docker Client.

## 📋 Übersicht

Das Test-Framework besteht aus mehreren Komponenten:
- **Umfassende Provider-Tests** (`test_comprehensive_providers.py`)
- **GitHub Actions Workflow** (`.github/workflows/provider-tests.yml`)
- **Integrationstests** für reale Konfigurationen
- **Benachrichtigungstests** für alle Provider

## 🚀 Lokale Ausführung

### Alle Tests ausführen:
```bash
# Umfassende Provider-Tests
python test_comprehensive_providers.py

# Einzelne Test-Dateien
python -m pytest tests/test_provider_integration.py -v
python -m pytest tests/test_provider_unification.py -v

# Benachrichtigungstests
python test_notification_summary.py
```

### Mit Coverage-Report:
```bash
pip install coverage
coverage run test_comprehensive_providers.py
coverage report -m
coverage html  # Erzeugt HTML-Report in htmlcov/
```

## 🔄 GitHub Actions Integration

Der Workflow wird automatisch ausgeführt bei:
- **Push** auf `main`, `beta`, `develop` Branches
- **Pull Requests** auf `main`, `beta`
- **Manueller Auslösung** über GitHub UI

### Workflow-Jobs:

1. **test-providers**: Testet alle Provider-Funktionen auf Python 3.9-3.12
2. **test-coverage**: Erzeugt Code-Coverage-Reports
3. **integration-test**: Testet mit realen Konfigurationen
4. **security-test**: Führt Sicherheitsscans durch
5. **notify-results**: Fasst alle Ergebnisse zusammen

## 📊 Test-Kategorien

### 1. Provider-Architektur Tests (`TestProviderArchitecture`)
- ✅ Provider-Erstellung für alle Typen
- ✅ Feldname-Kompatibilität (`protocol` vs `type`)
- ✅ Groß-/Kleinschreibung von Protokollen
- ✅ Konfigurationsvalidierung
- ✅ IP-Validierungsfunktionen
- ✅ Benachrichtigungsfunktionalität
- ✅ Legacy-Provider-Kompatibilität
- ✅ Vereinheitlichte Provider-Updates
- ✅ Reale Konfigurationsformate
- ✅ Unbekannte Provider-Typen

### 2. Edge Cases Tests (`TestEdgeCases`)
- ✅ Leere und Null-Werte
- ✅ Gemischte Groß-/Kleinschreibung
- ✅ Sonderzeichen in Konfigurationen

## 🔧 Unterstützte Provider

### Cloudflare Provider
```yaml
- name: cloudflare-test
  protocol: cloudflare  # oder type: cloudflare
  zone: example.com
  api_token: your_token_here
  record_name: sub.example.com
```

### IPV64 Provider
```yaml
- name: ipv64-test
  protocol: ipv64  # oder type: ipv64
  auth_method: token
  token: your_token_here
  domain: example.com
```

### DynDNS2 Provider
```yaml
- name: dyndns2-test
  protocol: dyndns2  # oder type: dyndns2
  url: https://updates.example.org/api/
  auth_method: basic
  username: your_username
  password: your_password
  hostname: test.example.com
```

## 🛡️ Sicherheitstests

- **Bandit**: Scannt nach bekannten Sicherheitslücken
- **Safety**: Überprüft Dependencies auf Vulnerabilities
- **Automatische Security-Reports** in GitHub Actions

## 📈 Coverage-Ziele

- **Mindest-Coverage**: 85%
- **Provider-Klassen**: 95%+
- **Kritische Funktionen**: 100%

## 🐛 Debugging

### Bei Testfehlern:
1. Prüfe die detaillierte Ausgabe: `python test_comprehensive_providers.py`
2. Führe einzelne Tests aus: `python -m pytest tests/test_file.py::test_function -v`
3. Aktiviere Debug-Logging in der Config

### Bei GitHub Actions Fehlern:
1. Prüfe die Action-Logs im "Actions" Tab
2. Lade Test-Artifacts herunter für detaillierte Reports
3. Teste lokal mit derselben Python-Version

## 📝 Neue Tests hinzufügen

### Provider-Test hinzufügen:
```python
def test_new_functionality(self):
    """Test new functionality description."""
    # Test implementation
    provider = create_provider(test_config)
    result = provider.new_method()
    self.assertTrue(result)
```

### In GitHub Actions integrieren:
Tests werden automatisch erkannt, wenn sie:
- In `test_*.py` Dateien stehen
- Mit `test_` beginnen
- Unittest oder pytest Framework verwenden

## 🎯 Best Practices

1. **Immer testen**: Vor jedem Commit lokale Tests ausführen
2. **Mock externe Services**: Verwende `unittest.mock` für API-Calls
3. **Reale Configs testen**: Verwende `config.example.yaml` Formate
4. **Edge Cases abdecken**: Teste Fehlerszenarien und Randwerte
5. **Dokumentation aktuell halten**: Bei Änderungen README updaten

## 🔗 Weitere Ressourcen

- [GitHub Actions Dokumentation](https://docs.github.com/en/actions)
- [Python unittest Framework](https://docs.python.org/3/library/unittest.html)
- [Coverage.py Dokumentation](https://coverage.readthedocs.io/)
- [Bandit Security Linter](https://bandit.readthedocs.io/)

---

**Status**: ✅ Alle 12 Tests bestehen
**Letzte Aktualisierung**: $(date)
**Python-Versionen**: 3.9, 3.10, 3.11, 3.12
