const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');

const TELEGRAM_TOKEN = process.env.TELEGRAM_TOKEN || '8352301516:AAFu5U234zRh6XIfeE5h9hlxf3jEecne7aQ';

// بررسی وجود توکن
if (!TELEGRAM_TOKEN) {
    console.error('❌ توکن تلگرام ارائه نشده!');
    process.exit(1);
}

const bot = new TelegramBot(TELEGRAM_TOKEN, {
    polling: {
        interval: 1000,
        params: {
            timeout: 30,
            limit: 100
        }
    }
});

console.log('🤖 ربات هوشمند راه‌اندازی شد...');
console.log('🔑 توکن:', TELEGRAM_TOKEN.substring(0, 10) + '...');

// تابع پیشرفته برای ارتباط با Puter.js
async function callPuterAI(userMessage) {
    try {
        console.log('📨 ارسال به Puter.js:', userMessage.substring(0, 50) + '...');
        
        const response = await axios.post('https://api.puter.com/v1/chat/completions', {
            messages: [{ 
                role: 'user', 
                content: userMessage 
            }],
            model: 'gpt-4',
            max_tokens: 1000,
            temperature: 0.7,
            stream: false
        }, {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'Telegram-AI-Bot/1.0'
            },
            timeout: 30000,
            validateStatus: function (status) {
                return status < 500; // فقط خطاهای سرور رو catch کن
            }
        });

        if (response.data && response.data.choices && response.data.choices[0]) {
            console.log('✅ پاسخ دریافت شد از Puter.js');
            return response.data.choices[0].message.content;
        } else {
            throw new Error('پاسخ نامعتبر از Puter.js');
        }
        
    } catch (error) {
        console.error('❌ خطا در Puter.js:', error.response?.data || error.message);
        
        // پاسخ‌های هوشمندانه در صورت خطا
        const fallbackResponses = [
            "متأسفم، سرور هوش مصنوعی در دسترس نیست. لطفاً کمی بعد تلاش کنید. 🚀",
            "در حال حاضر امکان پردازش پیام وجود ندارد. لطفاً صبر کنید... ⏳",
            "connection error. بعداً امتحان کنید. 🔌",
            "سرویس هوش مصنوعی موقتاً unavailable هست. 📡"
        ];
        
        return fallbackResponses[Math.floor(Math.random() * fallbackResponses.length)];
    }
}

// مدیریت پیام‌های کاربر
bot.on('message', async (msg) => {
    const chatId = msg.chat.id;
    const userMessage = msg.text;
    const userName = msg.from.first_name || 'کاربر';

    // نادیده گرفتن پیام‌های غیرمتنی و دستورات
    if (!userMessage || userMessage.startsWith('/')) {
        return;
    }

    console.log(`💬 پیام از ${userName}: ${userMessage}`);

    try {
        // نشان دادن وضعیت تایپ
        await bot.sendChatAction(chatId, 'typing');
        
        // دریافت پاسخ از هوش مصنوعی
        const aiResponse = await callPuterAI(userMessage);
        
        // ارسال پاسخ به کاربر
        await bot.sendMessage(chatId, aiResponse);
        
        console.log(`✅ پاسخ ارسال شد به ${userName}`);
        
    } catch (error) {
        console.error('❌ خطا در پردازش پیام:', error);
        await bot.sendMessage(chatId, 
            '⚠️ خطایی در پردازش پیام رخ داد. لطفاً دوباره تلاش کنید.\n\n' +
            '🔧 در حال بررسی مشکل...'
        );
    }
});

// دستور start
bot.onText(/\/start/, (msg) => {
    const chatId = msg.chat.id;
    const userName = msg.from.first_name;

    const welcomeMessage = `
🤖 سلام ${userName}! به ربات هوش مصنوعی خوش آمدید!

✨ من با استفاده از Puter.js کار می‌کنم و می‌تونم:

• به سوالاتت پاسخ بدم 🧠
• در مکالمه همراهت باشم 💬  
• متن بنویسم 📝
• ایده پردازی کنم 💡

🚀 ویژگی‌ها:
• هوش مصنوعی پیشرفته
• پاسخ‌های هوشمندانه
• 24/7 آنلاین
• بدون نیاز به VPN

📝 فقط کافیه پیام بفرستی و من پاسخ میدم!

💡 برای اطلاعات بیشتر /help را بفرست
    `;

    bot.sendMessage(chatId, welcomeMessage);
});

// دستور help
bot.onText(/\/help/, (msg) => {
    const chatId = msg.chat.id;

    const helpMessage = `
💡 راهنما و دستورات:

/start - شروع کار با ربات
/help - نمایش این راهنما  
/status - وضعیت ربات
/about - اطلاعات فنی

📝 نحوه استفاده:
• فقط پیام متنی بفرست
• منتظر پاسخ باش (۱۰-۳۰ ثانیه)
• در صورت خطا، دوباره تلاش کن

🌐 فناوری‌ها:
• Telegram Bot API
• Puter.js AI
• Node.js
• Railway Hosting

⚡ نسخه: 2.0.0
    `;

    bot.sendMessage(chatId, helpMessage);
});

// دستور status
bot.onText(/\/status/, (msg) => {
    const chatId = msg.chat.id;
    const uptime = process.uptime();
    const hours = Math.floor(uptime / 3600);
    const minutes = Math.floor((uptime % 3600) / 60);
    const seconds = Math.floor(uptime % 60);

    const statusMessage = `
📊 وضعیت ربات:

🟢 وضعیت: فعال
⏰ زمان فعالیت: ${hours} ساعت ${minutes} دقیقه ${seconds} ثانیه
🤖 حالت: Polling
🌐 میزبان: Railway.app
💾 حافظه: ${(process.memoryUsage().heapUsed / 1024 / 1024).toFixed(2)} MB
🔗 سرویس: Puter.js AI

✅ همه چیز正常 است!
    `;

    bot.sendMessage(chatId, statusMessage);
});

// دستور about
bot.onText(/\/about/, (msg) => {
    const chatId = msg.chat.id;

    const aboutMessage = `
ℹ️ اطلاعات فنی:

این یک ربات هوش مصنوعی است که با:
• Node.js توسعه داده شده
• از Puter.js برای هوش مصنوعی استفاده می‌کند
• روی Railway.app میزبانی می‌شود
• به صورت 24/7 آنلاین است

🔧 معماری:
• Telegram Bot API
• RESTful APIs
• Async/Await
• Error Handling

🚀 امکانات:
• پردازش زبان طبیعی
• پاسخ‌های هوشمند
• مدیریت خطا
• logging پیشرفته

⚡ نسخه: 2.0.0
    `;

    bot.sendMessage(chatId, aboutMessage);
});

// مدیریت خطاهای全局
process.on('unhandledRejection', (error) => {
    console.error('⚠️ Unhandled Rejection:', error);
});

process.on('uncaughtException', (error) => {
    console.error('⚠️ Uncaught Exception:', error);
});

// وقتی polling شروع می‌شود
bot.on('polling_start', () => {
    console.log('✅ Polling شروع شد. ربات آماده دریافت پیام...');
});

// مدیریت graceful shutdown
process.on('SIGINT', () => {
    console.log('\n🛑 دریافت سیگنال خاموشی...');
    bot.stopPolling();
    console.log('✅ ربات متوقف شد');
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('\n🛑 دریافت فرمان خاموشی...');
    bot.stopPolling();
    console.log('✅ ربات متوقف شد');
    process.exit(0);
});

module.exports = bot;
