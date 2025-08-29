# 🚀 SMM Services Telegram Bot

A powerful and feature-rich Telegram bot for Social Media Marketing (SMM) services. This bot provides a complete platform for selling social media services like Instagram followers, YouTube views, TikTok followers, and more.

## ✨ Features

### 🎯 Core Features
- **Multi-language Support** - English, Russian, and Uzbek
- **User Management** - Registration, profiles, and activity tracking
- **Balance System** - Virtual currency with USD conversion
- **Service Catalog** - Browse and order social media services
- **Payment Integration** - Multiple payment methods (Crypto, Uzbek providers)
- **Order Management** - Track order status and history
- **Referral System** - Earn bonuses by referring friends
- **Admin Panel** - Comprehensive admin dashboard

### 💳 Payment Methods
- **International Cards** - Visa/Mastercard via PayPal
- **Cryptocurrency** - Bitcoin, Ethereum, Solana, XRP, Dogecoin, Toncoin
- **Uzbek Providers** - Payme, Click, Uzcard, Humo

### 📊 Services Available
- Instagram Followers & Likes
- YouTube Views & Subscribers
- TikTok Followers & Views
- Twitter Followers & Retweets
- Facebook Page Likes
- And many more!

### 🔧 Technical Features
- **Async Architecture** - Built with aiogram 3.x and async SQLAlchemy
- **Database** - PostgreSQL with async support
- **Security** - Rate limiting, input validation, admin-only features
- **Logging** - Comprehensive logging with loguru
- **Settings Management** - Dynamic configuration system
- **API Integration** - JAP API for service delivery

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- PostgreSQL database (Supabase recommended)
- Telegram Bot Token
- JAP API credentials

### 1. Clone the Repository
```bash
git clone <repository-url>
cd follower-tg-service
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
```bash
# Copy the example environment file
cp env.example .env

# Edit the .env file with your credentials
nano .env
```

### 4. Database Setup
```bash
# Run the development setup script
python dev_setup.py
```

### 5. Start the Bot
```bash
python main.py
```

## 📋 Environment Variables

### Required Variables
```env
# Bot Configuration
BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=your_telegram_user_id

# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
DB_HOST=your_db_host
DB_PORT=5432
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password

# JAP API Configuration
JAP_API_URL=https://jap.services/api/v2
JAP_API_KEY=your_jap_api_key

# Security
SECRET_KEY=your_secret_key_for_encryption
```

### Optional Variables
```env
# Payment Providers
# Stripe removed as per requirements
COINGATE_API_TOKEN=your_coingate_token

# Uzbek Payment Providers
PAYME_MERCHANT_ID=your_payme_merchant_id
PAYME_SECRET_KEY=your_payme_secret_key
CLICK_MERCHANT_ID=your_click_merchant_id
CLICK_SECRET_KEY=your_click_secret_key

# Crypto Wallet Addresses
BITCOIN_ADDRESS=your_bitcoin_address
ETHEREUM_ADDRESS=your_ethereum_address
SOLANA_ADDRESS=your_solana_address
XRP_ADDRESS=your_xrp_address
DOGE_ADDRESS=your_doge_address
TONCOIN_ADDRESS=your_toncoin_address
```

## 🎮 Usage

### User Commands
- `/start` - Start the bot and show main menu
- `/help` - Show help information

### Admin Commands
- `/admin` - Access admin panel
- `/stats` - View bot statistics
- `/sync_services` - Sync services from JAP API

### User Interface
The bot provides an intuitive inline keyboard interface with:
- 📊 **Services** - Browse and order social media services
- 💰 **Balance** - View balance, add funds, transaction history
- 📋 **Orders** - Track your order status and history
- 👥 **Referrals** - Share your referral link and earn bonuses
- ⚙️ **Settings** - Change language and view account info
- 🆘 **Support** - Get help and contact information

## 🏗️ Project Structure

```
follower-tg-service/
├── bot/
│   ├── config.py              # Configuration management
│   ├── database/
│   │   ├── db.py              # Database connection
│   │   └── models.py          # Database models
│   ├── handlers/
│   │   ├── user_handlers.py   # User interaction handlers
│   │   ├── admin_handlers.py  # Admin panel handlers
│   │   └── admin_settings_handlers.py
│   ├── middleware/
│   │   └── security_middleware.py
│   ├── services/
│   │   ├── user_service.py    # User management
│   │   ├── balance_service.py # Balance and transactions
│   │   ├── service_service.py # Service management
│   │   ├── order_service.py   # Order processing
│   │   ├── payment_service.py # Payment processing
│   │   ├── referral_service.py
│   │   ├── settings_service.py
│   │   ├── jap_service.py     # JAP API integration
│   │   └── payment/           # Payment providers
│   └── utils/
│       ├── i18n.py            # Internationalization
│       ├── keyboards.py       # Inline keyboards
│       └── security.py        # Security utilities
├── main.py                    # Main bot application
├── dev_setup.py              # Development setup script
├── requirements.txt           # Python dependencies
├── env.example               # Environment variables template
└── README.md                 # This file
```

## 🔒 Security Features

- **Rate Limiting** - Prevents spam and abuse
- **Input Validation** - Sanitizes user input
- **Admin Authentication** - Secure admin access
- **Transaction Security** - Secure payment processing
- **Logging** - Comprehensive security event logging

## 🌐 Internationalization

The bot supports multiple languages:
- 🇬🇧 English
- 🇷🇺 Russian  
- 🇺🇿 Uzbek

All user-facing text is localized and can be easily extended.

## 💰 Payment Integration

### Supported Payment Methods
1. **PayPal** - International credit/debit cards
2. **CoinGate** - Cryptocurrency payments
3. **Payme** - Uzbek payment system
4. **Click** - Uzbek payment system
5. **Uzcard/Humo** - Uzbek card payments

### Payment Flow
1. User selects payment method
2. User enters amount
3. Payment is processed
4. Balance is updated automatically
5. Transaction is recorded

## 📊 Admin Panel

### Features
- **User Management** - View and manage users
- **Service Management** - Configure services and categories
- **Payment Management** - Monitor payments and transactions
- **Analytics** - View bot statistics and performance
- **Settings** - Configure bot behavior and limits

### Admin Commands
- `/admin` - Access admin dashboard
- `/stats` - Quick statistics overview
- `/sync_services` - Sync services from JAP API

## 🚀 Deployment

### Production Deployment
1. Set up a PostgreSQL database (Supabase recommended)
2. Configure environment variables
3. Set up payment provider accounts
4. Deploy to your server
5. Run the setup script
6. Start the bot

### Docker Deployment
```bash
# Build the Docker image
docker build -t smm-bot .

# Run the container
docker run -d --name smm-bot --env-file .env smm-bot
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you need help or have questions:
- 📧 Email: support@smmbot.com
- 💬 Telegram: @smmbot_support
- 🌐 Website: https://smmbot.com

## 🎉 Features in Development

- [ ] Web dashboard for admins
- [ ] Advanced analytics
- [ ] API for third-party integrations
- [ ] Mobile app companion
- [ ] More payment methods
- [ ] Advanced referral system

---

**Made with ❤️ for the SMM community**
