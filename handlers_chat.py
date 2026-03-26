from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ContentType
from loader import bot, db
from config import MAIN_CHAT_ID, ADMIN_ID
from keyboards import get_chat_game_keyboard
import json, re, asyncio, random, html

chat_router = Router()

@chat_router.message(F.content_type == ContentType.PINNED_MESSAGE)
async def delete_pin_service_message(message: Message):
    try:
        await message.delete()
    except:
        pass

@chat_router.message(Command("bal"))
async def cmd_balance(message: Message):
    user_data = await db.get_user_data(message.from_user.id)
    if not user_data:
        await message.reply("Вы не зарегистрированы.")
        return
    await message.reply(f"💰 Ваш баланс: {user_data[1]} RUB")

@chat_router.message(Command("getid"))
async def cmd_getid(message: Message):
    await message.reply(f"🆔 Ваш ID: <code>{message.from_user.id}</code>", parse_mode="HTML")

@chat_router.message(Command("spin"))
async def cmd_spin(message: Message):
    try:
        args = message.text.split()
        if len(args) < 2:
            await message.reply("Использование: /spin [сумма]")
            return
        
        amount = float(args[1])
        if amount < 100:
            await message.reply("Минимальная ставка 100 RUB")
            return
            
        user_data = await db.get_user_data(message.from_user.id)
        if not user_data or user_data[1] < amount:
            await message.reply("Недостаточно средств.")
            return
            
        await db.update_balance(message.from_user.id, -amount)
        
        msg = await message.answer_dice(emoji="🎰")
        value = msg.dice.value
        await asyncio.sleep(4)
        
        win = 0
        if value == 64:
            win = amount * 10
            await message.reply(f"🎰 JACKPOT! Вы выиграли {win} RUB!")
        elif value in [1, 22, 43]:
            win = amount * 3
            await message.reply(f"🎰 Выпало три в ряд! Вы выиграли {win} RUB!")
            
        if win > 0:
            await db.update_balance(message.from_user.id, win)
            
    except ValueError:
        await message.reply("Введите число.")

@chat_router.message(Command("dice"))
async def cmd_dice_pve(message: Message):
    try:
        args = message.text.split()
        if len(args) < 3:
            await message.reply("Использование: /dice [сумма] [число 1-6]")
            return
            
        amount = float(args[1])
        target = int(args[2])
        
        if amount < 10:
            await message.reply("Минимальная ставка 10 RUB")
            return
        if not (1 <= target <= 6):
            await message.reply("Число должно быть от 1 до 6")
            return
            
        user_data = await db.get_user_data(message.from_user.id)
        if not user_data or user_data[1] < amount:
            await message.reply("Недостаточно средств.")
            return
            
        await db.update_balance(message.from_user.id, -amount)
        
        msg = await message.answer_dice(emoji="🎲")
        value = msg.dice.value
        await asyncio.sleep(3)
        
        if value == target:
            win = amount * 2
            await db.update_balance(message.from_user.id, win)
            await message.reply(f"🎉 Вы угадали! Выигрыш: {win} RUB")
        else:
            await message.reply(f"❌ Не угадали. Выпало: {value}")
            
    except ValueError:
        await message.reply("Введите корректные числа.")

GAME_REGEX = r"^/(cub|dar|boul|bas|foot)(?:(2|3|4|5)x|total(2|3|4|5)|3p)?\s+(\d+(?:\.\d+)?)$"

