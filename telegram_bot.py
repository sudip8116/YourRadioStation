import asyncio
from telegram import Bot

TOKEN = "7526670917:AAHKYMGAX9DbClRbRHodaCLRJlcCXz1z0yc"
CHAT_ID = "-1003124021231"  # or @channelusername

async def main():
    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text="Hello from Python bot!")

if __name__ == "__main__":
    asyncio.run(main())
