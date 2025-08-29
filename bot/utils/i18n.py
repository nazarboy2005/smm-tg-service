"""
Internationalization (i18n) support for multiple languages
"""
from typing import Dict, Any
from enum import Enum


class Language(Enum):
    UZBEK = "uz"
    RUSSIAN = "ru"
    ENGLISH = "en"


# Translation dictionaries
TRANSLATIONS = {
    Language.ENGLISH: {
        # Main menu
        "welcome": "🎉 Welcome to SMM Services Bot!",
        "choose_language": "Please choose your language:",
        "language_selected": "✅ Language set to English",
        "main_menu": "🏠 Main Menu",
        "services": "📊 Services",
        "balance": "💰 Balance",
        "orders": "📋 Orders",
        "referrals": "👥 Referrals",
        "settings": "⚙️ Settings",
        "support": "🆘 Support",
        
        # Balance
        "your_balance": "💰 Your balance: {balance} coins",
        "add_balance": "💳 Add Balance",
        "transaction_history": "📊 Transaction History",
        "no_transactions": "No transactions yet",
        "min_deposit": "Minimum deposit: ${min_usd} USD",
        "max_deposit": "Maximum deposit: ${max_usd} USD",
        
        # Payment methods
        "choose_payment_method": "💳 Choose payment method:",
        "payment_cards": "💳 Cards (Visa/Mastercard)",
        "payment_crypto": "₿ Cryptocurrency",
        "payment_payme": "💙 Payme",
        "payment_click": "🟡 Click",
        "payment_uzcard": "💚 Uzcard",
        "payment_humo": "🔴 Humo",
        "enter_amount": "💵 Enter amount in USD (${min_usd} - ${max_usd}):",
        "invalid_amount": "❌ Invalid amount. Please enter a number between ${min_usd} and ${max_usd}",
        "payment_processing": "⏳ Processing payment...",
        "payment_success": "✅ Payment successful! {amount} coins added to your balance",
        "payment_failed": "❌ Payment failed. Please try again",
        
        # Services
        "choose_category": "📊 Choose service category:",
        "choose_service": "Select a service:",
        "no_services": "No services available at the moment. Please try again later.",
        "service_details": "📊 {name}\n💰 Price: {price} coins per 1000\n📊 Min: {min_qty} | Max: {max_qty}",
        "enter_link": "🔗 Enter your social media link:",
        "enter_quantity": "🔢 Enter quantity ({min_qty} - {max_qty}):",
        "invalid_link": "❌ Invalid link. Please enter a valid social media URL",
        "invalid_quantity": "❌ Invalid quantity. Please enter a number between {min_qty} and {max_qty}",
        "insufficient_balance": "❌ Insufficient balance. You need {required} coins, but have {current} coins",
        "order_confirmation": "📋 Order Confirmation\n\n🔗 Link: {link}\n📊 Service: {service}\n🔢 Quantity: {quantity}\n💰 Cost: {cost} coins\n\nConfirm order?",
        "order_created": "✅ Order created successfully!\nOrder ID: #{order_id}\n💰 {cost} coins deducted from balance",
        "order_failed": "❌ Failed to create order. Please try again",
        
        # Orders
        "your_orders": "📋 Your Orders",
        "no_orders": "No orders yet",
        "order_status": "📋 Order #{order_id}\n📊 Service: {service}\n🔗 Link: {link}\n🔢 Quantity: {quantity}\n💰 Cost: {cost} coins\n📊 Status: {status}\n📅 Created: {date}",
        "order_pending": "⏳ Pending",
        "order_in_progress": "🔄 In Progress",
        "order_completed": "✅ Completed",
        "order_partial": "⚠️ Partial",
        "order_cancelled": "❌ Cancelled",
        "order_error": "❌ Error",
        
        # Referrals
        "referral_info": "👥 Referral Program\n\n🎁 Earn {bonus} coins for each referral!\n👥 Total referrals: {count}\n💰 Total earned: {earned} coins\n\n🔗 Your referral link:\n{link}",
        "referral_joined": "🎉 New user joined via your referral! You earned {bonus} coins",
        
        # Settings
        "settings_menu": "⚙️ Settings",
        "change_language": "🌐 Change Language",
        "current_language": "Current language: {language}",
        
        # Admin
        "admin_menu": "👑 Admin Panel",
        "user_management": "👥 User Management",
        "service_management": "📊 Service Management",
        "payment_management": "💳 Payment Management",
        "analytics": "📈 Analytics",
        "settings_admin": "⚙️ Settings",
        
        # Common
        "back": "⬅️ Back",
        "cancel": "❌ Cancel",
        "confirm": "✅ Confirm",
        "yes": "✅ Yes",
        "no": "❌ No",
        "loading": "⏳ Loading...",
        "error": "❌ An error occurred. Please try again",
        "success": "✅ Success",
        "invalid_input": "❌ Invalid input",
        "access_denied": "❌ Access denied",
    },
    
    Language.RUSSIAN: {
        # Main menu
        "welcome": "🎉 Добро пожаловать в бот SMM услуг!",
        "choose_language": "Пожалуйста, выберите ваш язык:",
        "language_selected": "✅ Язык установлен на русский",
        "main_menu": "🏠 Главное меню",
        "services": "📊 Услуги",
        "balance": "💰 Баланс",
        "orders": "📋 Заказы",
        "referrals": "👥 Рефералы",
        "settings": "⚙️ Настройки",
        "support": "🆘 Поддержка",
        
        # Balance
        "your_balance": "💰 Ваш баланс: {balance} монет",
        "add_balance": "💳 Пополнить баланс",
        "transaction_history": "📊 История транзакций",
        "no_transactions": "Транзакций пока нет",
        "min_deposit": "Минимальный депозит: ${min_usd} USD",
        "max_deposit": "Максимальный депозит: ${max_usd} USD",
        
        # Payment methods
        "choose_payment_method": "💳 Выберите способ оплаты:",
        "payment_cards": "💳 Карты (Visa/Mastercard)",
        "payment_crypto": "₿ Криптовалюта",
        "payment_payme": "💙 Payme",
        "payment_click": "🟡 Click",
        "payment_uzcard": "💚 Uzcard",
        "payment_humo": "🔴 Humo",
        "enter_amount": "💵 Введите сумму в USD (${min_usd} - ${max_usd}):",
        "invalid_amount": "❌ Неверная сумма. Введите число от ${min_usd} до ${max_usd}",
        "payment_processing": "⏳ Обработка платежа...",
        "payment_success": "✅ Платеж успешен! {amount} монет добавлено на ваш баланс",
        "payment_failed": "❌ Платеж не удался. Попробуйте еще раз",
        
        # Services
        "choose_category": "📊 Выберите категорию услуг:",
        "choose_service": "Выберите услугу:",
        "no_services": "В данный момент нет доступных услуг. Пожалуйста, попробуйте позже.",
        "service_details": "📊 {name}\n💰 Цена: {price} монет за 1000\n📊 Мин: {min_qty} | Макс: {max_qty}",
        "enter_link": "🔗 Введите ссылку на социальную сеть:",
        "enter_quantity": "🔢 Введите количество ({min_qty} - {max_qty}):",
        "invalid_link": "❌ Неверная ссылка. Введите действительный URL социальной сети",
        "invalid_quantity": "❌ Неверное количество. Введите число от {min_qty} до {max_qty}",
        "insufficient_balance": "❌ Недостаточно средств. Нужно {required} монет, а у вас {current} монет",
        "order_confirmation": "📋 Подтверждение заказа\n\n🔗 Ссылка: {link}\n📊 Услуга: {service}\n🔢 Количество: {quantity}\n💰 Стоимость: {cost} монет\n\nПодтвердить заказ?",
        "order_created": "✅ Заказ успешно создан!\nID заказа: #{order_id}\n💰 {cost} монет списано с баланса",
        "order_failed": "❌ Не удалось создать заказ. Попробуйте еще раз",
        
        # Orders
        "your_orders": "📋 Ваши заказы",
        "no_orders": "Заказов пока нет",
        "order_status": "📋 Заказ #{order_id}\n📊 Услуга: {service}\n🔗 Ссылка: {link}\n🔢 Количество: {quantity}\n💰 Стоимость: {cost} монет\n📊 Статус: {status}\n📅 Создан: {date}",
        "order_pending": "⏳ Ожидание",
        "order_in_progress": "🔄 В процессе",
        "order_completed": "✅ Завершен",
        "order_partial": "⚠️ Частично",
        "order_cancelled": "❌ Отменен",
        "order_error": "❌ Ошибка",
        
        # Referrals
        "referral_info": "👥 Реферальная программа\n\n🎁 Зарабатывайте {bonus} монет за каждого реферала!\n👥 Всего рефералов: {count}\n💰 Всего заработано: {earned} монет\n\n🔗 Ваша реферальная ссылка:\n{link}",
        "referral_joined": "🎉 Новый пользователь присоединился по вашей ссылке! Вы заработали {bonus} монет",
        
        # Settings
        "settings_menu": "⚙️ Настройки",
        "change_language": "🌐 Изменить язык",
        "current_language": "Текущий язык: {language}",
        
        # Admin
        "admin_menu": "👑 Панель администратора",
        "user_management": "👥 Управление пользователями",
        "service_management": "📊 Управление услугами",
        "payment_management": "💳 Управление платежами",
        "analytics": "📈 Аналитика",
        "settings_admin": "⚙️ Настройки",
        
        # Common
        "back": "⬅️ Назад",
        "cancel": "❌ Отмена",
        "confirm": "✅ Подтвердить",
        "yes": "✅ Да",
        "no": "❌ Нет",
        "loading": "⏳ Загрузка...",
        "error": "❌ Произошла ошибка. Попробуйте еще раз",
        "success": "✅ Успешно",
        "invalid_input": "❌ Неверный ввод",
        "access_denied": "❌ Доступ запрещен",
    },
    
    Language.UZBEK: {
        # Main menu
        "welcome": "🎉 SMM xizmatlar botiga xush kelibsiz!",
        "choose_language": "Iltimos, tilingizni tanlang:",
        "language_selected": "✅ Til o'zbek tiliga o'rnatildi",
        "main_menu": "🏠 Asosiy menyu",
        "services": "📊 Xizmatlar",
        "balance": "💰 Balans",
        "orders": "📋 Buyurtmalar",
        "referrals": "👥 Taklif qilinganlar",
        "settings": "⚙️ Sozlamalar",
        "support": "🆘 Yordam",
        
        # Balance
        "your_balance": "💰 Sizning balansingiz: {balance} tanga",
        "add_balance": "💳 Balansni to'ldirish",
        "transaction_history": "📊 Tranzaksiyalar tarixi",
        "no_transactions": "Hali tranzaksiyalar yo'q",
        "min_deposit": "Minimal depozit: ${min_usd} USD",
        "max_deposit": "Maksimal depozit: ${max_usd} USD",
        
        # Payment methods
        "choose_payment_method": "💳 To'lov usulini tanlang:",
        "payment_cards": "💳 Kartalar (Visa/Mastercard)",
        "payment_crypto": "₿ Kriptovalyuta",
        "payment_payme": "💙 Payme",
        "payment_click": "🟡 Click",
        "payment_uzcard": "💚 Uzcard",
        "payment_humo": "🔴 Humo",
        "enter_amount": "💵 USD miqdorini kiriting (${min_usd} - ${max_usd}):",
        "invalid_amount": "❌ Noto'g'ri miqdor. ${min_usd} dan ${max_usd} gacha son kiriting",
        "payment_processing": "⏳ To'lov qayta ishlanmoqda...",
        "payment_success": "✅ To'lov muvaffaqiyatli! {amount} tanga balansingizga qo'shildi",
        "payment_failed": "❌ To'lov muvaffaqiyatsiz. Qayta urinib ko'ring",
        
        # Services
        "choose_category": "📊 Xizmat kategoriyasini tanlang:",
        "choose_service": "Xizmatni tanlang:",
        "no_services": "Hozircha xizmatlar mavjud emas. Iltimos keyinroq urinib ko'ring.",
        "service_details": "📊 {name}\n💰 Narx: {price} tanga 1000 ta uchun\n📊 Min: {min_qty} | Maks: {max_qty}",
        "enter_link": "🔗 Ijtimoiy tarmoq havolasini kiriting:",
        "enter_quantity": "🔢 Miqdorni kiriting ({min_qty} - {max_qty}):",
        "invalid_link": "❌ Noto'g'ri havola. Haqiqiy ijtimoiy tarmoq URL kiriting",
        "invalid_quantity": "❌ Noto'g'ri miqdor. {min_qty} dan {max_qty} gacha son kiriting",
        "insufficient_balance": "❌ Balans yetarli emas. {required} tanga kerak, lekin sizda {current} tanga bor",
        "order_confirmation": "📋 Buyurtmani tasdiqlash\n\n🔗 Havola: {link}\n📊 Xizmat: {service}\n🔢 Miqdor: {quantity}\n💰 Narx: {cost} tanga\n\nBuyurtmani tasdiqlaysizmi?",
        "order_created": "✅ Buyurtma muvaffaqiyatli yaratildi!\nBuyurtma ID: #{order_id}\n💰 {cost} tanga balansdan yechildi",
        "order_failed": "❌ Buyurtma yaratilmadi. Qayta urinib ko'ring",
        
        # Orders
        "your_orders": "📋 Sizning buyurtmalaringiz",
        "no_orders": "Hali buyurtmalar yo'q",
        "order_status": "📋 Buyurtma #{order_id}\n📊 Xizmat: {service}\n🔗 Havola: {link}\n🔢 Miqdor: {quantity}\n💰 Narx: {cost} tanga\n📊 Holat: {status}\n📅 Yaratilgan: {date}",
        "order_pending": "⏳ Kutilmoqda",
        "order_in_progress": "🔄 Jarayonda",
        "order_completed": "✅ Yakunlandi",
        "order_partial": "⚠️ Qisman",
        "order_cancelled": "❌ Bekor qilindi",
        "order_error": "❌ Xatolik",
        
        # Referrals
        "referral_info": "👥 Taklif dasturi\n\n🎁 Har bir taklif uchun {bonus} tanga ishlang!\n👥 Jami taklif qilinganlar: {count}\n💰 Jami ishlangan: {earned} tanga\n\n🔗 Sizning taklif havolangiz:\n{link}",
        "referral_joined": "🎉 Yangi foydalanuvchi sizning havola orqali qo'shildi! Siz {bonus} tanga ishladingiz",
        
        # Settings
        "settings_menu": "⚙️ Sozlamalar",
        "change_language": "🌐 Tilni o'zgartirish",
        "current_language": "Joriy til: {language}",
        
        # Admin
        "admin_menu": "👑 Admin paneli",
        "user_management": "👥 Foydalanuvchilarni boshqarish",
        "service_management": "📊 Xizmatlarni boshqarish",
        "payment_management": "💳 To'lovlarni boshqarish",
        "analytics": "📈 Analitika",
        "settings_admin": "⚙️ Sozlamalar",
        
        # Common
        "back": "⬅️ Orqaga",
        "cancel": "❌ Bekor qilish",
        "confirm": "✅ Tasdiqlash",
        "yes": "✅ Ha",
        "no": "❌ Yo'q",
        "loading": "⏳ Yuklanmoqda...",
        "error": "❌ Xatolik yuz berdi. Qayta urinib ko'ring",
        "success": "✅ Muvaffaqiyatli",
        "invalid_input": "❌ Noto'g'ri kiritilgan",
        "access_denied": "❌ Ruxsat rad etildi",
    }
}


def get_text(key: str, language: Language = Language.ENGLISH, **kwargs) -> str:
    """Get translated text by key and language"""
    try:
        text = TRANSLATIONS[language].get(key, TRANSLATIONS[Language.ENGLISH].get(key, key))
        if kwargs:
            return text.format(**kwargs)
        return text
    except (KeyError, ValueError):
        return key


def get_language_name(language: Language) -> str:
    """Get language display name"""
    names = {
        Language.ENGLISH: "English 🇬🇧",
        Language.RUSSIAN: "Русский 🇷🇺",
        Language.UZBEK: "O'zbek 🇺🇿"
    }
    return names.get(language, "English 🇬🇧")