@chat_router.message(F.text.regexp(GAME_REGEX))
async def cmd_create_chat_game(message: Message):
    match = re.match(GAME_REGEX, message.text)
    if not match: return
    
    alias = match.group(1)
    
    x_val = match.group(2)
    total_val = match.group(3)
    
    full_cmd = message.text.split()[0]
    amount = float(match.group(4))
    
    game_type_map = {
        "cub": "dice", "dar": "darts", "boul": "bowling", 
        "bas": "basketball", "foot": "football"
    }
    game_type = game_type_map.get(alias)
    
    mode = "classic"
    param = 0
    players_count = 2
    
    if x_val:
        mode = "x"
        param = int(x_val)
    elif total_val:
        mode = "total"
        param = int(total_val)
    elif "3p" in full_cmd:
        mode = "3p"
        players_count = 3
    
    if amount < 10:
        await message.answer("Минимальная ставка 10 RUB")
        return
        
    user_data = await db.get_user_data(message.from_user.id)
    if not user_data or user_data[1] < amount:
        await message.answer("Недостаточно средств.")
        return
        
    await db.update_balance(message.from_user.id, -amount)
    
    username = message.from_user.username or message.from_user.first_name
    
    players = [{
        "id": message.from_user.id,
        "name": username,
        "score": 0,
        "wins": 0,
        "moves": []
    }]
    
    game_id = await db.create_chat_game(
        message.chat.id, 0, message.from_user.id, username, 
        game_type, mode, param, amount, json.dumps(players)
    )
    
    emoji_map = {
        "dice": "🎲", "darts": "🎯", "bowling": "🎳", 
        "basketball": "🏀", "football": "⚽"
    }
    emoji = emoji_map.get(game_type, "🎲")
    
    mode_text = ""
    if mode == "x": mode_text = f" (До {param} побед)"
    elif mode == "total": mode_text = f" (Сумма {param} бросков)"
    elif mode == "3p": mode_text = " (3 игрока)"
    
    text = f"{emoji} <b>Игра #{game_id}</b>{mode_text}\n💰 Ставка: {amount} RUB\n👤 {html.escape(username)} (1/{players_count})\n\n👇 Нажми, чтобы вступить!"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Вступить", callback_data=f"join_chat_game_{game_id}")]
    ])
    
    sent_msg = await message.reply(text, reply_markup=kb, parse_mode="HTML")
    await db.update_chat_game(game_id, json.dumps(players), message_id=sent_msg.message_id)

@chat_router.message(F.text.regexp(r"^/(cub|dar|boul|bas|foot)(?:(2|3|4|5)x|total(2|3|4|5)|3p)?"))
async def cmd_chat_game_help(message: Message):
    match = re.match(r"^/([a-z]+)", message.text)
    alias = match.group(1) if match else "cub"
    
    base = alias
    for s in ["2x","3x","4x","5x","total","3p"]:
        base = base.replace(s, "")
    
    if "cub" in message.text: base = "cub"
    elif "dar" in message.text: base = "dar"
    elif "boul" in message.text: base = "boul"
    elif "bas" in message.text: base = "bas"
    elif "foot" in message.text: base = "foot"
    
    text = (
        f"ℹ️ <b>Как играть:</b>\n\n"
        f"/{base} [сумма] - Классика (1 на 1)\n"
        f"/{base}3p [сумма] - 3 игрока\n"
        f"/{base}[2-5]x [сумма] - До * побед\n"
        f"/{base}total[2-5] [сумма] - Сумма * бросков\n\n"
        f"<i>Пример: /{base} 100</i>"
    )
    await message.reply(text, parse_mode="HTML")

