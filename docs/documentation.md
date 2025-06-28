# Uitgebreide Documentatie - Cryptocurrency Trading System

## 1. Systeemoverzicht

Het Cryptocurrency Trading System is een geavanceerd platform dat geautomatiseerde analyse en handel in cryptocurrencies mogelijk maakt. Het systeem combineert verschillende analysemethoden om handelssignalen te genereren en biedt een futuristische gebruikersinterface voor visualisatie en interactie.

### 1.1 Kernfunctionaliteiten

- **Multi-factor Analyse**: Combineert technische indicatoren, marktsentiment, marktgegevens en projectfundamentals
- **Geautomatiseerde Handelssignalen**: Genereert BUY/SELL signalen op basis van gecombineerde analyse
- **Futuristisch 3D Dashboard**: Moderne visualisaties met neon-elementen
- **Demo & Live Modus**: Test zonder risico of handel met echte assets
- **Coinbase Integratie**: Verbinding met een van de grootste cryptocurrency exchanges

## 2. Architectuur

Het systeem is opgebouwd uit verschillende modulaire componenten die samenwerken:

### 2.1 Analyse Module

De analyse module bestaat uit vier submodules:

1. **Technische Analyse**: Berekent technische indicatoren zoals RSI, MACD, Moving Averages en Bollinger Bands
2. **Sentiment Analyse**: Verzamelt en analyseert marktsentiment via de Fear & Greed Index
3. **Marktgegevens Analyse**: Analyseert marktgegevens zoals volume, liquiditeit en marktkapitalisatie
4. **Project Fundamentals Analyse**: Beoordeelt fundamentele aspecten van cryptocurrencies zoals ontwikkelingsactiviteit en community engagement

Deze analyses worden gecombineerd door de **Orchestrator** die een gewogen score en handelssignaal genereert.

### 2.2 Trading Module

De trading module is verantwoordelijk voor:

1. **Signaalverwerking**: Interpreteren van handelssignalen
2. **Risicobeheer**: Toepassen van stop-loss en take-profit strategieën
3. **Orderuitvoering**: Plaatsen van orders via de Coinbase API
4. **Portfoliobeheer**: Bijhouden van open posities en portfolio prestaties

### 2.3 UI Module

De UI module biedt een futuristische gebruikersinterface met:

1. **3D Visualisaties**: Geavanceerde grafieken en datavisualisaties
2. **Neon Kleurenschema**: Modern en futuristisch ontwerp
3. **Interactieve Elementen**: Gebruiksvriendelijke besturingselementen
4. **Real-time Updates**: Live prijzen en analyses

## 3. Installatie & Configuratie

### 3.1 Systeemvereisten

- Python 3.8 of hoger
- Internetverbinding
- Coinbase account (voor live handel)

### 3.2 Installatiestappen

1. Clone de repository:
```bash
git clone https://github.com/yourusername/crypto_trading_system.git
cd crypto_trading_system
```

2. Installeer de benodigde packages:
```bash
python setup.py
```

3. Configureer de omgevingsvariabelen:
```bash
cp .env.template .env
# Bewerk .env en voeg je API keys toe
```

### 3.3 Configuratie-opties

In het `.env` bestand kun je de volgende instellingen configureren:

- `COINBASE_API_KEY`: Je Coinbase API key
- `COINBASE_API_SECRET`: Je Coinbase API secret
- `DEMO_MODE`: True/False om demo modus in te schakelen
- `LOG_LEVEL`: Logging niveau (INFO, DEBUG, etc.)
- `DEMO_PORTFOLIO_VALUE`: Startwaarde voor demo portfolio
- `MAX_POSITION_SIZE_PERCENT`: Maximaal percentage van portfolio per positie
- `STOP_LOSS_PERCENT`: Percentage voor stop-loss orders
- `TAKE_PROFIT_PERCENT`: Percentage voor take-profit orders

## 4. Gebruikshandleiding

### 4.1 Dashboard Starten

```bash
python run_dashboard.py
```

Het dashboard is toegankelijk via `http://localhost:8050` in je browser.

### 4.2 Analyse Uitvoeren

```bash
python run.py --analyze --symbols BTC-USD ETH-USD
```

Dit commando analyseert de opgegeven cryptocurrencies en slaat de resultaten op in de data directory.

### 4.3 Handel Uitvoeren

In demo modus:
```bash
python run.py --analyze --trade --demo --symbols BTC-USD
```

In live modus:
```bash
python run.py --analyze --trade --symbols BTC-USD
```

### 4.4 Dashboard Gebruiken

1. **Cryptocurrency Selecteren**: Kies een cryptocurrency uit de dropdown
2. **Tijdsperiode Selecteren**: Kies een tijdsperiode (24u, 7d, 30d, 90d)
3. **Analyse Uitvoeren**: Klik op "ANALYZE NOW" om een nieuwe analyse te starten
4. **Handel Uitvoeren**: Klik op "EXECUTE TRADE" om een order te plaatsen op basis van het huidige signaal

