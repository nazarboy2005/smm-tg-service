"""
Web server for the Telegram bot integration
"""
import os
import json
import hmac
import hashlib
import time
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, Response, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from bot.database.db import get_db
from bot.services.user_service import UserService
from bot.services.balance_service import BalanceService
from bot.services.order_service import OrderService
from bot.services.service_service import ServiceService
from bot.database.models import TransactionStatus
from bot.config import settings

# Global bot and dispatcher references (will be set from main.py)
bot = None
dp = None

def set_bot_and_dispatcher(bot_instance, dp_instance):
    """Set bot and dispatcher instances for webhook handling"""
    global bot, dp
    bot = bot_instance
    dp = dp_instance


# Create FastAPI app
app = FastAPI(
    title="Elite JAP Bot Web Interface",
    description="Web interface for the Elite JAP Bot",
    version="1.0.0"
)

# Setup templates and static files
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
static_dir = os.path.join(os.path.dirname(__file__), "static")

if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

templates = Jinja2Templates(directory=templates_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.post("/webhook")
async def webhook(request: Request):
    """Handle Telegram webhook updates"""
    try:
        # Verify webhook secret if configured
        if hasattr(settings, 'webhook_secret') and settings.webhook_secret:
            secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
            if secret_header != settings.webhook_secret:
                logger.warning("Invalid webhook secret token")
                raise HTTPException(status_code=403, detail="Invalid secret token")
        
        # Get update data
        update_data = await request.json()
        
        # Process update if bot and dispatcher are available
        if bot and dp:
            from aiogram.types import Update
            update = Update(**update_data)
            await dp.feed_update(bot, update)
        else:
            logger.error("Bot or dispatcher not initialized for webhook")
            raise HTTPException(status_code=500, detail="Bot not ready")
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def validate_telegram_data(data: Dict[str, Any]) -> bool:
    """Validate Telegram login data"""
    if "hash" not in data:
        return False
    
    # Get the hash from the data
    received_hash = data.pop("hash")
    
    # Sort the data alphabetically
    sorted_data = sorted(data.items(), key=lambda x: x[0])
    
    # Create a string of the form key=value for each item
    data_string = "\n".join([f"{k}={v}" for k, v in sorted_data])
    
    # Create a secret key using SHA-256
    secret_key = hashlib.sha256(settings.bot_token.encode()).digest()
    
    # Calculate the HMAC-SHA-256 hash
    calculated_hash = hmac.new(
        secret_key,
        data_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Compare the hashes
    return calculated_hash == received_hash


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Optional[Dict[str, Any]]:
    """Get current user from session or Telegram login data"""
    # Check session first
    user_data = request.session.get("user")
    if user_data:
        return user_data
    
    # Check for Telegram login data
    tg_data = {}
    for key, value in request.query_params.items():
        tg_data[key] = value
    
    # Validate Telegram login data
    if tg_data and "id" in tg_data and validate_telegram_data(tg_data):
        # Get user from database
        user = await UserService.get_user_by_telegram_id(db, int(tg_data["id"]))
        if user:
            user_data = {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_admin": user.is_admin
            }
            request.session["user"] = user_data
            return user_data
    
    return None


@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """Main page"""
    if not user:
        # Redirect to Telegram bot
        bot_url = f"https://t.me/{settings.bot_username}"
        return RedirectResponse(url=bot_url)
    
    # Get user data
    async for db in get_db():
        user_db = await UserService.get_user_by_telegram_id(db, user["telegram_id"])
        break
    
    if not user_db:
        return RedirectResponse(url=f"https://t.me/{settings.bot_username}")
    
    # Get user balance
    balance = await BalanceService.get_user_balance(db, user_db.id)
    
    # Get user orders
    orders = await OrderService.get_user_orders(db, user_db.id, limit=5)
    
    # Get popular services
    popular_services = await ServiceService.get_popular_services(db, limit=4)
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user": user,
            "balance": balance,
            "orders": orders,
            "popular_services": popular_services,
            "bot_username": settings.bot_username
        }
    )


