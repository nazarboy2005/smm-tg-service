# Railway Deployment Guide

This guide explains how to deploy the Follower Telegram Service bot on Railway.

## Prerequisites

1. A Railway account (https://railway.app)
2. A Telegram bot token from @BotFather
3. A PostgreSQL database (Railway provides this)

## Step 1: Create Railway Project

1. Go to https://railway.app and sign in
2. Click "New Project"
3. Select "Deploy from GitHub repo" and connect your repository
4. Railway will automatically detect the Dockerfile

## Step 2: Add PostgreSQL Database

1. In your Railway project dashboard, click "Add Service"
2. Select "Database" → "PostgreSQL"
3. Railway will create a PostgreSQL instance and provide connection details

## Step 3: Configure Environment Variables

Add these environment variables in Railway's dashboard:

### Required Variables
```
BOT_TOKEN=your_bot_token_from_botfather
ADMIN_IDS=your_telegram_user_id
DATABASE_URL=${{Postgres.DATABASE_URL}}
SECRET_KEY=your_random_secret_key_32_chars_min
JAP_API_URL=https://justanotherpanel.com/api/v2
JAP_API_KEY=your_jap_api_key
```

### Webhook Configuration (IMPORTANT)
```
USE_WEBHOOK=true
WEBHOOK_URL=https://your-app-name.up.railway.app
WEBHOOK_SECRET=your_webhook_secret_token
ENVIRONMENT=production
```

### Optional Payment Configuration
```
COINGATE_API_TOKEN=your_coingate_token
COINGATE_SANDBOX=false
PAYPAL_CLIENT_ID=your_paypal_client_id
PAYPAL_CLIENT_SECRET=your_paypal_client_secret
PAYME_MERCHANT_ID=your_payme_merchant_id
PAYME_SECRET_KEY=your_payme_secret_key
CLICK_MERCHANT_ID=your_click_merchant_id
CLICK_SECRET_KEY=your_click_secret_key
```

## Step 4: Get Your Railway Domain

1. After deployment, Railway will provide you with a domain like: `https://your-app-name.up.railway.app`
2. Copy this domain
3. Update the `WEBHOOK_URL` environment variable with this domain
4. The bot will automatically set up the webhook at `https://your-domain.railway.app/webhook`

## Step 5: Set Telegram Webhook

The bot will automatically configure the webhook when it starts if `USE_WEBHOOK=true` is set.

You can also manually set it using:
```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-app-name.up.railway.app/webhook", "secret_token": "your_webhook_secret"}'
```

## Step 6: Monitor Deployment

1. Check the deployment logs in Railway dashboard
2. Look for these success messages:
   - "Database initialized successfully"
   - "Web server started on port 8000"
   - "Webhook set successfully. Bot is now running in webhook mode."

## Step 7: Test Your Bot

1. Send `/start` to your bot in Telegram
2. The bot should respond with the language selection menu
3. Check Railway logs for any errors

## Environment Variables Reference

| Variable | Description | Required |
|----------|-------------|----------|
| `USE_WEBHOOK` | Set to `true` for Railway deployment | ✅ |
| `WEBHOOK_URL` | Your Railway app domain | ✅ |
| `WEBHOOK_SECRET` | Secret token for webhook security | ✅ |
| `BOT_TOKEN` | Telegram bot token | ✅ |
| `DATABASE_URL` | PostgreSQL connection string | ✅ |
| `ADMIN_IDS` | Comma-separated admin user IDs | ✅ |
| `SECRET_KEY` | App secret key (32+ chars) | ✅ |
| `JAP_API_URL` | JAP API endpoint | ✅ |
| `JAP_API_KEY` | JAP API key | ✅ |

## Troubleshooting

### Bot doesn't respond
- Check Railway logs for errors
- Verify `WEBHOOK_URL` matches your Railway domain exactly
- Ensure `USE_WEBHOOK=true` is set

### Database connection errors
- Verify `DATABASE_URL` is set to `${{Postgres.DATABASE_URL}}`
- Check if PostgreSQL service is running

### Webhook not working
- Check if webhook is set: `https://api.telegram.org/bot<TOKEN>/getWebhookInfo`
- Verify webhook secret matches in both Telegram and Railway

### Payment issues
- Ensure payment provider credentials are correctly set
- Check provider sandbox/production settings

## Production Checklist

- [ ] `USE_WEBHOOK=true`
- [ ] `ENVIRONMENT=production`
- [ ] `WEBHOOK_URL` set to Railway domain
- [ ] `WEBHOOK_SECRET` configured
- [ ] Database connected
- [ ] Payment providers configured
- [ ] Admin IDs set correctly
- [ ] Bot responds to `/start`

## Support

If you encounter issues:
1. Check Railway deployment logs
2. Verify all environment variables
3. Test webhook endpoint: `https://your-domain.railway.app/webhook`
4. Check Telegram webhook info: `https://api.telegram.org/bot<TOKEN>/getWebhookInfo`
