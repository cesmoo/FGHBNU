#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import json
import time
import uuid
import hashlib
import os
from typing import Optional, Dict, Any
from datetime import datetime

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    ContextTypes, MessageHandler, filters
)
from dotenv import load_dotenv

# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8609003431:AAGSSC1p-Hhr0IZ2iiB10qFU-jVf2B99QB4')

# Account
USERNAME = os.getenv('USERNAME', '959680090540')
PASSWORD = os.getenv('PASSWORD', 'Bbynnds8825')

# Betting
BET_AMOUNT = int(os.getenv('BET_AMOUNT', 10))
GAME_TYPE_ID = int(os.getenv('GAME_TYPE_ID', 30))
SELECT_TYPE = int(os.getenv('SELECT_TYPE', 13))
INTERVAL_SECONDS = int(os.getenv('INTERVAL_SECONDS', 15))

# API
API_BASE_URL = os.getenv('API_BASE_URL', 'https://api.bigwinqaz.com/api/webapi')
LANGUAGE = int(os.getenv('LANGUAGE', 7))

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================
# SIGNATURE GENERATOR
# ============================================================

class SignatureGenerator:
    """Generate API signature exactly like frontend"""
    
    def __init__(self, language: int = 7):
        self.language = language
    
    def generate_random(self) -> str:
        return uuid.uuid4().hex
    
    def generate_signature(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate signature with MD5 hash"""
        # Remove existing signature and timestamp
        clean_data = {k: v for k, v in data.items() 
                     if k not in ['signature', 'timestamp']}
        
        # Add language and random
        clean_data['language'] = self.language
        clean_data['random'] = self.generate_random()
        
        # Sort keys alphabetically
        sorted_data = {}
        for key in sorted(clean_data.keys()):
            value = clean_data[key]
            if value is not None and value != '':
                sorted_data[key] = value
        
        # JSON stringify and MD5 hash
        json_string = json.dumps(sorted_data, separators=(',', ':'))
        signature = hashlib.md5(json_string.encode()).hexdigest().upper()
        timestamp = int(time.time())
        
        return {
            **clean_data,
            'signature': signature,
            'timestamp': timestamp
        }

# ============================================================
# API CLIENT
# ============================================================

class APIClient:
    """API client with auto-signature and rate limiting"""
    
    BASE_URL = API_BASE_URL
    
    def __init__(self, token: str = "", language: int = 7):
        self.token = token
        self.language = language
        self.sig_gen = SignatureGenerator(language)
        self.session = requests.Session()
        self._last_request_time = 0
        self._min_request_interval = 2.0
        self._setup_headers()
    
    def _setup_headers(self):
        self.session.headers.update({
            'authority': 'api.bigwinqaz.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'ar-origin': 'https://www.777bigwingame.app',
            'cache-control': 'no-cache',
            'content-type': 'application/json;charset=UTF-8',
            'origin': 'https://www.777bigwingame.app',
            'pragma': 'no-cache',
            'referer': 'https://www.777bigwingame.app/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
        })
    
    def set_token(self, token: str):
        self.token = token
        self.session.headers['authorization'] = f'Bearer {token}'
    
    def _rate_limit(self):
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            time.sleep(sleep_time)
        self._last_request_time = time.time()
    
    def _post(self, endpoint: str, data: Dict[str, Any], retry: int = 3) -> Dict[str, Any]:
        self._rate_limit()
        
        for attempt in range(retry):
            try:
                signed_data = self.sig_gen.generate_signature(data)
                response = self.session.post(
                    f"{self.BASE_URL}/{endpoint}",
                    json=signed_data,
                    timeout=30
                )
                result = response.json()
                
                # Rate limit
                if result.get('code') == 13:
                    logger.warning(f"Rate limited, waiting 5 seconds...")
                    time.sleep(5)
                    continue
                
                return result
                
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout, retry {attempt+1}/{retry}")
                time.sleep(2)
            except Exception as e:
                logger.error(f"Request error: {e}")
                if attempt == retry - 1:
                    raise
        
        return {'code': -1, 'msg': 'Max retries exceeded'}
    
    # ============ Login ============
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        data = {
            'username': username,
            'pwd': password,
            'phonetype': 1,
            'logintype': 'mobile',
            'packId': '',
            'deviceId': '51ed4ee0f338a1bb24063ffdfcd31ce6',
            'pixelId': '',
            'fbcId': '',
            'fbc': '',
            'fbp': '',
            'adId': '',
        }
        return self._post('Login', data)
    
    # ============ Game Methods ============
    
    def get_game_issue(self, type_id: int) -> Optional[str]:
        """Get current issue number"""
        try:
            result = self._post('GetGameIssue', {'typeId': type_id})
            logger.debug(f"GetGameIssue response: {json.dumps(result, indent=2)}")
            
            if result.get('code') != 0:
                logger.warning(f"GetGameIssue failed: code={result.get('code')}, msg={result.get('msg')}")
                return None
            
            data = result.get('data')
            
            # Try different response formats
            if isinstance(data, dict):
                for key in ['issueNo', 'issuenumber', 'issueNumber', 'issue']:
                    if key in data and data[key]:
                        issue = str(data[key])
                        logger.info(f"✅ Found issue from '{key}': {issue}")
                        return issue
                
                # Check nested
                for key in ['data', 'result', 'issueInfo']:
                    if key in data and isinstance(data[key], dict):
                        nested = data[key]
                        for nkey in ['issueNo', 'issuenumber', 'issueNumber']:
                            if nkey in nested and nested[nkey]:
                                issue = str(nested[nkey])
                                logger.info(f"✅ Found issue from '{key}.{nkey}': {issue}")
                                return issue
            
            elif isinstance(data, str):
                return data
            
            elif isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], dict):
                    for key in ['issueNo', 'issuenumber']:
                        if key in data[0] and data[0][key]:
                            return str(data[0][key])
                return str(data[0])
            
            logger.warning(f"Could not extract issue from: {data}")
            return None
            
        except Exception as e:
            logger.error(f"GetGameIssue error: {e}")
            return None
    
    def place_bet(self, type_id: int, issue: str, select_type: int, 
                  amount: int, bet_count: int = 1, game_type: int = 2) -> Dict:
        """Place a bet"""
        return self._post('GameBetting', {
            'typeId': type_id,
            'issuenumber': issue,
            'amount': amount,
            'betCount': bet_count,
            'gameType': game_type,
            'selectType': select_type,
        })
    
    def get_balance(self) -> float:
        try:
            result = self._post('GetBalance', {})
            if result.get('code') == 0:
                data = result.get('data', {})
                if isinstance(data, dict):
                    return float(data.get('amount', 0))
            return 0.0
        except:
            return 0.0
    
    def get_user_info(self) -> Dict:
        return self._post('GetUserInfo', {})

# ============================================================
# TELEGRAM BOT
# ============================================================

class AutoBetBot:
    """Main Auto Bet Bot"""
    
    def __init__(self, username: str = None, password: str = None):
        self.username = username or USERNAME
        self.password = password or PASSWORD
        self.api = APIClient()
        self.is_running = False
        self.bet_task = None
        
        # Betting config - use working type_id 30
        self.bet_config = {
            'type_id': GAME_TYPE_ID,
            'select_type': SELECT_TYPE,
            'amount': BET_AMOUNT,
            'bet_count': 1,
            'game_type': 2
        }
        
        self.current_issue = None
        self.stats = {
            'total_bets': 0,
            'wins': 0,
            'losses': 0,
            'profit': 0
        }
        self.consecutive_failures = 0
    
    async def login(self) -> bool:
        """Login to the platform"""
        try:
            result = self.api.login(self.username, self.password)
            if result.get('code') == 0:
                token = result['data']['token']
                self.api.set_token(token)
                logger.info("✅ Login successful!")
                return True
            else:
                logger.error(f"❌ Login failed: {result.get('msg')}")
                return False
        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            return False
    
    async def get_current_issue(self) -> Optional[str]:
        """Get current issue number with retry"""
        type_id = self.bet_config['type_id']
        
        for attempt in range(5):
            try:
                issue = self.api.get_game_issue(type_id)
                if issue:
                    logger.info(f"✅ Got issue: {issue}")
                    return issue
                
                logger.warning(f"⚠️ Attempt {attempt+1}/5 failed, waiting...")
                await asyncio.sleep(3)
                
            except Exception as e:
                logger.error(f"Get issue attempt {attempt+1} failed: {e}")
                await asyncio.sleep(2)
        
        return None
    
    async def place_bet(self) -> bool:
        """Place a single bet"""
        type_id = self.bet_config['type_id']
        
        # Get current issue
        issue = await self.get_current_issue()
        if not issue:
            logger.warning("❌ No issue number available after retries")
            return False
        
        # Check if already bet on this issue
        if issue == self.current_issue:
            logger.info(f"⏳ Already bet on issue {issue}, waiting for next...")
            return False
        
        try:
            result = self.api.place_bet(
                type_id=type_id,
                issue=issue,
                select_type=self.bet_config['select_type'],
                amount=self.bet_config['amount'],
                bet_count=self.bet_config['bet_count'],
                game_type=self.bet_config['game_type']
            )
            
            logger.info(f"Bet response: code={result.get('code')}")
            
            if result.get('code') == 0:
                self.current_issue = issue
                self.stats['total_bets'] += 1
                self.consecutive_failures = 0
                logger.info(f"✅ Bet placed on issue {issue}")
                return True
            else:
                msg = result.get('msg', 'Unknown error')
                logger.warning(f"❌ Bet failed: {msg}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Place bet error: {e}")
            return False
    
    async def run_auto_bet(self):
        """Main auto-betting loop"""
        # Login first
        if not await self.login():
            logger.error("❌ Login failed, cannot start auto bet")
            return
        
        self.is_running = True
        interval = INTERVAL_SECONDS
        logger.info(f"🔄 Auto betting started - Interval: {interval}s")
        logger.info(f"💰 Bet Amount: {self.bet_config['amount']} USDT")
        logger.info(f"🎮 Game Type: {self.bet_config['type_id']}")
        
        while self.is_running:
            try:
                success = await self.place_bet()
                
                if success:
                    self.consecutive_failures = 0
                else:
                    self.consecutive_failures += 1
                
                # Dynamic wait time
                wait_time = interval
                if self.consecutive_failures > 5:
                    wait_time = 30
                    logger.warning(f"⚠️ {self.consecutive_failures} consecutive failures, waiting {wait_time}s")
                elif self.consecutive_failures > 3:
                    wait_time = 20
                
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"Auto bet loop error: {e}")
                await asyncio.sleep(10)
    
    async def stop_auto_bet(self):
        """Stop auto betting"""
        self.is_running = False
        if self.bet_task:
            self.bet_task.cancel()
        logger.info("⏹ Auto betting stopped")
    
    def get_stats(self) -> str:
        """Get betting statistics"""
        total = self.stats['total_bets']
        wins = self.stats['wins']
        win_rate = (wins / max(total, 1)) * 100
        
        return (
            f"📊 *Betting Statistics*\n"
            f"─────────────────\n"
            f"🎯 Total Bets: {total}\n"
            f"✅ Wins: {wins}\n"
            f"❌ Losses: {self.stats['losses']}\n"
            f"💰 Profit: {self.stats['profit']} USDT\n"
            f"📈 Win Rate: {win_rate:.1f}%"
        )
    
    def get_balance_text(self) -> str:
        """Get balance text"""
        balance = self.api.get_balance()
        return f"💰 *Balance*: {balance} USDT"

# ============================================================
# TELEGRAM HANDLERS
# ============================================================

bot = AutoBetBot()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    keyboard = [
        [
            InlineKeyboardButton("▶️ Start Auto Bet", callback_data="start_bot"),
            InlineKeyboardButton("⏹ Stop Auto Bet", callback_data="stop_bot"),
        ],
        [
            InlineKeyboardButton("💰 Balance", callback_data="balance"),
            InlineKeyboardButton("📊 Stats", callback_data="stats"),
        ],
        [
            InlineKeyboardButton("🔄 Refresh Login", callback_data="refresh"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    status = "🟢 Running" if bot.is_running else "🔴 Stopped"
    
    await update.message.reply_text(
        f"🤖 *Auto Bet Bot*\n\n"
        f"Welcome! Use the buttons below to control the bot.\n\n"
        f"Current config:\n"
        f"• Game Type: {GAME_TYPE_ID}\n"
        f"• Amount: {BET_AMOUNT} USDT\n"
        f"• Status: {status}",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Button click handler"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "start_bot":
        if bot.is_running:
            await query.edit_message_text("ℹ️ Bot is already running!", parse_mode='Markdown')
            return
        
        # Start in background
        bot.bet_task = asyncio.create_task(bot.run_auto_bet())
        await query.edit_message_text("🟢 *Auto bet started!*", parse_mode='Markdown')
    
    elif query.data == "stop_bot":
        if not bot.is_running:
            await query.edit_message_text("ℹ️ Bot is already stopped!", parse_mode='Markdown')
            return
        
        await bot.stop_auto_bet()
        await query.edit_message_text("🔴 *Auto bet stopped!*", parse_mode='Markdown')
    
    elif query.data == "balance":
        balance_text = bot.get_balance_text()
        await query.edit_message_text(balance_text, parse_mode='Markdown')
    
    elif query.data == "stats":
        await query.edit_message_text(bot.get_stats(), parse_mode='Markdown')
    
    elif query.data == "refresh":
        await query.edit_message_text("🔄 *Refreshing login...*", parse_mode='Markdown')
        if await bot.login():
            await query.edit_message_text("✅ *Login refreshed successfully!*", parse_mode='Markdown')
        else:
            await query.edit_message_text("❌ *Login refresh failed!*", parse_mode='Markdown')

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom commands"""
    text = update.message.text
    
    if text == "/stop":
        await bot.stop_auto_bet()
        await update.message.reply_text("🔴 Bot stopped!")
    
    elif text == "/status":
        status = "🟢 Running" if bot.is_running else "🔴 Stopped"
        await update.message.reply_text(f"🤖 Status: {status}")
    
    elif text.startswith("/bet"):
        parts = text.split()
        if len(parts) >= 2:
            try:
                amount = int(parts[1])
                bot.bet_config['amount'] = amount
                await update.message.reply_text(f"✅ Bet amount set to {amount} USDT")
            except ValueError:
                await update.message.reply_text("❌ Please enter a valid number")
    
    elif text == "/balance":
        await update.message.reply_text(bot.get_balance_text(), parse_mode='Markdown')

# ============================================================
# MAIN
# ============================================================

async def main():
    """Main entry point"""
    # Check configuration
    if not TELEGRAM_BOT_TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN is not set in .env file")
        return
    
    # Create application
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    # Start bot
    print("=" * 50)
    print("🤖 Auto Bet Bot Started!")
    print(f"📱 Telegram Bot: @{app.bot.username}")
    print(f"🎮 Game Type: {GAME_TYPE_ID}")
    print(f"💰 Bet Amount: {BET_AMOUNT} USDT")
    print("=" * 50)
    
    # Start polling
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
