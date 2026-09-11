const { Telegraf, Markup } = require('telegraf');
const express = require('express');

const BOT_TOKEN = process.env.BOT_TOKEN;
const app = express();
const bot = new Telegraf(BOT_TOKEN);

app.use(express.static('public'));
app.use(express.json());

// ለ Render Health Check የሚሆን ሮት
app.get('/', (req, res) => {
  res.send('Bot and Web App are running successfully!');
});

// /start ትዕዛዝ
bot.start((ctx) => {
  return ctx.reply(
    '👋 እንኳን ወደ ሀገር ቢንጎ (Hager Bingo) በሰላም መጡ!\n\nየቴሌግራም ስልክ ቁጥርዎን ለማካፈል ከታች ያለውን ቁልፍ ይጫኑ።',
    Markup.keyboard([
      [Markup.button.contactRequest('📱 ስልክ ቁጥር አጋራ')]
    ]).resize()
  );
});

// ስልክ ቁጥር ሲልክ የሚቀበለው
bot.on('contact', (ctx) => {
  const phone = ctx.message.contact.phone_number;
  const welcomeMessage = `✅ ምዝገባ ተሳክቷል! ስልክ ቁጥር: ${phone}`;

  return ctx.reply(
    welcomeMessage,
    Markup.inlineKeyboard([
      [Markup.button.webApp('🎮 Play Bingo', 'https://bingo-bot-app.onrender.com')],
      [Markup.button.callback('💰 Balance', 'balance'), Markup.button.callback('💲 Deposit (ትራንስፈር)', 'deposit')],
      [Markup.button.callback('📖 Instruction', 'instruction'), Markup.button.callback('📞 Support', 'support')],
      [Markup.button.callback('💵 Withdrawl (ብር ማውጣት)', 'withdraw')]
    ])
  );
});

// የ Deposit ቁልፍ ሲጫን
bot.action('deposit', (ctx) => {
  ctx.reply('🏦 **የቴሌብር ደፖዚት (Telebirr Deposit)**\n\nብር ለመላክ የሚከተለውን አካውንት ይጠቀሙ...');
});

// የ Balance ቁልፍ ሲጫን
bot.action('balance', (ctx) => {
  ctx.reply('💰 የአካውንትዎ ቀሪ ሂሳብ: **0.00 ብር**');
});

// የ Instruction ቁልፍ ሲጫን
bot.action('instruction', (ctx) => {
  ctx.reply('📖 **እንዴት ይጫወታሉ?**\n1. ቴሌግራምን በመጠቀም አካውንት ይክፈቱ...');
});

// የ Support ቁልፍ ሲጫን
bot.action('support', (ctx) => {
  ctx.reply('📞 ድጋፍ ካፈለጉ @admin ያነጋግሩ።');
});

// የ Withdraw ቁልፍ ሲጫን
bot.action('withdraw', (ctx) => {
  ctx.reply('💵 የብር ማውጣት (Withdraw) ጥያቄን ለማስተካከል እባክዎ ከላይ ያሉትን መመሪያዎች ይከተሉ።');
});

// ሰርቨሩን እና ቦቱን በቅደም ተከተል ማስነሳት
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  
  bot.launch().then(() => {
    console.log('Bot fully started...');
  }).catch((err) => {
    console.error('Failed to launch bot:', err);
  });
});
