# Contributing to Cryptocurrency Trading System

We verwelkomen bijdragen aan het Cryptocurrency Trading System! Dit document bevat richtlijnen voor het bijdragen aan dit project.

## Ontwikkelomgeving opzetten

1. Fork de repository
2. Clone je fork:
```bash
git clone https://github.com/jouw-username/crypto_trading_system.git
cd crypto_trading_system
```
3. Installeer de ontwikkelingsafhankelijkheden:
```bash
python setup.py
pip install pytest pytest-cov black flake8
```

## Codestijl

We volgen de PEP 8 codestijlrichtlijnen. Gebruik de volgende tools om je code te formatteren en te controleren:

- **Black**: Voor automatische codeformattering
  ```bash
  black .
  ```
- **Flake8**: Voor linting
  ```bash
  flake8 .
  ```

## Testen

Schrijf tests voor alle nieuwe functionaliteit. We gebruiken pytest voor het testen:

```bash
pytest
```

Voor testdekking:

```bash
pytest --cov=crypto_trading_system
```

## Pull Request Proces

1. Zorg ervoor dat je code voldoet aan de codestijlrichtlijnen
2. Zorg ervoor dat alle tests slagen
3. Update de documentatie indien nodig
4. Maak een pull request met een duidelijke beschrijving van de wijzigingen

## Branchstrategie

- `main`: Stabiele productieversie
- `develop`: Ontwikkelingsversie voor de volgende release
- Feature branches: Gebruik `feature/naam-van-feature` voor nieuwe functionaliteit

## Commit Berichten

Gebruik duidelijke en beschrijvende commit berichten:

```
[Component]: Korte beschrijving van de wijziging

Gedetailleerde beschrijving van de wijziging indien nodig.
```

Bijvoorbeeld:
```
[Analysis]: Voeg RSI indicator toe aan technische analyse

- Implementeert Relative Strength Index berekening
- Integreert RSI in scoring algoritme
- Voegt tests toe voor RSI functionaliteit
```

## Documentatie

Update de documentatie voor alle wijzigingen:

- Nieuwe functionaliteit moet worden gedocumenteerd in `docs/documentation.md`
- API wijzigingen moeten worden bijgewerkt in de betreffende docstrings
- Gebruikersinterface wijzigingen moeten worden bijgewerkt in de README

## Vragen?

Als je vragen hebt over het bijdrageproces, open dan een issue in de repository of neem contact op met de maintainers.

Bedankt voor je bijdrage aan het Cryptocurrency Trading System!
