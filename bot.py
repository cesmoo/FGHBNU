import asyncio
import os
import html
import random
import aiohttp
import time
import re
import string
import json
import hashlib
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types, F, BaseMiddleware
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    FSInputFile, ReplyKeyboardMarkup, KeyboardButton, 
    ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
)

import database as db 
import ai_engines
from ai_engines import AI_MODES, AI_MODE_EMOJIS

# ==========================================================
# ⚙️ Configuration
# ==========================================================
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
CHANNEL_ID = os.getenv("CHANNEL_ID", "")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

active_sessions = {}

# ==========================================================
# 🌐 API Configurations
# ==========================================================
SITE_CONFIGS = {
    "777BIGWIN": {
        "api_url": "https://api.bigwinqaz.com/api/webapi",
        "origin": "https://www.777bigwingame.app"
    },
    "6Lottery": {
        "api_url": "https://6lotteryapi.com/api/webapi",
        "origin": "https://www.6win566.com"
    },
    "CK LOTTERY": {
        "api_url": "https://ckygjf6r.com/api/webapi",
        "origin": "https://cklottery.cc"
    }
}

def get_signed_payload(payload: dict) -> dict:
    t = {k: v for k, v in payload.items() if k not in ['signature', 'timestamp']}
    if 'language' not in t: t['language'] = 7
    if 'random' not in t: t['random'] = uuid.uuid4().hex
    n = {}
    for key in sorted(t.keys()):
        val = t[key]
        if val is not None and val != "":
            n[key] = val
    json_str = json.dumps(n, separators=(',', ':'))
    signature = hashlib.md5(json_str.encode('utf-8')).hexdigest().upper()
    t['signature'] = signature
    t['timestamp'] = int(time.time())
    return t

def get_headers(site: str, token: str = "") -> dict:
    config = SITE_CONFIGS.get(site, SITE_CONFIGS["777BIGWIN"])
    headers = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json;charset=UTF-8',
        'origin': config["origin"],
        'referer': f'{config["origin"]}/',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
    }
    if token: headers['authorization'] = f'Bearer {token}'
    return headers

def get_select_type(bet_type: str) -> int:
    b = bet_type.lower()
    if b == "big": return 13
    elif b == "small": return 14
    elif b == "red": return 1
    elif b == "green": return 3
    elif b in ["violet", "purple"]: return 2
    return 13 

# ==========================================================
# 🌟 Premium Emojis & UI
# ==========================================================
TEXT_INFO = "Info"; TEXT_BALANCE = "Balance"; TEXT_STATUS = "Status"
TEXT_START = "Start Auto-Bet"; TEXT_STOP = "Stop Auto-Bet"
TEXT_GAMES = "Games"; TEXT_AI = "AI Mode"
TEXT_BETSIZE = "Set Bet-Size"; TEXT_PROFIT = "Profit Target"
TEXT_HIT = "Hit Betting"; TEXT_PREDICT = "AI Prediction"
TEXT_LOGOUT = "Logout"; TEXT_LOGIN = "Login"; TEXT_BACK = "Back"
TEXT_VIRTUAL_MODE = "Virtual Mode"; TEXT_REAL_MODE = "Real Mode"
TEXT_UPLOAD_CHANNEL = "Upload Channel"

E_INFO = KeyboardButton(text=TEXT_INFO, icon_custom_emoji_id="5868656545634689320", style="primary")
E_BALANCE = KeyboardButton(text=TEXT_BALANCE, icon_custom_emoji_id="5868108575387671725", style="primary")
E_STATUS = KeyboardButton(text=TEXT_STATUS, icon_custom_emoji_id="5877443460725739250", style="primary")
E_START = KeyboardButton(text=TEXT_START, icon_custom_emoji_id="5884248697980608904", style="success")
E_STOP = KeyboardButton(text=TEXT_STOP, icon_custom_emoji_id="5884289942371401145", style="danger")
E_GAMES = KeyboardButton(text=TEXT_GAMES, icon_custom_emoji_id="5868665489092263539", style="primary")
E_AI = KeyboardButton(text=TEXT_AI, icon_custom_emoji_id="5877652234091891383", style="primary")
E_BETSIZE = KeyboardButton(text=TEXT_BETSIZE, icon_custom_emoji_id="5877260593903177342", style="primary")
E_PROFIT = KeyboardButton(text=TEXT_PROFIT, icon_custom_emoji_id="5967574255670399788", style="primary")
E_HIT = KeyboardButton(text=TEXT_HIT, icon_custom_emoji_id="5869547610204280761", style="primary")
E_PREDICT = KeyboardButton(text=TEXT_PREDICT, icon_custom_emoji_id="5890997763331591703", style="primary")
E_LOGOUT = KeyboardButton(text=TEXT_LOGOUT, icon_custom_emoji_id="5875180111744995604", style="danger")
E_LOGIN = KeyboardButton(text=TEXT_LOGIN, icon_custom_emoji_id="5884041323843955199", style="primary")
E_BACK = KeyboardButton(text=TEXT_BACK, icon_custom_emoji_id="5848119413041431362", style="primary")
E_VIRTUAL = KeyboardButton(text=TEXT_VIRTUAL_MODE, icon_custom_emoji_id="5807868868886009920", style="primary")
E_REAL = KeyboardButton(text=TEXT_REAL_MODE, icon_custom_emoji_id="5868656545634689320", style="primary")
E_UPLOAD = KeyboardButton(text=TEXT_UPLOAD_CHANNEL, icon_custom_emoji_id="5890997763331591703", style="primary")

P_1 = '<tg-emoji emoji-id="5890997763331591703">⚙️</tg-emoji>'
P_2 = '<tg-emoji emoji-id="5875180111744995604">⚙️</tg-emoji>'
P_3 = '<tg-emoji emoji-id="5877443460725739250">⚙️</tg-emoji>'
P_4 = '<tg-emoji emoji-id="5967574255670399788">⚙️</tg-emoji>'
P_5 = '<tg-emoji emoji-id="5807868868886009920">⚙️</tg-emoji>'
P_6 = '<tg-emoji emoji-id="5807461353799030682">⚙️</tg-emoji>'
E_SETTING = '<tg-emoji emoji-id="5877260593903177342">⚙️</tg-emoji>'
E_CROWN   = '<tg-emoji emoji-id="5807868868886009920">👑</tg-emoji>'
E_LOSS    = '<tg-emoji emoji-id="5807461353799030682">💸</tg-emoji>'
E_GRID    = '<tg-emoji emoji-id="5884290437459480896">🔠</tg-emoji>'
E_EDIT    = '<tg-emoji emoji-id="5985774024968379294">📝</tg-emoji>'
E_DOC     = '<tg-emoji emoji-id="5956561916573782596">📄</tg-emoji>'
E_FLOWER  = '<tg-emoji emoji-id="5967574255670399788">🌸</tg-emoji>'

