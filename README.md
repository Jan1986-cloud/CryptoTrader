# Cryptocurrency Trading System

Een volledig geautomatiseerd cryptocurrency handelssysteem met real-time monitoring, geautomatiseerde besluitvorming en live handelsuitvoering.

## Overzicht

Dit systeem monitort continu alle verhandelbare cryptocurrencies, analyseert marktgegevens, neemt automatisch handelsbeslissingen en voert trades uit voor maximaal rendement. Het combineert technische analyse, sentiment analyse, marktgegevens en risicobeheer in één geïntegreerd systeem.

## 🚀 Nieuwe Automatiseringsfuncties

### Volledig Geautomatiseerd Handelen
- **Real-time Monitoring**: Monitort alle verhandelbare coins elk uur/dag/week
- **Automatische Besluitvorming**: Kiest automatisch de beste handelsmogelijkheden
- **Live Handelsuitvoering**: Voert trades automatisch uit via Coinbase API
- **Portfolio Management**: Beheert posities op basis van percentages van portfolio waarde
- **Risicobeheer**: Automatische stop-losses en portfolio optimalisatie

### Kernfunctionaliteiten
- **Geautomatiseerde Analyse**: Analyseert alle factoren die cryptoprijzen beïnvloeden
- **Handelssignalen**: Genereert en voert automatisch BUY/SELL signalen uit
- **Futuristisch Dashboard**: 3D visualisaties met neon kleuren
- **1-uurs Tijdsframe**: Snelle analyse voor altcoin trading
- **Portfolio Percentage Management**: Maximale inzet per positie configureerbaar
- **Risk Management**: Stop-losses, position sizing, en dagelijkse verlieslimieten
- **Coinbase Integratie**: Volledige API integratie voor live trading

## Automatisch Handelen Starten

### Snelle Start
```bash
# Start het volledig geautomatiseerde systeem
python run_automated_trader.py

# Met aangepaste instellingen
python run_automated_trader.py --max-position 0.05 --max-invested 0.6 --interval 1800
```

### Configuratie Opties
- `--interval`: Analyse interval in seconden (standaard: 3600 = 1 uur)
- `--max-position`: Maximaal percentage per positie (standaard: 0.1 = 10%)
- `--max-invested`: Maximaal geïnvesteerd percentage (standaard: 0.8 = 80%)
- `--min-confidence`: Minimum vertrouwen voor trades (standaard: 0.75 = 75%)
- `--demo`: Demo modus voor testen

### Voorbeeld Configuraties

**Conservatief (Veilig)**:
```bash
python run_automated_trader.py --max-position 0.05 --max-invested 0.5 --min-confidence 0.85
```

**Agressief (Hoog Rendement)**:
```bash
python run_automated_trader.py --max-position 0.15 --max-invested 0.9 --min-confidence 0.7 --interval 1800
```

**Snelle Altcoin Trading**:
```bash
python run_automated_trader.py --interval 900 --max-position 0.08 --min-confidence 0.8
```

## Railway Deployment (Aanbevolen)

### Stap 1: GitHub Repository
1. Fork of clone deze repository naar je eigen GitHub account
2. Zorg ervoor dat alle bestanden aanwezig zijn (Procfile, railway.json, requirements.txt)

