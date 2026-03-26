from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from loader import bot, db, crypto
from config import CHANNEL_ID, ADMIN_ID, SUPPORT_CHAT_ID, MAIN_CHAT_ID
import json, re, asyncio, random
from keyboards import (
    get_subscription_keyboard, get_main_keyboard, get_admin_main_keyboard, 
    get_admin_mailing_keyboard, get_admin_promos_keyboard, get_profile_keyboard, 
    get_profile_back_keyboard, get_deposit_methods_keyboard, get_back_keyboard, 
    get_currencies_keyboard, get_payment_keyboard, get_admin_promo_type_keyboard,
    get_games_keyboard, get_bot_games_keyboard, get_games_players_keyboard,
    get_rps_keyboard, get_21_keyboard, get_admin_games_keyboard,
    get_game_menu_keyboard, get_game_mode_keyboard, get_game_choice_keyboard,
    get_game_stats_back_keyboard, get_game_bet_back_keyboard,
    get_pvp_create_type_keyboard, get_pvp_games_list_keyboard, get_pvp_bet_cancel_keyboard,
    get_pvp_move_keyboard, get_pvp_join_move_keyboard, get_withdraw_keyboard
)
from states import BroadcastState, SupportState, DepositState, AdminState, GameState, PvPState
from aiogram.filters import Command, StateFilter
import asyncio
from datetime import datetime, timedelta
import random
import string
import html

router = Router()

async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['creator', 'administrator', 'member']
    except:
        return False

@router.message(Command("start"), F.chat.type == "private")
async def cmd_start(message: Message):
    is_banned, expires, reason, ban_type = await db.get_ban_status(message.from_user.id)
    if is_banned and ban_type == 2:
        if expires == 0:
            expire_text = "Навсегда"
        else:
            expire_text = f"До {datetime.fromtimestamp(expires).strftime('%d.%m.%Y %H:%M')}"
        await message.answer(f"🚫 Вы забанены в боте.\nПричина: {reason}\nСрок: {expire_text}")
        return

    referrer_id = 0
    args = message.text.split()
    game_to_join = None
    
    if len(args) > 1:
        param = args[1]
        if param.startswith("ref_"):
            try:
                referrer_id = int(param.split("_")[1])
                if referrer_id == message.from_user.id:
                    referrer_id = 0 
                elif not await db.user_exists(referrer_id):
                    referrer_id = 0
            except:
                referrer_id = 0
        elif param.startswith("join_"):
             try:
                 game_to_join = int(param.split("_")[1])
             except: pass
                
    is_subscribed = await check_sub(message.from_user.id)
    referral_confirmed = 1 if is_subscribed else 0
    
    if not await db.user_exists(message.from_user.id):
        current_date = datetime.now().strftime("%d.%m.%Y")
        await db.add_user(message.from_user.id, message.from_user.username, current_date, referrer_id, confirmed=referral_confirmed)
        
        if referrer_id != 0 and referral_confirmed:
            try:
                await bot.send_message(referrer_id, f"🎉 У вас новый реферал: @{message.from_user.username or message.from_user.id}")
            except: pass

    if not is_subscribed:
        await message.answer("Для использования бота подпишитесь на канал!", reply_markup=get_subscription_keyboard())
    else:
        if game_to_join:
             game = await db.get_pvp_game(game_to_join)
             if not game:
                 await message.answer("Игра не найдена или уже сыграна.")
             else:
                 _, game_type, creator_id, creator_name, bet, _, joiner_id, _, _, _ = game
                 
                 if creator_id == message.from_user.id:
                     await message.answer("Вы не можете играть сами с собой!")
                 elif joiner_id != 0:
                     await message.answer("В этой игре уже есть участник.")
                 else:
                     emoji_map = {
                         "dice": "🎲", "football": "⚽", "basketball": "🏀", 
                         "darts": "🎯", "bowling": "🎳"
                     }
                     emoji = emoji_map.get(game_type, "🎲")
                     
                     text = f"🎮 <b>Игра #{game_to_join}</b>\n\n👤 Создатель: {html.escape(creator_name)}\n💰 Ставка: {bet} RUB\n{emoji} Тип: {game_type}\n\nХотите сыграть?"
                     
                     kb = InlineKeyboardMarkup(inline_keyboard=[
                         [InlineKeyboardButton(text="✅ Играть", callback_data=f"pvp_confirm_join_{game_to_join}")]
                     ])
                     await message.answer(text, reply_markup=kb)
                     return


        await message.answer("⚡️ Добро пожаловать в Casino Bot", reply_markup=get_main_keyboard())

@router.callback_query(F.data == "check_subscription")
async def check_subscription_handler(callback: CallbackQuery):
    if await check_sub(callback.from_user.id):
        await callback.message.delete()
        await callback.message.answer("⚡️ Добро пожаловать в Casino Bot", reply_markup=get_main_keyboard())
    else:
        await callback.answer("❌ Вы не подписаны на канал!", show_alert=True)

@router.message(F.text == "Профиль", F.chat.type == "private")
async def profile_handler(message: Message, state: FSMContext):
    is_banned, expires, reason, ban_type = await db.get_ban_status(message.from_user.id)
    if is_banned and ban_type == 2:
        if expires == 0:
            expire_text = "Навсегда"
        else:
            expire_text = f"До {datetime.fromtimestamp(expires).strftime('%d.%m.%Y %H:%M')}"
        await message.answer(f"🚫 Вы забанены в боте.\nПричина: {reason}\nСрок: {expire_text}")
        return

    await state.clear()
    is_subscribed = await check_sub(message.from_user.id)
    if not is_subscribed:
        await message.answer("Подпишитесь на канал!", reply_markup=get_subscription_keyboard())
        return

    user_data = await db.get_user_data(message.from_user.id)
    if not user_data:
        return
        
    username, balance, reg_date, _ = user_data
    username_display = f"@{username}" if username else "@none"
    reg_date_display = reg_date if reg_date else "Неизвестно"
    
    text = f"""🖥 Личный кабинет:

🌐️ Данные TG аккаунта:
 ID: {message.from_user.id}
 Username: {username_display}

💰 Данные аккаунта в боте:
 Баланс: {balance} RUB
 Дата регистрации: {reg_date_display}"""
    
    try:
        photo = FSInputFile("assets/photo/profile.jpg")
        await message.answer_photo(photo=photo, caption=text, reply_markup=get_profile_keyboard())
    except:
        await message.answer(text, reply_markup=get_profile_keyboard())

@router.message(F.text == "Игры", F.chat.type == "private")
async def games_handler(message: Message, state: FSMContext):
    await state.clear()
    try:
        photo = FSInputFile("assets/photo/games.jpg")
        await message.answer_photo(photo=photo, caption="🎮 Выберите режим:", reply_markup=get_games_keyboard())
    except:
        await message.answer("🎮 Выберите режим:", reply_markup=get_games_keyboard())

@router.message(F.text == "Поддержка", F.chat.type == "private")
async def support_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    is_banned, expires, reason, ban_type = await db.get_ban_status(user_id)
    if is_banned:
        if expires == 0:
            expire_text = "Навсегда"
        else:
            expire_text = f"До {datetime.fromtimestamp(expires).strftime('%d.%m.%Y %H:%M')}"
        
        await message.answer(f"🚫 Вы забанены в службе поддержки.\nПричина: {reason}\nСрок: {expire_text}")
        return

    current_time = datetime.now().timestamp()
    
    last_ticket = last_ticket_time.get(user_id, 0)
    if current_time - last_ticket < 120:
        remaining = int(120 - (current_time - last_ticket))
        await message.answer(f"⚠️ Пожалуйста, подождите {remaining} сек. перед созданием нового обращения.")
        return

    await message.answer("⁉️ Напишите краткое описание проблемы/вопроса. (Максимум 128 символов)")
    await state.set_state(SupportState.question)

