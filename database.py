import aiosqlite
from datetime import datetime

class Database:
    def __init__(self, db_file):
        self.db_file = db_file
        self.cache = set()

    async def connect(self):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, user_id INTEGER UNIQUE, username TEXT, balance REAL DEFAULT 0.0, reg_date TEXT, topic_id INTEGER)")
            try:
                await db.execute("ALTER TABLE users ADD COLUMN balance REAL DEFAULT 0.0")
            except: pass
            try:
                await db.execute("ALTER TABLE users ADD COLUMN reg_date TEXT")
            except: pass
            try:
                await db.execute("ALTER TABLE users ADD COLUMN topic_id INTEGER")
            except: pass
            try:
                await db.execute("ALTER TABLE users ADD COLUMN total_withdrawn REAL DEFAULT 0.0")
            except: pass
            try:
                await db.execute("ALTER TABLE users ADD COLUMN referrer_id INTEGER DEFAULT 0")
            except: pass
            try:
                await db.execute("ALTER TABLE users ADD COLUMN referral_earnings REAL DEFAULT 0.0")
            except: pass
            
            try:
                await db.execute("ALTER TABLE users ADD COLUMN referral_confirmed INTEGER DEFAULT 1")
            except: pass
            
            try:
                await db.execute("ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0")
            except: pass

            try:
                await db.execute("ALTER TABLE users ADD COLUMN ban_expires REAL DEFAULT 0")
            except: pass

            try:
                await db.execute("ALTER TABLE users ADD COLUMN ban_reason TEXT")
            except: pass

            try:
                await db.execute("ALTER TABLE users ADD COLUMN ban_type INTEGER DEFAULT 1")
            except: pass
            
            await db.execute("CREATE TABLE IF NOT EXISTS chat_games (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER, message_id INTEGER, creator_id INTEGER, creator_name TEXT, game_type TEXT, mode TEXT, param INTEGER, bet REAL, players TEXT, status TEXT DEFAULT 'pending', created_at REAL)")
            
            await db.execute("CREATE TABLE IF NOT EXISTS moderators (user_id INTEGER PRIMARY KEY)")
            
            await db.commit()
            
            async with db.execute("SELECT user_id FROM users") as cursor:
                 rows = await cursor.fetchall()
                 self.cache = {row[0] for row in rows}
                 


    async def user_exists(self, user_id):
        return user_id in self.cache

    async def add_user(self, user_id, username, reg_date, referrer_id=0, confirmed=1):
        if user_id in self.cache:
            return
        
        self.cache.add(user_id)
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("INSERT INTO users (user_id, username, reg_date, balance, topic_id, referrer_id, referral_earnings, referral_confirmed, is_banned, ban_expires, ban_reason, ban_type) VALUES (?, ?, ?, 0.0, 0, ?, 0.0, ?, 0, 0, NULL, 0)", (user_id, username, reg_date, referrer_id, confirmed))
            await db.commit()

    async def get_user_data(self, user_id):
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute("SELECT username, balance, reg_date, topic_id FROM users WHERE user_id = ?", (user_id,)) as cursor:
                return await cursor.fetchone()

    async def update_balance(self, user_id, amount):
         async with aiosqlite.connect(self.db_file) as db:
            await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
            await db.commit()
            
    async def ban_user(self, user_id, duration_minutes, ban_type, reason):
        async with aiosqlite.connect(self.db_file) as db:
            expires = 0
            if duration_minutes > 0:
                expires = datetime.now().timestamp() + (duration_minutes * 60)
            
            await db.execute("UPDATE users SET is_banned = 1, ban_expires = ?, ban_type = ?, ban_reason = ? WHERE user_id = ?", (expires, ban_type, reason, user_id))
            await db.commit()

    async def unban_user(self, user_id):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("UPDATE users SET is_banned = 0, ban_expires = 0, ban_reason = NULL, ban_type = 0 WHERE user_id = ?", (user_id,))
            await db.commit()

    async def get_ban_status(self, user_id):
        async with aiosqlite.connect(self.db_file) as db:
            try:
                await db.execute("ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0")
                await db.execute("ALTER TABLE users ADD COLUMN ban_expires REAL DEFAULT 0")
                await db.execute("ALTER TABLE users ADD COLUMN ban_reason TEXT")
                await db.execute("ALTER TABLE users ADD COLUMN ban_type INTEGER DEFAULT 1")
                await db.commit()
            except: pass
            
            async with db.execute("SELECT is_banned, ban_expires, ban_reason, ban_type FROM users WHERE user_id = ?", (user_id,)) as cursor:
                res = await cursor.fetchone()
                if not res: return False, 0, None, 0
                is_banned, expires, reason, ban_type = res
                
                if is_banned:
                    if expires > 0 and datetime.now().timestamp() > expires:
                        await self.unban_user(user_id)
                        return False, 0, None, 0
                    return True, expires, reason, ban_type
                return False, 0, None, 0

    async def get_game_settings(self, game_name):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("CREATE TABLE IF NOT EXISTS game_settings (game_name TEXT PRIMARY KEY, coefficient REAL)")
            async with db.execute("SELECT coefficient FROM game_settings WHERE game_name = ?", (game_name,)) as cursor:
                res = await cursor.fetchone()
                return res[0] if res else 2.0 

    async def set_game_coefficient(self, game_name, coefficient):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("CREATE TABLE IF NOT EXISTS game_settings (game_name TEXT PRIMARY KEY, coefficient REAL)")
            await db.execute("INSERT OR REPLACE INTO game_settings (game_name, coefficient) VALUES (?, ?)", (game_name, coefficient))
            await db.commit()
            
    async def get_all_game_settings(self):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("CREATE TABLE IF NOT EXISTS game_settings (game_name TEXT PRIMARY KEY, coefficient REAL)")
            async with db.execute("SELECT game_name, coefficient FROM game_settings") as cursor:
                return await cursor.fetchall()

    async def check_payment(self, invoice_id):
        async with aiosqlite.connect(self.db_file) as db:
             await db.execute("CREATE TABLE IF NOT EXISTS payments (invoice_id INTEGER PRIMARY KEY, user_id INTEGER, amount REAL)")
             async with db.execute("SELECT invoice_id FROM payments WHERE invoice_id = ?", (invoice_id,)) as cursor:
                 return bool(await cursor.fetchone())

    async def add_payment(self, invoice_id, user_id, amount):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("INSERT INTO payments (invoice_id, user_id, amount) VALUES (?, ?, ?)", (invoice_id, user_id, amount))
            await db.commit()

    async def add_pending_deposit(self, invoice_id, amount_rub):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("CREATE TABLE IF NOT EXISTS pending_deposits (invoice_id INTEGER PRIMARY KEY, amount_rub REAL)")
            await db.execute("INSERT INTO pending_deposits (invoice_id, amount_rub) VALUES (?, ?)", (invoice_id, amount_rub))
            await db.commit()

    async def get_pending_deposit(self, invoice_id):
        async with aiosqlite.connect(self.db_file) as db:
             await db.execute("CREATE TABLE IF NOT EXISTS pending_deposits (invoice_id INTEGER PRIMARY KEY, amount_rub REAL)")
             async with db.execute("SELECT amount_rub FROM pending_deposits WHERE invoice_id = ?", (invoice_id,)) as cursor:
                 result = await cursor.fetchone()
                 return result[0] if result else None

    async def get_user_stats(self, user_id):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("CREATE TABLE IF NOT EXISTS payments (invoice_id INTEGER PRIMARY KEY, user_id INTEGER, amount REAL)")
            async with db.execute("SELECT SUM(amount) FROM payments WHERE user_id = ?", (user_id,)) as cursor:
                result = await cursor.fetchone()
                total_deposited = result[0] if result[0] else 0.0
    
            try:
                await db.execute("ALTER TABLE users ADD COLUMN total_withdrawn REAL DEFAULT 0.0")
                await db.commit()
            except: pass
            
            async with db.execute("SELECT total_withdrawn FROM users WHERE user_id = ?", (user_id,)) as cursor:
                 result = await cursor.fetchone()
                 total_withdrawn = result[0] if result else 0.0
                 
            return total_deposited, total_withdrawn

    async def get_referral_stats(self, user_id):
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ? AND referral_confirmed = 1", (user_id,)) as cursor:
                 count = (await cursor.fetchone())[0]
            
            async with db.execute("SELECT referral_earnings FROM users WHERE user_id = ?", (user_id,)) as cursor:
                 res = await cursor.fetchone()
                 earnings = res[0] if res else 0.0
                 
            return count, earnings

    async def get_referrer(self, user_id):
         async with aiosqlite.connect(self.db_file) as db:
              async with db.execute("SELECT referrer_id FROM users WHERE user_id = ?", (user_id,)) as cursor:
                   res = await cursor.fetchone()
                   if res and res[0] != 0:
                       return res[0]
                   return None

    async def update_user_topic(self, user_id, topic_id):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("UPDATE users SET topic_id = ? WHERE user_id = ?", (topic_id, user_id))
            await db.commit()
    
    async def confirm_referral(self, user_id):
        async with aiosqlite.connect(self.db_file) as db:
             async with db.execute("SELECT referrer_id, referral_confirmed FROM users WHERE user_id = ?", (user_id,)) as cursor:
                 row = await cursor.fetchone()
                 if row:
                     referrer_id, confirmed = row
                     if referrer_id != 0 and confirmed == 0:
                         await db.execute("UPDATE users SET referral_confirmed = 1 WHERE user_id = ?", (user_id,))
                         await db.commit()
                         return referrer_id
        return None

    async def update_referral_earnings(self, user_id, amount):
         async with aiosqlite.connect(self.db_file) as db:
            await db.execute("UPDATE users SET referral_earnings = referral_earnings + ? WHERE user_id = ?", (amount, user_id))
            await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
            await db.commit()

    async def create_promo(self, code, amount, activations=1, expires_at=0):
        async with aiosqlite.connect(self.db_file) as db:
            try:
                await db.execute("ALTER TABLE promocodes ADD COLUMN activations INTEGER DEFAULT 1")
                await db.execute("ALTER TABLE promocodes ADD COLUMN expires_at REAL DEFAULT 0")
                await db.commit()
            except:
                pass
            
            await db.execute("CREATE TABLE IF NOT EXISTS promocodes (code TEXT PRIMARY KEY, amount REAL, activations INTEGER, expires_at REAL)")
            await db.execute("INSERT INTO promocodes (code, amount, activations, expires_at) VALUES (?, ?, ?, ?)", (code, amount, activations, expires_at))
            await db.commit()

    async def get_promo(self, code):
        async with aiosqlite.connect(self.db_file) as db:
            try:
                await db.execute("ALTER TABLE promocodes ADD COLUMN activations INTEGER DEFAULT 1")
                await db.execute("ALTER TABLE promocodes ADD COLUMN expires_at REAL DEFAULT 0")
                await db.commit()
            except:
                pass
                
            await db.execute("CREATE TABLE IF NOT EXISTS promocodes (code TEXT PRIMARY KEY, amount REAL, activations INTEGER, expires_at REAL)")
            async with db.execute("SELECT amount, activations, expires_at FROM promocodes WHERE code = ?", (code,)) as cursor:
                return await cursor.fetchone()

    async def delete_promo(self, code):
        async with aiosqlite.connect(self.db_file) as db:
             await db.execute("DELETE FROM promocodes WHERE code = ?", (code,))
             await db.commit()

    async def get_all_promos(self):
        async with aiosqlite.connect(self.db_file) as db:
            try:
                await db.execute("ALTER TABLE promocodes ADD COLUMN activations INTEGER DEFAULT 1")
                await db.execute("ALTER TABLE promocodes ADD COLUMN expires_at REAL DEFAULT 0")
                await db.commit()
            except:
                pass
                
            await db.execute("CREATE TABLE IF NOT EXISTS promocodes (code TEXT PRIMARY KEY, amount REAL, activations INTEGER, expires_at REAL)")
            async with db.execute("SELECT code, amount, activations, expires_at FROM promocodes") as cursor:
                return await cursor.fetchall()
    
    async def is_promo_used_by_user(self, user_id, code):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("CREATE TABLE IF NOT EXISTS promo_uses (user_id INTEGER, code TEXT, PRIMARY KEY (user_id, code))")
            async with db.execute("SELECT 1 FROM promo_uses WHERE user_id = ? AND code = ?", (user_id, code)) as cursor:
                return bool(await cursor.fetchone())

    async def activate_promo(self, user_id, code):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("CREATE TABLE IF NOT EXISTS promo_uses (user_id INTEGER, code TEXT, PRIMARY KEY (user_id, code))")
            await db.execute("INSERT INTO promo_uses (user_id, code) VALUES (?, ?)", (user_id, code))
            
            async with db.execute("SELECT activations FROM promocodes WHERE code = ?", (code,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    activations = row[0]
                    if activations > 0:
                        new_activations = activations - 1
                        if new_activations == 0:
                            await db.execute("DELETE FROM promocodes WHERE code = ?", (code,))
                        else:
                            await db.execute("UPDATE promocodes SET activations = ? WHERE code = ?", (new_activations, code))
            await db.commit()

    async def get_user_by_topic(self, topic_id):
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute("SELECT user_id FROM users WHERE topic_id = ?", (topic_id,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else None

    async def get_users(self):
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute("SELECT user_id FROM users") as cursor:
                return await cursor.fetchall()
                
    async def get_user_game_stats(self, user_id, game_name):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("CREATE TABLE IF NOT EXISTS game_stats (user_id INTEGER, game_name TEXT, wins INTEGER DEFAULT 0, losses INTEGER DEFAULT 0, draws INTEGER DEFAULT 0, total_profit REAL DEFAULT 0.0, PRIMARY KEY (user_id, game_name))")
            async with db.execute("SELECT wins, losses, draws, total_profit FROM game_stats WHERE user_id = ? AND game_name = ?", (user_id, game_name)) as cursor:
                res = await cursor.fetchone()
                return res if res else (0, 0, 0, 0.0)

    async def update_user_game_stat(self, user_id, game_name, result, profit):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("CREATE TABLE IF NOT EXISTS game_stats (user_id INTEGER, game_name TEXT, wins INTEGER DEFAULT 0, losses INTEGER DEFAULT 0, draws INTEGER DEFAULT 0, total_profit REAL DEFAULT 0.0, PRIMARY KEY (user_id, game_name))")
            
            await db.execute("INSERT OR IGNORE INTO game_stats (user_id, game_name) VALUES (?, ?)", (user_id, game_name))
            
            if result == 'win':
                await db.execute("UPDATE game_stats SET wins = wins + 1, total_profit = total_profit + ? WHERE user_id = ? AND game_name = ?", (profit, user_id, game_name))
            elif result == 'loss':
                await db.execute("UPDATE game_stats SET losses = losses + 1, total_profit = total_profit + ? WHERE user_id = ? AND game_name = ?", (profit, user_id, game_name))
            elif result == 'draw':
                await db.execute("UPDATE game_stats SET draws = draws + 1 WHERE user_id = ? AND game_name = ?", (user_id, game_name))
            
            await db.commit()

    async def create_pvp_game(self, game_type, creator_id, creator_name, bet):
        async with aiosqlite.connect(self.db_file) as db:
            try:
                await db.execute("ALTER TABLE pvp_games ADD COLUMN creator_value INTEGER DEFAULT 0")
            except: pass
            try:
                await db.execute("ALTER TABLE pvp_games ADD COLUMN joiner_id INTEGER DEFAULT 0")
            except: pass
            try:
                await db.execute("ALTER TABLE pvp_games ADD COLUMN joiner_name TEXT")
            except: pass
            try:
                await db.execute("ALTER TABLE pvp_games ADD COLUMN joiner_value INTEGER DEFAULT 0")
            except: pass
            
            await db.execute("CREATE TABLE IF NOT EXISTS pvp_games (id INTEGER PRIMARY KEY AUTOINCREMENT, game_type TEXT, creator_id INTEGER, creator_name TEXT, bet REAL, created_at REAL, creator_value INTEGER DEFAULT 0, joiner_id INTEGER DEFAULT 0, joiner_name TEXT, joiner_value INTEGER DEFAULT 0, joined_at REAL DEFAULT 0)")
            async with db.execute("INSERT INTO pvp_games (game_type, creator_id, creator_name, bet, created_at, creator_value, joiner_id, joiner_value, joined_at) VALUES (?, ?, ?, ?, ?, 0, 0, 0, 0)", (game_type, creator_id, creator_name, bet, datetime.now().timestamp())) as cursor:
                game_id = cursor.lastrowid
                await db.commit()
                return game_id

    async def get_pvp_games(self):
        async with aiosqlite.connect(self.db_file) as db:
            try:
                await db.execute("ALTER TABLE pvp_games ADD COLUMN creator_value INTEGER DEFAULT 0")
            except: pass
            try:
                await db.execute("ALTER TABLE pvp_games ADD COLUMN joiner_id INTEGER DEFAULT 0")
            except: pass
            try:
                await db.execute("ALTER TABLE pvp_games ADD COLUMN joiner_name TEXT")
            except: pass
            try:
                await db.execute("ALTER TABLE pvp_games ADD COLUMN joiner_value INTEGER DEFAULT 0")
            except: pass
            
            await db.execute("CREATE TABLE IF NOT EXISTS pvp_games (id INTEGER PRIMARY KEY, game_type TEXT, creator_id INTEGER, creator_name TEXT, bet REAL, created_at REAL, creator_value INTEGER DEFAULT 0, joiner_id INTEGER DEFAULT 0, joiner_name TEXT, joiner_value INTEGER DEFAULT 0)")
            async with db.execute("SELECT id, game_type, creator_id, creator_name, bet, creator_value FROM pvp_games WHERE joiner_id = 0 ORDER BY id DESC") as cursor:
                return await cursor.fetchall()

    async def get_pvp_game(self, game_id):
        async with aiosqlite.connect(self.db_file) as db:
            try:
                await db.execute("ALTER TABLE pvp_games ADD COLUMN creator_value INTEGER DEFAULT 0")
            except: pass
            try:
                await db.execute("ALTER TABLE pvp_games ADD COLUMN joiner_id INTEGER DEFAULT 0")
            except: pass
            try:
                await db.execute("ALTER TABLE pvp_games ADD COLUMN joiner_name TEXT")
            except: pass
            try:
                await db.execute("ALTER TABLE pvp_games ADD COLUMN joiner_value INTEGER DEFAULT 0")
            except: pass

            try:
                await db.execute("ALTER TABLE pvp_games ADD COLUMN joined_at REAL DEFAULT 0")
            except: pass

            async with db.execute("SELECT id, game_type, creator_id, creator_name, bet, creator_value, joiner_id, joiner_name, joiner_value, joined_at FROM pvp_games WHERE id = ?", (game_id,)) as cursor:
                return await cursor.fetchone()

    async def delete_pvp_game(self, game_id):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("DELETE FROM pvp_games WHERE id = ?", (game_id,))
            await db.commit()

    async def join_pvp_game(self, game_id, joiner_id, joiner_name):
        async with aiosqlite.connect(self.db_file) as db:
            try:
                await db.execute("ALTER TABLE pvp_games ADD COLUMN joined_at REAL DEFAULT 0")
            except: pass
            
            await db.execute("UPDATE pvp_games SET joiner_id = ?, joiner_name = ?, joined_at = ? WHERE id = ?", (joiner_id, joiner_name, datetime.now().timestamp(), game_id))
            await db.commit()

    async def get_active_game_by_user(self, user_id):
        async with aiosqlite.connect(self.db_file) as db:
            try: await db.execute("ALTER TABLE pvp_games ADD COLUMN joined_at REAL DEFAULT 0")
            except: pass
            
            async with db.execute("SELECT * FROM pvp_games WHERE creator_id = ? AND creator_value = 0", (user_id,)) as cursor:
                 game = await cursor.fetchone()
                 if game: return game
            async with db.execute("SELECT * FROM pvp_games WHERE joiner_id = ? AND joiner_value = 0", (user_id,)) as cursor:
                 game = await cursor.fetchone()
                 if game: return game
            return None

    async def update_pvp_game_move(self, game_id, user_id, value):
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute("SELECT creator_id, joiner_id FROM pvp_games WHERE id = ?", (game_id,)) as cursor:
                row = await cursor.fetchone()
                if not row: return False
                creator_id, joiner_id = row
            
            if user_id == creator_id:
                await db.execute("UPDATE pvp_games SET creator_value = ? WHERE id = ?", (value, game_id))
            elif user_id == joiner_id:
                await db.execute("UPDATE pvp_games SET joiner_value = ? WHERE id = ?", (value, game_id))
            else:
                return False
                
            await db.commit()
            return True

    async def get_old_pending_games(self, limit_seconds):
        async with aiosqlite.connect(self.db_file) as db:
            try: await db.execute("ALTER TABLE pvp_games ADD COLUMN joined_at REAL DEFAULT 0")
            except: pass
            
            threshold = datetime.now().timestamp() - limit_seconds
            async with db.execute("SELECT id, creator_id, bet FROM pvp_games WHERE joiner_id = 0 AND created_at < ?", (threshold,)) as cursor:
                return await cursor.fetchall()

    async def get_stalled_active_games(self, limit_seconds):
        async with aiosqlite.connect(self.db_file) as db:
            try: await db.execute("ALTER TABLE pvp_games ADD COLUMN joined_at REAL DEFAULT 0")
            except: pass
            
            threshold = datetime.now().timestamp() - limit_seconds
            async with db.execute("SELECT id, game_type, creator_id, creator_name, bet, creator_value, joiner_id, joiner_name, joiner_value, joined_at FROM pvp_games WHERE joiner_id != 0 AND joined_at < ? AND (creator_value = 0 OR joiner_value = 0) AND joined_at != 0", (threshold,)) as cursor:
                return await cursor.fetchall()

    async def get_all_active_pvp_games(self):
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute("SELECT id, creator_name, bet, joiner_name FROM pvp_games ORDER BY id DESC LIMIT 20") as cursor:
                return await cursor.fetchall()

    async def create_chat_game(self, chat_id, message_id, creator_id, creator_name, game_type, mode, param, bet, players_json):
        async with aiosqlite.connect(self.db_file) as db:
            cursor = await db.execute("INSERT INTO chat_games (chat_id, message_id, creator_id, creator_name, game_type, mode, param, bet, players, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (chat_id, message_id, creator_id, creator_name, game_type, mode, param, bet, players_json, datetime.now().timestamp()))
            await db.commit()
            return cursor.lastrowid

    async def get_chat_game(self, game_id):
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute("SELECT * FROM chat_games WHERE id = ?", (game_id,)) as cursor:
                return await cursor.fetchone()

    async def delete_chat_game(self, game_id):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("DELETE FROM chat_games WHERE id = ?", (game_id,))
            await db.commit()
            
    async def get_active_chat_games(self, chat_id):
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute("SELECT * FROM chat_games WHERE chat_id = ? AND status != 'finished'", (chat_id,)) as cursor:
                return await cursor.fetchall()

    async def update_chat_game(self, game_id, players_json, status=None, message_id=None):
        async with aiosqlite.connect(self.db_file) as db:
            sql = "UPDATE chat_games SET players = ?"
            params = [players_json]
            
            if status:
                sql += ", status = ?"
                params.append(status)
            if message_id:
                sql += ", message_id = ?"
                params.append(message_id)
                
            sql += " WHERE id = ?"
            params.append(game_id)
            
            await db.execute(sql, tuple(params))
            await db.commit()

    async def get_old_chat_games(self, limit_seconds):
        async with aiosqlite.connect(self.db_file) as db:
            threshold = datetime.now().timestamp() - limit_seconds
            async with db.execute("SELECT id, chat_id, message_id, creator_id, bet FROM chat_games WHERE status = 'pending' AND created_at < ?", (threshold,)) as cursor:
                return await cursor.fetchall()

    async def get_active_chat_game_by_user(self, user_id):
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute("SELECT * FROM chat_games WHERE creator_id = ? AND status != 'finished'", (user_id,)) as cursor:
                return await cursor.fetchone()

    async def add_moderator(self, user_id):
        async with aiosqlite.connect(self.db_file) as db:
            try:
                await db.execute("INSERT INTO moderators (user_id) VALUES (?)", (user_id,))
                await db.commit()
                return True
            except:
                return False

    async def remove_moderator(self, user_id):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("DELETE FROM moderators WHERE user_id = ?", (user_id,))
            await db.commit()

    async def is_moderator(self, user_id):
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute("SELECT user_id FROM moderators WHERE user_id = ?", (user_id,)) as cursor:
                return await cursor.fetchone() is not None

    async def get_all_moderators(self):
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute("SELECT user_id FROM moderators") as cursor:
                return await cursor.fetchall()
