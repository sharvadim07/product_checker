from dataclasses import dataclass
from typing import Tuple, List, Dict, Optional
from datetime import datetime
from datetime import date
from collections import OrderedDict
import aiosqlite

import config

@dataclass
class Product():
    product_id : int
    created_at : datetime
    date_prod : date
    date_exp : date
    label_path : str
"""
    product_id INT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMPNOT NOT NULL,
    date_prod DATE,
    date_exp DATE,
    label_path VARCHAR(200),
    telegram_user_id INT NOT NULL,
    FOREIGN KEY (telegram_user_id) REFERENCES user (telegram_user_id) 
"""

@dataclass
class BotUser():
    telegram_user_id : int
    created_at : datetime
    products : Optional[OrderedDict[int, Product]]
"""
    telegram_user_id BIGINT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
"""

async def get_all_bot_users_with_products() -> OrderedDict[int, BotUser]:
    bot_users : OrderedDict[int, BotUser] = OrderedDict()
    async with aiosqlite.connect(config.SQLITE_DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT *
              FROM bot_user
              JOIN products USING(telegram_user_id)
             ORDER BY telegram_user_id;
            """
        ) as cursor:
            async for row in cursor:
                if row["telegram_user_id"] not in bot_users:
                    bot_users[row["telegram_user_id"]] = BotUser(
                        row["telegram_user_id"],
                        row["created_at"],
                        OrderedDict({row["product_id"] : Product(
                            row["product_id"],
                            row["created_at"],
                            row["date_prod"],
                            row["date_exp"],
                            row["label_path"]
                        )})
                    )
                else:
                    bot_users[row["telegram_user_id"]].products[row["product_id"]] = \
                        Product(
                            row["product_id"],
                            row["created_at"],
                            row["date_prod"],
                            row["date_exp"],
                            row["label_path"]
                        )
    return bot_users

async def get_all_bot_users() -> OrderedDict[int, BotUser]:
    bot_users : OrderedDict[int, BotUser] = OrderedDict()
    async with aiosqlite.connect(config.SQLITE_DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT telegram_user_id, created_at
              FROM bot_user
             ORDER BY telegram_user_id;
            """
        ) as cursor:
            async for row in cursor:
                bot_users[row["telegram_user_id"]] = BotUser(
                    row["telegram_user_id"],
                    row["created_at"],
                    None
                )
    return bot_users

async def add_new_bot_user(telegram_user_id : int) -> None:
    async with aiosqlite.connect(config.SQLITE_DB_FILE) as db:
        await db.execute(
            f"""
            INSERT INTO bot_user (telegram_user_id)
            VALUES ({telegram_user_id});
            """
        )
        await db.commit()

async def get_bot_user(telegram_user_id : int) -> Optional[BotUser]:
    async with aiosqlite.connect(config.SQLITE_DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            f"""
            SELECT *
              FROM bot_user
             WHERE telegram_user_id = {telegram_user_id};
            """
        ) as cursor:
            async for row in cursor:
                return BotUser(
                    row["telegram_user_id"],
                    row["created_at"],
                    None
                )
    return None

async def get_add_bot_user(telegram_user_id) -> Optional[BotUser]:
    bot_user = await get_bot_user(telegram_user_id)
    if not bot_user:
        await add_new_bot_user(telegram_user_id)
        bot_user = await get_bot_user(telegram_user_id)
        return bot_user
    else:
        return bot_user