@router.message(F.chat.id == SUPPORT_CHAT_ID)
async def support_reply_handler(message: Message):
    if not message.message_thread_id:
        return

    user_id = await db.get_user_by_topic(message.message_thread_id)
    if user_id:
        text = message.text
        if text and (text == "/ban" or text.startswith("/ban ")):
            try:
                parts = text.split(maxsplit=3)
                if len(parts) < 4:
                     await message.reply("Использование: /ban [Время мин] [Тип: 1-саппорт, 2-бот] [Причина]")
                     return
                
                minutes = int(parts[1])
                ban_type = int(parts[2])
                reason = parts[3]
                
                if ban_type not in [1, 2]:
                    await message.reply("Тип бана должен быть 1 (саппорт) или 2 (бот).")
                    return
                
                await db.ban_user(user_id, minutes, ban_type, reason)
                
                if minutes == 0:
                    time_str = "навсегда"
                else:
                    time_str = f"на {minutes} минут"
                
                type_str = "в службе поддержки" if ban_type == 1 else "в боте"
                    
                await message.reply(f"🚫 Пользователь забанен {time_str} {type_str}.\nПричина: {reason}")
                await bot.send_message(user_id, f"🚫 Вы были забанены администратором {time_str} {type_str}.\nПричина: {reason}")
                return
            except ValueError:
                await message.reply("Время и тип должны быть числами.")
                return

        elif text and (text == "/unban" or text.startswith("/unban ")):
            try:
                parts = text.split(maxsplit=1)
                reason = parts[1] if len(parts) > 1 else "Не указана"
                
                await db.unban_user(user_id)
                await message.reply(f"✅ Пользователь разбанен.")
                await bot.send_message(user_id, f"✅ Вы были разбанены администратором.")
                return
            except:
                pass

        try:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✍️ Ответить", callback_data=f"reply_ticket")]
            ])
            
            if message.text:
                await bot.send_message(chat_id=user_id, text=f"💬 <b>Ответ поддержки:</b>\n{message.text}", reply_markup=keyboard)
            elif message.photo:
                await bot.send_photo(chat_id=user_id, photo=message.photo[-1].file_id, caption=f"💬 <b>Ответ поддержки:</b>\n{message.caption or ''}", reply_markup=keyboard)
            else:
                await message.copy_to(chat_id=user_id, reply_markup=keyboard)
        except:
            pass

@router.callback_query(F.data == "profile_back")
async def profile_back_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    
    user_data = await db.get_user_data(callback.from_user.id)
    username, balance, reg_date, _ = user_data
    username_display = f"@{username}" if username else "@none"
    reg_date_display = reg_date if reg_date else "Неизвестно"
    
    text = f"""🖥 Личный кабинет:

🌐️ Данные TG аккаунта:
 ID: {callback.from_user.id}
 Username: {username_display}

💰 Данные аккаунта в боте:
 Баланс: {balance} RUB
 Дата регистрации: {reg_date_display}"""

    try:
        photo = FSInputFile("assets/photo/profile.jpg")
        await callback.message.answer_photo(photo=photo, caption=text, reply_markup=get_profile_keyboard())
    except:
        await callback.message.answer(text, reply_markup=get_profile_keyboard())

@router.callback_query(F.data == "profile_stats")
async def profile_stats_callback(callback: CallbackQuery):
    deposited, withdrawn = await db.get_user_stats(callback.from_user.id)
    text = f"📊 Статистика:\n\nПополнил: {deposited} RUB\nВывел: {withdrawn} RUB"
    try:
        photo = FSInputFile("assets/photo/profile.jpg")
        await callback.message.edit_media(media=types.InputMediaPhoto(media=photo, caption=text), reply_markup=get_profile_back_keyboard())
    except:
        await callback.message.edit_text(text, reply_markup=get_profile_back_keyboard())

@router.callback_query(F.data == "profile_promo")
async def profile_promo_callback(callback: CallbackQuery):
    text = "💌 Для того, чтобы активировать промокод введите его в чат"
    try:
        photo = FSInputFile("assets/photo/profile.jpg")
        await callback.message.edit_media(media=types.InputMediaPhoto(media=photo, caption=text), reply_markup=get_profile_back_keyboard())
    except:
         await callback.message.edit_text(text, reply_markup=get_profile_back_keyboard())

@router.callback_query(F.data == "profile_referral")
async def profile_referral_callback(callback: CallbackQuery):
    invited_count, earnings = await db.get_referral_stats(callback.from_user.id)
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{callback.from_user.id}"
    
    text = f"""👥 Реферальная программа:

💸 Получай процент от пополнения реферала!
 └ Ставка: 1%

Приглашено вами: {invited_count}
Заработано: {earnings:.2f} RUB

🔗 Ваша реферальная ссылка:
{ref_link}"""

    try:
        photo = FSInputFile("assets/photo/referrals.jpg")
        await callback.message.edit_media(media=types.InputMediaPhoto(media=photo, caption=text), reply_markup=get_profile_back_keyboard())
    except:
        await callback.message.edit_text(text, reply_markup=get_profile_back_keyboard())

@router.callback_query(F.data == "deposit")
async def deposit_start(callback: CallbackQuery):
    try:
        photo = FSInputFile("assets/photo/profile.jpg")
        await callback.message.edit_media(media=types.InputMediaPhoto(media=photo, caption="💳 Выберите способ пополнения:"), reply_markup=get_deposit_methods_keyboard())
    except:
        await callback.message.edit_text("💳 Выберите способ пополнения:", reply_markup=get_deposit_methods_keyboard())


@router.callback_query(F.data == "dep_cryptobot")
async def deposit_cryptobot(callback: CallbackQuery, state: FSMContext):
    try:
        photo = FSInputFile("assets/photo/profile.jpg")
        await callback.message.edit_media(media=types.InputMediaPhoto(media=photo, caption="💸 Введите сумму пополнения в рублях\nМинимум: 10 RUB"), reply_markup=get_back_keyboard("deposit"))
    except:
         await callback.message.edit_text("💸 Введите сумму пополнения в рублях\nМинимум: 10 RUB", reply_markup=get_back_keyboard("deposit"))
    await state.set_state(DepositState.amount)

