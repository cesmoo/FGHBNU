#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Bot configuration"""
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    OWNER_ID = int(os.getenv('OWNER_ID', '0'))
    
    # Account
    USERNAME = os.getenv('USERNAME', '')
    PASSWORD = os.getenv('PASSWORD', '')
    
    # Betting
    BET_AMOUNT = int(os.getenv('BET_AMOUNT', 10))
    GAME_TYPE_ID = int(os.getenv('GAME_TYPE_ID', 30))
    SELECT_TYPE = int(os.getenv('SELECT_TYPE', 13))
    INTERVAL_SECONDS = int(os.getenv('INTERVAL_SECONDS', 15))
    BET_SEQUENCE = os.getenv('BET_SEQUENCE', '10-20-40-80')
    
    # API
    LANGUAGE = int(os.getenv('LANGUAGE', 7))
    
    # Database
    MONGO_URI = os.getenv('MONGO_URI', '')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
