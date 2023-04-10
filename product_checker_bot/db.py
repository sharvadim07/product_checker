from collections import OrderedDict
from dataclasses import dataclass
from datetime import date
from datetime import datetime
from dateutil.parser import parse
from typing import Optional, Tuple

import aiosqlite
import sqlite3
from product_checker_bot.config import config


@dataclass
class Product:
    product_id: int
    created_at: str
    date_prod: Optional[str]
    date_exp: Optional[str]
    label_path: Optional[str]

    def shelf_life_days(self) -> Optional[int]:
        if self.date_exp:
            if self.date_prod:
                return (parse(self.date_exp).date() - parse(self.date_prod).date()).days
            else:
                return (
                    parse(self.date_exp).date() - parse(self.created_at).date()
                ).days
        else:
            return None

    def remaining_shelf_life_days(self) -> Optional[int]:
        if self.date_exp:
            return (parse(self.date_exp).date() - datetime.now().date()).days
        else:
            return None

    def remaining_shelf_life_percent(self) -> Optional[float]:
        shelf_life_days = self.shelf_life_days()
        remaining_shelf_life_days = self.remaining_shelf_life_days()
        if shelf_life_days is not None and remaining_shelf_life_days is not None:
            return round((remaining_shelf_life_days / shelf_life_days) * 100, 1)
        else:
            return None


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
class BotUser:
    telegram_user_id: int
    created_at: str
    products: Optional[OrderedDict[int, Product]]


"""
    telegram_user_id BIGINT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
"""


def get_bot_users_and_products_db() -> OrderedDict[int, BotUser]:
    bot_users: OrderedDict[int, BotUser] = OrderedDict()
    with sqlite3.connect(config.SQLITE_DB_FILE) as db:
        db.row_factory = sqlite3.Row
        cursor = db.execute(
            """
            SELECT *,
                   bot_user.created_at AS bot_user_created_at,
                   product.created_at AS product_created_at
              FROM bot_user
              LEFT JOIN product USING(telegram_user_id)
             ORDER BY telegram_user_id, product.date_exp DESC;
            """
        )
        for row in cursor:
            if row["telegram_user_id"] not in bot_users:
                if row["product_id"] is not None:
                    bot_users[row["telegram_user_id"]] = BotUser(
                        row["telegram_user_id"],
                        row["bot_user_created_at"],
                        OrderedDict(
                            {
                                row["product_id"]: Product(
                                    row["product_id"],
                                    row["product_created_at"],
                                    row["date_prod"],
                                    row["date_exp"],
                                    row["label_path"],
                                )
                            }
                        ),
                    )
                else:
                    bot_users[row["telegram_user_id"]] = BotUser(
                        row["telegram_user_id"], row["bot_user_created_at"], None
                    )
            else:
                bot_user = bot_users.get(row["telegram_user_id"])
                if bot_user and bot_user.products:
                    if row["product_id"] is not None:
                        bot_user.products[row["product_id"]] = Product(
                            row["product_id"],
                            row["product_created_at"],
                            row["date_prod"],
                            row["date_exp"],
                            row["label_path"],
                        )
    return bot_users


async def get_all_bot_users_db() -> OrderedDict[int, BotUser]:
    bot_users: OrderedDict[int, BotUser] = OrderedDict()
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
                    row["telegram_user_id"], row["created_at"], None
                )
    return bot_users


async def add_new_bot_user_db(telegram_user_id: int) -> Optional[BotUser]:
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
                bot_user = BotUser(row["telegram_user_id"], row["created_at"], None)
    return bot_user


async def get_bot_user_db(telegram_user_id: int) -> Optional[BotUser]:
    bot_user = None
    async with aiosqlite.connect(config.SQLITE_DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            f"""
            SELECT *,
                   bot_user.created_at AS bot_user_created_at,
                   product.created_at AS product_created_at
              FROM bot_user
              LEFT JOIN product USING(telegram_user_id)
             WHERE telegram_user_id = {telegram_user_id}
             ORDER BY product.date_exp DESC;
            """
        ) as cursor:
            async for row in cursor:
                if row["product_id"] is not None:
                    if not bot_user:
                        bot_user = BotUser(
                            row["telegram_user_id"],
                            row["bot_user_created_at"],
                            OrderedDict(
                                {
                                    row["product_id"]: Product(
                                        row["product_id"],
                                        row["product_created_at"],
                                        row["date_prod"],
                                        row["date_exp"],
                                        row["label_path"],
                                    )
                                }
                            ),
                        )
                    else:
                        bot_user.products[row["product_id"]] = Product(
                            row["product_id"],
                            row["product_created_at"],
                            row["date_prod"],
                            row["date_exp"],
                            row["label_path"],
                        )
                else:
                    bot_user = BotUser(row["telegram_user_id"], row["created_at"], None)
    return bot_user


