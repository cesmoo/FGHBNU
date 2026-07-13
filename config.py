#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv
import logging

load_dotenv()

class Config:
    """Bot configuration"""
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    OWNER_ID = int(os.getenv('OWNER_ID', '0'))
    
    # Account
    USERNAME = os.getenv('USERNAME', '959680090540')
    PASSWORD = os.getenv('PASSWORD', 'Bbynnds8825')
    
    # Site
    SITE = os.getenv('SITE', '777BIGWIN')
    
    # Betting
    BET_AMOUNT = int(os.getenv('BET_AMOUNT', 10))
    GAME_TYPE_ID = int(os.getenv('GAME_TYPE_ID', 30))
    SELECT_TYPE = int(os.getenv('SELECT_TYPE', 13))
    INTERVAL_SECONDS = int(os.getenv('INTERVAL_SECONDS', 15))
    BET_SEQUENCE = os.getenv('BET_SEQUENCE', '10-20-40-80')
    
    # AI Mode
    AI_MODE = os.getenv('AI_MODE', 'pattern')
    
    # API
    LANGUAGE = int(os.getenv('LANGUAGE', 7))
    
    # MongoDB
    MONGO_URI = os.getenv('MONGO_URI', '')
    
    # Logging - Default to INFO if not set
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()  # 👈 FIX: Add .upper() and default
    
    @classmethod
    def get_bet_sequence(cls) -> list:
        return [int(x.strip()) for x in cls.BET_SEQUENCE.split('-') if x.strip()]
    
    @classmethod
    def validate(cls):
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        if not cls.MONGO_URI:
            raise ValueError("MONGO_URI is required")
        return True

# Print config on load (for debugging)
print(f"✅ LOG_LEVEL: {Config.LOG_LEVEL}")
