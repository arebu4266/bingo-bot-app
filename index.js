const { Telegraf, Markup } = require('telegraf');
const express = require('express');

const BOT_TOKEN = process.env.BOT_TOKEN || "8916087599:AAEzVTNsD0JjZwfalO...";
const app = express();
const bot = new Telegraf(BOT_TOKEN);

app.use(express.static('public'));
app.use(express.json());

// ተጠቃሚው /start ሲል ስልክ ቁጥሩን እንዲልክ መጠየቅ
bot.start((ctx) => {
    return ctx.reply(
        `👋 እንኳን ወደ ሐገር ቢንጋ (Hager Bingo) በሰላም መጡ!\n\nለመቀጠል እባክዎ ከታች ያለውን አዝራር በመጫን ስልክ ቁጥርዎን ያጋሩ (Share Contact)።`,
        Markup.keyboard([
            [Markup.button.contactRequest('📱 ስልክ ቁጥር አጋራ (Share Contact)')]
        ]).resize()
    );
});

// ተጠቃሚው ስልክ ቁጥሩን ሼር ሲያደርግ ዋናውን ምናሌ (Menu) ማሳየት
bot.on('contact', (ctx) => {
    const phone = ctx.message.contact.phone_number;
    
    const welcomeMessage = `✅ ምዝገባዎ ተሳክቷል! ስልክ ቁጥርዎ: ${phone}\n\n💳 ቴሌብር (Telebirr) በመጠቀም አካውንትዎን ጫን አድርገው ጨዋታውን ይጀምሩ።`;
    
    return ctx.reply(
        welcomeMessage,
        Markup.inlineKeyboard([
            [Markup.button.webApp('🎮 Play Bingo', 'https://bingo-bot-app-production.up.railway.app')],
            [Markup.button.callback('💰 Balance', 'balance'), Markup.button.callback('💲 Deposit (ቴሌብር)', 'deposit')],
            [Markup.button.callback('📖 Instruction', 'instruction'), Markup.button.callback('📞 Support', 'support')],
            [Markup.button.callback('💵 Withdraw', 'withdraw')]
        ])
    );
});

// የ Deposit (ቴሌብር) ቁልፍ ሲጫን
bot.action('deposit', (ctx) => {
    ctx.reply(`💳 **የቴሌብር ዲፖዚት (Telebirr Deposit)**\n\nቁጥር: \`0934664761\`\nስም: **ፍጡማ ኢብራሂም**\n\nእባክዎ ከላይ ባለው ቁጥር ብር ላኩና የትራንዛክሽን ቁጥሩን (Transaction ID) በዚህ ቦት ይላኩ።`);
});

// የ Balance ቁልፍ ሲጫን
bot.action('balance', (ctx) => {
    ctx.reply(`💰 የአካውንትዎ ቀሪ ሂሳብ: **0.00 ብር**`);
});

// የ Instruction ቁልፍ ሲጫን
bot.action('instruction', (ctx) => {
    ctx.reply(`📖 **እንዴት ይጫወታሉ?**\n1. ቴሌብር በመጠቀም አካውንትዎን ዎችን ያድርጉ።\n2. 'Play Bingo' በመጫን ሚኒ አፑን ይክፈቱ።\n3. 200 ቁጥሮች አውቶማቲክ እየተጠሩ ይጫወቱ!`);
});

bot.action('support', (ctx) => {
    ctx.reply(`📞 ድጋፍ ከፈለጉ @admin ያነጋግሩ።`);
});

bot.action('withdraw', (ctx) => {
    ctx.reply(`💵 የውጭ ማውጣት (Withdraw) ጥያቄዎን ለማስተካከል እባክዎ አድሚን ያነጋግሩ።`);
});

bot.launch().then(() => console.log('Bot fully started...'));
app.listen(process.env.PORT || 3000, () => console.log('Server running...'));