### Stap 2: Railway Setup
1. Ga naar [Railway.app](https://railway.app) en maak een account aan
2. Klik op "New Project" en selecteer "Deploy from GitHub repo"
3. Selecteer je cryptocurrency trading system repository
4. Railway detecteert automatisch de Python applicatie en gebruikt de Procfile

### Stap 3: Environment Variables
Voeg de volgende environment variables toe in Railway:
```
COINBASE_API_KEY=your_coinbase_api_key
COINBASE_API_SECRET=your_coinbase_api_secret
COINBASE_API_PASSPHRASE=your_coinbase_passphrase
DEBUG=False
DEMO_MODE=False
```

### Stap 4: Deploy
Railway zal automatisch deployen. Je krijgt een publieke URL voor je dashboard.

## Lokale Installatie

1. Clone de repository:
```bash
git clone https://github.com/yourusername/crypto_trading_system.git
cd crypto_trading_system
```

2. Installeer de benodigde packages:
```bash
pip install -r requirements.txt
```

3. Maak een `.env` bestand aan op basis van het template:
```bash
cp .env.template .env
```

4. Vul je API keys in het `.env` bestand in:
```
COINBASE_API_KEY=your_coinbase_api_key
COINBASE_API_SECRET=your_coinbase_api_secret
COINBASE_API_PASSPHRASE=your_coinbase_passphrase
DEMO_MODE=False
```

## Gebruik

### Dashboard (Monitoring)
```bash
python run_dashboard.py
```
Het dashboard is toegankelijk via `http://localhost:8050`

### Volledig Geautomatiseerd Handelen
```bash
python run_automated_trader.py
```

### Validatie Tests
```bash
python validate_automation.py
```

## Projectstructuur

```
crypto_trading_system/
├── crypto_trading_system/src/    # Hoofdcode
│   ├── automation/               # Automatisering modules
│   │   ├── monitor.py           # Real-time monitoring
│   │   ├── decision_engine.py   # Geautomatiseerde besluitvorming
│   │   ├── trade_executor.py    # Live handelsuitvoering
│   │   ├── risk_manager.py      # Risicobeheer
│   │   └── auto_trader.py       # Hoofdorchestrator
│   ├── analysis/                # Analyse modules
│   ├── api/                     # API clients
│   ├── models/                  # Data modellen
│   ├── trading/                 # Trading engine
│   ├── ui/                      # Dashboard UI
│   └── utils/                   # Hulpfuncties
├── run_automated_trader.py      # Start automatisch handelen
├── run_dashboard.py             # Start dashboard
├── validate_automation.py       # Validatie tests
├── requirements.txt             # Python dependencies
├── Procfile                     # Railway deployment
├── railway.json                 # Railway configuratie
└── README.md                    # Deze documentatie
```

## Veiligheid en Risicobeheer

Het systeem bevat uitgebreide veiligheidsfuncties:

- **Stop-Loss Orders**: Automatische bescherming tegen grote verliezen
- **Position Sizing**: Beperkt risico per positie
- **Daily Loss Limits**: Stopt handelen bij dagelijkse verlieslimieten
- **Portfolio Diversificatie**: Voorkomt overconcentratie in één asset
- **Demo Mode**: Test het systeem zonder echte trades

## Monitoring en Controle

- **Real-time Status**: Continu monitoring van systeemstatus
- **Performance Metrics**: Tracking van rendement en succes ratio
- **Risk Alerts**: Waarschuwingen bij risicosituaties
- **Emergency Stop**: Onmiddellijke stop van alle activiteiten

## GitHub Workflow voor AI-tools

Dit project is gestructureerd om gemakkelijk te bewerken met AI-tools:

### Aanpassingen maken
1. **Via GitHub Web Interface**: Bewerk bestanden direct in de browser
2. **Via AI-tools**: Upload bestanden naar AI-tools voor modificatie
3. **Lokale ontwikkeling**: Clone, bewerk, en push terug naar GitHub

### Automatische Deployment
Elke push naar de main branch triggert automatisch een nieuwe deployment op Railway.

## Support

Voor vragen of problemen:
1. Check de logs in het dashboard
2. Run `validate_automation.py` voor diagnostiek
3. Gebruik demo mode voor veilig testen

---

**Waarschuwing**: Cryptocurrency trading brengt risico's met zich mee. Test het systeem altijd eerst in demo mode en investeer alleen wat je kunt verliezen.

### Analyse Uitvoeren

```bash
python run.py --analyze --symbols BTC-USD ETH-USD
```

### Handel Uitvoeren (Demo Modus)

```bash
python run.py --analyze --trade --demo --symbols BTC-USD
```

### Handel Uitvoeren (Live Modus)

```bash
python run.py --analyze --trade --symbols BTC-USD
```

## Projectstructuur

```
crypto_trading_system/
├── crypto_trading_system/        # Hoofdpackage
│   ├── src/                      # Broncode
│   │   ├── analysis/             # Analyse modules
│   │   │   ├── technical.py      # Technische analyse
│   │   │   ├── sentiment.py      # Sentiment analyse
│   │   │   ├── market.py         # Marktgegevens analyse
│   │   │   ├── project.py        # Project fundamentals analyse
│   │   │   └── orchestrator.py   # Analyse orchestrator
│   │   ├── api/                  # API clients
│   │   │   └── clients.py        # Coinbase en CoinGecko clients
│   │   ├── config/               # Configuratie
│   │   │   └── settings.py       # Systeeminstellingen
│   │   ├── models/               # Datamodellen
│   │   │   └── data_models.py    # Datastructuren
│   │   ├── trading/              # Handelslogica
│   │   │   └── engine.py         # Handelsengine
│   │   ├── ui/                   # Gebruikersinterface
│   │   │   └── dashboard.py      # Dashboard UI
│   │   └── utils/                # Hulpfuncties
│   │       └── helpers.py        # Algemene hulpfuncties
│   └── data/                     # Dataopslag
├── docs/                         # Documentatie
├── .env.template                 # Template voor omgevingsvariabelen
├── setup.py                      # Setup script
├── run.py                        # Hoofdscript
└── run_dashboard.py              # Dashboard starter
```

## Aanpassen met AI Tools

Dit project is ontworpen om gemakkelijk aangepast te kunnen worden met AI tools. De codestructuur is modulair en goed gedocumenteerd, wat het eenvoudig maakt om specifieke onderdelen te wijzigen zonder het hele systeem te beïnvloeden.

### Tips voor Aanpassingen

1. **Analyse Modules**: Voeg nieuwe indicatoren toe in de betreffende analyse modules
2. **Dashboard UI**: Pas het dashboard aan in `src/ui/dashboard.py`
3. **Handelslogica**: Wijzig handelsstrategieën in `src/trading/engine.py`
4. **Configuratie**: Pas instellingen aan in `src/config/settings.py`

## Licentie

Dit project is beschikbaar onder de MIT licentie.
