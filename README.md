# Elite JAP Bot - SMM Services Telegram Bot

A powerful Telegram bot for Social Media Marketing (SMM) services, integrated with the Just Another Panel (JAP) API.

## 🚀 Features

- **Multi-language Support**: English, Russian, Uzbek
- **JAP API Integration**: Direct integration with Just Another Panel
- **Payment Processing**: Multiple payment methods (PayPal, Crypto, Uzbek providers)
- **Web Dashboard**: Beautiful web interface for users
- **Referral System**: Built-in referral rewards
- **Admin Panel**: Comprehensive admin controls
- **Order Management**: Track and manage SMM orders
- **Real-time Updates**: Live order status updates

## 📋 Requirements

- Python 3.8+
- PostgreSQL database
- Telegram Bot Token
- JAP API Key

## 🛠️ Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd follower-tg-service
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables
```bash
cp env.example .env
```

Edit the `.env` file with your configuration:
```env
# Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here
BOT_USERNAME=your_bot_username_here
ADMIN_IDS=123456789,987654321

# Database Configuration
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/database_name

# JAP API Configuration
JAP_API_KEY=your_jap_api_key_here

# Other settings...
```

### 4. Set up the database
```bash
# Create database tables
python -c "import asyncio; from bot.database.db import init_db; asyncio.run(init_db())"
```

## 🚀 Running the Bot

### Polling Mode (Recommended for Development)
```bash
python start_bot.py
```

Or directly:
```bash
python main.py
```

### Webhook Mode (Production)
Set `USE_WEBHOOK=true` in your `.env` file and configure the webhook URL.

## 🧪 Testing

Run the test script to verify your configuration:
```bash
python test_polling.py
```

## 📱 Bot Commands

- `/start` - Start the bot and show main menu
- `/ping` - Test bot responsiveness
- `/test` - Test bot functionality
- `/balance` - Check your balance
- `/services` - Browse available services
- `/orders` - View your orders
- `/referral` - Get your referral link

## 🌐 Web Dashboard

The bot includes a web dashboard accessible at `http://localhost:8000` (when running).

Features:
- User authentication via Telegram
- Balance management
- Order tracking
- Service browsing
- Payment processing

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BOT_TOKEN` | Telegram bot token | Yes |
| `BOT_USERNAME` | Bot username | Yes |
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `JAP_API_KEY` | JAP API key | Yes |
| `ADMIN_IDS` | Comma-separated admin user IDs | No |
| `SECRET_KEY` | Secret key for sessions | Yes |

### JAP API Integration

The bot integrates with Just Another Panel API v2. Make sure you have:
- Valid JAP API key
- Active JAP account with balance
- Services configured in your JAP panel

## 📊 Database Schema

The bot uses the following main tables:
- `users` - User accounts and profiles
- `balances` - User balance tracking
- `transactions` - Payment and balance transactions
- `services` - Available SMM services
- `orders` - User orders and their status
- `referral_rewards` - Referral system tracking

## 🔒 Security Features

- Telegram login validation
- Session management
- Admin-only commands
- Payment verification
- Rate limiting

## 🚨 Troubleshooting

### Common Issues

1. **Bot not responding**
   - Check if `BOT_TOKEN` is correct
   - Verify bot is not blocked by users
   - Check logs for errors

2. **Database connection issues**
   - Verify `DATABASE_URL` format
   - Check database server is running
   - Ensure database exists

3. **JAP API errors**
   - Verify `JAP_API_KEY` is correct
   - Check JAP account balance
   - Ensure services are available

4. **Payment issues**
   - Verify payment provider credentials
   - Check webhook URLs for production
   - Review payment logs

### Logs

Logs are written to `logs/bot.log` by default. Check this file for detailed error information.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the logs for error details

## 🔄 Updates

To update the bot:
1. Pull the latest changes
2. Update dependencies: `pip install -r requirements.txt`
3. Run database migrations if needed
4. Restart the bot

---

**Note**: This bot is designed for legitimate SMM services. Please ensure compliance with Telegram's Terms of Service and applicable laws in your jurisdiction.