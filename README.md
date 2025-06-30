# Crypto Trading SaaS - AI-Powered Cryptocurrency Analysis Platform

A professional-grade SaaS application for cryptocurrency trading and analysis, powered by advanced AI and designed for multi-user deployment on Railway.

## 🚀 Features

### Core Functionality
- **AI-Powered Analysis**: Advanced market analysis using Google Gemini AI
- **Real-time Data**: Live cryptocurrency market data and technical indicators
- **Secure API Vault**: Bank-grade encryption for user API keys
- **Portfolio Management**: Automated portfolio optimization and risk management
- **Multi-user Support**: Complete SaaS architecture with user authentication
- **Subscription Management**: Integrated Stripe payment processing

### Technical Features
- **Modern Architecture**: Flask backend with responsive HTML/CSS/JS frontend
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: Secure user registration, login, and session management
- **Encryption**: AES-256 encryption for sensitive data
- **Caching**: Intelligent analysis caching to optimize performance
- **Mobile Ready**: Responsive design optimized for all devices

## 🏗️ Architecture

```
crypto_saas/
├── src/
│   ├── main.py                 # Flask application factory
│   ├── config.py              # Configuration management
│   ├── models/
│   │   └── user.py            # Database models
│   ├── routes/
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── api_keys.py        # API key management
│   │   ├── analysis.py        # AI analysis endpoints
│   │   └── payments.py        # Stripe payment processing
│   ├── services/
│   │   └── ai_analysis.py     # Google Gemini AI integration
│   ├── utils/
│   │   └── encryption.py      # Encryption utilities
    │   └── frontend/              # React + Vite front-end source & build
├── wsgi.py                    # WSGI entry point
├── requirements.txt           # Python dependencies
├── Procfile                   # Railway deployment config
├── railway.json              # Railway configuration
└── .env.template             # Environment variables template

```text

## 🖥️ Frontend

The front-end is built with React, Vite, and Tailwind CSS for a professional dark-mode fintech UI.

### Development

```bash
cd frontend
npm install
npm run dev
```

### Production Build

```bash
cd frontend
npm run build
```

The production build is output to `frontend/dist`, and Flask will serve it automatically.

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL database
- Stripe account (for payments)
- Google Gemini API key (for AI analysis)

### Local Development

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd crypto_saas
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   ```bash
   cp .env.template .env
   # Edit .env with your actual configuration values
   ```

3. **Database Setup**
   ```bash
   # Create PostgreSQL database
   createdb crypto_saas_db
   
   # Initialize database tables
   python -c "from src.main import create_app; app = create_app(); app.app_context().push(); from src.models.user import db; db.create_all()"
   ```

4. **Run Development Server**
   ```bash
   python wsgi.py
   ```

   Visit `http://localhost:5000` to access the application.

## 🚂 Railway Deployment

### Automatic Deployment

1. **Connect Repository**
   - Connect your GitHub repository to Railway
   - Railway will automatically detect the Python project

2. **Environment Variables**
   Set the following environment variables in Railway:
   
   ```
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=postgresql://... (provided by Railway)
   STRIPE_PUBLISHABLE_KEY=pk_live_...
   STRIPE_SECRET_KEY=sk_live_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   GEMINI_API_KEY=your_gemini_api_key
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your_email@gmail.com
   MAIL_PASSWORD=your_app_password
   ENCRYPTION_KEY=your-32-byte-base64-key
   SUBSCRIPTION_PRICE=2999
   SUBSCRIPTION_CURRENCY=usd
   ```

3. **Deploy**
   - Push to your main branch
   - Railway will automatically build and deploy
   - Access your app at `https://your-app.railway.app`

### Manual Configuration

If you need to manually configure Railway:

