#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import os

logger = logging.getLogger(__name__)

DB_PATH = os.getenv('DB_PATH', 'data/bot.db')

def init_db():
    """Initialize database tables"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            tg_id INTEGER PRIMARY KEY,
            phone TEXT,
            user_id TEXT,
            nickname TEXT,
            balance TEXT,
            last_login TEXT,
            ai_mode TEXT,
            expire_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Keys table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS keys (
            key_str TEXT PRIMARY KEY,
            duration TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            used_at TEXT
        )
    ''')
    
    # Bet history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bet_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER,
            issue TEXT,
            bet_type TEXT,
            amount INTEGER,
            result TEXT,
            profit REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {DB_PATH}")


# ==========================================
# 👤 User Data Functions
# ==========================================

async def get_user(user_id: int) -> Optional[Dict]:
    """User ၏ Data များကို ယူရန်"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE tg_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


async def save_user_login(user_id: int, phone: str, site_user_id: str, 
                         nickname: str, balance: str, login_time: str, ai_mode: str):
    """Login အောင်မြင်ပါက User Data များကို သိမ်းဆည်း/Update လုပ်ရန်"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO users 
        (tg_id, phone, user_id, nickname, balance, last_login, ai_mode, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (user_id, phone, site_user_id, nickname, balance, login_time, ai_mode))
    
    conn.commit()
    conn.close()


async def update_user_ai_mode(user_id: int, ai_mode: str):
    """User ရွေးချယ်ထားသော AI Mode ကို သိမ်းဆည်းရန်"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE users SET ai_mode = ?, updated_at = CURRENT_TIMESTAMP
        WHERE tg_id = ?
    ''', (ai_mode, user_id))
    
    conn.commit()
    conn.close()


async def update_user_balance(user_id: int, balance: str):
    """User ၏ Balance ကို Update လုပ်ရန်"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE users SET balance = ?, updated_at = CURRENT_TIMESTAMP
        WHERE tg_id = ?
    ''', (balance, user_id))
    
    conn.commit()
    conn.close()


# ==========================================
# 🔑 Auth & Subscription Functions
# ==========================================

async def create_key(key_str: str, duration: str):
    """Owner ထုတ်လိုက်သော Key ကို DB တွင်သိမ်းရန်"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO keys (key_str, duration, created_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    ''', (key_str, duration))
    
    conn.commit()
    conn.close()


async def get_key(key_str: str) -> Optional[Dict]:
    """Key အချက်အလက်ကို ဆွဲယူရန်"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM keys WHERE key_str = ?', (key_str,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


async def delete_key(key_str: str):
    """အသုံးပြုပြီးသော Key ကို ဖျက်ရန်"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM keys WHERE key_str = ?', (key_str,))
    
    conn.commit()
    conn.close()


async def update_user_subscription(user_id: int, expire_iso: str):
    """User ၏ အသုံးပြုခွင့် သက်တမ်းကို Update လုပ်ရန်"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE users SET expire_date = ?, updated_at = CURRENT_TIMESTAMP
        WHERE tg_id = ?
    ''', (expire_iso, user_id))
    
    conn.commit()
    conn.close()


async def get_user_subscription(user_id: int) -> Optional[str]:
    """User ၏ သက်တမ်းကုန်ဆုံးမည့် အချိန်ကို ယူရန်"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT expire_date FROM users WHERE tg_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    return row[0] if row else None


# ==========================================
# 📊 Bet History Functions
# ==========================================

async def save_bet_history(tg_id: int, issue: str, bet_type: str, 
                           amount: int, result: str, profit: float):
    """Bet history ကို သိမ်းဆည်းရန်"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO bet_history (tg_id, issue, bet_type, amount, result, profit, created_at)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (tg_id, issue, bet_type, amount, result, profit))
    
    conn.commit()
    conn.close()


async def get_bet_history(tg_id: int, limit: int = 50) -> List[Dict]:
    """User ၏ Bet history ကို ယူရန်"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM bet_history WHERE tg_id = ? 
        ORDER BY created_at DESC LIMIT ?
    ''', (tg_id, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


# Initialize database on import
init_db()
