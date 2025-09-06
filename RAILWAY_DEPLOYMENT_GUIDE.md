# 🚀 Railway Deployment Guide for Elite JAP Bot

This guide will help you deploy your Telegram bot service to Railway with a fully functional web interface.

## 📋 Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **Telegram Bot Token**: Get from [@BotFather](https://t.me/BotFather)
4. **Database**: Supabase PostgreSQL database (recommended)

## 🗄️ Database Setup (Supabase)

### Step 1: Create Supabase Project
1. Go to [supabase.com](https://supabase.com) and create a new project
2. Wait for the project to be fully initialized
3. Go to **Settings** → **Database**
4. Copy the **Connection string** (Transaction Pooler)

### Step 2: Configure Database URL
Use the **Transaction Pooler** connection string format:
```
postgresql://postgres.qgziqlgwaoqyqtcmmjsv:[YOUR-PASSWORD]@aws-1-eu-north-1.pooler.supabase.com:6543/postgres
```

**Important**: Use port `6543` (Transaction Pooler) for IPv4 compatibility and to avoid PREPARE statement issues.

## 🚀 Railway Deployment

### Step 1: Connect Repository
1. Go to [railway.app](https://railway.app) and sign in
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your repository
5. Railway will automatically detect the `Dockerfile`

### Step 2: Configure Environment Variables
In your Railway project dashboard, go to **Variables** and add:

#### Required Variables:
```bash
# Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here
BOT_USERNAME=your_bot_username_here
ADMIN_IDS=123456789,987654321  # Comma-separated admin Telegram IDs

# Database Configuration
DATABASE_URL=postgresql://postgres.qgziqlgwaoqyqtcmmjsv:[YOUR-PASSWORD]@aws-1-eu-north-1.pooler.supabase.com:6543/postgres

# Payment Configuration (Choose one or more)
TELEGRAM_PAYMENTS_TOKEN=your_telegram_payments_token_here
PAYME_MERCHANT_ID=your_payme_merchant_id
CLICK_MERCHANT_ID=your_click_merchant_id

# Admin Contact
ADMIN_CONTACT=@your_admin_username

# Environment
ENVIRONMENT=production
USE_WEBHOOK=true

# Security
SECRET_KEY=your_very_secure_secret_key_here
WEBHOOK_SECRET=your_webhook_secret_here

# Optional: JAP API
JAP_API_URL=your_jap_api_url_here
JAP_API_KEY=your_jap_api_key_here
```

#### Railway Auto-Provided Variables:
- `RAILWAY_STATIC_URL` - Automatically set by Railway
- `PORT` - Automatically set by Railway

### Step 3: Deploy
1. Railway will automatically build and deploy your application
2. The deployment will use `main_webhook.py` as the entry point
3. Your bot will be available at the Railway-provided URL

## 🌐 Web Interface Features

Your deployed bot includes a full web interface with:

### 🏠 Dashboard
- User balance display
- Recent orders overview
- Popular services showcase
- Quick access to bot

### 💳 Payment System
- Multiple payment methods support
- Secure payment processing
- Transaction history
- Real-time balance updates

### 📱 Mobile-Responsive Design
- Bootstrap 5 framework
- Modern UI/UX design
- Telegram login integration
- Cross-platform compatibility

## 🔧 Configuration Details

### Railway Configuration (`railway.json`)
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE"
  },
  "deploy": {
    "startCommand": "python main_webhook.py",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Docker Configuration
- **Base Image**: Python 3.11 slim
- **Port**: 8000 (Railway will override with PORT env var)
- **Health Check**: `/health` endpoint
- **Entry Point**: `main_webhook.py`

## 🔍 Health Monitoring

### Health Check Endpoint
Your bot provides a health check at `/health` that returns:
```json
{
  "status": "healthy",
  "webhook_configured": true,
  "bot_username": "your_bot_username"
}
```

### Monitoring Features
- Automatic restart on failure
- Health check every 30 seconds
- Comprehensive logging
- Error tracking and reporting

## 🛠️ Troubleshooting

### Common Issues

#### 1. Database Connection Issues
**Problem**: Database connection fails
**Solution**: 
- Verify `DATABASE_URL` is correct
- Use Transaction Pooler (port 6543)
- Check Supabase project status

#### 2. Webhook Not Working
**Problem**: Bot doesn't receive updates
**Solution**:
- Verify `BOT_TOKEN` is correct
- Check `RAILWAY_STATIC_URL` is set
- Ensure `USE_WEBHOOK=true`

#### 3. Web Interface Not Loading
**Problem**: Web pages return errors
**Solution**:
- Check database connection
- Verify all required environment variables
- Check Railway deployment logs

### Debug Commands
```bash
# Check Railway logs
railway logs

# Check environment variables
railway variables

# Restart deployment
railway redeploy
```

## 📊 Performance Optimization

### Database Optimization
- Uses Supabase Transaction Pooler for better performance
- Connection pooling with asyncpg
- Optimized queries for high throughput

### Web Server Optimization
- FastAPI with async support
- Static file serving
- Template caching
- Gzip compression

## 🔐 Security Features

### Authentication
- Telegram login integration
- Session management
- CSRF protection
- Secure cookie handling

### Payment Security
- SSL/TLS encryption
- Secure payment processing
- Transaction validation
- Fraud prevention

## 📈 Scaling

### Automatic Scaling
- Railway automatically scales based on traffic
- Database connection pooling
- Efficient resource utilization

### Monitoring
- Real-time performance metrics
- Error tracking
- Uptime monitoring
- Resource usage tracking

## 🎯 Post-Deployment

### 1. Test Your Bot
1. Visit your Railway URL
2. Test the web interface
3. Send a message to your bot
4. Verify webhook is working

### 2. Configure Domain (Optional)
1. Go to Railway project settings
2. Add custom domain
3. Update `WEB_BASE_URL` environment variable

### 3. Set Up Monitoring
1. Enable Railway monitoring
2. Set up alerts for failures
3. Monitor performance metrics

## 📞 Support

If you encounter any issues:

1. **Check Railway Logs**: Use `railway logs` command
2. **Verify Environment Variables**: Ensure all required variables are set
3. **Test Database Connection**: Verify Supabase connection
4. **Check Bot Token**: Ensure bot token is valid

## 🎉 Success!

Once deployed, your bot will have:
- ✅ Full Telegram bot functionality
- ✅ Modern web interface
- ✅ Secure payment processing
- ✅ Database integration
- ✅ Health monitoring
- ✅ Automatic scaling

Your Elite JAP Bot is now ready to serve users with a professional web interface and reliable Telegram integration!

---

**Need Help?** Check the troubleshooting section or contact support through your bot's admin interface.