async def new_user_product_db(telegram_user_id: int) -> None:
    async with aiosqlite.connect(config.SQLITE_DB_FILE) as db:
        await db.execute(
            f"""
            INSERT INTO product (telegram_user_id)
            VALUES ({telegram_user_id});
            """
        )
        await db.commit()


async def remove_all_products_db(telegram_user_id: int) -> None:
    async with aiosqlite.connect(config.SQLITE_DB_FILE) as db:
        await db.execute(
            f"""
            DELETE FROM product
             WHERE telegram_user_id == "{telegram_user_id}";
            """
        )
        await db.commit()


async def get_product_db(product_id: int) -> Optional[Product]:
    product = None
    async with aiosqlite.connect(config.SQLITE_DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            f"""
            SELECT *
              FROM product
             WHERE product_id = {product_id};
            """
        ) as cursor:
            async for row in cursor:
                if row["product_id"] is not None:
                    if not product:
                        product = Product(
                            row["product_id"],
                            row["created_at"],
                            row["date_prod"],
                            row["date_exp"],
                            row["label_path"],
                        )
    return product


async def _update_product_db(
    product_id: int,
    label_path: Optional[str] = None,
    date_prod: Optional[str] = None,
    date_exp: Optional[str] = None,
) -> None:
    async with aiosqlite.connect(config.SQLITE_DB_FILE) as db:
        await db.execute(
            f"""
            UPDATE product
               SET label_path = IIF("{label_path}" = "None", label_path, "{label_path}"),
                   date_prod = IIF("{date_prod}" = "None", date_prod, DATE("{date_prod}")),
                   date_exp = IIF("{date_exp}" = "None", date_exp, DATE("{date_exp}"))
             WHERE product_id = "{product_id}";
            """
        )
        await db.commit()


async def remove_product_db(
    product_id: int,
) -> None:
    async with aiosqlite.connect(config.SQLITE_DB_FILE) as db:
        await db.execute(
            f"""
            DELETE FROM product
             WHERE product_id = {product_id};
            """
        )
        await db.commit()


async def get_add_bot_user(telegram_user_id: int) -> BotUser:
    # Get user from DB
    bot_user = await get_bot_user_db(telegram_user_id)
    if not bot_user:
        bot_user = await add_new_bot_user_db(telegram_user_id)
    if not bot_user:
        raise ValueError("bot_user is None")
    return bot_user


async def new_user_product(telegram_user_id: int) -> Tuple[Product, BotUser]:
    # Get user with products
    bot_user = await get_add_bot_user(telegram_user_id)
    # Add new product to DB
    await new_user_product_db(bot_user.telegram_user_id)
    # Get user with products
    bot_user = await get_add_bot_user(telegram_user_id)
    if not bot_user.products:
        raise ValueError("bot_user.products is None")
    return (
        max(bot_user.products.values(), key=lambda v: v.product_id),
        bot_user,
    )


async def update_product(
    product_id: int,
    label_path: Optional[str] = None,
    prod_date: Optional[Tuple[str, date]] = None,
    exp_date: Optional[Tuple[str, date]] = None,
) -> Product:
    prod_date_str = None
    exp_date_str = None
    if prod_date:
        # prod_date_str = prod_date[1].strftime("%d/%m/%Y")
        prod_date_str = prod_date[1].strftime("%Y-%m-%d")
    if exp_date:
        # exp_date_str = exp_date[1].strftime("%d/%m/%Y")
        exp_date_str = exp_date[1].strftime("%Y-%m-%d")
    await _update_product_db(
        product_id=product_id,
        label_path=label_path,
        date_prod=prod_date_str,
        date_exp=exp_date_str,
    )
    product = await get_product_db(product_id)
    if not product:
        raise ValueError("Product not updated in DB.")
    else:
        return product


async def remove_product(cur_product: Product, bot_user: BotUser) -> None:
    if bot_user.products:
        bot_user.products.pop(cur_product.product_id)
    await remove_product_db(cur_product.product_id)