@chat_router.callback_query(F.data.startswith("join_chat_game_"))
async def join_chat_game_callback(callback: CallbackQuery):
    game_id = int(callback.data.replace("join_chat_game_", ""))
    game = await db.get_chat_game(game_id)
    
    if not game:
        await callback.answer("Игра не найдена.", show_alert=True)
        return
    
    gid, cid, mid, cre_id, cre_name, gtype, mode, param, bet, players_json, status, created = game
    
    if status != 'pending':
        await callback.answer("Игра уже идет или завершена.", show_alert=True)
        return
        
    players = json.loads(players_json)
    
    if any(p['id'] == callback.from_user.id for p in players):
        await callback.answer("Вы уже в игре!", show_alert=True)
        return
        
    max_p = 3 if mode == "3p" else 2
    if len(players) >= max_p:
        await callback.answer("Игра полная.", show_alert=True)
        return
        
    user_data = await db.get_user_data(callback.from_user.id)
    if not user_data or user_data[1] < bet:
        await callback.answer("Недостаточно средств.", show_alert=True)
        return
        
    await db.update_balance(callback.from_user.id, -bet)
    
    new_player = {
        "id": callback.from_user.id,
        "name": callback.from_user.username or callback.from_user.first_name,
        "score": 0,
        "wins": 0,
        "moves": []
    }
    players.append(new_player)
    
    emoji_map = {
        "dice": "🎲", "darts": "🎯", "bowling": "🎳", 
        "basketball": "🏀", "football": "⚽"
    }
    emoji = emoji_map.get(gtype, "🎲")
    mode_text = ""
    if mode == "x": mode_text = f" (До {param} побед)"
    elif mode == "total": mode_text = f" (Сумма {param} бросков)"
    elif mode == "3p": mode_text = " (3 игрока)"
    
    player_list = "\n".join([f"👤 {html.escape(p['name'])}" for p in players])
    text = f"{emoji} <b>Игра #{gid}</b>{mode_text}\n💰 Ставка: {bet} RUB\n{player_list}\n({len(players)}/{max_p})"
    
    if len(players) == max_p:
        await db.update_chat_game(gid, json.dumps(players), status='active')
        
        if mode == "classic": mode_desc = "Классика (1 бросок)"
        elif mode == "3p": mode_desc = "3 Игрока (1 бросок)"
        elif mode == "x": mode_desc = f"Игра ведётся до {param} бросков (Сумма)"
        elif mode == "total": mode_desc = f"Игра ведётся (Сумма {param} бросков)"
        
        p_list = ""
        for i, p in enumerate(players):
            p_list += f"{i+1}️⃣ - {html.escape(p['name'])} [0]\n"
            
        start_text = (
            f"{emoji} <b>{gtype.upper()} {mode.upper()} #{gid}</b>\n\n"
            f"⚡️ {mode_desc}\n\n"
            f"👥 <b>Игроки:</b>\n{p_list}\n"
            f"— Отправьте {emoji} в ответ на это сообщение\n\n"
            f"💰 <b>Ставка: {bet} RUB</b>"
        )
        
        await bot.edit_message_text(text=text + "\n\n🚀 Игра началась!", chat_id=cid, message_id=mid, parse_mode="HTML")
        msg = await bot.send_message(cid, start_text, reply_markup=get_chat_game_keyboard(gid, gtype), parse_mode="HTML", reply_to_message_id=mid)
        await db.update_chat_game(gid, json.dumps(players), status='active', message_id=msg.message_id)
        asyncio.create_task(game_auto_roll_monitor(gid, param))
    else:
        await db.update_chat_game(gid, json.dumps(players))
        await bot.edit_message_text(text=text, chat_id=cid, message_id=mid, reply_markup=callback.message.reply_markup, parse_mode="HTML")
    


@chat_router.callback_query(F.data.startswith("chat_game_move_"))
async def chat_game_move_callback(callback: CallbackQuery):
    game_id = int(callback.data.replace("chat_game_move_", ""))
    await process_chat_game_move(game_id, callback.from_user, None, callback)

@chat_router.message(F.dice)
async def chat_game_manual_dice(message: Message):
    if message.forward_from or message.forward_date:
        return

    if not message.reply_to_message:
        return
        
    reply_id = message.reply_to_message.message_id
    games = await db.get_active_chat_games(message.chat.id)
    
    game = next((g for g in games if g[2] == reply_id), None)
    
    if not game:
         txt = message.reply_to_message.text or message.reply_to_message.caption or ""
         if '#' in txt:
             match = re.search(r"#(\d+)", txt)
             if match:
                 parsed_id = int(match.group(1))
                 game = next((g for g in games if g[0] == parsed_id), None)
    
    if not game:
        return
    
    gid, _, mid, _, _, gtype, _, _, _, _, _, _ = game
    
    emoji_map = {
        "dice": "🎲", "darts": "🎯", "bowling": "🎳", 
        "basketball": "🏀", "football": "⚽"
    }
    
    expected_emoji = emoji_map.get(gtype, "🎲")
    if message.dice.emoji != expected_emoji:
         await message.reply("Неверный тип кубика для этой игры.")
         return
        
    await process_chat_game_move(gid, message.from_user, message.dice.value, message)