@router.callback_query(F.data == "deposit_back")
async def deposit_back_to_methods(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await deposit_start(callback)

@router.message(DepositState.amount)
async def process_deposit_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount < 10:
            await message.answer("Минимум 10 RUB. Попробуйте снова.")
            return
    except ValueError:
        await message.answer("Введите число.")
        return

    await state.update_data(amount=amount)
    
    text = f"— Сумма: {amount} RUB\n\n💸 Выберите валюту, которой хотите оплатить счёт"
    try:
        photo = FSInputFile("assets/photo/profile.jpg")
        await message.answer_photo(photo=photo, caption=text, reply_markup=get_currencies_keyboard())
    except:
        await message.answer(text, reply_markup=get_currencies_keyboard())

@router.callback_query(F.data.startswith("pay_"))
async def process_currency_selection(callback: CallbackQuery, state: FSMContext):
    currency = callback.data.split("_")[1]
    data = await state.get_data()
    amount_rub = data.get('amount')
    
    if not amount_rub:
        await callback.answer("Ошибка, начните заново.", show_alert=True)
        return
        
    try:
        rates = await crypto.get_exchange_rates()
        rate = None
        for r in rates:
            if r.source == currency and r.target == 'RUB':
                rate = float(r.rate)
                break
        
        if not rate:
             await callback.answer(f"Не удалось получить курс {currency}/RUB", show_alert=True)
             return

        amount_crypto = float(amount_rub) / rate
        amount_crypto = round(amount_crypto, 6)

        invoice = await crypto.create_invoice(asset=currency, amount=amount_crypto, fiat='RUB', accepted_assets=currency)
        await db.add_pending_deposit(invoice.invoice_id, float(amount_rub))

        await callback.message.delete()
        
        text = f"✅ Счёт создан!\n\n💰 Сумма: {amount_rub} RUB\n💎 Валюта: {currency} ({amount_crypto})\n\nОплатите по ссылке ниже:"
        try:
             photo = FSInputFile("assets/photo/profile.jpg")
             await callback.message.answer_photo(photo=photo, caption=text, reply_markup=get_payment_keyboard(invoice.bot_invoice_url, invoice.invoice_id))
        except:
             await callback.message.answer(text, reply_markup=get_payment_keyboard(invoice.bot_invoice_url, invoice.invoice_id))
        
    except Exception as e:
        await callback.answer(f"Ошибка создания счета: {e}", show_alert=True)

@router.callback_query(F.data == "deposit_amount_back")
async def deposit_amount_back(callback: CallbackQuery, state: FSMContext):
    await deposit_cryptobot(callback, state)

@router.callback_query(F.data.startswith("check_pay_"))
async def check_payment(callback: CallbackQuery):
    invoice_id = int(callback.data.split("_")[2])
    try:
        invoices = await crypto.get_invoices(invoice_ids=invoice_id)
        
        invoice = None
        if isinstance(invoices, list):
            if invoices:
                 invoice = invoices[0]
        else:
            invoice = invoices
            
        if invoice and invoice.status == 'paid':
             await process_successful_payment(callback.from_user.id, invoice)
             await callback.message.delete()
             await callback.message.answer("✅ Оплата прошла успешно! Баланс пополнен.")
        elif invoice:
             await callback.answer("❌ Счёт еще не оплачен.", show_alert=True)
        else:
             await callback.answer("❌ Счёт не найден.", show_alert=True)
             
    except Exception as e:
         await callback.answer(f"Ошибка проверки: {e}", show_alert=True)

async def process_successful_payment(user_id, invoice):
    is_processed = await db.check_payment(invoice.invoice_id)
    if not is_processed:
        amount_rub = await db.get_pending_deposit(invoice.invoice_id)
        if not amount_rub:
             amount_rub = 0
        
        if amount_rub > 0:
            await db.add_payment(invoice.invoice_id, user_id, amount_rub)
            await db.update_balance(user_id, amount_rub)
            
            referrer_id = await db.get_referrer(user_id)
            if referrer_id:
                commission = amount_rub * 0.01
                if commission > 0:
                    await db.update_referral_earnings(referrer_id, commission)
                    try:
                        await bot.send_message(referrer_id, f"💸 Начислено {commission} RUB за пополнение реферала!")
                    except: pass

@router.callback_query(F.data == "withdraw")
async def withdraw_menu(callback: CallbackQuery):
    user_data = await db.get_user_data(callback.from_user.id)
    balance = user_data[1] if user_data else 0
    
    text = (
        f"💸 <b>Меню вывода средств</b>\n\n"
        f" ┗Ваш баланс: {balance} RUB\n"
        f" ┗Минимум для вывода: 100 RUB"
    )
    
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer(text, reply_markup=get_withdraw_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "withdraw_start")
async def withdraw_start(callback: CallbackQuery, state: FSMContext):
    user_data = await db.get_user_data(callback.from_user.id)
    balance = user_data[1] if user_data else 0
    
    if balance < 100:
        await callback.answer("Минимальная сумма для вывода 100 RUB", show_alert=True)
        return
    
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer(
        f"💰 Ваш баланс: {balance} RUB\n\n"
        "Введите сумму для вывода (минимум 100 RUB):",
        reply_markup=get_back_keyboard("withdraw")
    )
    await state.set_state(DepositState.withdraw_amount)

@router.message(DepositState.withdraw_amount)
async def process_withdraw_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
    except:
        await message.reply("Укажите корректную сумму.")
        return
    
    if amount < 100:
        await message.reply("Минимальная сумма для вывода 100 RUB")
        return
    
    user_data = await db.get_user_data(message.from_user.id)
    balance = user_data[1] if user_data else 0
    
    if amount > balance:
        await message.reply("Недостаточно средств на балансе.")
        return
    
    usdt_amount = round(amount / 78, 2)
    
    try:
        check = await crypto.create_check(asset="USDT", amount=usdt_amount)
        
        await db.update_balance(message.from_user.id, -amount)
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💵 Получить чек", url=check.bot_check_url)]
        ])
        
        await message.answer(
            f"✅ Вывод успешен!\n\n"
            f"💰 Сумма: {amount} RUB (~{usdt_amount} USDT)\n"
            f"Нажмите кнопку ниже чтобы получить чек:",
            reply_markup=kb
        )
        await state.clear()
        
    except Exception as e:
        error_msg = str(e)
        if "NOT_ENOUGH_COINS" in error_msg:
            await message.reply("❌ В казне недостаточно монет!")
        else:
            await message.reply(f"Ошибка вывода: {e}")
        await state.clear()


@router.message(F.text == "Поддержка")
async def support_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    is_banned, expires, reason = await db.get_ban_status(user_id)
    if is_banned:
        if expires == 0:
            expire_text = "Навсегда"
        else:
            expire_text = f"До {datetime.fromtimestamp(expires).strftime('%d.%m.%Y %H:%M')}"
        
        await message.answer(f"🚫 Вы забанены в боте.\nПричина: {reason}\nСрок: {expire_text}")
        return

    current_time = datetime.now().timestamp()
    
    last_ticket = last_ticket_time.get(user_id, 0)
    if current_time - last_ticket < 120:
        remaining = int(120 - (current_time - last_ticket))
        await message.answer(f"⚠️ Пожалуйста, подождите {remaining} сек. перед созданием нового обращения.")
        return

    await message.answer("⁉️ Напишите краткое описание проблемы/вопроса. (Максимум 128 символов)")
    await state.set_state(SupportState.question)

last_ticket_time = {}

@router.message(SupportState.question)
async def process_question(message: Message, state: FSMContext):
    if len(message.text) > 128:
        await message.answer("Слишком длинное сообщение. Максимум 128 символов.")
        return

    user_data = await db.get_user_data(message.from_user.id)
    topic_id = user_data[3]
    last_ticket_time[message.from_user.id] = datetime.now().timestamp()

    if not topic_id:
        topic_name = f"@{message.from_user.username} | {message.from_user.id}" if message.from_user.username else f"{message.from_user.id} | {message.from_user.id}"
        topic = await bot.create_forum_topic(chat_id=SUPPORT_CHAT_ID, name=topic_name)
        topic_id = topic.message_thread_id
        await db.update_user_topic(message.from_user.id, topic_id)

    username_text = f"@{message.from_user.username}" if message.from_user.username else "Без юзернейма"
    
    admin_text = (
        f"📩 <b>Тикет от пользователя {username_text}</b>:\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n\n"
        f"📝 <b>Сообщение:</b>\n{message.text}"
    )

    await bot.send_message(chat_id=SUPPORT_CHAT_ID, message_thread_id=topic_id, text=admin_text)
    await message.answer("Ваше сообщение отправлено в поддержку.")
    await state.clear()

@router.message(F.chat.id == SUPPORT_CHAT_ID)
async def support_reply_handler(message: Message):
    if not message.message_thread_id:
        return

    user_id = await db.get_user_by_topic(message.message_thread_id)
    if user_id:
        text = message.text
        if text and (text == "/ban" or text.startswith("/ban ")):
            try:
                parts = text.split(maxsplit=2)
                if len(parts) < 3:
                     await message.reply("Использование: /ban [Время мин] [Причина]")
                     return
                
                minutes = int(parts[1])
                reason = parts[2]
                
                await db.ban_user(user_id, minutes, reason)
                
                if minutes == 0:
                    time_str = "навсегда"
                else:
                    time_str = f"на {minutes} минут"
                    
                await message.reply(f"🚫 Пользователь забанен {time_str}.\nПричина: {reason}")
                await bot.send_message(user_id, f"🚫 Вы были забанены администратором {time_str}.\nПричина: {reason}")
                return
            except ValueError:
                await message.reply("Время должно быть числом.")
                return

        elif text and (text == "/unban" or text.startswith("/unban ")):
            try:
                parts = text.split(maxsplit=1)
                reason = parts[1] if len(parts) > 1 else "Не указана"
                
                await db.unban_user(user_id)
                await message.reply(f"✅ Пользователь разбанен.")
                await bot.send_message(user_id, f"✅ Вы были разбанены администратором.")
                return
            except:
                pass

        try:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✍️ Ответить", callback_data=f"reply_ticket")]
            ])
            
            if message.text:
                await bot.send_message(chat_id=user_id, text=f"💬 <b>Ответ поддержки:</b>\n{message.text}", reply_markup=keyboard)
            elif message.photo:
                await bot.send_photo(chat_id=user_id, photo=message.photo[-1].file_id, caption=f"💬 <b>Ответ поддержки:</b>\n{message.caption or ''}", reply_markup=keyboard)
            else:
                await message.copy_to(chat_id=user_id, reply_markup=keyboard)
        except:
            pass

@router.callback_query(F.data == "reply_ticket")
async def reply_ticket_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📝 Напишите ваш ответ:")
    await state.set_state(SupportState.question)
    await callback.answer()

