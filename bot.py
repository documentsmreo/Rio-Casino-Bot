import asyncio
from loader import dp, bot, db
from handlers import router, pvp_maintenance_task
from handlers_chat import chat_router, chat_game_maintenance_task

async def main():
    await db.connect()  
    dp.include_router(chat_router)
    dp.include_router(router)
    asyncio.create_task(pvp_maintenance_task())
    asyncio.create_task(chat_game_maintenance_task())
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
