from aiogram import Bot
import config

API_TOKEN = config.token

async def delete_webhook():
    bot = Bot(token=API_TOKEN)
    await bot.delete_webhook()
    await bot.session.close()  # Закрытие сессии
    print("Webhook удален")

if __name__ == "__main__":
    import asyncio
    asyncio.run(delete_webhook())