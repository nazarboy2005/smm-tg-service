"""
Enhanced internationalization utilities with better language support
"""
from typing import Dict, Any, Optional
from enum import Enum
from loguru import logger


class Language(Enum):
    """Supported languages"""
    ENGLISH = "en"
    UZBEK = "uz"
    RUSSIAN = "ru"


class EnhancedI18n:
    """Enhanced internationalization manager"""
    
    def __init__(self):
        self.translations = {
            Language.ENGLISH: {
                "welcome": "🎉 Welcome to SMM Services Bot!\n\n👋 Hello, {name}!\n\n🌟 Premium Social Media Marketing Services\n\n📊 What we offer:\n• Instagram Followers & Likes\n• YouTube Views & Subscribers\n• TikTok Followers & Views\n• Twitter Followers & Retweets\n• And much more!\n\n💰 Features:\n• Instant delivery\n• 24/7 support\n• Secure payments\n• Money-back guarantee\n\n💡 Select an option below to get started",
                "language_selected": "✅ Language set to {language}",
                "price_per_1000": "coins per 1000 members",
                "service_price": "Price: {price} coins per 1000 members",
                "order_now": "🛒 Order Now",
                "price_calculator": "📊 Price Calculator",
                "back_to_menu": "🔙 Back to Main Menu",
                "error_occurred": "❌ An error occurred. Please try again.",
                "service_not_found": "❌ Service not found",
                "invalid_platform": "❌ Invalid platform selection",
                "loading_services": "❌ Error loading services",
                # Keyboard texts
                "browse_services": "🛍️ Browse Services",
                "my_balance": "💰 My Balance",
                "my_orders": "📊 My Orders",
                "popular_services": "🔥 Popular Services",
                "settings": "⚙️ Settings",
                "support": "🆘 Support",
                "admin_panel": "👑 Admin Panel",
                "back_to_menu": "🔙 Back to Main Menu",
                "select_language": "🌐 Select Language",
                "add_funds": "💳 Add Funds",
                "order_history": "📋 Order History",
                "language_settings": "🌐 Language Settings",
                "contact_support": "📞 Contact Support",
                "faq": "❓ FAQ",
                # Admin panel texts
                "admin_panel_welcome": "👑 Admin Panel\n\nWelcome, {name}!🇶🇦\n\n📋 Available Admin Functions:\n• User Management\n• Service Management\n• Payment Management\n• Analytics\n• Settings\n\n💡 Select an option below to get started",
                "user_management": "👥👥 User Management",
                "service_management": "📊📈 Service Management", 
                "payment_management": "💳💳 Payment Management",
                "analytics": "📈📈 Analytics",
                "admin_settings": "⚙️⚙️ Settings",
                "back": "⬅️ Back"
            },
            Language.UZBEK: {
                "welcome": "🎉 SMM Xizmatlar Botiga Xush Kelibsiz!\n\n👋 Salom, {name}!\n\n🌟 Premium Ijtimoiy Tarmoq Marketing Xizmatlari\n\n📊 Bizning xizmatlarimiz:\n• Instagram Obunachilar va Layklar\n• YouTube Ko'rishlar va Obunachilar\n• TikTok Obunachilar va Ko'rishlar\n• Twitter Obunachilar va Retweetlar\n• Va boshqalar!\n\n💰 Xususiyatlar:\n• Darhol yetkazib berish\n• 24/7 qo'llab-quvvatlash\n• Xavfsiz to'lovlar\n• Pulni qaytarish kafolati\n\n💡 Boshlash uchun quyidagi variantlardan birini tanlang",
                "language_selected": "✅ Til {language} ga o'rnatildi",
                "price_per_1000": "1000 a'zo uchun tangalar",
                "service_price": "Narx: {price} tanga 1000 a'zo uchun",
                "order_now": "🛒 Buyurtma Berish",
                "price_calculator": "📊 Narx Kalkulyatori",
                "back_to_menu": "🔙 Asosiy Menuga Qaytish",
                "error_occurred": "❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.",
                "service_not_found": "❌ Xizmat topilmadi",
                "invalid_platform": "❌ Noto'g'ri platforma tanlovi",
                "loading_services": "❌ Xizmatlarni yuklashda xatolik",
                # Keyboard texts
                "browse_services": "🛍️ Xizmatlarni Ko'rish",
                "my_balance": "💰 Mening Balansim",
                "my_orders": "📊 Mening Buyurtmalarim",
                "popular_services": "🔥 Mashhur Xizmatlar",
                "settings": "⚙️ Sozlamalar",
                "support": "🆘 Qo'llab-quvvatlash",
                "admin_panel": "👑 Admin Panel",
                "back_to_menu": "🔙 Asosiy Menuga Qaytish",
                "select_language": "🌐 Tilni Tanlash",
                "add_funds": "💳 Pul Qo'shish",
                "order_history": "📋 Buyurtma Tarixi",
                "language_settings": "🌐 Til Sozlamalari",
                "contact_support": "📞 Qo'llab-quvvatlashga Murojaat",
                "faq": "❓ Savol-Javob",
                # Admin panel texts
                "admin_panel_welcome": "👑 Admin Panel\n\nXush kelibsiz, {name}!🇶🇦\n\n📋 Mavjud Admin Funksiyalari:\n• Foydalanuvchilarni Boshqarish\n• Xizmatlarni Boshqarish\n• To'lovlarni Boshqarish\n• Analitika\n• Sozlamalar\n\n💡 Boshlash uchun quyidagi variantlardan birini tanlang",
                "user_management": "👥👥 Foydalanuvchilarni Boshqarish",
                "service_management": "📊📈 Xizmatlarni Boshqarish", 
                "payment_management": "💳💳 To'lovlarni Boshqarish",
                "analytics": "📈📈 Analitika",
                "admin_settings": "⚙️⚙️ Sozlamalar",
                "back": "⬅️ Orqaga"
            },
            Language.RUSSIAN: {
                "welcome": "🎉 Добро пожаловать в SMM Services Bot!\n\n👋 Привет, {name}!\n\n🌟 Премиум услуги маркетинга в социальных сетях\n\n📊 Что мы предлагаем:\n• Instagram Подписчики и Лайки\n• YouTube Просмотры и Подписчики\n• TikTok Подписчики и Просмотры\n• Twitter Подписчики и Ретвиты\n• И многое другое!\n\n💰 Особенности:\n• Мгновенная доставка\n• Поддержка 24/7\n• Безопасные платежи\n• Гарантия возврата денег\n\n💡 Выберите опцию ниже, чтобы начать",
                "language_selected": "✅ Язык установлен на {language}",
                "price_per_1000": "монет за 1000 участников",
                "service_price": "Цена: {price} монет за 1000 участников",
                "order_now": "🛒 Заказать Сейчас",
                "price_calculator": "📊 Калькулятор Цен",
                "back_to_menu": "🔙 Назад в Главное Меню",
                "error_occurred": "❌ Произошла ошибка. Пожалуйста, попробуйте снова.",
                "service_not_found": "❌ Услуга не найдена",
                "invalid_platform": "❌ Неверный выбор платформы",
                "loading_services": "❌ Ошибка загрузки услуг",
                # Keyboard texts
                "browse_services": "🛍️ Просмотр Услуг",
                "my_balance": "💰 Мой Баланс",
                "my_orders": "📊 Мои Заказы",
                "popular_services": "🔥 Популярные Услуги",
                "settings": "⚙️ Настройки",
                "support": "🆘 Поддержка",
                "admin_panel": "👑 Панель Администратора",
                "back_to_menu": "🔙 Назад в Главное Меню",
                "select_language": "🌐 Выбрать Язык",
                "add_funds": "💳 Пополнить Счет",
                "order_history": "📋 История Заказов",
                "language_settings": "🌐 Настройки Языка",
                "contact_support": "📞 Связаться с Поддержкой",
                "faq": "❓ Часто Задаваемые Вопросы",
                # Admin panel texts
                "admin_panel_welcome": "👑 Панель Администратора\n\nДобро пожаловать, {name}!🇶🇦\n\n📋 Доступные Функции Администратора:\n• Управление Пользователями\n• Управление Услугами\n• Управление Платежами\n• Аналитика\n• Настройки\n\n💡 Выберите опцию ниже, чтобы начать",
                "user_management": "👥👥 Управление Пользователями",
                "service_management": "📊📈 Управление Услугами", 
                "payment_management": "💳💳 Управление Платежами",
                "analytics": "📈📈 Аналитика",
                "admin_settings": "⚙️⚙️ Настройки",
                "back": "⬅️ Назад"
            }
        }
    
    def get_text(self, key: str, language: Language, **kwargs) -> str:
        """Get translated text"""
        try:
            if language not in self.translations:
                language = Language.ENGLISH
            
            text = self.translations[language].get(key, self.translations[Language.ENGLISH].get(key, key))
            return text.format(**kwargs) if kwargs else text
        except Exception as e:
            logger.error(f"Error getting translation for key '{key}' in language {language}: {e}")
            return key
    
    def get_language_name(self, language: Language) -> str:
        """Get language display name"""
        names = {
            Language.ENGLISH: "English",
            Language.UZBEK: "O'zbekcha",
            Language.RUSSIAN: "Русский"
        }
        return names.get(language, "English")


# Global instance
i18n = EnhancedI18n()


def get_text(key: str, language: Language = Language.ENGLISH, **kwargs) -> str:
    """Convenience function to get translated text"""
    return i18n.get_text(key, language, **kwargs)


def get_language_name(language: Language) -> str:
    """Convenience function to get language name"""
    return i18n.get_language_name(language)


def get_welcome_text(language: Language, name: str) -> str:
    """Get welcome text for a specific language"""
    return get_text("welcome", language, name=name)


def get_service_price_text(price: float, language: Language = Language.ENGLISH) -> str:
    """Get service price text"""
    return get_text("service_price", language, price=price)
