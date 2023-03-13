from dataclasses import dataclass
from typing import Tuple, List, Dict, Optional
from datetime import date
from collections import OrderedDict
import aiosqlite

from config import config

@dataclass
class Product():
    product_id : int
    created_at : str
    date_prod : Optional[str]
    date_exp : Optional[str]
    label_path : Optional[str]
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
    created_at : str
    products : Optional[OrderedDict[int, Product]]
"""
    telegram_user_id BIGINT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
"""

async def get_bot_users_and_products_db() -> OrderedDict[int, BotUser]:
    bot_users : OrderedDict[int, BotUser] = OrderedDict()
    async with aiosqlite.connect(config.SQLITE_DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT *
              FROM bot_user
              LEFT JOIN products USING(telegram_user_id)
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

async def add_new_bot_user_db(telegram_user_id : int) -> Optional[BotUser]:
    bot_user = None
    async with aiosqlite.connect(config.SQLITE_DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            f"""
            INSERT INTO bot_user (telegram_user_id)
            VALUES ({telegram_user_id});
            """
        )
        await db.commit()
        async with db.execute(
            f"""
            SELECT *
              FROM bot_user
             WHERE telegram_user_id = {telegram_user_id};
            """
        ) as cursor:
            async for row in cursor:
                bot_user = BotUser(
                    row["telegram_user_id"],
                    row["created_at"],
                    None
                )
    return bot_user

async def get_bot_user_db(telegram_user_id : int) -> Optional[BotUser]:
    bot_user = None
    async with aiosqlite.connect(config.SQLITE_DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            f"""
            SELECT *
              FROM bot_user
              LEFT JOIN product USING(telegram_user_id)
             WHERE telegram_user_id = {telegram_user_id}
             ORDER BY product_id;
            """
        ) as cursor:
            async for row in cursor:
                if row["product_id"] != None:
                    if not bot_user:
                        bot_user = BotUser(
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
                        bot_user.products[row["product_id"]] = \
                            Product(
                                row["product_id"],
                                row["created_at"],
                                row["date_prod"],
                                row["date_exp"],
                                row["label_path"]
                            )
                else:
                    bot_user = BotUser(
                        row["telegram_user_id"],
                        row["created_at"],
                        None
                    )
    return bot_user

async def new_user_product_db(telegram_user_id : int) -> None:
    async with aiosqlite.connect(config.SQLITE_DB_FILE) as db:
        await db.execute(
            f"""
            INSERT INTO product (telegram_user_id)
            VALUES ({telegram_user_id});
            """
        )
        await db.commit()

async def update_product_db(
        product_id : int, 
        label_path : Optional[str] = None, 
        date_prod : Optional[str] = None, 
        date_exp : Optional[str] = None
    ) -> None:
    async with aiosqlite.connect(config.SQLITE_DB_FILE) as db:
        await db.execute(
            f"""
            UPDATE product
               SET label_path = IIF("{label_path}" = "None", label_path, "{label_path}"),
                   date_prod = IIF("{date_prod}" = "None", label_path, "{date_prod}"),
                   date_exp = IIF("{date_exp}" = "None", label_path, "{date_exp}")
             WHERE product_id = "{product_id}";
            """
        )
        await db.commit()

async def remove_product_db(
        product_id : int, 
    ) -> None:
    async with aiosqlite.connect(config.SQLITE_DB_FILE) as db:
        await db.execute(
            f"""
            DELETE FROM product
             WHERE product_id = {product_id};
            """
        )
        await db.commit()

async def get_add_bot_user(telegram_user_id : int) -> BotUser:
    # Get user from DB
    bot_user = await get_bot_user_db(telegram_user_id)
    if not bot_user:
        bot_user = await add_new_bot_user_db(telegram_user_id)
    if not bot_user:
        raise ValueError("bot_user is None")
    return bot_user

async def new_user_product(bot_user : BotUser) -> Product:
    # Add new product to DB
    await new_user_product_db(bot_user.telegram_user_id)
    # Get user with products
    updated_bot_user = await get_bot_user_db(bot_user.telegram_user_id)
    if not updated_bot_user:
        raise ValueError("bot_user is None")
    if not updated_bot_user.products:
        raise ValueError("bot_user.products is None")
    bot_user.products = updated_bot_user.products
    return list(bot_user.products.values())[-1]

async def update_product(
        cur_product : Product,
        label_path : Optional[str] = None,
        prod_date : Optional[Tuple[str, date]] = None,
        exp_date : Optional[Tuple[str, date]] = None,
    ) -> None:
    if label_path:
        cur_product.label_path = label_path
    if prod_date:
        cur_product.date_prod = prod_date[1].strftime("%d/%m/%Y")
    if exp_date:
        cur_product.date_exp = exp_date[1].strftime("%d/%m/%Y")
    await update_product_db(
        cur_product.product_id,
        cur_product.label_path,
        cur_product.date_prod,
        cur_product.date_exp
    )

async def remove_product(
        cur_product : Product,
        bot_user : BotUser
    ) -> None:
    if bot_user.products:
        bot_user.products.pop(cur_product.product_id)
    await remove_product_db(cur_product.product_id)