async def process_chat_game_move(game_id, user, value, messageable):
    game = await db.get_chat_game(game_id)
    if not game:
        if isinstance(messageable, CallbackQuery): await messageable.answer("Игра завершена.", show_alert=True)
        return
        
    gid, cid, mid, cre_id, cre_name, gtype, mode, param, bet, players_json, status, created = game
    
    if status != 'active':
         if isinstance(messageable, CallbackQuery): await messageable.answer("Игра не активна.", show_alert=True)
         return

    players = json.loads(players_json)
    player_idx = next((i for i, p in enumerate(players) if p['id'] == user.id), None)
    
    if player_idx is None:
        if isinstance(messageable, CallbackQuery): await messageable.answer("Вы не участник.", show_alert=True)
        else: await messageable.reply("Вы не участник этой игры.")
        return
        
    player = players[player_idx]

    if mode == "classic" or mode == "3p":
        target = 1
    elif mode == "total" or mode == "x":
         target = param
    else:
        target = 1

    if len(player['moves']) >= target:
        if isinstance(messageable, CallbackQuery):
             await messageable.answer("Вы уже сделали все ходы.", show_alert=True)
        else:
             await messageable.reply("Вы уже сделали все ходы.")
        return

    my_moves_cnt = len(player['moves'])
        
    val = value
    if val is None:
        emoji_map = {
            "dice": "🎲", "football": "⚽", "basketball": "🏀", 
            "darts": "🎯", "bowling": "🎳"
        }
        emoji = emoji_map.get(gtype, "🎲")
        
        if isinstance(messageable, CallbackQuery):
            msg = await messageable.message.answer_dice(emoji=emoji)
        else:
            msg = await messageable.reply_dice(emoji=emoji)
            
        val = msg.dice.value
        await asyncio.sleep(3)
    else:
        pass
    
    player['moves'].append(val)
    player['score'] += val
    players[player_idx] = player
    
    await db.update_chat_game(gid, json.dumps(players))
    
    if val is not None:
         pass
    else:
         if isinstance(messageable, CallbackQuery):
             await messageable.message.answer(f"👤 {html.escape(player['name'])}: {val}")

    if mode == "classic": mode_desc = "Классика (1 бросок)"
    elif mode == "3p": mode_desc = "3 Игрока (1 бросок)"
    elif mode == "x": mode_desc = f"Игра ведётся до {param} бросков (Сумма)"
    elif mode == "total": mode_desc = f"Игра ведётся (Сумма {param} бросков)"
    
    emoji_map = {
        "dice": "🎲", "darts": "🎯", "bowling": "🎳", 
        "basketball": "🏀", "football": "⚽"
    }
    emoji = emoji_map.get(gtype, "🎲")
    
    p_list = ""
    for i, p in enumerate(players):
        curr_score = p['score'] if (mode=='x' or mode=='total') else (p['moves'][0] if p['moves'] else 0)
        p_list += f"{i+1}️⃣ - {html.escape(p['name'])} [{curr_score}]\n"
        
    update_text = (
        f"{emoji} <b>{gtype.upper()} {mode.upper()} #{gid}</b>\n\n"
        f"⚡️ {mode_desc}\n\n"
        f"👥 <b>Игроки:</b>\n{p_list}\n"
        f"— Отправьте {emoji} в ответ на это сообщение\n\n"
        f"💰 <b>Ставка: {bet} RUB</b>"
    )
    
    try:
        await bot.edit_message_text(text=update_text, chat_id=cid, message_id=mid, reply_markup=get_chat_game_keyboard(gid, gtype), parse_mode="HTML")
    except Exception as e:
        print(f"Edit error: {e}")

    if len(player['moves']) == target and target > 1:
        await bot.send_message(cid, f"👤 <b>{html.escape(player['name'])}</b> закончил! Всего: {player['score']} очков.", parse_mode="HTML")
    
    max_moves = max(len(p['moves']) for p in players)
    min_moves = min(len(p['moves']) for p in players)
    
    if min_moves == max_moves:
        round_num = min_moves
        
        if mode == "x":
             pass
             await db.update_chat_game(gid, json.dumps(players))

        if min_moves >= target:
             if isinstance(messageable, CallbackQuery):
                 await finish_chat_game(messageable.message, gid, players, bet, mode)
             else:
                 await finish_chat_game(messageable, gid, players, bet, mode)
             await db.update_chat_game(gid, json.dumps(players), status='finished')