1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   railway login
   ```

2. **Initialize Project**
   ```bash
   railway init
   railway link
   ```

3. **Set Environment Variables**
   ```bash
   railway variables set SECRET_KEY="your-secret-key"
   railway variables set STRIPE_SECRET_KEY="sk_live_..."
   # ... set all required variables
   ```

4. **Deploy**
   ```bash
   railway up
   ```

## 🔧 Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key for sessions | `your-very-long-random-secret-key` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:port/db` |
| `STRIPE_SECRET_KEY` | Stripe secret key | `sk_live_...` |
| `STRIPE_PUBLISHABLE_KEY` | Stripe publishable key | `pk_live_...` |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook secret | `whsec_...` |
| `GEMINI_API_KEY` | Google Gemini AI API key | `your_gemini_api_key` |
| `ENCRYPTION_KEY` | 32-byte base64 encryption key | `base64-encoded-key` |

### Optional Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `SUBSCRIPTION_PRICE` | Monthly subscription price (cents) | `2999` |
| `SUBSCRIPTION_CURRENCY` | Subscription currency | `usd` |
| `MAIL_SERVER` | SMTP server for emails | `smtp.gmail.com` |
| `MAIL_PORT` | SMTP port | `587` |

## 💳 Stripe Setup

1. **Create Stripe Account**
   - Sign up at [stripe.com](https://stripe.com)
   - Get your API keys from the dashboard

2. **Configure Webhooks**
   - Add webhook endpoint: `https://your-app.railway.app/api/payments/webhook`
   - Subscribe to events:
     - `customer.subscription.created`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.payment_succeeded`
     - `invoice.payment_failed`

3. **Test Payments**
   - Use test card: `4242 4242 4242 4242`
   - Any future expiry date and CVC

## 🤖 AI Integration

The application uses Google Gemini AI for market analysis:

1. **Get API Key**
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key

2. **Configure Analysis**
   - The AI analyzes market sentiment, technical indicators, and trends
   - Results are cached for performance
   - Users can request analysis for individual cryptocurrencies or portfolios

## 🔒 Security Features

- **Encryption**: All sensitive data encrypted with AES-256
- **Authentication**: Secure session management with Flask-Login
- **Password Security**: Bcrypt hashing with salt
- **API Security**: Rate limiting and input validation
- **HTTPS**: Enforced in production
- **CSRF Protection**: Built-in CSRF tokens

## 📊 Database Schema

### Users Table
- User authentication and profile information
- Subscription status and Stripe integration
- Encrypted API key storage

### Analysis Cache Table
- Cached AI analysis results
- Automatic expiration and cleanup
- User-specific caching

### User Sessions Table
- Secure session management
- Device tracking and security

## 🧪 Testing

### Run Tests Locally
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

### Test Endpoints
- Health check: `GET /health`
- Authentication: `POST /api/auth/login`
- Analysis: `GET /api/analyze/BTC`
- Payments: `POST /api/payments/create-checkout-session`

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify `DATABASE_URL` is correct
   - Ensure PostgreSQL is running
   - Check firewall settings

2. **Stripe Webhook Issues**
   - Verify webhook URL is accessible
   - Check webhook secret configuration
   - Review Stripe dashboard for failed webhooks

3. **AI Analysis Failures**
   - Verify Gemini API key is valid
   - Check API quota and billing
   - Review error logs for specific issues

4. **Static File Issues**
   - Ensure static files are properly served
   - Check file permissions
   - Verify Railway build process

### Logs and Monitoring

```bash
# View Railway logs
railway logs

# Monitor application health
curl https://your-app.railway.app/health
```

## 📈 Performance Optimization

- **Caching**: Analysis results cached for 1-2 hours
- **Database**: Indexed queries and connection pooling
- **Static Files**: Served efficiently with proper headers
- **API Limits**: Rate limiting to prevent abuse
- **CDN**: Consider adding CDN for static assets

## 🔄 Updates and Maintenance

### Updating Dependencies
```bash
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt
```

### Database Migrations
```bash
# Create migration
flask db migrate -m "Description"

# Apply migration
flask db upgrade
```

### Monitoring
- Monitor Railway metrics dashboard
- Set up Stripe webhook monitoring
- Track user registration and subscription metrics

## 📞 Support

For technical support or questions:
- Check the troubleshooting section above
- Review Railway deployment logs
- Verify all environment variables are set correctly

## 📄 License

This project is proprietary software. All rights reserved.

---

**Built with ❤️ for professional cryptocurrency trading and analysis.**

