#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List

load_dotenv()

logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI", "")
if not MONGO_URI:
    raise ValueError("❌ MONGO_URI is not set in .env file!")

client = AsyncIOMotorClient(MONGO_URI)
db = client["autobet_db"]
users_collection = db["users"]
keys_collection = db["keys"]
bet_history_collection = db["bet_history"]


def init_db():
    try:
        client.admin.command('ping')
        logger.info("✅ MongoDB connection verified")
        return True
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        return False


async def get_user(user_id: int) -> Optional[Dict]:
    return await users_collection.find_one({"_id": user_id})


async def save_user_login(user_id: int, phone: str, site_user_id: str, 
                         nickname: str, balance: str, login_time: str, ai_mode: str):
    await users_collection.update_one(
        {"_id": user_id},
        {"$set": {
            "phone": phone,
            "user_id": site_user_id,
            "nickname": nickname,
            "balance": balance,
            "last_login": login_time,
            "ai_mode": ai_mode,
            "updated_at": login_time
        }},
        upsert=True
    )


async def update_user_ai_mode(user_id: int, ai_mode: str):
    await users_collection.update_one(
        {"_id": user_id},
        {"$set": {"ai_mode": ai_mode}},
        upsert=True
    )


async def update_user_balance(user_id: int, balance: str):
    await users_collection.update_one(
        {"_id": user_id},
        {"$set": {"balance": balance}},
        upsert=True
    )


async def create_key(key_str: str, duration: str):
    await keys_collection.insert_one({"key": key_str, "duration": duration})


async def get_key(key_str: str) -> Optional[Dict]:
    return await keys_collection.find_one({"key": key_str})


async def delete_key(key_str: str):
    await keys_collection.delete_one({"key": key_str})


async def update_user_subscription(user_id: int, expire_iso: str):
    await users_collection.update_one(
        {"_id": user_id},
        {"$set": {"expire_date": expire_iso}},
        upsert=True
    )


async def get_user_subscription(user_id: int) -> Optional[str]:
    user = await get_user(user_id)
    if user and "expire_date" in user:
        return user["expire_date"]
    return None


async def save_bet_history(tg_id: int, issue: str, bet_type: str, 
                           amount: int, result: str, profit: float):
    await bet_history_collection.insert_one({
        "tg_id": tg_id,
        "issue": issue,
        "bet_type": bet_type,
        "amount": amount,
        "result": result,
        "profit": profit,
    })


async def get_bet_history(tg_id: int, limit: int = 50) -> List[Dict]:
    cursor = bet_history_collection.find({"tg_id": tg_id}).sort("_id", -1).limit(limit)
    return await cursor.to_list(length=limit)