async def finish_chat_game(message, gid, players, bet, mode):
    game = await db.get_chat_game(gid)
    gtype = game[5] if game else "dice"
    
    emoji_map = {
        "dice": "🎲", "football": "⚽", "basketball": "🏀", 
        "darts": "🎯", "bowling": "🎳"
    }
    emoji = emoji_map.get(gtype, "🎲")
    
    type_name_map = {
        "dice": "CUBE", "football": "FOOTBALL", "basketball": "BASKETBALL",
        "darts": "DARTS", "bowling": "BOWLING"
    }
    type_name = type_name_map.get(gtype, "GAME")
    
    mode_str = ""
    if mode == "classic": mode_str = "CLASSIC"
    elif mode == "3p": mode_str = "3 PLAYERS"
    elif mode == "x":
         param = game[7]
         mode_str = f"{param}X"
    elif mode == "total":
         param = game[7]
         mode_str = f"TOTAL {param}"
         
    header = f"{emoji} {type_name} {mode_str} #{gid}"
    
    if mode == "x" or mode == "total":
        sorted_players = sorted(players, key=lambda p: p['score'], reverse=True)
    else:
        sorted_players = sorted(players, key=lambda p: p['moves'][0], reverse=True)
        
    if mode == "x" or mode == "total":
        max_s = sorted_players[0]['score']
        winners = [p for p in players if p['score'] == max_s]
    else:
        if not players[0].get('moves'): max_s = 0
        else: max_s = sorted_players[0]['moves'][0]
        winners = [p for p in players if (p['moves'][0] if p['moves'] else 0) == max_s]
    
    p_list = ""
    for i, p in enumerate(players):
        score_val = p['score'] if (mode == "x" or mode == "total") else (p['moves'][0] if p['moves'] else 0)
        p_list += f"{i+1}️⃣ - {html.escape(p['name'])} [{score_val}]\n"
        
    text = f"<b>{header}</b>\n\n"
    
    if len(winners) == 1:
        w = winners[0]
        win_amount = bet * len(players)
        text += f"💰 <b>Выигрыш: {win_amount} RUB</b>\n\n"
        text += f"👥 <b>Игроки:</b>\n{p_list}\n"
        text += f"⚡️ <b>Победитель: {html.escape(w['name'])}</b>"
        
        await db.update_balance(w['id'], win_amount)
    else:
        text += f"💰 <b>Выигрыш: 0 RUB</b> (Возврат)\n\n"
        text += f"👥 <b>Игроки:</b>\n{p_list}\n"
        text += f"⚡️ <b>Ничья!</b>"
        
        for p in players:
            await db.update_balance(p['id'], bet)
            
    chat_id = 0
    if isinstance(message, (int, str)):
         chat_id = game[1]
    else:
         chat_id = message.chat.id
         
    await bot.send_message(chat_id, text, parse_mode="HTML")

@chat_router.message(Command("allgames"))
async def cmd_allgames(message: Message):
    games = await db.get_active_chat_games(message.chat.id)
    if not games:
        await message.reply("Активных игр нет.")
        return
        
    text = "📋 <b>Список активных игр:</b>\n"
    for game in games:
        gid, cid, mid, cid, cname, gtype, mode, param, bet, players_json, status, created = game
        players = json.loads(players_json)
        text += f"#{gid} {gtype} {mode} | {bet} RUB | {len(players)} игроков\n"
        
    await message.reply(text, parse_mode="HTML")

@chat_router.message(Command("del"))
async def cmd_del_game(message: Message):
    if not message.reply_to_message:
        await message.reply("Ответьте на сообщение с игрой.")
        return
        
    reply_id = message.reply_to_message.message_id
    games = await db.get_active_chat_games(message.chat.id)
    game = next((g for g in games if g[2] == reply_id), None)
    
    if not game:
        await message.reply("Игра не найдена.")
        return
        
    gid, cid, mid, cre_id, cre_name, gtype, mode, param, bet, players_json, status, created = game
    
    if message.from_user.id != cre_id and message.from_user.id != ADMIN_ID:
        await message.reply("Вы не можете удалить эту игру.")
        return
        
    if status == 'active' and message.from_user.id != ADMIN_ID:
        await message.reply("Нельзя удалить активную игру!")
        return
        
    players = json.loads(players_json)
    for p in players:
        await db.update_balance(p['id'], bet)
        
    await db.delete_chat_game(gid)
    await message.reply(f"✅ Игра #{gid} удалена. Ставки возвращены.")