@app.get("/services", response_class=HTMLResponse)
async def services(
    request: Request,
    user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """Services page"""
    if not user:
        return RedirectResponse(url=f"https://t.me/{settings.bot_username}")
    
    # Get categories
    async for db in get_db():
        categories = await ServiceService.get_active_categories(db)
        break
    
    return templates.TemplateResponse(
        "services.html",
        {
            "request": request,
            "user": user,
            "categories": categories,
            "bot_username": settings.bot_username
        }
    )


@app.get("/orders", response_class=HTMLResponse)
async def orders(
    request: Request,
    user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """Orders page"""
    if not user:
        return RedirectResponse(url=f"https://t.me/{settings.bot_username}")
    
    # Get user orders
    async for db in get_db():
        user_db = await UserService.get_user_by_telegram_id(db, user["telegram_id"])
        orders = await OrderService.get_user_orders(db, user_db.id)
        break
    
    return templates.TemplateResponse(
        "orders.html",
        {
            "request": request,
            "user": user,
            "orders": orders,
            "bot_username": settings.bot_username
        }
    )


@app.get("/balance", response_class=HTMLResponse)
async def balance(
    request: Request,
    user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """Balance page"""
    if not user:
        return RedirectResponse(url=f"https://t.me/{settings.bot_username}")
    
    # Get user balance
    async for db in get_db():
        user_db = await UserService.get_user_by_telegram_id(db, user["telegram_id"])
        balance = await BalanceService.get_user_balance(db, user_db.id)
        
        # Get payment methods
        from bot.services.payment_service import payment_service
        payment_methods = await payment_service.get_available_providers(db)
        break
    
    return templates.TemplateResponse(
        "balance.html",
        {
            "request": request,
            "user": user,
            "balance": balance,
            "payment_methods": payment_methods,
            "bot_username": settings.bot_username
        }
    )


@app.get("/payment/{transaction_id}", response_class=HTMLResponse)
async def payment_page(
    transaction_id: str,
    request: Request,
    user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """Payment page for a specific transaction"""
    if not user:
        return RedirectResponse(url=f"https://t.me/{settings.bot_username}")
    
    # Get transaction details
    async for db in get_db():
        user_db = await UserService.get_user_by_telegram_id(db, user["telegram_id"])
        
        # Get transaction
        transaction = await BalanceService.get_transaction_by_id(db, int(transaction_id))
        if not transaction or transaction.user_id != user_db.id:
            return RedirectResponse(url="/balance")
        
        # Get user balance
        balance = await BalanceService.get_user_balance(db, user_db.id)
        
        # Get payment methods
        from bot.services.payment_service import payment_service
        payment_methods = await payment_service.get_available_providers(db)
        
        # Calculate coins amount
        coins_amount = transaction.amount
        break
    
    return templates.TemplateResponse(
        "payment.html",
        {
            "request": request,
            "user": user,
            "balance": balance,
            "transaction_id": transaction_id,
            "amount_usd": transaction.usd_amount,
            "coins_amount": coins_amount,
            "payment_methods": payment_methods,
            "bot_username": settings.bot_username
        }
    )


@app.post("/process_payment")
async def process_payment(
    request: Request,
    user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """Process payment"""
    if not user:
        return RedirectResponse(url=f"https://t.me/{settings.bot_username}")
    
    # Get form data
    form_data = await request.form()
    transaction_id = form_data.get("transaction_id")
    selected_method = form_data.get("selected_method")
    
    if not transaction_id or not selected_method:
        return RedirectResponse(url="/balance")
    
    # Get transaction details
    async for db in get_db():
        user_db = await UserService.get_user_by_telegram_id(db, user["telegram_id"])
        
        # Get transaction
        transaction = await BalanceService.get_transaction_by_id(db, int(transaction_id))
        if not transaction or transaction.user_id != user_db.id:
            return RedirectResponse(url="/balance")
        
        # Process payment with selected method
        from bot.services.payment_service import payment_service
        
        # Create payment with provider
        result = await payment_service.create_payment_web(
            db=db,
            provider_name=selected_method,
            transaction_id=int(transaction_id),
            user_id=user_db.id,
            amount_usd=float(transaction.usd_amount),
            return_url=f"{request.base_url}payment/success/{transaction_id}",
            cancel_url=f"{request.base_url}payment/cancel/{transaction_id}"
        )
        break
    
    if result and result.success and result.payment_url:
        # Redirect to payment URL
        return RedirectResponse(url=result.payment_url, status_code=303)
    else:
        # Redirect to failure page
        error_message = result.error_message if result else "Payment initialization failed"
        return RedirectResponse(
            url=f"/payment/failure/{transaction_id}?error={error_message}",
            status_code=303
        )


@app.get("/payment/success/{transaction_id}", response_class=HTMLResponse)
async def payment_success(
    transaction_id: str,
    request: Request,
    user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """Payment success page"""
    if not user:
        return RedirectResponse(url=f"https://t.me/{settings.bot_username}")
    
    # Get transaction details
    async for db in get_db():
        user_db = await UserService.get_user_by_telegram_id(db, user["telegram_id"])
        
        # Get transaction
        transaction = await BalanceService.get_transaction_by_id(db, int(transaction_id))
        if not transaction or transaction.user_id != user_db.id:
            return RedirectResponse(url="/balance")
        
        # Complete transaction if not already completed
        if transaction.status != TransactionStatus.COMPLETED:
            await BalanceService.complete_transaction(db, int(transaction_id))
        
        # Get updated balance
        balance = await BalanceService.get_user_balance(db, user_db.id)
        break
    
    return templates.TemplateResponse(
        "payment_success.html",
        {
            "request": request,
            "user": user,
            "balance": balance,
            "transaction_id": transaction_id,
            "coins_amount": transaction.amount,
            "bot_username": settings.bot_username
        }
    )


@app.get("/payment/failure/{transaction_id}", response_class=HTMLResponse)
async def payment_failure(
    transaction_id: str,
    request: Request,
    error: str = "",
    user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """Payment failure page"""
    if not user:
        return RedirectResponse(url=f"https://t.me/{settings.bot_username}")
    
    # Get transaction details
    async for db in get_db():
        user_db = await UserService.get_user_by_telegram_id(db, user["telegram_id"])
        
        # Get transaction
        transaction = await BalanceService.get_transaction_by_id(db, int(transaction_id))
        if not transaction or transaction.user_id != user_db.id:
            return RedirectResponse(url="/balance")
        
        # Get balance
        balance = await BalanceService.get_user_balance(db, user_db.id)
        break
    
    return templates.TemplateResponse(
        "payment_failure.html",
        {
            "request": request,
            "user": user,
            "balance": balance,
            "transaction_id": transaction_id,
            "error_message": error,
            "bot_username": settings.bot_username
        }
    )


@app.get("/payment/cancel/{transaction_id}")
async def payment_cancel(
    transaction_id: str,
    request: Request,
    user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """Payment cancelled by user"""
    if not user:
        return RedirectResponse(url=f"https://t.me/{settings.bot_username}")
    
    # Get transaction details
    async for db in get_db():
        user_db = await UserService.get_user_by_telegram_id(db, user["telegram_id"])
        
        # Get transaction
        transaction = await BalanceService.get_transaction_by_id(db, int(transaction_id))
        if not transaction or transaction.user_id != user_db.id:
            return RedirectResponse(url="/balance")
        
        # Mark transaction as cancelled
        await BalanceService.fail_transaction(db, int(transaction_id), "Cancelled by user")
        break
    
    return RedirectResponse(url="/balance")


@app.get("/logout")
async def logout(request: Request):
    """Logout"""
    request.session.pop("user", None)
    return RedirectResponse(url="/")


def start_web_server():
    """Start web server"""
    import uvicorn
    
    # Get port from environment or Railway's PORT variable, use default as fallback
    port = int(os.environ.get("PORT", os.environ.get("WEB_PORT", 8000)))
    
    logger.info(f"Starting web server on 0.0.0.0:{port}")
    
    # Start server with Railway-compatible configuration
    uvicorn.run(
        "bot.web.server:app",
        host="0.0.0.0",
        port=port,
        reload=settings.environment == "development",
        access_log=True,
        server_header=False,
        date_header=False
    )
