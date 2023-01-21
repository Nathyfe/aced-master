import logging
import os
from math import ceil
from pprint import pprint

import config as cfg
import dbmanagement as dbm
import functions as fct
import nextcord
from nextcord.ext import commands, tasks

logging.basicConfig(level=logging.INFO)


class MyBot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.sql = dbm.MySQL(self)
        self.pool = None
        self.check_receipts.start()

    async def on_ready(self):
        print("Connected.", self.user.name, "is ready!")

    async def prepare_cache(self):
        conf = await fct.getConfig()
        self.raw_conf = conf
        self.labels = []
        for lab in self.raw_conf["Data"]["Types"]:
            if not lab["Enabled"]:
                continue
            temp = {}
            temp["id"] = lab["ID"]
            temp["name"] = lab["Name"]
            temp["weights"] = []
            for price in lab["Prices"]:
                temp["weights"].append(
                    {"min": price["From"], "max": price["To"], "price": price["Price"]}
                )
            self.labels.append(temp)

        self.countries = {
            i["ID"]: i["Name"] for i in self.raw_conf["Data"]["Countries"]
        }
        self.states = {i["ID"]: i["Name"] for i in self.raw_conf["Data"]["States"]}

        # pprint(self.labels)

    def getLabelById(self, label_id):
        label = [la for la in self.labels if la["id"] == label_id]
        if not label:
            return 0
        else:
            return label[0]

    def getLabelPrice(self, label_id, weight):
        label = self.getLabelById(label_id)
        for w in label["weights"]:
            if w["min"] <= ceil(weight) <= w["max"]:
                return w["price"]

        return -1

    @tasks.loop(minutes=5)
    async def check_receipts(self):
        waiting = await self.sql.get_waiting_receipts()
        for wait in waiting:
            status, pdf = await fct.getPDF(wait["order_id"], api=wait["api_key"])
            if status != 200:
                continue

            await self.sql.receipt_done(wait["order_id"])
            user = self.get_user(wait["user_id"]) or (
                await self.fetch_user(wait["user_id"])
            )
            try:
                await user.send(
                    f"Your receipt for {wait['order_id']} is ready! You can download it here:",
                    file=nextcord.File(pdf),
                )
            except Exception:
                pass

    @check_receipts.before_loop
    async def before_loop(self):
        await self.wait_until_ready()


bot = MyBot(
    intents=nextcord.Intents(
        guilds=True,
        messages=True,
        message_content=True,
    ),
    command_prefix=";",
    activity=nextcord.Activity(
        type=nextcord.ActivityType.watching, name="label supplies..."
    ),
)


for cog in os.listdir("./cogs"):
    if cog.endswith(".py"):
        bot.load_extension("cogs." + cog[:-3])


bot.loop.run_until_complete(bot.sql.init())
bot.loop.run_until_complete(bot.prepare_cache())
bot.run(cfg.TOKEN)
