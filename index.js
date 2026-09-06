const { Telegraf, Markup } = require('telegraf');
const express = require('express');

const BOT_TOKEN = "8916087599:AAEzVTNSd0JjZwfal0E7pdX5bYEMpYTcehg";
const app = express();
const bot = new Telegraf(BOT_TOKEN);

app.use(express.static('public'));
app.use(express.json());

bot.start((ctx) => {
  ctx.reply(
    'እንኳን ወደ ቢንጎ ጨዋታ በደህና መጡ! ለመመዝገብ የስልክ ቁጥርዎን ያጋሩ።',
    Markup.keyboard([
      [Markup.button.contactRequest('📲 በስልክ ቁጥር ተመዝገብ')]
    ]).resize()
  );
});

bot.on('contact', (ctx) => {
  const phone = ctx.message.contact.phone_number;
  ctx.reply(
    `ምዝገባዎ ተሳክቷል! የስልክ ቁጥር: ${phone}`,
    Markup.inlineKeyboard([
      [Markup.button.webApp('🎮 የቢንጎ Mini App ክፈት', 'https://your-domain.com')]
    ])
  );
});

bot.launch().then(() => console.log('Bot fully started!')).catch(err => console.error(err));
app.listen(3000, () => console.log('Server running on port 3000'));