@router.message(Command("admin812"), F.chat.type == "private")
async def cmd_admin(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await message.answer("Админ-панель:", reply_markup=get_admin_main_keyboard())

@router.callback_query(F.data == "admin_back_main")
async def admin_back_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Админ-панель:", reply_markup=get_admin_main_keyboard())

@router.callback_query(F.data == "admin_mailing")
async def admin_mailing_menu(callback: CallbackQuery, state: FSMContext):
    await state.set_data({})
    await callback.message.edit_text("Меню рассылки:", reply_markup=get_admin_mailing_keyboard({}))
    await state.set_state(BroadcastState.menu)

@router.callback_query(F.data == "admin_text")
async def cb_text(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите текст рассылки:")
    await state.set_state(BroadcastState.text)
    await callback.answer()

@router.message(BroadcastState.text)
async def process_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    data = await state.get_data()
    await message.answer("Текст сохранен.", reply_markup=get_admin_mailing_keyboard(data))
    await state.set_state(BroadcastState.menu)

@router.callback_query(F.data == "admin_photo")
async def cb_photo(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Отправьте фото для рассылки:")
    await state.set_state(BroadcastState.photo)
    await callback.answer()

@router.message(BroadcastState.photo)
async def process_photo(message: Message, state: FSMContext):
    if message.photo:
        await state.update_data(photo=message.photo[-1].file_id)
        phrase = "Фото сохранено."
    else:
        phrase = "Это не фото."
    data = await state.get_data()
    await message.answer(phrase, reply_markup=get_admin_mailing_keyboard(data))
    await state.set_state(BroadcastState.menu)

@router.callback_query(F.data == "admin_button")
async def cb_button(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите текст кнопки:")
    await state.set_state(BroadcastState.button_text)
    await callback.answer()

@router.message(BroadcastState.button_text)
async def process_button_text(message: Message, state: FSMContext):
    await state.update_data(button_text=message.text)
    await message.answer("Теперь введите ссылку для кнопки:")
    await state.set_state(BroadcastState.button_url)

@router.message(BroadcastState.button_url)
async def process_button_url(message: Message, state: FSMContext):
    await state.update_data(button_url=message.text)
    data = await state.get_data()
    await message.answer("Кнопка сохранена.", reply_markup=get_admin_mailing_keyboard(data))
    await state.set_state(BroadcastState.menu)

@router.callback_query(F.data == "admin_cancel")
async def cb_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Рассылка отменена.", reply_markup=get_admin_main_keyboard())

@router.callback_query(F.data == "admin_send")
async def cb_send(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get('text') and not data.get('photo'):
        await callback.answer("Добавьте хотя бы текст или фото!", show_alert=True)
        return
    
    users = await db.get_users()
    text = data.get('text')
    photo = data.get('photo')
    btn_text = data.get('button_text')
    btn_url = data.get('button_url')

    keyboard = None
    if btn_text and btn_url:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=btn_text, url=btn_url)]])

    count = 0
    await callback.message.edit_text("Рассылка запущена...")
    
    for user in users:
        user_id = user[0]
        try:
            if photo:
                await bot.send_photo(chat_id=user_id, photo=photo, caption=text, reply_markup=keyboard)
            elif text:
                await bot.send_message(chat_id=user_id, text=text, reply_markup=keyboard)
            count += 1
        except:
            pass
    
    await callback.message.answer(f"Рассылка завершена. Отправлено: {count}")
    await state.clear()
    await callback.message.answer("Админ-панель:", reply_markup=get_admin_main_keyboard())

@router.callback_query(F.data == "admin_promos")
async def admin_promos_menu(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Управление промокодами:", reply_markup=get_admin_promos_keyboard())
    await state.set_state(AdminState.menu)

@router.callback_query(F.data == "admin_treasury")
async def admin_treasury_menu(callback: CallbackQuery):
    try:
        balance = await crypto.get_balance()
        text = "💰 <b>Казна (CryptoBot)</b>\n\n"
        
        for b in balance:
            if float(b.available) > 0:
                text += f"• {b.currency_code}: {b.available}\n"
        
        if text == "💰 <b>Казна (CryptoBot)</b>\n\n":
            text += "Баланс пуст."
            
    except Exception as e:
        text = f"Ошибка получения баланса: {e}"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Пополнить казну", callback_data="treasury_deposit")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back_main")]
    ])
    
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "treasury_deposit")
async def treasury_deposit_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "💰 Введите сумму для пополнения казны (в USDT):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_treasury")]
        ])
    )
    await state.set_state(AdminState.treasury_deposit)

@router.message(AdminState.treasury_deposit)
async def process_treasury_deposit(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
    except:
        await message.reply("Укажите корректную сумму.")
        return
    
    if amount < 1:
        await message.reply("Минимальная сумма 1 USDT")
        return
    
    try:
        invoice = await crypto.create_invoice(asset="USDT", amount=amount)
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить", url=invoice.bot_invoice_url)],
            [InlineKeyboardButton(text="🔄 Проверить", callback_data=f"check_treasury_{invoice.invoice_id}")]
        ])
        
        await message.answer(
            f"💰 Счет на пополнение казны\n\n"
            f"Сумма: {amount} USDT\n"
            f"Нажмите кнопку для оплаты:",
            reply_markup=kb
        )
        await state.clear()
        
    except Exception as e:
        await message.reply(f"Ошибка создания счета: {e}")
        await state.clear()

@router.callback_query(F.data.startswith("check_treasury_"))
async def check_treasury_payment(callback: CallbackQuery):
    invoice_id = int(callback.data.split("_")[2])
    try:
        invoices = await crypto.get_invoices(invoice_ids=invoice_id)
        
        invoice = None
        if isinstance(invoices, list) and invoices:
            invoice = invoices[0]
        else:
            invoice = invoices
            
        if invoice and invoice.status == 'paid':
            await callback.message.delete()
            await callback.message.answer("✅ Казна пополнена!")
        else:
            await callback.answer("❌ Счёт еще не оплачен.", show_alert=True)
            
    except Exception as e:
        await callback.answer(f"Ошибка проверки: {e}", show_alert=True)

@router.callback_query(F.data == "admin_moderators")
async def admin_moderators_menu(callback: CallbackQuery, state: FSMContext):
    mods = await db.get_all_moderators()
    text = "👮 <b>Управление модераторами</b>\n\n"
    if mods:
        text += "Текущие модераторы:\n"
        for m in mods:
            text += f"• {m[0]}\n"
    else:
        text += "Модераторов нет.\n"
    text += "\nОтправьте ID пользователя для добавления/удаления:"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back_main")]
    ])
    
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await state.set_state(AdminState.moderator_id)

@router.message(AdminState.moderator_id)
async def process_moderator_id(message: Message, state: FSMContext):
    try:
        user_id = int(message.text)
    except:
        await message.reply("Укажите корректный ID.")
        return
    
    is_mod = await db.is_moderator(user_id)
    if is_mod:
        await db.remove_moderator(user_id)
        await message.answer(f"✅ Пользователь {user_id} снят с модератора.", reply_markup=get_admin_main_keyboard())
    else:
        await db.add_moderator(user_id)
        await message.answer(f"✅ Пользователь {user_id} назначен модератором.", reply_markup=get_admin_main_keyboard())
    
    await state.clear()

@router.callback_query(F.data == "promo_list")
async def promo_list(callback: CallbackQuery):
    promocodes = await db.get_all_promos()
    if not promocodes:
        await callback.answer("Промокодов нет.", show_alert=True)
        return
    
    msg = "Список промокодов:\n"
    for code, amount, acts, expires in promocodes:
        info = ""
        if acts == -1:
            exp_date = datetime.fromtimestamp(expires).strftime('%d.%m.%Y %H:%M')
            info = f"до {exp_date}"
        else:
            info = f"{acts} активаций"
        msg += f"<code>{code}</code> - {amount} RUB ({info})\n"
    
    await callback.message.answer(msg, parse_mode="HTML")