async def game_auto_roll_monitor(game_id, target_moves):
    while True:
        await asyncio.sleep(60)
        game = await db.get_chat_game(game_id)
        if not game: break
        
        gid, cid, mid, cre_id, cre_name, gtype, mode, param, bet, players_json, status, created = game
        if status != 'active': break
        
        players = json.loads(players_json)
        changed = False
        
        for p in players:
            if len(p['moves']) < target_moves:
                emoji_map = {
                    "dice": "🎲", "football": "⚽", "basketball": "🏀", 
                    "darts": "🎯", "bowling": "🎳"
                }
                emoji = emoji_map.get(gtype, "🎲")
                
                try:
                    msg = await bot.send_dice(cid, emoji=emoji)
                    val = msg.dice.value
                    p['moves'].append(val)
                    p['score'] += val
                    changed = True
                    await bot.send_message(cid, f"⏳ Авто-ход для {html.escape(p['name'])}: {val}")
                    
                    if len(p['moves']) == target_moves:
                         await bot.send_message(cid, f"👤 <b>{html.escape(p['name'])}</b> закончил! Всего: {p['score']} очков.", parse_mode="HTML")
                         
                except Exception as e:
                    print(f"Auto roll error: {e}")
                    
        if changed:
            await db.update_chat_game(gid, json.dumps(players))
            max_moves = max(len(p['moves']) for p in players)
            min_moves = min(len(p['moves']) for p in players)
            
            if mode == 'x':
                 pass

            if min_moves >= target_moves:
                 await finish_chat_game(mid, gid, players, bet, mode)
                 await db.update_chat_game(gid, json.dumps(players), status='finished')
                 break 

@chat_router.message(Command("adelgame"))
async def cmd_admin_del_game(message: Message):
    is_mod = await db.is_moderator(message.from_user.id)
    if message.from_user.id != ADMIN_ID and not is_mod:
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Использование: /adelgame [ID игры]")
        return
    
    try:
        game_id = int(args[1])
    except:
        await message.reply("Укажите корректный ID.")
        return
    
    game = await db.get_chat_game(game_id)
    if not game:
        await message.reply("Игра не найдена.")
        return
    
    gid, cid, mid, cre_id, cre_name, gtype, mode, param, bet, players_json, status, created = game
    
    players = json.loads(players_json)
    for p in players:
        await db.update_balance(p['id'], bet)
    
    await db.delete_chat_game(gid)
    await message.reply(f"✅ Игра #{gid} удалена. Ставки возвращены.")

@chat_router.message(Command("afast"))
async def cmd_admin_fast(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Использование: /afast [сумма] [секунды]")
        return
    
    try:
        amount = float(args[1])
    except:
        await message.reply("Укажите корректную сумму.")
        return
    
    duration = 15
    if len(args) >= 3:
        try:
            duration = int(args[2])
        except:
            pass
    
    if amount < 10:
        await message.reply("Минимальная сумма 10 RUB")
        return
    
    username = message.from_user.username or message.from_user.first_name
    creator_id = message.from_user.id
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎉 Участвовать", callback_data=f"fast_join_{creator_id}")]
    ])
    
    text = (
        f"🎁 <b>Розыгрыш от @{html.escape(username)}</b>\n\n"
        f"Нажмите кнопку «Участвовать», чтобы принять участие\n\n"
        f"💰 <b>Приз: {amount} RUB</b>\n\n"
        f"⏱ Итоги через {duration} секунд"
    )
    
    sent = await message.answer(text, reply_markup=kb, parse_mode="HTML")
    
    key = f"{sent.chat.id}_{sent.message_id}"
    fast_participants[key] = {'creator_id': creator_id, 'users': [], 'chat_id': sent.chat.id}
    
    try:
        await bot.pin_chat_message(message.chat.id, sent.message_id, disable_notification=True)
    except:
        pass
    
    asyncio.create_task(run_fast_game(sent.chat.id, sent.message_id, amount, username, is_admin=True, duration=duration))

@chat_router.message(Command("fast"))
async def cmd_fast(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Использование: /fast [сумма]")
        return
    
    try:
        amount = float(args[1])
    except:
        await message.reply("Укажите корректную сумму.")
        return
    
    if amount < 10:
        await message.reply("Минимальная сумма 10 RUB")
        return
    
    user_data = await db.get_user_data(message.from_user.id)
    if not user_data or user_data[1] < amount:
        await message.reply("Недостаточно средств.")
        return
    
    await db.update_balance(message.from_user.id, -amount)
    
    username = message.from_user.username or message.from_user.first_name
    creator_id = message.from_user.id
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎉 Участвовать", callback_data=f"fast_join_{creator_id}")]
    ])
    
    text = (
        f"🎁 <b>Розыгрыш от @{html.escape(username)}</b>\n\n"
        f"Нажмите кнопку «Участвовать», чтобы принять участие\n\n"
        f"💰 <b>Приз: {amount} RUB</b>\n\n"
        f"⏱ Итоги через 15 секунд"
    )
    
    sent = await message.answer(text, reply_markup=kb, parse_mode="HTML")
    
    key = f"{sent.chat.id}_{sent.message_id}"
    fast_participants[key] = {'creator_id': creator_id, 'users': []}
    
    asyncio.create_task(run_fast_game(sent.chat.id, sent.message_id, amount, username, is_admin=False, duration=15))

