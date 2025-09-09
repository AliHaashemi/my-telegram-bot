const TelegramBot = require('node-telegram-bot-api');

// خواندن توکن از environment variables
const TELEGRAM_TOKEN = process.env.TELEGRAM_TOKEN;

const bot = new TelegramBot(TELEGRAM_TOKEN, {
    polling: {
        interval: 1000,
        params: {
            timeout: 30,
            limit: 100
        }
    }
});

console.log('🚀 ربات روی سرور Railway راه‌اندازی شد...');

// مدیریت خطاها
bot.on('polling_error', (error) => {
    console.log('⚠️ خطای اتصال:', error.code);
});

// تابع تولید پاسخ
function generateResponse(message) {
    const responses = {
        'سلام': 'سلام! چطوری؟ 😊',
        'خوبی': 'من خوبم ممنون! تو چطوری؟ 🤖',
        'اسمت چیه': 'من ربات تو روی Railway هستم! 🚀',
        'ساعت چنده': `ساعت: ${new Date().toLocaleTimeString('fa-IR')} ⏰`,
        'default': 'جالب بود! بیشتر بگو... 💬'
    };

    const lowerMsg = message.toLowerCase();
    if (lowerMsg.includes('سلام')) return responses['سلام'];
    if (lowerMsg.includes('خوبی')) return responses['خوبی'];
    if (lowerMsg.includes('اسم')) return responses['اسمت چیه'];
    if (lowerMsg.includes('ساعت')) return responses['ساعت چنده'];
    
    return responses['default'];
}

// مدیریت پیام‌ها
bot.on('message', async (msg) => {
    const chatId = msg.chat.id;
    const userMessage = msg.text;

    if (!userMessage || userMessage.startsWith('/')) return;

    try {
        await bot.sendChatAction(chatId, 'typing');
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        const response = generateResponse(userMessage);
        await bot.sendMessage(chatId, response);
        
    } catch (error) {
        console.log('❌ خطا:', error.message);
    }
});

// دستورات
bot.onText(/\/start/, (msg) => {
    bot.sendMessage(msg.chat.id, 
        '🤖 سلام! من روی Railway部署 شدم! 🚀\n\n' +
        '✨ می‌تونی با من چت کنی\n' +
        '🌐 24/7 آنلاین هستم\n' +
        '⚡ بدون نیاز به VPN!'
    );
});

bot.onText(/\/info/, (msg) => {
    bot.sendMessage(msg.chat.id,
        'ℹ️ اطلاعات:\n\n' +
        '• میزبان: Railway.app\n' +
        '• وضعیت: فعال\n' +
        '• منطقه: خارج از ایران\n' +
        '• نسخه: 1.0.0'
    );
});

// مدیریت خطاهای سرور
process.on('unhandledRejection', (error) => {
    console.log('⚠️ Unhandled Rejection:', error);
});

process.on('uncaughtException', (error) => {
    console.log('⚠️ Uncaught Exception:', error);
});

console.log('✅ ربات آماده است...');