# ==========================================================
# 🛠️ Helpers & Middleware
# ==========================================================
def extract_balance(bal_str: str) -> float:
    try: return float(re.sub(r'[^\d.]', '', str(bal_str))) if re.sub(r'[^\d.]', '', str(bal_str)) else 0.0
    except: return 0.0

async def delete_message_later(msg: types.Message, delay: int = 5):
    await asyncio.sleep(delay)
    try: await msg.delete()
    except: pass

def parse_duration(duration_str: str):
    duration_str = duration_str.upper()
    if duration_str.endswith('H') and duration_str[:-1].isdigit(): return timedelta(hours=int(duration_str[:-1]))
    elif duration_str.endswith('D') and duration_str[:-1].isdigit(): return timedelta(days=int(duration_str[:-1]))
    return None

def get_myanmar_time() -> datetime:
    return datetime.utcnow() + timedelta(hours=6, minutes=30)

class AuthMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user_id = text = None
        if isinstance(event, types.Message): user_id, text = event.from_user.id, event.text or ""
        elif isinstance(event, types.CallbackQuery): user_id = event.from_user.id
        
        if user_id:
            if user_id == OWNER_ID or await db.is_uid_allowed(str(user_id)) or (text and text.startswith("PSP-") and len(text) == 20):
                return await handler(event, data)
            expire_iso = await db.get_user_subscription(user_id)
            if expire_iso and get_myanmar_time() < datetime.fromisoformat(expire_iso):
                return await handler(event, data)
            if isinstance(event, types.Message): await event.answer("ᴄᴏɴᴛᴀᴄᴛ ᴜꜱ @iwillgoforwardsalone")
            elif isinstance(event, types.CallbackQuery): await event.answer("အသုံးပြုခွင့် သက်တမ်းကုန်သွားပါပြီ။", show_alert=True)
            return 
        return await handler(event, data)

dp.message.middleware(AuthMiddleware())
dp.callback_query.middleware(AuthMiddleware())

VALID_AI_NAMES = [m["name"] for m in ai_engines.AI_MODES.values()]

class LoginForm(StatesGroup):
    select_site = State(); enter_phone = State(); enter_password = State(); main_menu = State()
    select_game_type = State(); enter_bet_sequence = State(); enter_profit_target = State()
    enter_custom_pattern = State(); enter_virtual_balance = State() 

# ==========================================================
# ⌨️ Keyboards
# ==========================================================
def get_main_keyboard(): return ReplyKeyboardMarkup(keyboard=[[E_LOGIN]], resize_keyboard=True)
def get_site_keyboard(): return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="777BIGWIN", style="success"), KeyboardButton(text="6Lottery", style="danger")], [KeyboardButton(text="CK LOTTERY", style="primary")], [E_BACK]], resize_keyboard=True)
def get_logged_in_keyboard(): return ReplyKeyboardMarkup(keyboard=[[E_INFO, E_BALANCE, E_STATUS], [E_START, E_STOP], [E_GAMES, E_AI], [E_BETSIZE, E_PROFIT], [E_HIT, E_PREDICT], [E_VIRTUAL, E_REAL], [E_UPLOAD, E_LOGOUT]], resize_keyboard=True)
def get_game_type_keyboard(): return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Win Go 30s", style="success"), KeyboardButton(text="Win Go 1m", style="primary")], [E_BACK]], resize_keyboard=True)
def get_upload_toggle_keyboard(): return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="✅ Upload ON", style="success"), KeyboardButton(text="❌ Upload OFF", style="danger")], [E_BACK]], resize_keyboard=True)
def get_cancel_keyboard(): return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Cancel")]], resize_keyboard=True)