@router.callback_query(F.data == "promo_add")
async def promo_add(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите сумму промокода (RUB):")
    await state.set_state(AdminState.promo_amount)
    await callback.answer()

@router.message(AdminState.promo_amount)
async def process_promo_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        await state.update_data(amount=amount)
        await message.answer("Выберите тип ограничения:", reply_markup=get_admin_promo_type_keyboard())
    except ValueError:
        await message.answer("Введите число.")

@router.callback_query(F.data == "promo_type_activations")
async def promo_type_activations(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите количество активаций:")
    await state.set_state(AdminState.promo_count)
    await callback.answer()

@router.message(AdminState.promo_count)
async def process_promo_count(message: Message, state: FSMContext):
    try:
        count = int(message.text)
        data = await state.get_data()
        amount = data.get('amount')
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
        
        await db.create_promo(code, amount, activations=count, expires_at=0)
        
        await message.answer(f"✅ Промокод (Активации) создан:\n<code>{code}</code>\nСумма: {amount} RUB\nАктиваций: {count}", reply_markup=get_admin_promos_keyboard())
        await state.set_state(AdminState.menu)
    except ValueError:
        await message.answer("Введите целое число.")

@router.callback_query(F.data == "promo_type_time")
async def promo_type_time(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите время действия (в часах):")
    await state.set_state(AdminState.promo_time)
    await callback.answer()

@router.message(AdminState.promo_time)
async def process_promo_time(message: Message, state: FSMContext):
    try:
        hours = int(message.text)
        data = await state.get_data()
        amount = data.get('amount')
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
        
        expires_at = datetime.now() + timedelta(hours=hours)
        timestamp = expires_at.timestamp()
        
        await db.create_promo(code, amount, activations=-1, expires_at=timestamp)
        
        await message.answer(f"✅ Промокод (Время) создан:\n<code>{code}</code>\nСумма: {amount} RUB\nДо: {expires_at.strftime('%d.%m.%Y %H:%M')}", reply_markup=get_admin_promos_keyboard())
        await state.set_state(AdminState.menu)
    except ValueError:
        await message.answer("Введите целое число.")

@router.callback_query(F.data == "promo_delete")
async def promo_delete(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите код промокода для удаления:")
    await state.set_state(AdminState.promo_delete)
    await callback.answer()

@router.message(AdminState.promo_delete)
async def process_promo_delete(message: Message, state: FSMContext):
    code = message.text.strip()
    promo = await db.get_promo(code)
    if promo:
        await db.delete_promo(code)
        await message.answer(f"❌ Промокод <code>{code}</code> удален.", reply_markup=get_admin_promos_keyboard())
    else:
        await message.answer("Промокод не найден.", reply_markup=get_admin_promos_keyboard())
    await state.set_state(AdminState.menu)



@router.callback_query(F.data == "games_main")
async def games_main_callback(callback: CallbackQuery):
    try:
        await callback.message.edit_caption(caption="🎮 Выберите режим:", reply_markup=get_games_keyboard())
    except:
        await callback.message.edit_text(text="🎮 Выберите режим:", reply_markup=get_games_keyboard())

@router.callback_query(F.data == "games_bot")
async def games_bot_callback(callback: CallbackQuery):
    try:
        await callback.message.edit_caption(caption="🎮 Выберите режим:", reply_markup=get_bot_games_keyboard())
    except:
        await callback.message.edit_text(text="🎮 Выберите режим:", reply_markup=get_bot_games_keyboard())

@router.callback_query(F.data == "games_players")
async def games_players_callback(callback: CallbackQuery):
    try:
        await callback.message.edit_caption(caption="🎮 Выберите режим:", reply_markup=get_games_players_keyboard())
    except:
        await callback.message.edit_text(text="🎮 Выберите режим:", reply_markup=get_games_players_keyboard())

@router.callback_query(F.data.startswith("game_"))
async def game_start_callback(callback: CallbackQuery, state: FSMContext):
    game_id = callback.data
    if game_id == "game_settings":
         return

    if game_id == "game_exit":
        await state.clear()
        await callback.message.delete()
        try:
             photo = FSInputFile("assets/photo/games.jpg")
             await callback.message.answer_photo(photo=photo, caption="🎮 Выберите режим игры:", reply_markup=get_games_keyboard())
        except:
             await callback.message.answer("🎮 Выберите режим игры:", reply_markup=get_games_keyboard())
        return

    rules_map = {
        "game_21": "🃏 <b>21 Очко</b>\nНаберите сумму очков, близкую к 21, но не больше. Обыграйте дилера!",
        "game_rps": "✊✌✋ <b>ЦУЕФА</b>\nКлассическая игра: Камень бьет Ножницы, Ножницы режут Бумагу, Бумага накрывает Камень.",
        "game_football": "⚽ <b>Футбол</b>\nЗабейте гол или угадайте исход удара!",
        "game_basketball": "🏀 <b>Баскетбол</b>\nЗабросьте мяч в корзину или угадайте исход броска!",
        "game_darts": "🎯 <b>Дартс</b>\nПопадите в цель точнее соперника!",
        "game_bowling": "🎳 <b>Боулинг</b>\nСбейте больше кеглей, чем соперник!",
        "game_dice": "🎲 <b>Кубик</b>\nВыбросьте больше очков или угадайте результат броска!"
    }
    
    rule = rules_map.get(game_id, "Правила игры.")
    try:
        await callback.message.edit_caption(caption=rule, reply_markup=get_game_menu_keyboard(game_id))
    except:
        await callback.message.edit_text(text=rule, reply_markup=get_game_menu_keyboard(game_id))

@router.callback_query(F.data.startswith("play_"))
async def game_play_callback(callback: CallbackQuery, state: FSMContext):
    real_game_id = callback.data.replace("play_", "")
    
    await state.update_data(current_game=real_game_id)
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer("💰 Введите сумму ставки (минимум 10 RUB):", reply_markup=get_game_bet_back_keyboard(real_game_id))
    await state.set_state(GameState.bet_amount)
    await callback.answer()

@router.callback_query(F.data.startswith("stats_"))
async def game_stats_callback(callback: CallbackQuery):
    game_id = callback.data.replace("stats_", "")
    stats = await db.get_user_game_stats(callback.from_user.id, game_id)
    wins, losses, draws, profit = stats
    
    msg = f"📊 <b>Ваша статистика:</b>\n\n🏆 Побед: {wins}\n📉 Поражений: {losses}\n🤝 Ничьих: {draws}\n💰 Общий профит: {profit} RUB"
    try:
        await callback.message.edit_caption(caption=msg, reply_markup=get_game_stats_back_keyboard(game_id))
    except:
        await callback.message.edit_text(msg, reply_markup=get_game_stats_back_keyboard(game_id))


        
@router.message(GameState.bet_amount)
async def game_bet_handler(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount < 10:
            await message.answer("Минимум 10 RUB. Попробуйте снова.")
            return
            
        user_data = await db.get_user_data(message.from_user.id)
        balance = user_data[1]
        
        if amount > balance:
            await message.answer("Недостаточно средств на балансе.")
            return
            
        await state.update_data(bet=amount)
        data = await state.get_data()
        game_id = data.get('current_game')
        
        mode_kb = get_game_mode_keyboard(game_id)
        if mode_kb:
            await message.answer("Выберите режим игры:", reply_markup=mode_kb)
            await state.set_state(GameState.mode)
            return

        await db.update_balance(message.from_user.id, -amount)
        
        if game_id == "game_rps":
             await message.answer(f"Ставка {amount} RUB принята.\nВыберите: Камень, Ножницы или Бумага:", reply_markup=get_rps_keyboard())
             await state.set_state(GameState.playing)

        elif game_id == "game_21":
             deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11] * 4
             random.shuffle(deck)
             user_hand = [deck.pop(), deck.pop()]
             bot_hand = [deck.pop(), deck.pop()]
             
             await state.update_data(deck=deck, user_hand=user_hand, bot_hand=bot_hand)
             
             user_score = sum(user_hand)
             dealer_show = bot_hand[0]
             
             await message.answer(f"Ставка {amount} RUB принята.\nВаши карты: {user_hand} (Сумма: {user_score})\nКарта дилера: {dealer_show} ({dealer_show})", reply_markup=get_21_keyboard())
             await state.set_state(GameState.playing)
             
        elif game_id in ["game_darts", "game_bowling"]:
             emoji_map = {"game_darts": "🎯", "game_bowling": "🎳"}
             emoji = emoji_map.get(game_id)
             await message.answer(f"Ставка {amount} RUB принята. Играем в {emoji}!")
             await run_simple_dice_game(message, state, game_id, amount, emoji)

    except ValueError:
        await message.answer("Введите число.")

@router.callback_query(GameState.mode, F.data.startswith("mode_"))
async def game_mode_callback(callback: CallbackQuery, state: FSMContext):
    mode = callback.data.split("_")[1]
    await state.update_data(game_mode=mode)
    data = await state.get_data()
    game_id = data.get("current_game")
    amount = data.get("bet")
    
    if mode == "points":
        await db.update_balance(callback.from_user.id, -amount)
        emoji_map = {"game_football": "⚽", "game_basketball": "🏀", "game_dice": "🎲"}
        emoji = emoji_map.get(game_id)
        await callback.message.answer(f"Ставка {amount} RUB принята. Играем в {emoji} (По очкам)!")
        await run_simple_dice_game(callback.message, state, game_id, amount, emoji, mode="points")
        
    elif mode in ["specific", "overunder"]:
        choice_kb = get_game_choice_keyboard(game_id)
        await callback.message.edit_text("Выберите исход:", reply_markup=choice_kb)
        await db.update_balance(callback.from_user.id, -amount)

@router.callback_query(GameState.mode, F.data.startswith("choice_"))
async def game_choice_callback(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.split("_")[1]
    data = await state.get_data()
    game_id = data.get("current_game")
    game_mode = data.get("game_mode")
    amount = data.get("bet")
    
    emoji_map = {"game_football": "⚽", "game_basketball": "🏀", "game_dice": "🎲"}
    emoji = emoji_map.get(game_id)
    
    await callback.message.answer(f"Ставка {amount} RUB принята. Бросаем {emoji}!")
    
    msg = await callback.message.answer_dice(emoji=emoji)
    val = msg.dice.value
    await asyncio.sleep(4)
    
    settings_key = f"{game_id}_{game_mode}"
    coeff = await db.get_game_settings(settings_key)
    win = False
    
    if game_id == "game_football":
        is_goal = val >= 3
        if (choice == "hit" and is_goal) or (choice == "miss" and not is_goal):
            win = True
            
    elif game_id == "game_basketball":
        is_score = val >= 4
        if (choice == "hit" and is_score) or (choice == "miss" and not is_score):
            win = True
            
    elif game_id == "game_dice":
        if (choice == "under" and val <= 3) or (choice == "over" and val >= 4):
            win = True
            
    if win:
        win_amount = amount * coeff
        await db.update_balance(callback.from_user.id, win_amount)
        await db.update_user_game_stat(callback.from_user.id, game_id, 'win', win_amount - amount)
        await callback.message.answer(f"🏆 Победа! (Результат: {val})\nВыигрыш: {win_amount} RUB", reply_markup=get_game_menu_keyboard(game_id))
    else:
        await db.update_user_game_stat(callback.from_user.id, game_id, 'loss', -amount)
        await callback.message.answer(f"😢 Проигрыш. (Результат: {val})", reply_markup=get_game_menu_keyboard(game_id))
        
    await state.clear()

async def run_simple_dice_game(message: Message, state: FSMContext, game_id, amount, emoji, mode=None):
    msg_user = await message.answer_dice(emoji=emoji)
    user_value = msg_user.dice.value
    await asyncio.sleep(4)
    
    msg_bot = await message.answer_dice(emoji=emoji)
    bot_value = msg_bot.dice.value
    await asyncio.sleep(4)
    
    settings_key = game_id
    if mode:
        settings_key = f"{game_id}_{mode}"
        
    coeff = await db.get_game_settings(settings_key)
    
    if user_value > bot_value:
        win_amount = amount * coeff
        await db.update_balance(message.from_user.id, win_amount)
        await db.update_user_game_stat(message.from_user.id, game_id, 'win', win_amount - amount)
        await message.answer(f"🏆 Вы победили! (Ваш: {user_value}, Бот: {bot_value})\nВыигрыш: {win_amount} RUB", reply_markup=get_game_menu_keyboard(game_id))
    elif user_value < bot_value:
         await db.update_user_game_stat(message.from_user.id, game_id, 'loss', -amount)
         await message.answer(f"😢 Вы проиграли. (Ваш: {user_value}, Бот: {bot_value})", reply_markup=get_game_menu_keyboard(game_id))
    else:
        await db.update_balance(message.from_user.id, amount)
        await db.update_user_game_stat(message.from_user.id, game_id, 'draw', 0)
        await message.answer(f"🤝 Ничья! (Ваш: {user_value}, Бот: {bot_value})\nСтавка возвращена.", reply_markup=get_game_menu_keyboard(game_id))
    
    await state.clear()



@router.callback_query(GameState.playing, F.data.startswith("rps_"))
async def rps_game_logic(callback: CallbackQuery, state: FSMContext):
    user_choice = callback.data.split("_")[1]
    bot_choices = ["rock", "scissors", "paper"]
    bot_choice = random.choice(bot_choices)
    
    emoji_map = {"rock": "✊", "scissors": "✂️", "paper": "✋"}
    
    data = await state.get_data()
    amount = data.get("bet")
    game_id = data.get("current_game")
    coeff = await db.get_game_settings(game_id)
    
    result_text = f"Вы: {emoji_map[user_choice]}\nБот: {emoji_map[bot_choice]}\n"
    
    win = False
    draw = False
    
    if user_choice == bot_choice:
        draw = True
    elif (user_choice == "rock" and bot_choice == "scissors") or \
         (user_choice == "scissors" and bot_choice == "paper") or \
         (user_choice == "paper" and bot_choice == "rock"):
        win = True
        
    if draw:
        await db.update_balance(callback.from_user.id, amount)
        await db.update_user_game_stat(callback.from_user.id, game_id, 'draw', 0)
        result_text += "🤝 Ничья! Ставка возвращена."
    elif win:
        win_amount = amount * coeff
        await db.update_balance(callback.from_user.id, win_amount)
        await db.update_user_game_stat(callback.from_user.id, game_id, 'win', win_amount - amount)
        result_text += f"🏆 Вы победили!\nВыигрыш: {win_amount} RUB"
    else:
        await db.update_user_game_stat(callback.from_user.id, game_id, 'loss', -amount)
        result_text += "😢 Вы проиграли."
        
    await callback.message.edit_text(result_text, reply_markup=get_game_menu_keyboard(game_id))
    await state.clear()

@router.callback_query(GameState.playing, F.data.startswith("21_"))
async def blackjack_game_logic(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]
    data = await state.get_data()
    deck = data.get("deck")
    user_hand = data.get("user_hand")
    bot_hand = data.get("bot_hand")
    amount = data.get("bet")
    game_id = data.get("current_game")
    
    if action == "hit":
        user_hand.append(deck.pop())
        user_score = sum(user_hand)
        
        if user_score > 21:
             await db.update_user_game_stat(callback.from_user.id, game_id, 'loss', -amount)
             await callback.message.edit_text(f"Ваши карты: {user_hand} (Сумма: {user_score})\n💥 Перебор! Вы проиграли.", reply_markup=get_game_menu_keyboard(game_id))
             await state.clear()
        else:
             dealer_show = bot_hand[0]
             await callback.message.edit_text(f"Ваши карты: {user_hand} (Сумма: {user_score})\nКарта дилера: {dealer_show} ({dealer_show})", reply_markup=get_21_keyboard())
             await state.update_data(deck=deck, user_hand=user_hand)
             
    elif action == "stand":
        user_score = sum(user_hand)
        bot_score = sum(bot_hand)
        
        while bot_score < 17:
            bot_hand.append(deck.pop())
            bot_score = sum(bot_hand)
            
        result_text = f"Ваши карты: {user_hand} (Сумма: {user_score})\nКарты дилера: {bot_hand} (Сумма: {bot_score})\n"
        
        coeff = await db.get_game_settings(game_id)
        
        if bot_score > 21:
            win_amount = amount * coeff
            await db.update_balance(callback.from_user.id, win_amount)
            await db.update_user_game_stat(callback.from_user.id, game_id, 'win', win_amount - amount)
            result_text += f"🎉 Дилер перебрал! Вы выиграли {win_amount} RUB"
        elif user_score > bot_score:
            win_amount = amount * coeff
            await db.update_balance(callback.from_user.id, win_amount)
            await db.update_user_game_stat(callback.from_user.id, game_id, 'win', win_amount - amount)
            result_text += f"🏆 Вы победили! Выигрыш: {win_amount} RUB"
        elif user_score == bot_score:
            await db.update_balance(callback.from_user.id, amount)
            await db.update_user_game_stat(callback.from_user.id, game_id, 'draw', 0)
            result_text += "🤝 Ничья! Ставка возвращена."
        else:
            await db.update_user_game_stat(callback.from_user.id, game_id, 'loss', -amount)
            result_text += "😢 Вы проиграли."
            
        await callback.message.edit_text(result_text, reply_markup=get_game_menu_keyboard(game_id))
        await state.clear()

@router.callback_query(F.data == "admin_games")
async def admin_games_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    
    settings = await db.get_all_game_settings()
    settings_dict = {name: coeff for name, coeff in settings}
    
    await callback.message.edit_text("⚙️ Настройки коэффициентов игр:", reply_markup=get_admin_games_keyboard(settings_dict))

@router.callback_query(F.data.startswith("admin_coef_"))
async def admin_edit_coef(callback: CallbackQuery, state: FSMContext):
     game_id = callback.data.replace("admin_coef_", "")
     await state.update_data(edit_game=game_id)
     await callback.message.answer(f"Введите новый коэффициент для игры (текущий: стандарт):")
     await state.set_state(AdminState.edit_coefficient)
     await callback.answer()

@router.message(AdminState.edit_coefficient)
async def admin_save_coef(message: Message, state: FSMContext):
    try:
        new_coef = float(message.text)
        data = await state.get_data()
        game_id = data.get("edit_game")
        
        await db.set_game_coefficient(game_id, new_coef)
        await message.answer(f"✅ Коэффициент для {game_id} обновлен до {new_coef}")
        
        settings = await db.get_all_game_settings()
        settings_dict = {name: coeff for name, coeff in settings}
        await message.answer("⚙️ Настройки игр:", reply_markup=get_admin_games_keyboard(settings_dict))
        await state.clear()
    except ValueError:
        await message.answer("Введите число.")

@router.message(F.text & ~F.text.startswith("/"), StateFilter(None))
async def check_promo_activation(message: Message, state: FSMContext):
    code = message.text.strip()
    promo = await db.get_promo(code)
    
    if promo:
        amount, activations, expires_at = promo
        
        if await db.is_promo_used_by_user(message.from_user.id, code):
            await message.answer("❌ Вы уже активировали этот промокод.")
            return

        if activations == -1:
            if datetime.now().timestamp() > expires_at:
                await db.delete_promo(code)
                await message.answer("❌ Срок действия промокода истек.")
                return
        
        await db.activate_promo(message.from_user.id, code)
        await db.update_balance(message.from_user.id, amount)
        await message.answer(f"✅ Промокод активирован! Начислено: {amount} RUB")
    else:
        curr_state = await state.get_state()
        if curr_state is None:
             pass 

@router.callback_query(F.data == "pvp_create")
async def pvp_create_start(callback: CallbackQuery):
    try:
        await callback.message.edit_caption(caption="🎮 Выберите игру для создания:", reply_markup=get_pvp_create_type_keyboard())
    except:
        await callback.message.edit_text(text="🎮 Выберите игру для создания:", reply_markup=get_pvp_create_type_keyboard())

@router.callback_query(F.data == "pvp_cancel_create")
async def pvp_cancel_create(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.edit_caption(caption="🎮 Выберите режим игры:", reply_markup=get_games_players_keyboard())
    except:
        await callback.message.edit_text(text="🎮 Выберите режим игры:", reply_markup=get_games_players_keyboard())

@router.callback_query(F.data.startswith("pvp_type_"))
async def pvp_type_selected(callback: CallbackQuery, state: FSMContext):
    game_type = callback.data.replace("pvp_type_", "")
    await state.update_data(pvp_game_type=game_type)
    
    try:
        await callback.message.edit_caption(caption=f"💰 Введите сумму ставки (минимум 10 RUB):", reply_markup=get_pvp_bet_cancel_keyboard())
    except:
        await callback.message.edit_text(text=f"💰 Введите сумму ставки (минимум 10 RUB):", reply_markup=get_pvp_bet_cancel_keyboard())
    await state.set_state(PvPState.bet_amount)

@router.message(PvPState.bet_amount)
async def pvp_bet_amount_handler(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount < 10:
            await message.answer("Минимум 10 RUB. Попробуйте снова.")
            return

        user_data = await db.get_user_data(message.from_user.id)
        balance = user_data[1]

        if amount > balance:
            await message.answer("Недостаточно средств на балансе.")
            return
        
        active_game = await db.get_active_game_by_user(message.from_user.id)
        if active_game:
            await message.answer("❌ У вас уже есть активная игра! Завершите её.")
            return

        data = await state.get_data()
        game_type = data.get("pvp_game_type")
        username = message.from_user.username or message.from_user.first_name

        await db.update_balance(message.from_user.id, -amount)
        game_id = await db.create_pvp_game(game_type, message.from_user.id, username, amount)
        
        emoji_map = {
            "dice": "🎲", "football": "⚽", "basketball": "🏀", 
            "darts": "🎯", "bowling": "🎳"
        }
        emoji = emoji_map.get(game_type, "🎲")

        await message.answer(f"✅ Игра создана!\n{emoji} Тип: {game_type}\n💰 Ставка: {amount} RUB\n⌛ Ожидание игрока...", reply_markup=get_games_players_keyboard())
        await state.clear()
        
        try:
             bot_info = await bot.get_me()
             link = f"https://t.me/{bot_info.username}?start=join_{game_id}"
             kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💰 Поставить ставку", url=link)]])
             await bot.send_message(MAIN_CHAT_ID, f"🎮 <b>Новая игра! #{game_id}</b>\n\n👤 Игрок: {html.escape(username)}\n💰 Ставка: {amount} RUB\n{emoji} Тип: {game_type}\n\n👇 Жми кнопку, чтобы сыграть!", reply_markup=kb)
        except Exception as e:
             print(f"Chat notification error: {e}")

    except ValueError:
        await message.answer("Введите число.")

@router.callback_query(F.data == "pvp_list")
async def pvp_list_callback(callback: CallbackQuery):
    games = await db.get_pvp_games()
    if not games:
        await callback.answer("Активных игр нет.", show_alert=True)
        return
        
    try:
        await callback.message.edit_caption(caption="📋 Список активных игр (нажмите, чтобы сыграть):", reply_markup=get_pvp_games_list_keyboard(games))
    except:
        await callback.message.edit_text(text="📋 Список активных игр (нажмите, чтобы сыграть):", reply_markup=get_pvp_games_list_keyboard(games))

@router.callback_query(F.data.startswith("pvp_join_") & ~F.data.startswith("pvp_join_move_") & ~F.data.startswith("pvp_confirm_join_"))
async def pvp_join_callback(callback: CallbackQuery):
    game_id = int(callback.data.replace("pvp_join_", ""))
    game = await db.get_pvp_game(game_id)
    
    if not game:
        await callback.answer("Игра не найдена или уже сыграна.", show_alert=True)
        await pvp_list_callback(callback)
        return
        
    _, game_type, creator_id, creator_name, bet, _, joiner_id, _, _, _ = game
    
    if callback.from_user.id == creator_id:
        await db.delete_pvp_game(game_id)
        await db.update_balance(creator_id, bet)
        await callback.answer("✅ Вы удалили свою игру. Ставка возвращена.", show_alert=True)
        await pvp_list_callback(callback)
        return

    emoji_map = {
        "dice": "🎲", "football": "⚽", "basketball": "🏀", 
        "darts": "🎯", "bowling": "🎳"
    }
    emoji = emoji_map.get(game_type, "🎲")
    
    text = f"🎮 <b>Игра #{game_id}</b>\n\n👤 Создатель: {html.escape(creator_name)}\n💰 Ставка: {bet} RUB\n{emoji} Тип: {game_type}\n\nХотите сыграть?"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Играть", callback_data=f"pvp_confirm_join_{game_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="pvp_list")]
    ])
    try:
        await callback.message.edit_caption(caption=text, reply_markup=keyboard)
    except:
        await callback.message.edit_text(text=text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("pvp_confirm_join_"))
async def pvp_confirm_join_callback(callback: CallbackQuery):
    game_id = int(callback.data.replace("pvp_confirm_join_", ""))
    game = await db.get_pvp_game(game_id)
    
    if not game:
        await callback.answer("Игра не найдена или уже сыграна.", show_alert=True)
        await pvp_list_callback(callback)
        return
        
    _, game_type, creator_id, creator_name, bet, _, joiner_id, _, _, _ = game
    
    if callback.from_user.id == creator_id:
        await callback.answer("Нельзя играть с самим собой!", show_alert=True)
        return

    if joiner_id != 0:
        await callback.answer("В этой игре уже есть участник.", show_alert=True)
        return

    user_data = await db.get_user_data(callback.from_user.id)
    balance = user_data[1]
    
    if balance < bet:
        await callback.answer("Недостаточно средств для участия.", show_alert=True)
        return
        
    active_game = await db.get_active_game_by_user(callback.from_user.id)
    if active_game:
        await callback.answer("❌ У вас уже есть активная игра!", show_alert=True)
        return

    await db.update_balance(callback.from_user.id, -bet)
    joiner_name = callback.from_user.username or callback.from_user.first_name
    await db.join_pvp_game(game_id, callback.from_user.id, joiner_name)
    
    kb = get_pvp_join_move_keyboard(game_id, game_type)
    
    emoji_map = {
        "dice": "🎲", "football": "⚽", "basketball": "🏀", 
        "darts": "🎯", "bowling": "🎳"
    }
    emoji = emoji_map.get(game_type, "🎲")
    
    await callback.message.delete()
    await callback.message.answer(f"⚔️ <b>Дуэль началась!</b>\n🔴 {html.escape(creator_name)} vs 🔵 {html.escape(joiner_name)}\n💰 Ставка: {bet} RUB\n\n{emoji} Ждем броски от обоих игроков!", reply_markup=kb)
    
    try:
         await bot.send_message(creator_id, f"⚔️ <b>Игрок {html.escape(joiner_name)} принял ваш вызов!</b>\nID игры: {game_id}\n\n{emoji} Сделайте ваш ход (нажмите кнопку или отправьте эмодзи):", reply_markup=kb)
    except: pass

@router.callback_query(F.data.startswith("pvp_join_move_"))
async def pvp_action_throw_callback(callback: CallbackQuery):
    game_id = int(callback.data.replace("pvp_join_move_", ""))
    await process_pvp_move(callback.from_user.id, game_id, callback.message)
    await callback.answer()

@router.message(F.dice)
async def pvp_manual_throw_handler(message: Message):
    game = await db.get_active_game_by_user(message.from_user.id)
    if game:
        game_id = game[0]
        await process_pvp_move(message.from_user.id, game_id, message, manual_value=message.dice.value)

async def process_pvp_move(user_id, game_id, message_obj, manual_value=None):
    game = await db.get_pvp_game(game_id)
    if not game:
        if not manual_value:
            await message_obj.edit_text("Игра не найдена.")
        return

    id, game_type, creator_id, creator_name, bet, creator_value, joiner_id, joiner_name, joiner_value, _ = game
    
    if user_id == creator_id and creator_value != 0:
        if not manual_value: await message_obj.answer("Вы уже сделали ход!")
        return
    if user_id == joiner_id and joiner_value != 0:
        if not manual_value: await message_obj.answer("Вы уже сделали ход!")
        return

    value = manual_value
    emoji_map = {
        "dice": "🎲", "football": "⚽", "basketball": "🏀", 
        "darts": "🎯", "bowling": "🎳"
    }
    emoji = emoji_map.get(game_type, "🎲")

    if value is None:
        msg = await message_obj.answer_dice(emoji=emoji)
        value = msg.dice.value
        await asyncio.sleep(3)
    
    updated = await db.update_pvp_game_move(game_id, user_id, value)
    
    if updated:
        game_fresh = await db.get_pvp_game(game_id)
        creator_v = game_fresh[5]
        joiner_v = game_fresh[8]
        
        if creator_v != 0 and joiner_v != 0:
            await finish_pvp_game(game_fresh)
        else:
             if not manual_value:
                 await message_obj.edit_text(f"{emoji} Ваш ход: {value}\n⏳ Ожидание соперника...")
             else:
                 await message_obj.answer(f"{emoji} Ваш ход принят: {value}\n⏳ Ожидание соперника...")

async def finish_pvp_game(game):
    id, game_type, creator_id, creator_name, bet, creator_val, joiner_id, joiner_name, joiner_val, _ = game
    
    emoji_map = {
        "dice": "🎲", "football": "⚽", "basketball": "🏀", 
        "darts": "🎯", "bowling": "🎳"
    }
    emoji = emoji_map.get(game_type, "🎲")
    
    result_text = f"{emoji} <b>Игра #{id} завершена!</b>\n\n🔴 {html.escape(creator_name)}: {creator_val}\n🔵 {html.escape(joiner_name)}: {joiner_val}\n"
    win_amount = bet * 2
    
    if creator_val > joiner_val:
        await db.update_balance(creator_id, win_amount)
        result_text += f"\n🏆 <b>Победил {html.escape(creator_name)}!</b>\n💰 Выигрыш: {win_amount} RUB"
    elif joiner_val > creator_val:
        await db.update_balance(joiner_id, win_amount)
        result_text += f"\n🏆 <b>Победил {html.escape(joiner_name)}!</b>\n💰 Выигрыш: {win_amount} RUB"
    else:
        await db.update_balance(creator_id, bet)
        await db.update_balance(joiner_id, bet)
        result_text += "\n🤝 <b>Ничья!</b> Ставки возвращены."
        
    await db.delete_pvp_game(id)
    
    try:
        await bot.send_message(creator_id, result_text, parse_mode="HTML")
    except: pass
    
    try:
        await bot.send_message(joiner_id, result_text, parse_mode="HTML")
    except: pass

    try:
        await bot.send_message(MAIN_CHAT_ID, result_text, parse_mode="HTML")
    except: pass
    
@router.callback_query(F.data == "admin_pvp_cancel_menu")
async def admin_pvp_cancel_menu(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    
    games = await db.get_all_active_pvp_games()
    text = "Введите ID игры для отмены (или отправьте 0 для отмены всех старых игр > 24ч):\n\n"
    if games:
        for g in games:
            gid, cname, bet, jname = g
            status = "Ожидание" if not jname else f"vs {html.escape(jname)}"
            text += f"🆔 <code>{gid}</code> | {html.escape(cname)} | {bet}₽ | {status}\n"
    else:
        text += "Активных игр нет."
        
    await callback.message.answer(text)
    await state.set_state(AdminState.pvp_cancel_id)

@router.message(AdminState.pvp_cancel_id)
async def admin_pvp_cancel_handler(message: Message, state: FSMContext):
    try:
        game_id = int(message.text)
        if game_id == 0:
             pass 
        
        game = await db.get_pvp_game(game_id)
        if not game:
            await message.answer("Игра не найдена.")
            return
            
        _, _, creator_id, _, bet, _, joiner_id, _, _, _ = game
        
        await db.delete_pvp_game(game_id)
        
        await db.update_balance(creator_id, bet)
        if joiner_id != 0:
            await db.update_balance(joiner_id, bet)
            
        await message.answer(f"✅ Игра {game_id} отменена. Средства возвращены.")
        await state.clear()
    except ValueError:
        await message.answer("Введите число.")

async def pvp_maintenance_task():
    while True:
        try:
            pending_games = await db.get_old_pending_games(900)
            for game in pending_games:
                gid, cid, bet = game
                await db.delete_pvp_game(gid)
                await db.update_balance(cid, bet)
                try:
                    await bot.send_message(cid, f"⏰ Ваша игра #{gid} была отменена из-за отсутствия оппонента (15 мин). Ставка возвращена.")
                except: pass
                
            stalled_games = await db.get_stalled_active_games(60)
            for game in stalled_games:
                gid, gtype, cid, cname, bet, cval, jid, jname, jval, jat = game
                
                updated = False
                if cval == 0:
                    val = random.randint(1, 6)
                    await db.update_pvp_game_move(gid, cid, val)
                    try: await bot.send_message(cid, f"⏰ Время вышло! Авто-ход: {val}")
                    except: pass
                    updated = True
                    
                if jval == 0:
                    val = random.randint(1, 6)
                    await db.update_pvp_game_move(gid, jid, val)
                    try: await bot.send_message(jid, f"⏰ Время вышло! Авто-ход: {val}")
                    except: pass
                    updated = True
                    
                if updated:
                    fresh_game = await db.get_pvp_game(gid)
                    if fresh_game[5] != 0 and fresh_game[8] != 0:
                        await finish_pvp_game(fresh_game)
                        
        except Exception as e:
            print(f"PvP Maintenance Error: {e}")
            
        await asyncio.sleep(30)

