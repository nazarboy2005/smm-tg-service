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
        "payment_paypal": "💳 PayPal",
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
        "choose_service_type": "Choose service type:",
        "no_services": "No services available at the moment. Please try again later.",
        "popular_services": "Popular Services",
        "popular_services_desc": "Most popular services chosen by our customers:",
        "telegram_services": "Telegram Services",
        "instagram_services": "Instagram Services",
        "tiktok_services": "TikTok Services",
        "youtube_services": "YouTube Services",
        "members": "Members",
        "followers": "Followers",
        "subscribers": "Subscribers",
        "views": "Views",
        "likes": "Likes",
        "comments": "Comments",
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
        
        # Stickers
        "sticker_response_1": "😄 Nice sticker! Let me show you our services:",
        "sticker_response_2": "🎉 I love stickers too! Check out what we offer:",
        "sticker_response_3": "😊 Thanks for the sticker! Here's your menu:",
        
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
        "invalid_value": "❌ Invalid value",
        "please_try_again": "Please try again",
        "error_updating_setting": "❌ Error updating setting",
        "error_getting_configuration": "❌ Error getting configuration",
        "error_exporting_settings": "❌ Error exporting settings",
        "setting_key_not_found": "❌ Error: Setting key not found",
        "need_help": "Need help? We're here to assist you!",
        "contact_methods": "Contact Methods:",
        "support_hours": "Support Hours:",
        "common_issues": "Common Issues:",
        "before_contacting_support": "Before contacting support:",
        "select_option_below": "Select an option below:",
        "payment_problems": "Payment problems",
        "order_status_questions": "Order status questions",
        "account_issues": "Account issues",
        "technical_problems": "Technical problems",
        "check_order_history": "Check your order history",
        "verify_payment_status": "Verify payment status",
        "read_faq_section": "Read our FAQ section",
        "select_service_to_start": "Select a service to get started:",
        "last_7_days": "Last 7 days",
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
        "payment_paypal": "💳 PayPal",
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
        "choose_service_type": "Выберите тип услуги:",
        "no_services": "В данный момент нет доступных услуг. Пожалуйста, попробуйте позже.",
        "popular_services": "Популярные услуги",
        "popular_services_desc": "Самые популярные услуги, выбранные нашими клиентами:",
        "telegram_services": "Услуги Telegram",
        "instagram_services": "Услуги Instagram",
        "tiktok_services": "Услуги TikTok",
        "youtube_services": "Услуги YouTube",
        "members": "Участники",
        "followers": "Подписчики",
        "subscribers": "Подписчики",
        "views": "Просмотры",
        "likes": "Лайки",
        "comments": "Комментарии",
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
        
        # Stickers
        "sticker_response_1": "😄 Отличный стикер! Позвольте показать вам наши услуги:",
        "sticker_response_2": "🎉 Я тоже люблю стикеры! Посмотрите, что мы предлагаем:",
        "sticker_response_3": "😊 Спасибо за стикер! Вот ваше меню:",
        
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
        "invalid_value": "❌ Неверное значение",
        "please_try_again": "Попробуйте еще раз",
        "error_updating_setting": "❌ Ошибка обновления настройки",
        "error_getting_configuration": "❌ Ошибка получения конфигурации",
        "error_exporting_settings": "❌ Ошибка экспорта настроек",
        "setting_key_not_found": "❌ Ошибка: Ключ настройки не найден",
        "need_help": "Нужна помощь? Мы здесь, чтобы помочь вам!",
        "contact_methods": "Способы связи:",
        "support_hours": "Часы поддержки:",
        "common_issues": "Частые проблемы:",
        "before_contacting_support": "Перед обращением в поддержку:",
        "select_option_below": "Выберите опцию ниже:",
        "payment_problems": "Проблемы с оплатой",
        "order_status_questions": "Вопросы о статусе заказа",
        "account_issues": "Проблемы с аккаунтом",
        "technical_problems": "Технические проблемы",
        "check_order_history": "Проверьте историю заказов",
        "verify_payment_status": "Проверьте статус платежа",
        "read_faq_section": "Прочитайте раздел FAQ",
        "select_service_to_start": "Выберите услугу для начала:",
        "last_7_days": "Последние 7 дней",
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
        "payment_paypal": "💳 PayPal",
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
        "choose_service_type": "Xizmat turini tanlang:",
        "no_services": "Hozircha xizmatlar mavjud emas. Iltimos keyinroq urinib ko'ring.",
        "popular_services": "Mashhur xizmatlar",
        "popular_services_desc": "Mijozlarimiz tomonidan eng ko'p tanlanadigan xizmatlar:",
        "telegram_services": "Telegram xizmatlari",
        "instagram_services": "Instagram xizmatlari",
        "tiktok_services": "TikTok xizmatlari",
        "youtube_services": "YouTube xizmatlari",
        "members": "A'zolar",
        "followers": "Obunachilar",
        "subscribers": "Obunachilar",
        "views": "Ko'rishlar",
        "likes": "Yoqtirishlar",
        "comments": "Izohlar",
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
        
        # Stickers
        "sticker_response_1": "😄 Ajoyib stiker! Xizmatlarimizni ko'rsataman:",
        "sticker_response_2": "🎉 Men ham stikerlarni yaxshi ko'raman! Takliflarimizni ko'ring:",
        "sticker_response_3": "😊 Stiker uchun rahmat! Menyuingiz:",
        
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
        "invalid_value": "❌ Noto'g'ri qiymat",
        "please_try_again": "Qayta urinib ko'ring",
        "error_updating_setting": "❌ Sozlashni yangilashda xatolik",
        "error_getting_configuration": "❌ Konfiguratsiyani olishda xatolik",
        "error_exporting_settings": "❌ Sozlamalarni eksport qilishda xatolik",
        "setting_key_not_found": "❌ Xatolik: Sozlash kaliti topilmadi",
        "need_help": "Yordam kerakmi? Sizga yordam berish uchun bu yerdamiz!",
        "contact_methods": "Aloqa usullari:",
        "support_hours": "Yordam soatlari:",
        "common_issues": "Keng tarqalgan muammolar:",
        "before_contacting_support": "Yordam bilan bog'lanishdan oldin:",
        "select_option_below": "Quyidagi variantni tanlang:",
        "payment_problems": "To'lov muammolari",
        "order_status_questions": "Buyurtma holati savollari",
        "account_issues": "Hisob muammolari",
        "technical_problems": "Texnik muammolar",
        "check_order_history": "Buyurtmalar tarixini tekshiring",
        "verify_payment_status": "To'lov holatini tekshiring",
        "read_faq_section": "FAQ bo'limini o'qiting",
        "select_service_to_start": "Boshlash uchun xizmatni tanlang:",
        "last_7_days": "So'nggi 7 kun",
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