fast_participants = {}

@chat_router.callback_query(F.data.startswith("fast_join_"))
async def fast_join_callback(callback: CallbackQuery):
    key = f"{callback.message.chat.id}_{callback.message.message_id}"
    
    if key not in fast_participants:
        await callback.answer("Розыгрыш завершен!", show_alert=True)
        return
    
    user_id = callback.from_user.id
    username = callback.from_user.username or callback.from_user.first_name
    
    creator_id = fast_participants[key].get('creator_id', 0)
    if user_id == creator_id:
        await callback.answer("Создатель не может участвовать!", show_alert=True)
        return
    
    if any(p['id'] == user_id for p in fast_participants[key]['users']):
        await callback.answer("Вы уже участвуете!", show_alert=True)
        return
    
    fast_participants[key]['users'].append({'id': user_id, 'name': username})
    await callback.answer("Вы участвуете в розыгрыше!", show_alert=True)

async def run_fast_game(chat_id, message_id, amount, creator_name, is_admin, duration=15):
    await asyncio.sleep(duration)
    
    key = f"{chat_id}_{message_id}"
    data = fast_participants.get(key, {'users': []})
    participants = data.get('users', [])
    
    if key in fast_participants:
        del fast_participants[key]
    
    try:
        await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
    except:
        pass
    
    if is_admin:
        await asyncio.sleep(5)
        try:
            await bot.unpin_chat_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            print(f"Unpin error: {e}")
    
    if len(participants) == 0:
        await bot.send_message(chat_id, "🎁 Розыгрыш отменен - нет участников.")
        return
    
    p_list = "\n".join([f"— @{html.escape(p['name'])}" for p in participants])
    
    text = (
        f"🎁 <b>Быстрый розыгрыш</b>\n\n"
        f"👥 <b>Участники:</b>\n\n"
        f"{p_list}"
    )
    
    await bot.send_message(chat_id, text, parse_mode="HTML")
    
    winner = random.choice(participants)
    
    await db.update_balance(winner['id'], amount)
    
    win_text = (
        f"🥳 <b>Победитель - {html.escape(winner['name'])}</b>\n"
        f"💰 Приз составил {amount} RUB"
    )
    
    await bot.send_message(chat_id, win_text, parse_mode="HTML")

@chat_router.message(Command("addmod"))
async def cmd_add_mod(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Использование: /addmod [ID]")
        return
    
    try:
        user_id = int(args[1])
    except:
        await message.reply("Укажите корректный ID.")
        return
    
    result = await db.add_moderator(user_id)
    if result:
        await message.reply(f"✅ Пользователь {user_id} назначен модератором.")
    else:
        await message.reply(f"Пользователь уже модератор.")

@chat_router.message(Command("delmod"))
async def cmd_del_mod(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Использование: /delmod [ID]")
        return
    
    try:
        user_id = int(args[1])
    except:
        await message.reply("Укажите корректный ID.")
        return
    
    await db.remove_moderator(user_id)
    await message.reply(f"✅ Пользователь {user_id} снят с модератора.")

@chat_router.message(Command("mods"))
async def cmd_list_mods(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    mods = await db.get_all_moderators()
    if not mods:
        await message.reply("Модераторов нет.")
        return
    
    text = "👮 <b>Модераторы:</b>\n"
    for m in mods:
        text += f"• {m[0]}\n"
    
    await message.reply(text, parse_mode="HTML")

async def chat_game_maintenance_task():
    while True:
        try:
            old_games = await db.get_old_chat_games(900)
            
            for game in old_games:
                game_id, chat_id, message_id, creator_id, bet = game
                
                await db.update_balance(creator_id, bet)
                await db.delete_chat_game(game_id)
                
                try:
                    await bot.delete_message(chat_id, message_id)
                except:
                    pass
                    
                try:
                    await bot.send_message(chat_id, f"🗑 Игра #{game_id} удалена из-за неактивности (15 мин). Ставка возвращена.")
                except:
                    pass
                    
        except:
            pass
            
        await asyncio.sleep(60)
