# 🚀 Quick Setup Guide

This guide will help you set up the SMM Bot in just a few minutes!

## 📋 Prerequisites

Before you start, make sure you have:
- Python 3.8 or higher
- A PostgreSQL database (Supabase recommended)
- A Telegram Bot Token (get from @BotFather)
- JAP API credentials

## ⚡ Quick Start

### 1. Clone and Install
```bash
git clone <repository-url>
cd follower-tg-service
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy the example environment file
cp env.example .env

# Edit the .env file with your credentials
nano .env
```

**Required settings in .env:**
```env
BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=your_telegram_user_id
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
JAP_API_URL=https://jap.services/api/v2
JAP_API_KEY=your_jap_api_key
SECRET_KEY=your_secret_key_for_encryption
```

### 3. Setup Database
```bash
# Run the setup script
python dev_setup.py
```

### 4. Test Everything
```bash
# Run tests to verify everything works
python test_bot.py
```

### 5. Start the Bot
```bash
python main.py
```

## 🎯 What's Next?

### For Users
1. Start the bot with `/start`
2. Choose your language
3. Browse services and add balance
4. Place your first order!

### For Admins
1. Use `/admin` to access admin panel
2. Configure services and settings
3. Monitor user activity and payments
4. View analytics and reports

## 🔧 Configuration Options

### Payment Methods
Enable payment methods by adding credentials to `.env`:
- **PayPal**: `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET`
- **CoinGate**: `COINGATE_API_TOKEN`
- **Payme**: `PAYME_MERCHANT_ID` and `PAYME_SECRET_KEY`
- **Click**: `CLICK_MERCHANT_ID` and `CLICK_SECRET_KEY`

### Crypto Wallets
Add your crypto wallet addresses:
```env
BITCOIN_ADDRESS=your_bitcoin_address
ETHEREUM_ADDRESS=your_ethereum_address
SOLANA_ADDRESS=your_solana_address
XRP_ADDRESS=your_xrp_address
DOGE_ADDRESS=your_doge_address
TONCOIN_ADDRESS=your_toncoin_address
```

## 🆘 Need Help?

If you encounter any issues:

1. **Check the logs**: Look at `logs/bot.log` for error messages
2. **Run tests**: Use `python test_bot.py` to diagnose issues
3. **Verify configuration**: Make sure all required environment variables are set
4. **Check database**: Ensure your database is accessible and properly configured

### Common Issues

**Bot not responding:**
- Check if `BOT_TOKEN` is correct
- Verify the bot is not blocked by users

**Database connection failed:**
- Check `DATABASE_URL` format
- Ensure database server is running
- Verify credentials are correct

**Payment not working:**
- Check payment provider credentials
- Verify webhook URLs are configured
- Check payment provider account status

## 🎉 You're Ready!

Once everything is set up and tested, your SMM Bot is ready to serve customers! 

**Key Features Available:**
- ✅ Multi-language support
- ✅ Multiple payment methods
- ✅ Service catalog
- ✅ Order management
- ✅ Referral system
- ✅ Admin panel
- ✅ Transaction history
- ✅ Balance management

**Next Steps:**
1. Configure your services in the admin panel
2. Set up payment providers
3. Customize bot settings
4. Start marketing your bot!

---

**Need more help?** Check the full [README.md](README.md) for detailed documentation.
