# 📁 Projekt-Struktur

## Ordner-Organisation

```
dyndns-docker-client/
├── 📂 .github/workflows/     # GitHub Actions CI/CD
├── 📂 config/               # Konfigurationsdateien
│   └── config.example.yaml  # Beispiel-Konfiguration
├── 📂 docs/                 # Dokumentation
│   ├── TESTING.md          # Test-Dokumentation
│   ├── CODE_IMPROVEMENT_ROADMAP.md
│   ├── PROVIDER_UNIFICATION_SUMMARY.md
│   ├── STATE_REFACTORING_SUMMARY.md
│   ├── CODE_OF_CONDUCT.md
│   ├── CONTRIBUTING
│   └── SECURITY.md
├── 📂 scripts/             # Utility-Scripts
│   └── commit_provider_unification.sh
├── 📂 tests/               # Alle Test-Dateien
│   ├── test_comprehensive_providers.py  # Umfassende Provider-Tests
│   ├── test_notification_summary.py     # Benachrichtigungstests
│   ├── test_provider_integration.py     # Integration Tests
│   ├── test_provider_unification.py     # Provider-Vereinheitlichung
│   ├── test_real_world_config.py        # Reale Konfigurations-Tests
│   ├── test_basic_fixed.py              # Basis-Tests
│   ├── test_dyndns.py                   # DynDNS-Tests
│   ├── test_provider_config_mock.py     # Mock-Tests
│   ├── test_provider_creation.py        # Provider-Erstellung
│   └── test_state_refactoring.py        # State-Refactoring
├── 📄 update_dyndns.py     # Haupt-Anwendung
├── 📄 notify.py           # Benachrichtigungssystem
├── 📄 requirements.txt    # Python-Abhängigkeiten
├── 📄 Dockerfile         # Docker-Container
├── 📄 README.md          # Projekt-Hauptdokumentation
├── 📄 README.de.md       # Deutsche Dokumentation
└── 📄 LICENSE            # Lizenz
```

## 🎯 Warum diese Struktur?

### ✅ Vorteile:
- **Übersichtlich**: Alle zusammengehörigen Dateien in eigenen Ordnern
- **Wartbar**: Klare Trennung zwischen Code, Tests und Dokumentation
- **Skalierbar**: Einfaches Hinzufügen neuer Tests oder Dokumentation
- **Standard**: Entspricht Python/GitHub-Konventionen

### 📂 Ordner-Zwecke:

**`tests/`** - Alle Test-Dateien
- Komplette Test-Suite für Provider-Architektur
- Integration Tests mit realen Konfigurationen
- Mock-Tests für externe Services
- Benachrichtigungstests

**`docs/`** - Dokumentation
- Technische Dokumentation
- Entwicklungsrichtlinien
- Sicherheitsrichtlinien
- Beitragsleitfäden

**`config/`** - Konfigurationen
- Beispiel-Konfigurationen
- Template-Dateien
- Umgebungseinstellungen

**`scripts/`** - Utility-Scripts
- Git-Commit-Helfer
- Deployment-Scripts
- Maintenance-Tools

## 🚀 Verwendung

### Tests ausführen:
```bash
# Alle Tests
python -m pytest tests/ -v

# Umfassende Provider-Tests
python tests/test_comprehensive_providers.py

# Benachrichtigungstests
python tests/test_notification_summary.py
```

### Dokumentation:
```bash
# Test-Dokumentation
docs/TESTING.md

# Projekt-Roadmap
docs/CODE_IMPROVEMENT_ROADMAP.md
```

### Konfiguration:
```bash
# Beispiel-Config kopieren
cp config/config.example.yaml config/config.yaml
```

## 🔄 CI/CD Integration

GitHub Actions erkennt automatisch:
- Alle Tests in `tests/`
- Dokumentation in `docs/`
- Konfigurationen in `config/`

Die Ordnerstruktur ist vollständig mit dem GitHub Actions Workflow kompatibel.