## 5. Technische Details

### 5.1 Analyse Algoritmes

#### 5.1.1 Technische Indicatoren

- **RSI (Relative Strength Index)**: Meet overkocht/oververkocht condities
- **MACD (Moving Average Convergence Divergence)**: Identificeert momentum en trendveranderingen
- **Moving Averages**: Identificeert trends op verschillende tijdschalen
- **Bollinger Bands**: Meet volatiliteit en potentiële prijsniveaus

#### 5.1.2 Sentiment Analyse

- **Fear & Greed Index**: Meet marktsentiment op een schaal van 0-100
- **Social Media Sentiment**: Analyseert sentiment op sociale media platforms

#### 5.1.3 Marktgegevens Analyse

- **Volume Analyse**: Beoordeelt handelsvolume en veranderingen
- **Liquiditeit Metrics**: Meet marktdiepte en liquiditeit
- **Marktkapitalisatie**: Analyseert veranderingen in marktkapitalisatie

#### 5.1.4 Project Fundamentals

- **Ontwikkelingsactiviteit**: Meet GitHub commits en ontwikkelingsactiviteit
- **Community Engagement**: Beoordeelt community groei en activiteit
- **Tokenomics**: Analyseert token distributie en economisch model

### 5.2 Scoring Algoritme

Het scoring algoritme combineert alle analyses met de volgende gewichten:

- Technische Analyse: 40%
- Sentiment Analyse: 20%
- Marktgegevens: 25%
- Project Fundamentals: 15%

De uiteindelijke score wordt vertaald naar een van de volgende signalen:
- STRONG_BUY: Score > 0.7
- BUY: Score tussen 0.3 en 0.7
- NEUTRAL: Score tussen -0.3 en 0.3
- SELL: Score tussen -0.7 en -0.3
- STRONG_SELL: Score < -0.7

### 5.3 Handelslogica

De handelsengine gebruikt de volgende regels:

1. Koop alleen als er geen bestaande positie is
2. Verkoop alleen als er een bestaande positie is
3. Positiegrootte wordt bepaald door portfolio waarde en risico-instellingen
4. Stop-loss en take-profit orders worden automatisch geplaatst

## 6. Aanpassen en Uitbreiden

### 6.1 Nieuwe Indicatoren Toevoegen

Om een nieuwe technische indicator toe te voegen:

1. Open `src/analysis/technical.py`
2. Voeg een nieuwe methode toe die de indicator berekent
3. Voeg de indicator toe aan de `analyze_technical` methode
4. Update de gewichten in de scoring berekening

### 6.2 Dashboard Aanpassen

Om het dashboard aan te passen:

1. Open `src/ui/dashboard.py`
2. Wijzig de layout, kleuren of componenten
3. Voeg nieuwe visualisaties toe met Plotly

### 6.3 Handelsstrategieën Aanpassen

Om handelsstrategieën aan te passen:

1. Open `src/trading/engine.py`
2. Wijzig de `execute_signal` methode
3. Pas risicobeheer parameters aan in `src/config/settings.py`

## 7. Probleemoplossing

### 7.1 Veelvoorkomende Problemen

1. **API Verbindingsproblemen**
   - Controleer je internetverbinding
   - Verifieer dat je API keys correct zijn
   - Controleer of de Coinbase API beschikbaar is

2. **Dashboard Laadt Niet**
   - Controleer of alle dependencies zijn geïnstalleerd
   - Controleer of poort 8050 beschikbaar is
   - Controleer de logs voor foutmeldingen

3. **Analyse Fouten**
   - Controleer of de data directory bestaat en schrijfbaar is
   - Controleer of de cryptocurrency symbolen geldig zijn
   - Controleer de logs voor specifieke foutmeldingen

### 7.2 Logging

Logs worden opgeslagen in de `logs` directory. Het log niveau kan worden ingesteld in het `.env` bestand.

## 8. Toekomstige Ontwikkelingen

Geplande verbeteringen voor toekomstige versies:

1. **Machine Learning Modellen**: Implementatie van ML voor verbeterde voorspellingen
2. **Meer Exchanges**: Integratie met andere cryptocurrency exchanges
3. **Backtesting Module**: Uitgebreide backtesting functionaliteit
4. **Mobile App**: Mobiele versie van het dashboard
5. **Geavanceerde Visualisaties**: Meer 3D en interactieve visualisaties

## 9. Bijdragen

Bijdragen aan dit project zijn welkom! Volg deze stappen:

1. Fork de repository
2. Maak een feature branch
3. Commit je wijzigingen
4. Push naar de branch
5. Open een Pull Request

## 10. Licentie

Dit project is beschikbaar onder de MIT licentie.
