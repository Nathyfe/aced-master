import logging

import aiomysql


class MySQL:
    def __init__(self, client):
        self.client = client

    async def init(self):
        if self.client.pool is None:
            self.client.pool = await aiomysql.create_pool(
                host="209.126.5.58",
                user="aced",
                password="s1tmfhWp9UBUgy4",
                db="ays_aced",
                cursorclass=aiomysql.DictCursor,
                autocommit=True,
            )

    async def query(self, sql, *params):
        logging.info("======= SQL Query =======")
        logging.info((sql, params))
        if self.client.pool is None:
            await self.init()
        async with self.client.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, params)
                r = await cur.fetchall()
        logging.info(r)
        logging.info("=========================")
        return r  # Returns a list of fetched rows (if SELECT)

    async def get_current_guild_prices(self, guild_id):
        return await self.query("SELECT * FROM prices WHERE guild_id = %s", guild_id)

    async def get_price(self, guild_id, label_id, weight):
        return await self.query(
            "SELECT * FROM prices WHERE guild_id = %s AND label_id = %s AND min_weight <= %s AND %s <= max_weight",
            guild_id,
            label_id,
            weight,
            weight,
        )

    async def update_prices(self, guild_id, prices):
        current = await self.get_current_guild_prices(guild_id)
        current = {i["label_id"]: i for i in current}
        for label_id, pricew in prices.items():
            if label_id in current:
                await self.query(
                    "DELETE FROM prices WHERE guild_id = %s AND label_id = %s",
                    guild_id,
                    label_id,
                )
            for price in pricew:
                await self.query(
                    "INSERT INTO prices(guild_id, label_id, min_weight, max_weight, price) VALUES (%s, %s, %s, %s, %s)",
                    guild_id,
                    label_id,
                    price["min_weight"],
                    price["max_weight"],
                    price["price"],
                )

    async def get_balance(self, guild_id, user_id):
        return await self.query(
            "SELECT * FROM credits WHERE guild_id = %s AND user_id = %s",
            guild_id,
            user_id,
        )

    async def add_balance(self, guild_id, user_id, amount):
        c = await self.get_balance(guild_id, user_id)
        if not c:
            return await self.query(
                "INSERT INTO credits(guild_id, user_id, balance) VALUES (%s, %s, %s)",
                guild_id,
                user_id,
                amount,
            )
        else:
            return await self.query(
                "UPDATE credits SET balance = balance + %s WHERE guild_id = %s AND user_id = %s",
                 amount,
                guild_id,
                user_id,
            )

    async def remove_balance(self, guild_id, user_id, amount):
        c = await self.get_balance(guild_id, user_id)
        if not c or c[0]["balance"] < amount:
            return False

        return await self.query(
            "UPDATE credits SET balance = balance - %s WHERE guild_id = %s AND user_id = %s",
            amount,
            guild_id,
            user_id,
        )

    async def enable_server(self, server_id, api_key):
        return await self.query(
            "INSERT INTO servers (guild_id, api_key) VALUES (%s, %s) ON DUPLICATE KEY UPDATE api_key = %s",
            server_id,
            api_key,
            api_key,
        )

    async def disable_server(self, server_id):
        return await self.query("DELETE FROM servers WHERE guild_id = %s", server_id)

    async def get_api_key(self, guild_id):
        return await self.query("SELECT * FROM servers WHERE guild_id = %s", guild_id)

    async def register_order(self, order_id, guild_id, user_id, receipt_sent):
        return await self.query(
            f"INSERT INTO orders (order_id, guild_id, user_id, receipt_sent, time_receipt) VALUES (%s, %s, %s, %s, {'CURRENT_TIMESTAMP()' if receipt_sent else 'NULL'})",
            order_id,
            guild_id,
            user_id,
            receipt_sent,
        )

    async def get_waiting_receipts(self):
        return await self.query(
            "SELECT * FROM orders JOIN servers ON orders.guild_id = servers.guild_id WHERE orders.receipt_sent = 0"
        )

    async def receipt_done(self, order_id):
        return await self.query(
            "UPDATE orders SET receipt_sent = 1, time_receipt = CURRENT_TIMESTAMP() WHERE order_id = %s",
            order_id,
        )