def get_ai_mode_keyboard():
    standard_modes = [m for k, m in AI_MODES.items() if not k.startswith("pro_") and k != "babathapai"]
    keyboard = []
    row = []
    for mode in standard_modes:
        emoji_id = AI_MODE_EMOJIS.get(mode["name"], "5868656545634689320")
        row.append(KeyboardButton(text=mode["name"], icon_custom_emoji_id=emoji_id, style="primary"))
        if len(row) == 2: keyboard.append(row); row = []
    if row: keyboard.append(row)
    keyboard.append([KeyboardButton(text="Pro AI Features", icon_custom_emoji_id="5807868868886009920", style="success")])
    keyboard.append([KeyboardButton(text="BACK", icon_custom_emoji_id="5848119413041431362", style="primary")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_pro_ai_mode_keyboard():
    pro_modes = [m for k, m in AI_MODES.items() if k.startswith("pro_") or k == "babathapai"]
    keyboard = []
    row = []
    for mode in pro_modes:
        row.append(KeyboardButton(text=mode["name"], icon_custom_emoji_id="5807868868886009920", style="primary"))
        if len(row) == 2: keyboard.append(row); row = []
    if row: keyboard.append(row)
    keyboard.append([KeyboardButton(text="BACK", icon_custom_emoji_id="5848119413041431362", style="danger")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_hit_betting_inline_keyboard(current_wait: int = 0):
    keyboard = []
    number_buttons = []
    for i in range(1, 10):
        btn_style = "success" if current_wait == i else "primary"
        number_buttons.append(InlineKeyboardButton(text=str(i), callback_data=f"hitbet_{i}", style=btn_style))
    for i in range(0, 9, 3): keyboard.append(number_buttons[i:i+3])
    disable_text = "0 (Disabled)" if current_wait == 0 else "0 (Disable)"
    keyboard.append([InlineKeyboardButton(text=disable_text, callback_data="hitbet_0", style="danger")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_ai_prediction_toggle_keyboard(is_enabled: bool):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🟢 Enabled" if is_enabled else "🔴 Disabled", callback_data="toggle_aipred", style="success" if is_enabled else "danger")]])

# ==========================================================
# 👑 Owner Commands
# ==========================================================
@dp.message(F.text.startswith(".key "))
async def cmd_generate_key(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    parts = message.text.split(" ")
    if len(parts) < 2: return await message.answer("⚠️ Format: <code>.key 2H</code>")
    duration = parts[1].strip().upper()
    if not parse_duration(duration): return await message.answer("⚠️ Format: <code>2H</code>")
    key_str = f"PSP-{get_myanmar_time().strftime('%Y%m%d')}{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
    await db.create_key(key_str, duration)
    await message.answer(f"✅ Key: <code>{key_str}</code>\n⏱️ Duration: <b>{duration}</b>")

@dp.message(F.text.startswith(".gen "))
async def cmd_gen_keys(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    parts = message.text.split(" ")
    try: count, duration = int(parts[1]), parts[2].strip().upper()
    except: return await message.answer("⚠️ Format: <code>.gen 5 2H</code>")
    keys = []
    for _ in range(count):
        k = f"PSP-{get_myanmar_time().strftime('%Y%m%d')}{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
        await db.create_key(k, duration)
        keys.append(f"<code>{k}</code>")
    await message.answer(f"✅ Keys {count} created.\n\n" + "\n".join(keys))

@dp.message(F.text.startswith(".add "))
async def cmd_add_uid(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    await db.add_allowed_uid(message.text.split(" ")[1].strip())
    await message.answer(f"✅ UID added.")

@dp.message(F.text.startswith(".del "))
async def cmd_del_uid(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    await db.remove_allowed_uid(message.text.split(" ")[1].strip())
    await message.answer(f"🗑️ UID removed.")

@dp.message(lambda msg: msg.text and msg.text.startswith("PSP-") and len(msg.text) == 20)
async def process_key_redemption(message: types.Message):
    key_str = message.text.strip()
    key_data = await db.get_key(key_str)
    if key_data:
        td = parse_duration(key_data["duration"]) or timedelta(days=1)
        current_expire = get_myanmar_time()
        existing_expire_iso = await db.get_user_subscription(message.from_user.id)
        if existing_expire_iso and datetime.fromisoformat(existing_expire_iso) > current_expire:
            current_expire = datetime.fromisoformat(existing_expire_iso)
        new_expire = current_expire + td
        await db.update_user_subscription(message.from_user.id, new_expire.isoformat())
        await db.delete_key(key_str)
        await message.answer(f"ʟɪᴄᴇɴsေ ᴋေʏ ᴀᴄᴛɪᴠေ\nေxᴘɪʀေ ᴛɪᴍေ <b>{new_expire.strftime('%Y-%m-%d %I:%M %p')}</b> (MMT)")
    else: await message.answer("ɪɴᴄᴏʀʀေᴄᴛ ᴋေʏ")

# ==========================================================
# 🤖 Authentication & API
# ==========================================================
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear(); await message.answer("An ဝင်ရန် Login ကိုနှိပ်ပါ", reply_markup=get_main_keyboard())

@dp.message(F.text == TEXT_LOGIN)
async def login_start(message: types.Message, state: FSMContext):
    await state.set_state(LoginForm.select_site); await message.answer("Site ရွေးပါ", reply_markup=get_site_keyboard())

@dp.message(LoginForm.select_site)
async def process_site(message: types.Message, state: FSMContext):
    if message.text == "Back": await state.clear(); return await message.answer("Cancelled", reply_markup=get_main_keyboard())
    await state.update_data(site=message.text); await state.set_state(LoginForm.enter_phone); await message.answer("Phone", reply_markup=ReplyKeyboardRemove())

@dp.message(LoginForm.enter_phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text); await state.set_state(LoginForm.enter_password); await message.answer("Password")

async def api_get_user_info(site: str, token: str):
    config = SITE_CONFIGS.get(site)
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{config['api_url']}/GetUserInfo", headers=get_headers(site, token), json=get_signed_payload({'language': 7})) as resp:
            return await resp.json()

@dp.message(LoginForm.enter_password)
async def process_password(message: types.Message, state: FSMContext):
    data = await state.get_data()
    username, site_name, user_tg_id = data.get('phone'), data.get('site', '777BIGWIN'), message.from_user.id
    loading_msg = await message.answer("🔄 Login...")

    try:
        config = SITE_CONFIGS.get(site_name)
        payload = {'username': username, 'pwd': message.text, 'phonetype': 1, 'logintype': 'mobile', 'deviceId': uuid.uuid4().hex, 'language': 7}
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{config['api_url']}/Login", headers=get_headers(site_name), json=get_signed_payload(payload)) as resp:
                api_result = await resp.json()
                
        if api_result.get("code") == 0 or api_result.get("msg") == "success":
            token = api_result.get("data", {}).get("token", "") if isinstance(api_result.get("data"), dict) else str(api_result.get("data"))
            user_info = await api_get_user_info(site_name, token)
            
            info_data = user_info.get("data", {}) if user_info.get("code") == 0 else {}
            user_id = str(info_data.get("userId", info_data.get("id", "N/A")))
            nickname = info_data.get("nickName", "Unknown")
            balance_text = f"{info_data.get('balance', info_data.get('amount', 0.0))} Ks"
            
            db_user = await db.get_user(user_tg_id)
            ai_mode = db_user.get("ai_mode", "🎯 Pattern AI") if db_user else "🎯 Pattern AI"
            if ai_mode not in VALID_AI_NAMES: ai_mode = "🎯 Pattern AI"

            await db.save_user_login(user_tg_id, username, user_id, nickname, balance_text, get_myanmar_time().strftime("%Y-%m-%d %H:%M:%S"), ai_mode)
            active_sessions[user_tg_id] = {
                "site": site_name, "token": token, "game_type_id": 30, "game_type_name": "WINGO_30S",
                "is_auto_betting": False, "ai_mode": ai_mode, "bet_sequence": [10], "current_bet_step": 0,          
                "profit_target": 0, "start_balance": extract_balance(balance_text), "session_profit": 0.0, 
                "hit_wait": 0, "current_misses": 0, "is_ai_prediction_enabled": False, "last_predicted_issue": None,
                "is_virtual_mode": False, "virtual_balance": 0.0, "virtual_session_profit": 0.0,
                "upload_channel": False, "model_accuracies": {}, "last_prediction_value": None
            }
            await loading_msg.delete()
            await message.answer(f"🏆 <b>LOGIN SUCCESSFUL!</b>\n{nickname} | {balance_text}", reply_markup=get_logged_in_keyboard())
            await state.set_state(LoginForm.main_menu)
        else:
            await loading_msg.delete(); await message.answer(f"❌ Login Failed: {api_result.get('msg')}", reply_markup=get_main_keyboard()); await state.clear()
    except Exception as e:
        await loading_msg.delete(); await message.answer(f"⚠️ Error: {e}", reply_markup=get_main_keyboard()); await state.clear()

# ==========================================================
# 📊 API & Database Deep Scanning Logic
# ==========================================================
async def get_latest_game_result(target_issue, user_tg_id):
    session_data = active_sessions.get(user_tg_id, {})
    site, token, type_id = session_data.get("site"), session_data.get("token"), session_data.get("game_type_id", 30)
    config = SITE_CONFIGS.get(site)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{config['api_url']}/GetNoaverageEmerdList", headers=get_headers(site, token), json=get_signed_payload({'pageSize': 10, 'pageNo': 1, 'typeId': type_id, 'language': 7})) as resp:
                records = (await resp.json()).get('data', {}).get('list', [])
        for item in records:
            if str(item['issueNumber']) == str(target_issue):
                num = int(item['number'])
                size = "BIG" if num >= 5 else "SMALL"
                return f"{num} | {size}"
    except: pass
    return "? | ?"

async def get_ai_prediction(user_tg_id):
    session_data = active_sessions.get(user_tg_id, {})
    site, token, type_id = session_data.get("site"), session_data.get("token"), session_data.get("game_type_id", 30)
    config = SITE_CONFIGS.get(site)

    try:
        # API မှ နောက်ဆုံး ၁၀ ပွဲကို ဆွဲယူခြင်း
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{config['api_url']}/GetNoaverageEmerdList", headers=get_headers(site, token), json=get_signed_payload({'pageSize': 10, 'pageNo': 1, 'typeId': type_id, 'language': 7})) as resp:
                records = (await resp.json()).get('data', {}).get('list', [])
                
        if records:
            last_completed_issue = records[0]['issueNumber']
            next_issue = str(int(last_completed_issue) + 1)
            
            # ၁။ Database ထဲသို့ ရလဒ်အသစ်များ အလိုအလျောက် မှတ်သားခြင်း
            for item in records:
                num = int(item['number'])
                size_text = "BIG" if num >= 5 else "SMALL"
                await db.save_game_record(site, type_id, item['issueNumber'], num, size_text)
            
            # ၂။ Database မှ Historical Data (9000 ပွဲစာ) ပြန်လည်ဆွဲထုတ်ခြင်း
            db_records = await db.get_game_history(site, type_id, limit=9000)
            
            history_docs = []
            for item in db_records:
                history_docs.append({"size": item['size'], "number": item['number']})
            
            # Database ပြဿနာရှိ၍ Data မရပါက API မှရထားသော Data သာသုံးမည်
            if not history_docs:
                for item in records:
                    num = int(item['number'])
                    size_text = "BIG" if num >= 5 else "SMALL"
                    history_docs.append({"size": size_text, "number": num})
            
            user_ai_name = session_data.get("ai_mode", "🎯 Pattern AI")
            
            if user_ai_name == "Set Pattern":
                pat, step = session_data.get("custom_pattern", ["BIG"]), session_data.get("custom_pattern_step", 0)
                target_bet = pat[step]
                if step == 0 and ("BIG" if int(records[0]['number']) >= 5 else "SMALL") != ("SMALL" if target_bet == "BIG" else "BIG"):
                    return "wait", 100, next_issue, user_ai_name
                return target_bet.lower(), 100, next_issue, user_ai_name
            else:
                mode_key = "pattern"
                for key, val in ai_engines.AI_MODES.items():
                    if val["name"] == user_ai_name: mode_key = key; break
                
                # Model အစစ်ခေါ်ယူခြင်း (Deep Scan အပါအဝင်)
                predicted_size, _, confidence, _ = ai_engines.get_prediction(history_docs, mode_key, model_accuracies=session_data.get("model_accuracies", {}))
                return predicted_size.lower(), confidence, next_issue, user_ai_name
        else: return None, 0, None, None
    except Exception as e:
        print(f"Prediction Error: {e}")
        return None, 0, None, None

async def place_auto_bet(user_tg_id, current_issue, bet_type, total_amount=10, silent=False):
    try:
        session = active_sessions.get(user_tg_id)
        if not session or "token" not in session: return False
        site, token, type_id = session["site"], session["token"], session.get("game_type_id", 30)
        
        base, count = (10000, total_amount//10000) if total_amount >= 10000 else (1000, total_amount//1000) if total_amount >= 1000 else (100, total_amount//100) if total_amount >= 100 else (10, total_amount//10)
        payload = {'typeId': type_id, 'issuenumber': current_issue, 'amount': base, 'betCount': count, 'gameType': 2, 'selectType': get_select_type(bet_type), 'language': 7}
        
        async with aiohttp.ClientSession() as http:
            async with http.post(f"{SITE_CONFIGS[site]['api_url']}/GameBetting", headers=get_headers(site, token), json=get_signed_payload(payload)) as resp:
                res = await resp.json()
        return res.get("code") == 0 or res.get("msg") == "success"
    except: return False

def update_model_accuracies(user_tg_id, actual_result_size):
    if user_tg_id not in active_sessions: return
    session = active_sessions[user_tg_id]
    if "model_accuracies" not in session: session["model_accuracies"] = {}
    active_ai, last_pred = session.get("ai_mode"), session.get("last_prediction_value")
    if last_pred and actual_result_size and last_pred != "wait" and actual_result_size != "?":
        is_win = (last_pred.lower() == actual_result_size.lower())
        session["model_accuracies"][active_ai] = (session["model_accuracies"].get(active_ai, 0.5) * 0.8) + (1.0 if is_win else 0.0) * 0.2

# ==========================================================
# 🔮 AI Loops & Features
# ==========================================================
@dp.message(F.text == TEXT_PREDICT)
async def btn_ai_prediction_toggle(message: types.Message):
    if message.from_user.id not in active_sessions: return await message.answer("Login ဝင်ပေးပါ။")
    await message.answer("AI Prediction Broadcast", reply_markup=get_ai_prediction_toggle_keyboard(active_sessions[message.from_user.id].get("is_ai_prediction_enabled", False)))

@dp.callback_query(F.data == "toggle_aipred")
async def process_toggle_aipred(callback: types.CallbackQuery):
    user_tg_id = callback.from_user.id
    if user_tg_id not in active_sessions: return await callback.answer("Session Expired.")
    new_state = not active_sessions[user_tg_id].get("is_ai_prediction_enabled", False)
    active_sessions[user_tg_id]["is_ai_prediction_enabled"] = new_state
    await callback.message.edit_reply_markup(reply_markup=get_ai_prediction_toggle_keyboard(new_state))
    if new_state: asyncio.create_task(prediction_broadcast_loop(user_tg_id, callback.message))

async def prediction_broadcast_loop(user_tg_id, message: types.Message):
    if "current_win_streak" not in active_sessions.get(user_tg_id, {}): active_sessions[user_tg_id].update({"current_win_streak": 0, "current_lose_streak": 0, "longest_win_streak": 0, "longest_lose_streak": 0})
    while active_sessions.get(user_tg_id, {}).get("is_ai_prediction_enabled", False):
        try:
            pred, conf, issue, ai_name = await get_ai_prediction(user_tg_id)
            if pred == "wait": await asyncio.sleep(2); continue
            last = active_sessions[user_tg_id].get("last_predicted_issue")
            gn = active_sessions[user_tg_id].get("game_type_name", "WINGO_30S")

            if issue and issue != last:
                if gn == "WINGO_1M": await asyncio.sleep(30)
                elif gn == "WINGO_30S": await asyncio.sleep(5)
                active_sessions[user_tg_id]["last_predicted_issue"], active_sessions[user_tg_id]["last_prediction_value"] = issue, pred
                lw, ll = active_sessions[user_tg_id]["longest_win_streak"], active_sessions[user_tg_id]["longest_lose_streak"]
                
                txt = f"<blockquote>\n{P_1} Ai Prediction - Live\n{P_2} {gn} : <code>{issue}</code>\n{P_3} Prediction : <b>{pred.upper()}</b> 〔 {lw} 〕|〔 {ll} 〕\n{P_4} Status : Waiting...\n</blockquote>"
                pred_msg = await message.answer(txt)
                
                ch_msg_id = (await bot.send_message(chat_id=CHANNEL_ID, text=txt)).message_id if active_sessions[user_tg_id].get("upload_channel") and CHANNEL_ID else None
                
                res = "? | ?"
                for _ in range(60 if gn == "WINGO_1M" else 30):
                    if not active_sessions.get(user_tg_id, {}).get("is_ai_prediction_enabled", False): break
                    await asyncio.sleep(1)
                    res = await get_latest_game_result(issue, user_tg_id)
                    if res != "? | ?": break
                
                if res != "? | ?":
                    actual = res.split(" | ")[1].strip().lower()
                    update_model_accuracies(user_tg_id, actual)
                    if pred.lower() == actual:
                        stat = f"{P_5}WIN{res}"; active_sessions[user_tg_id]["current_win_streak"] += 1; active_sessions[user_tg_id]["current_lose_streak"] = 0
                        active_sessions[user_tg_id]["longest_win_streak"] = max(active_sessions[user_tg_id]["longest_win_streak"], active_sessions[user_tg_id]["current_win_streak"])
                    else:
                        stat = f"{P_6} LOSE{res}"; active_sessions[user_tg_id]["current_lose_streak"] += 1; active_sessions[user_tg_id]["current_win_streak"] = 0
                        active_sessions[user_tg_id]["longest_lose_streak"] = max(active_sessions[user_tg_id]["longest_lose_streak"], active_sessions[user_tg_id]["current_lose_streak"])
                else: stat = "⚖️ DRAW"
                
                lw, ll = active_sessions[user_tg_id]["longest_win_streak"], active_sessions[user_tg_id]["longest_lose_streak"]
                try:
                    ftxt = f"<blockquote>\n{P_1} Ai Prediction - Live\n{P_2} {gn} : <code>{issue}</code>\n{P_3} Prediction : <b>{pred.upper()}</b> 〔 {lw} 〕|〔 {ll} 〕\n{P_4} Status : {stat}\n</blockquote>"
                    await pred_msg.edit_text(ftxt)
                    if ch_msg_id: await bot.edit_message_text(chat_id=CHANNEL_ID, message_id=ch_msg_id, text=ftxt)
                except: pass
            await asyncio.sleep(2)
        except: await asyncio.sleep(5)

async def auto_bet_loop(user_tg_id, message: types.Message):
    await message.answer("🚀 Auto-Bet စတင်ပါပြီ! 🛑 Stop Auto-Bet ဖြင့် ရပ်တန့်ပါ။")
    last, session = None, active_sessions[user_tg_id]
    is_virtual, gn = session.get("is_virtual_mode", False), session.get("game_type_name", "WINGO_30S")
    if not is_virtual: bal_url, bal_headers = f"{SITE_CONFIGS[session['site']]['api_url']}/GetBalance", get_headers(session["site"], session["token"])

    while active_sessions.get(user_tg_id, {}).get("is_auto_betting", False):
        try:
            pred, _, issue, ai_name = await get_ai_prediction(user_tg_id)
            if issue and issue != last:
                if gn == "WINGO_1M": await asyncio.sleep(30)
                if pred == "wait":
                    msg = await message.answer(f"<blockquote>\n{E_DOC} Trigger စောင့်နေပါသည်\n{E_DOC} {gn} : <code>{issue}</code>\n</blockquote>")
                    last = issue; asyncio.create_task(delete_message_later(msg, 7)); await asyncio.sleep(2); continue 
                    
                hw, cm = session.get("hit_wait", 0), session.get("current_misses", 0)
                if hw > 0 and cm < hw:
                    msg = await message.answer(f"<blockquote>\n{E_DOC} Hit Wait: {cm}/{hw}\n{E_DOC} {gn} : <code>{issue}</code>\n{E_FLOWER} Pred: {pred.upper()}\n</blockquote>")
                    res = "? | ?"
                    for _ in range(45):
                        if not active_sessions.get(user_tg_id, {}).get("is_auto_betting"): break
                        await asyncio.sleep(2)
                        res = await get_latest_game_result(issue, user_tg_id)
                        if res != "? | ?": break
                    try:
                        actual = res.split(" | ")[1].strip().lower()
                        update_model_accuracies(user_tg_id, actual)
                        if pred.lower() == actual: active_sessions[user_tg_id]["current_misses"] = 0; await msg.edit_text(f"🔄 AI အမှန်ခန့်မှန်း (Reset)\nResult: {res}")
                        elif actual != "?": 
                            active_sessions[user_tg_id]["current_misses"] += 1
                            await msg.edit_text(f"🎯 Target Reached!" if active_sessions[user_tg_id]["current_misses"] >= hw else f"❌ Loss: {active_sessions[user_tg_id]['current_misses']}/{hw}")
                        asyncio.create_task(delete_message_later(msg, 5)) 
                    except: pass
                    last = issue; await asyncio.sleep(2); continue 

                seq, step = session.get("bet_sequence", [10]), session.get("current_bet_step", 0)
                if step >= len(seq): step = 0
                amt = seq[step]

                if is_virtual: c_bal = session.get("virtual_balance", 0.0)
                else:
                    async with aiohttp.ClientSession() as http:
                        async with http.post(bal_url, headers=bal_headers, json=get_signed_payload({'language': 7})) as resp:
                            d = (await resp.json()).get("data", {})
                            c_bal = float(d.get("balance", d.get("amount", 0.0)) if isinstance(d, dict) else d)
                
                if c_bal < amt: await message.answer("⚠️ လက်ကျန်ငွေမလုံလောက်ပါ။ Stop."); active_sessions[user_tg_id]["is_auto_betting"] = False; break

                active_sessions[user_tg_id]["last_prediction_value"] = pred
                await message.answer(f"<blockquote>\n{E_DOC} {gn} : <code>{issue}</code>\n{E_DOC} {ai_name}\n{E_FLOWER} Pred: <b>{pred.upper()}</b> | {amt} Ks\n</blockquote>")
                last = issue; await asyncio.sleep(7) 

                if is_virtual: res = await get_latest_game_result(issue, user_tg_id) if (await get_latest_game_result(issue, user_tg_id)) != "? | ?" else f"{random.randint(0,9)} | {'BIG' if random.randint(0,9)>=5 else 'SMALL'}"
                else: 
                    if not await place_auto_bet(user_tg_id, issue, pred, amt, True): await asyncio.sleep(5); continue
                    res = "? | ?"
                    for _ in range(45):
                        if not active_sessions.get(user_tg_id, {}).get("is_auto_betting"): break 
                        await asyncio.sleep(2)
                        res = await get_latest_game_result(issue, user_tg_id)
                        if res != "? | ?": break 
                
                if is_virtual:
                    try:
                        if pred.lower() == res.split(" | ")[1].strip().lower(): session["virtual_balance"] += amt * 0.96
                        else: session["virtual_balance"] -= amt
                        n_bal = session["virtual_balance"]; await db.update_virtual_balance(user_tg_id, n_bal)
                    except: pass
                else:
                    async with aiohttp.ClientSession() as http:
                        async with http.post(bal_url, headers=bal_headers, json=get_signed_payload({'language': 7})) as resp:
                            d = (await resp.json()).get("data", {})
                            n_bal = float(d.get("balance", d.get("amount", 0.0)) if isinstance(d, dict) else d)

                try:
                    actual = res.split(" | ")[1].strip().lower() 
                    update_model_accuracies(user_tg_id, actual)
                    if pred.lower() == actual:
                        prof = amt * 0.96; stat = f"{E_SETTING} <b>WIN</b> {E_CROWN} +{prof} Ks"
                        if is_virtual: session["virtual_session_profit"] += prof
                        else: active_sessions[user_tg_id]["session_profit"] += prof
                        active_sessions[user_tg_id]["current_bet_step"] = active_sessions[user_tg_id]["current_misses"] = 0 
                    elif actual == "?": stat = f"⚙️ DRAW (Pending)"
                    else:
                        stat = f"{E_SETTING} <b>LOSE</b> {E_LOSS} {amt} Ks"
                        if is_virtual: session["virtual_session_profit"] -= amt
                        else: active_sessions[user_tg_id]["session_profit"] -= amt
                        active_sessions[user_tg_id]["current_bet_step"] = (step + 1) % len(seq)
                        
                    if ai_name == "Set Pattern" and actual != "?": active_sessions[user_tg_id]["custom_pattern_step"] = (session.get("custom_pattern_step", 0) + 1) % len(session.get("custom_pattern", ["BIG"]))
                    c_prof = session.get("virtual_session_profit", 0.0) if is_virtual else active_sessions[user_tg_id].get("session_profit", 0.0)
                    
                    await message.answer(f"<blockquote>\n{stat}\n───────────────\n{E_GRID} {gn} : <code>{issue}</code>\n{E_GRID} Result: <code>{res}</code>\n{E_EDIT} Bal: K{n_bal:,.2f}\n{E_EDIT} Total Profit: {c_prof:,.2f} Ks\n</blockquote>")
                    if not is_virtual: await db.update_user_balance(user_tg_id, f"{n_bal:.2f} Ks")
                    if session.get("profit_target", 0) > 0 and c_prof >= session["profit_target"]: await message.answer("🎉 Target ပြည့်ပါပြီ။ Stop."); active_sessions[user_tg_id]["is_auto_betting"] = False; break
                except: pass
            else: await asyncio.sleep(5) 
        except Exception as e: print(f"Loop Error: {e}"); await asyncio.sleep(5)

# ==========================================================
# 🎯 Feature Handlers
# ==========================================================
@dp.message(F.text == TEXT_UPLOAD_CHANNEL)
async def cmd_upload_channel_menu(msg: types.Message):
    if msg.from_user.id not in active_sessions: return
    await msg.answer(f"📡 <b>Upload Channel</b>\nလက်ရှိ: {'ON 🟢' if active_sessions[msg.from_user.id].get('upload_channel') else 'OFF 🔴'}", reply_markup=get_upload_toggle_keyboard())

@dp.message(F.text.in_(["✅ Upload ON", "❌ Upload OFF"]))
async def cmd_toggle_upload(msg: types.Message):
    if msg.from_user.id not in active_sessions: return
    is_on = msg.text == "✅ Upload ON"
    active_sessions[msg.from_user.id]["upload_channel"] = is_on
    await msg.answer(f"✅ Upload Channel: {'ON' if is_on else 'OFF'}", reply_markup=get_logged_in_keyboard())

@dp.message(F.text == TEXT_HIT)
async def btn_hit_betting(msg: types.Message):
    if msg.from_user.id in active_sessions: await msg.answer("🎯 Hit Betting", reply_markup=get_hit_betting_inline_keyboard(active_sessions[msg.from_user.id].get("hit_wait", 0)))

@dp.callback_query(F.data.startswith("hitbet_"))
async def process_hit_bet(cb: types.CallbackQuery):
    if cb.from_user.id in active_sessions: active_sessions[cb.from_user.id]["hit_wait"], active_sessions[cb.from_user.id]["current_misses"] = int(cb.data.split("_")[1]), 0
    await cb.message.edit_reply_markup(reply_markup=get_hit_betting_inline_keyboard(int(cb.data.split("_")[1])))

@dp.message(F.text == TEXT_PROFIT)
async def btn_set_profit(msg: types.Message, state: FSMContext):
    if msg.from_user.id in active_sessions: await state.set_state(LoginForm.enter_profit_target); await msg.answer(f"🎯 Target: {active_sessions[msg.from_user.id].get('profit_target', 0)}", reply_markup=get_cancel_keyboard())

@dp.message(LoginForm.enter_profit_target)
async def process_profit(msg: types.Message, state: FSMContext):
    if msg.text.lower() == 'cancel': await state.set_state(LoginForm.main_menu); return await msg.answer("❌ Cancelled", reply_markup=get_logged_in_keyboard())
    if msg.text.isdigit(): active_sessions[msg.from_user.id]["profit_target"] = int(msg.text); await state.set_state(LoginForm.main_menu); await msg.answer(f"✅ Profit: {msg.text}", reply_markup=get_logged_in_keyboard())

@dp.message(F.text == TEXT_AI)
async def cmd_ai_mode(msg: types.Message):
    if msg.from_user.id in active_sessions: await msg.answer(f"🤖 Mode: {active_sessions[msg.from_user.id].get('ai_mode')}", reply_markup=get_ai_mode_keyboard())

@dp.message(F.text.in_(VALID_AI_NAMES))
async def set_ai_mode(msg: types.Message, state: FSMContext):
    if msg.text == "Set Pattern": await state.set_state(LoginForm.enter_custom_pattern); return await msg.answer("🛠️ ဥပမာ: BSBS", reply_markup=get_cancel_keyboard())
    active_sessions[msg.from_user.id]["ai_mode"] = msg.text
    await db.update_user_ai_mode(msg.from_user.id, msg.text)
    await msg.answer(f"✅ AI: {msg.text}", reply_markup=get_logged_in_keyboard())

@dp.message(LoginForm.enter_custom_pattern)
async def process_custom_pattern(msg: types.Message, state: FSMContext):
    if msg.text.lower() == 'cancel': await state.set_state(LoginForm.main_menu); return await msg.answer("❌ Cancelled", reply_markup=get_logged_in_keyboard())
    rp = msg.text.upper().replace(" ", "")
    if not all(c in ['B', 'S'] for c in rp) or not rp: return await msg.answer("❌ B/S သာရိုက်ပါ။")
    if msg.from_user.id in active_sessions: active_sessions[msg.from_user.id].update({"custom_pattern": ["BIG" if c=='B' else "SMALL" for c in rp], "custom_pattern_step": 0, "ai_mode": "Set Pattern"})
    await db.update_user_ai_mode(msg.from_user.id, "Set Pattern"); await state.set_state(LoginForm.main_menu)
    await msg.answer(f"✅ Pattern: {rp}", reply_markup=get_logged_in_keyboard())

@dp.message(F.text == "BACK")
async def back_to_main(msg: types.Message): await msg.answer("Menu", reply_markup=get_logged_in_keyboard())

@dp.message(F.text == TEXT_BETSIZE)
async def btn_set_betsize(msg: types.Message, state: FSMContext):
    if msg.from_user.id in active_sessions: await state.set_state(LoginForm.enter_bet_sequence); await msg.answer(f"⚙️ Seq: {'-'.join(map(str, active_sessions[msg.from_user.id].get('bet_sequence', [10])))}", reply_markup=get_cancel_keyboard())

@dp.message(LoginForm.enter_bet_sequence)
async def process_bet_seq(msg: types.Message, state: FSMContext):
    if msg.text.lower() == 'cancel': await state.set_state(LoginForm.main_menu); return await msg.answer("❌ Cancelled", reply_markup=get_logged_in_keyboard())
    try:
        s = [int(x.strip()) for x in msg.text.split('-')]
        if not s or any(x<=0 for x in s): raise ValueError
        active_sessions[msg.from_user.id].update({"bet_sequence": s, "current_bet_step": 0})
        await state.set_state(LoginForm.main_menu); await msg.answer(f"✅ Seq: {'-'.join(map(str, s))}", reply_markup=get_logged_in_keyboard())
    except: await msg.answer("❌ 10-20-40")

@dp.message(F.text == TEXT_START)
async def btn_start(msg: types.Message):
    if msg.from_user.id in active_sessions and not active_sessions[msg.from_user.id].get("is_auto_betting"):
        if "bet_sequence" not in active_sessions[msg.from_user.id]: active_sessions[msg.from_user.id].update({"bet_sequence": [10], "current_bet_step": 0})
        active_sessions[msg.from_user.id]["is_auto_betting"] = True; asyncio.create_task(auto_bet_loop(msg.from_user.id, msg))

@dp.message(F.text == TEXT_STOP)
async def btn_stop(msg: types.Message):
    if msg.from_user.id in active_sessions: active_sessions[msg.from_user.id]["is_auto_betting"] = False; await msg.answer("🛑 Stopped.")

@dp.message(F.text == TEXT_STATUS)
async def btn_status(msg: types.Message):
    if msg.from_user.id in active_sessions:
        s = active_sessions[msg.from_user.id]; v = s.get("is_virtual_mode")
        txt = f"📊 Status: {'Virtual' if v else 'Real'} | {'Running 🟢' if s.get('is_auto_betting') else 'Stopped 🔴'}\n🤖 AI: {s.get('ai_mode')}\n⚙️ Seq: {'-'.join(map(str, s.get('bet_sequence', [])))} (Step {s.get('current_bet_step',0)+1})\n💰 Bal: {s.get('virtual_balance', 0.0) if v else s.get('start_balance', 0.0):.2f}\n📈 Profit: {s.get('virtual_session_profit', 0.0) if v else s.get('session_profit', 0.0):.2f}"
        await msg.answer(txt)

@dp.message(LoginForm.main_menu, F.text == TEXT_BALANCE)
async def check_balance(msg: types.Message, state: FSMContext):
    if msg.from_user.id not in active_sessions: return
    s = active_sessions[msg.from_user.id]; lm = await msg.answer("🔄 Checking...")
    try:
        if s.get("is_virtual_mode"): bal = f"{s.get('virtual_balance', 0.0):.2f} Ks"
        else:
            async with aiohttp.ClientSession() as http:
                async with http.post(f"{SITE_CONFIGS[s['site']]['api_url']}/GetBalance", headers=get_headers(s["site"], s["token"]), json=get_signed_payload({'language': 7})) as resp:
                    d = (await resp.json()).get("data")
                    bal = f"{float(d.get('balance', d.get('amount', 0.0)) if isinstance(d, dict) else d):.2f} Ks"
        await state.update_data(balance=bal); await lm.delete(); await msg.answer(f"💰 Balance: {bal}", reply_markup=get_logged_in_keyboard())
    except: await lm.delete(); await msg.answer("⚠️ Error", reply_markup=get_logged_in_keyboard())

@dp.message(LoginForm.main_menu, F.text == TEXT_INFO)
async def show_info(msg: types.Message, state: FSMContext):
    d = await state.get_data(); s = active_sessions.get(msg.from_user.id, {})
    exp = await db.get_user_subscription(msg.from_user.id)
    await msg.answer(f"👤 User: {d.get('username')}\n🌐 Site: {s.get('site')}\n💰 Bal: {d.get('balance')}\n🔑 Exp: {datetime.fromisoformat(exp).strftime('%Y-%m-%d %I:%M %p') if exp else 'N/A'}", reply_markup=get_logged_in_keyboard())

@dp.message(LoginForm.main_menu, F.text == TEXT_LOGOUT)
async def logout(msg: types.Message, state: FSMContext):
    if msg.from_user.id in active_sessions: del active_sessions[msg.from_user.id]
    await state.clear(); await msg.answer("👋 Logged out.", reply_markup=get_main_keyboard())

@dp.message(F.text == "Pro AI Features")
async def cmd_pro_ai_menu(msg: types.Message):
    if msg.from_user.id in active_sessions: await msg.answer("Pro AI Features (Advanced Deep Scan)", reply_markup=get_pro_ai_mode_keyboard())

@dp.message(F.text == TEXT_GAMES)
async def cmd_games(msg: types.Message, state: FSMContext):
    if msg.from_user.id in active_sessions: await state.set_state(LoginForm.select_game_type); await msg.answer(f"🎮 Current: {active_sessions[msg.from_user.id].get('game_type_name')}", reply_markup=get_game_type_keyboard())

@dp.message(LoginForm.select_game_type)
async def process_game_type(msg: types.Message, state: FSMContext):
    if msg.text.upper() == "BACK": await state.set_state(LoginForm.main_menu); return await msg.answer("Menu", reply_markup=get_logged_in_keyboard())
    if msg.text in ["Win Go 30s", "Win Go 1m"]:
        active_sessions[msg.from_user.id].update({"game_type_id": 30 if msg.text=="Win Go 30s" else 1, "game_type_name": "WINGO_30S" if msg.text=="Win Go 30s" else "WINGO_1M"})
        await state.set_state(LoginForm.main_menu); await msg.answer(f"✅ Game: {msg.text}", reply_markup=get_logged_in_keyboard())

@dp.message(F.text == TEXT_VIRTUAL_MODE)
async def cmd_virtual_mode(msg: types.Message, state: FSMContext):
    if msg.from_user.id not in active_sessions: return
    if active_sessions[msg.from_user.id].get("is_virtual_mode"): return await msg.answer("✅ Virtual Mode active.")
    await state.set_state(LoginForm.enter_virtual_balance); await msg.answer("🧪 Virtual Balance? (e.g. 10000)", reply_markup=get_cancel_keyboard())

@dp.message(LoginForm.enter_virtual_balance)
async def process_virtual_bal(msg: types.Message, state: FSMContext):
    if msg.text.lower() == 'cancel': await state.set_state(LoginForm.main_menu); return await msg.answer("❌ Cancelled", reply_markup=get_logged_in_keyboard())
    try:
        vb = float(msg.text.replace(",", ""))
        active_sessions[msg.from_user.id].update({"is_virtual_mode": True, "virtual_balance": vb, "virtual_session_profit": 0.0, "start_balance": vb})
        await db.set_virtual_balance(msg.from_user.id, vb); await state.set_state(LoginForm.main_menu)
        await msg.answer(f"🧪 Virtual Mode Started (K{vb:,.2f})", reply_markup=get_logged_in_keyboard())
    except: await msg.answer("❌ Number only.", reply_markup=get_cancel_keyboard())

@dp.message(F.text == TEXT_REAL_MODE)
async def cmd_real_mode(msg: types.Message):
    if msg.from_user.id in active_sessions and active_sessions[msg.from_user.id].get("is_virtual_mode"):
        active_sessions[msg.from_user.id].update({"is_virtual_mode": False, "session_profit": 0.0, "start_balance": extract_balance(active_sessions[msg.from_user.id].get("balance", "0.00"))})
        await msg.answer("🔴 Real Mode Started", reply_markup=get_logged_in_keyboard())

async def main():
    print("🚀 Auto-Bet (Deep Memory Edition) Bot Started...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try: asyncio.run(main())
    except KeyboardInterrupt: print("Stopped.")
