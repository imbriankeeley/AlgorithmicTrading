# Crypto Trading Bot System

A sophisticated Bitcoin trading bot system implementing a momentum-based strategy with comprehensive backtesting capabilities and a web-based dashboard for monitoring and control.

## Features

- **Backtesting Engine**

  - Historical data analysis and strategy validation
  - Performance metrics calculation
  - Risk assessment tools
  - Parameter optimization

- **Trading Bot**

  - Real-time market data processing
  - Automated trade execution
  - Risk management controls
  - SMS notifications for critical events

- **Web Dashboard**
  - Real-time trade monitoring
  - Performance visualization
  - Strategy parameter configuration
  - Historical data analysis

## Tech Stack

- **Backend**

  - Python 3.11+
  - FastAPI
  - Supabase
  - Pandas for data analysis
  - SQLAlchemy for ORM

- **Frontend**

  - Next.js 14
  - React
  - TailwindCSS
  - Recharts for data visualization

- **Infrastructure**
  - Docker
  - Cloudflare hosting
  - Coinbase Advanced API
  - Twilio for notifications

## Getting Started

### Prerequisites

```bash
# Required software
- Docker
- Python 3.11+
- Node.js 18+
- pnpm
```

### Environment Setup

1. Clone the repository

```bash
git clone https://github.com/yourusername/crypto-trading-bot.git
cd crypto-trading-bot
```

2. Set up environment variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start the development environment

```bash
docker-compose up -d
```

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
pnpm install
pnpm dev
```

## System Architecture

The system is built with a microservices architecture:

1. **Backend Services**

   - Trading Engine Service
   - Backtesting Service
   - Data Collection Service
   - Notification Service

2. **Frontend Application**

   - Real-time Dashboard
   - Configuration Interface
   - Analytics Views

3. **Data Storage**
   - Supabase for persistent storage
   - Time-series data for market information
   - Trade history and performance metrics

## Configuration

Key configuration parameters are stored in `.env` files:

```env
# Exchange API Configuration
COINBASE_API_KEY=your_api_key
COINBASE_API_SECRET=your_api_secret

# Database Configuration
DATABASE_URL=your_supabase_url

# Trading Parameters
INITIAL_CAPITAL=500
POSITION_SIZE_PERCENT=1
TAKE_PROFIT_PERCENT=2
STOP_LOSS_PERCENT=1
```

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
pnpm test
```

## Deployment

Deployment is handled through Docker and Cloudflare:

```bash
# Build containers
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Coinbase API for market data
- TradingView for charting inspiration
- Crypto trading community for strategy insights

## Project Status

Currently in Phase 1 of development:

- ✅ Phase 1: Backtesting System
- 🚧 Phase 2: Live Trading System
- 📝 Phase 3: Dashboard Development

## Contact

Brian Keeley - work@imbriankeeley.com
Project Link: [https://github.com/imbriankeeley/AlgorithmicTrading](https://github.com/imbriankeeley/AlgorithmicTrading)

---

**Note:** This is a sophisticated trading system. Always start with small amounts and thoroughly test strategies before deploying with real capital.
