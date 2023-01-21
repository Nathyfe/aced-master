# from asyncio import sleep
# from pprint import pprint

import asyncio
import json

import functions as fct
from nextcord import ButtonStyle, Color, Embed, File, SelectOption, ui


class SelectLabelType(ui.View):
    def __init__(self, bot, prices, user):
        super().__init__()

        self.add_item(SelectLabelTypeDropdown(bot, prices, user))


class SelectLabelTypeDropdown(ui.Select):
    def __init__(self, bot, prices, user):
        super().__init__(placeholder="Please choose label type...")

        labels = {i["label_id"] for i in prices}
        self.options = [
            SelectOption(label=i["name"], value=i["id"])
            for i in bot.labels
            if i["id"] in labels
        ]
        self.user = user

    async def callback(self, interaction):
        if interaction.user != self.user:
            return
        self.infos = {}
        self.infos["type"] = self.values[0]

        embed = Embed(title="Shipping label creation")
        the_label = interaction.client.getLabelById(self.values[0])
        embed.add_field(name="Label type", value=the_label["name"])

        print("TYPE", self.infos["type"])
        if self.infos["type"] not in [
            "4c0980a2-a73b-4bf1-915e-b3371d38a4b3"
        ]:  # RoyalMail
            interaction.message = await interaction.edit(
                content="Please enter package weight (in lbs)", embed=embed, view=None
            )

            def check(msg):
                return (
                    msg.author.id == interaction.user.id
                    and msg.channel.id == interaction.channel.id
                )

            mess = await interaction.client.wait_for("message", check=check)
            try:
                weight = int(mess.content)
            except TypeError:
                return await mess.reply(
                    "This is an invalid weight. Please try again. Just send a number, without units.\nCreation aborted."
                )
            if interaction.client.getLabelPrice(the_label["id"], weight) == -1:
                return await mess.reply(
                    f"Weight must be between \
                    {the_label['weights'][0]['min']} and {the_label['weights'][-1]['max']} lbs.\nCreation aborted."
                )
            self.infos["weight"] = weight

            embed.add_field(name="Weight", value=f"{weight} lbs")

        interaction.message = await interaction.edit(
            content="",
            embed=embed,
            view=FillLabelForms(interaction.client, self.infos, self.user),
        )
        self.view.stop()


class FillLabelForms(ui.View):
    def __init__(self, bot, infos, user):
        super().__init__()
        self.infos = infos
        self.user = user

        self.fields = {
            "FromCountry": {
                "label": "Sender country (full country name)",
                "required": True,
                "validate": (lambda x: x in bot.countries.values()),
            },
            "FromName": {"label": "Sender name", "required": True},
            "FromCompany": {"label": "Sender company", "required": False},
            "FromStreet": {
                "label": "Sender street address",
                "required": True,
                "max_length": 200,
            },
            "FromStreet2": {
                "label": "Sender secondary address",
                "required": False,
                "max_length": 200,
            },
            "FromCity": {
                "label": "Sender city",
                "required": True,
            },
            "FromState": {
                "label": "Sender state (two letter state code)",
                "required": True,
                "min_length": 2,
                "max_length": 2,
                "validate": (lambda x: x in bot.states.keys()),
            },
            "FromZip": {"label": "Sender ZIP code", "required": True, "max_length": 9},
            "ToCountry": {
                "label": "Receiver country (full country name)",
                "required": True,
                "validate": (lambda x: x in bot.countries.values()),
            },
            "ToName": {
                "label": "Receiver name",
                "required": True,
            },
            "ToCompany": {
                "label": "Receiver company",
                "required": False,
            },
            "ToStreet": {
                "label": "Receiver street address",
                "required": True,
                "max_length": 200,
            },
            "ToStreet2": {
                "label": "Receiver secondary address",
                "required": False,
                "max_length": 200,
            },
            "ToCity": {
                "label": "Receiver city",
                "required": True,
            },
            "ToState": {
                "label": "Receiver state (two letter state code)",
                "required": True,
                "min_length": 2,
                "max_length": 2,
                "validate": (lambda x: x in bot.states.keys()),
            },
            "ToZip": {"label": "Receiver ZIP code", "required": True, "max_length": 9},
        }

        if self.infos["type"] in [
            "998754e5-efb9-4a9f-ac44-5411b1dc3bc3",  # USPS Priority V4 OLD
            "e231706d-3613-41f3-831f-d50a75cd474a",  # USPS Priority V4
            "7d1a2971-bb0b-41e3-b42c-cd0e30af43cb",  # USPS Express V4 OLD
            "2555c1be-32e2-4fd7-8020-3f980ebec6aa",  # USPS Express V4
            "23f036ee-d8c4-4cef-a5eb-6423b33b754d",  # USPS First Class V4 OLD
            "24ea82b4-411a-4c61-8647-b9eec19cf91d",  # USPS First Class V4
            "575eeafd-5fb2-4d3d-903e-4fc0396b2a48",  # USPS Priority
            "0d5c057a-788f-4f10-9cdb-754ba8e17384",  # USPS Express
            "266f57b5-abbd-46e2-b78b-823275d26bfd",  # FedEx Ground
            "72f18c4c-a6c1-4fde-b726-9dc764995336",  # UPS Ground
        ]:
            self.infos["FromCountry"] = "US"
            self.infos["ToCountry"] = "US"
            self.fields["FromCountry"]["hide"] = True
            self.fields["ToCountry"]["hide"] = True

        if self.infos["type"] in ["4c0980a2-a73b-4bf1-915e-b3371d38a4b3"]:  # RoyalMail
            self.infos["FromCountry"] = "UK"
            self.infos["ToCountry"] = "UK"
            self.fields["FromCountry"]["hide"] = True
            self.fields["ToCountry"]["hide"] = True
            self.fields["FromState"]["hide"] = True
            self.fields["ToState"]["hide"] = True
            self.fields["FromState"]["required"] = False
            self.fields["ToState"]["required"] = False

    async def check_confirm_button(self):
        for i in range(4):
            if self.children[i].style != ButtonStyle.green:
                self.children[4].style = ButtonStyle.red
                self.children[4].disabled = True
                break
        else:
            self.children[4].style = ButtonStyle.green
            self.children[4].disabled = False

    @ui.button(label="Sender info")
    async def sender_info(self, button, interaction):
        if self.user != interaction.user:
            return

        await interaction.response.send_modal(
            FillInfos(
                button, "Sender information", "FromCountry", "FromName", "FromCompany"
            )
        )

    @ui.button(label="Sender address")
    async def sender_address(self, button, interaction):
        if self.user != interaction.user:
            return

        await interaction.response.send_modal(
            FillInfos(
                button,
                "Sender address",
                "FromStreet",
                "FromStreet2",
                "FromCity",
                "FromState",
                "FromZip",
            )
        )

    @ui.button(label="Receiver info")
    async def receiver_info(self, button, interaction):
        if self.user != interaction.user:
            return

        await interaction.response.send_modal(
            FillInfos(
                button, "Receiver information", "ToCountry", "ToName", "ToCompany"
            )
        )

    @ui.button(label="Receiver address")
    async def receiver_address(self, button, interaction):
        if self.user != interaction.user:
            return

        await interaction.response.send_modal(
            FillInfos(
                button,
                "Receiver address",
                "ToStreet",
                "ToStreet2",
                "ToCity",
                "ToState",
                "ToZip",
            )
        )

    @ui.button(label="Confirm", style=ButtonStyle.red, row=1, disabled=True)
    async def confirm(self, button, interaction):
        if self.user != interaction.user:
            return

        for field, vals in self.fields.items():
            if vals["required"] and field not in self.infos:
                return await interaction.send(
                    f"Please fill in all the forms. Missing {field}"
                )

        embed = Embed(
            title="Confirm embed creation",
            description="Please make sure all information below are correct then press Confirm.",
        )
        embed.add_field(
            name="Label type",
            value=interaction.client.getLabelById(self.infos["type"])["name"],
        )
        if "weight" in self.infos:
            embed.add_field(name="Weight", value=str(self.infos["weight"]) + f'{" lbs" if not self.infos["type"] in [ "23f036ee-d8c4-4cef-a5eb-6423b33b754d", "24ea82b4-411a-4c61-8647-b9eec19cf91d" ] else " ozs"}')
            gprice = await interaction.client.sql.get_price(
                interaction.guild.id, self.infos["type"], self.infos["weight"]
            )
        else:
            gprice = await interaction.client.sql.get_price(
                interaction.guild.id, self.infos["type"], 0
            )

        self.infos["price"] = gprice[0]["price"]
        embed.add_field(
            name="Price",
            value="$" + str(gprice[0]["price"]),
        )

        userbal = await interaction.client.sql.get_balance(
            interaction.guild.id, interaction.user.id
        )
        if not userbal or userbal[0]["balance"] < gprice[0]["price"]:
            return await interaction.send("You do not have enough credits.")

        def format(*args):
            return "\n".join(
                [
                    "• **" + self.fields[k]["label"] + ":** " + v
                    for k, v in self.infos.items()
                    if k in args
                ]
            )

        embed.add_field(
            name="Sender information",
            value=format("FromCountry", "FromName", "FromCompany"),
            inline=False,
        )
        embed.add_field(
            name="Sender address",
            value=format(
                "FromStreet",
                "FromStreet2",
                "FromCity",
                "FromState",
                "FromZip",
            ),
            inline=False,
        )
        embed.add_field(
            name="Receiver information",
            value=format("ToCountry", "ToName", "ToCompany"),
            inline=False,
        )
        embed.add_field(
            name="Receiver address",
            value=format("ToStreet", "ToStreet2", "ToCity", "ToState", "ToZip"),
            inline=False,
        )
        await interaction.send(
            embed=embed, view=ConfirmCreation(self, interaction, self.user)
        )

    @ui.button(label="Cancel", style=ButtonStyle.red, row=1)
    async def cancel(self, button, interaction):
        if self.user != interaction.user:
            return

        await interaction.send("Label creation cancelled...")
        await self.stop(interaction)

    async def stop(self, interaction):
        for c in self.children:
            c.disabled = True

        await interaction.message.edit(view=self)
        super().stop()


def getValOr(dic, idx, default=None):
    if idx in dic:
        return dic[idx]
    else:
        return default


class FillInfos(ui.Modal):
    def __init__(self, button, title, *fields):
        super().__init__(title)
        self.button = button
        self.parent_view = self.button.view

        self.fields = {
            f: self.parent_view.fields[f]
            for f in fields
            if not self.parent_view.fields[f].get("hide", False)
        }
        self.inputs = {}
        for n, f in self.fields.items():
            self.inputs[n] = ui.TextInput(
                **{
                    "max_length": 100,
                    "default_value": getValOr(self.parent_view.infos, n),
                    **{k: v for k, v in f.items() if k not in ["validate", "hide"]},
                }
            )
            self.add_item(self.inputs[n])

    async def callback(self, interaction):
        self.button.style = ButtonStyle.green
        for name, vals in self.fields.items():
            if "validate" not in vals or (
                "validate" in vals and vals["validate"](self.inputs[name].value)
            ):
                self.parent_view.infos[name] = self.inputs[name].value
            else:
                if name in self.parent_view.infos:
                    self.parent_view.infos.pop(name)
                self.button.style = ButtonStyle.red

        await self.parent_view.check_confirm_button()
        await interaction.edit(view=self.parent_view)


class ConfirmCreation(ui.View):
    def __init__(self, infos_view, pinter, user):
        super().__init__()
        self.pinter = pinter
        self.pview = infos_view
        self.infos = infos_view.infos
        self.user = user

    @ui.button(label="Confirm", style=ButtonStyle.green)
    async def confirm(self, button, interaction):
        if self.user != interaction.user:
            return

        price = self.infos.pop("price")
        if self.infos["type"] in [
            "4c0980a2-a73b-4bf1-915e-b3371d38a4b3"
        ]:  # RoyalMail # Bypassing bug in API
            self.infos["weight"] = 0
        await self.pview.stop(self.pinter)
        await self.stop(interaction)
        bal = await interaction.client.sql.get_balance(
            interaction.guild.id, interaction.user.id
        )
        if not bal or bal[0]["balance"] < price:
            return await interaction.send(
                "You do not have enough balance to buy this label."
            )

        await interaction.response.defer(with_message=True)
        status, resp = await fct.createLabel(interaction, self.infos)
        if status != 200 or not resp["Data"]:
            return await interaction.send(
                "An error occured: ```json\n" + json.dumps(resp, indent=4) + "\n```"
            )
        await interaction.client.sql.remove_balance(
            interaction.guild.id, interaction.user.id, price
        )
        resp_id = resp["Data"]["Order"]["ID"]
        await interaction.send(
            embed=Embed(
                description=f"Your label has been ordered. Here is your order ID: `{resp_id}`.\
            \nYou will receive your receipt soon.",
                color=Color.green(),
            )
        )
        api_key = (await interaction.client.sql.get_api_key(interaction.guild.id))[0][
            "api_key"
        ]

        await asyncio.sleep(120)

        status, pdf = await fct.getPDF(resp_id, api=api_key)
        if status != 200:
            await interaction.send(
                "The order receipt isn't ready yet, you will receive it once it's ready."
            )
            await interaction.client.sql.register_order(
                resp_id, interaction.guild.id, interaction.user.id, 0
            )
        else:
            try:
                await interaction.user.send(
                    "Here is your order receipt:", file=File(pdf)
                )
            except Exception:
                await interaction.send(
                    "Couldn't DM you. Here is your order receipt:", file=File(pdf)
                )
            finally:
                await interaction.client.sql.register_order(
                    resp_id, interaction.guild.id, interaction.user.id, 1
                )

    @ui.button(label="Cancel", style=ButtonStyle.red)
    async def cancel(self, button, interaction):
        if self.user != interaction.user:
            return

        await interaction.send(
            embed=Embed(description="Creation aborted, please edit necessary infos.")
        )
        await self.stop(interaction)

    async def stop(self, interaction):
        for c in self.children:
            c.disabled = True

        await interaction.message.edit(view=self)
        super().stop()


class ConfirmResetSetup(ui.View):
    def __init__(self, current, user, conf=1):
        super().__init__()
        self.currentp = current
        self.conf = conf
        self.user = user

    @ui.button(label="Confirm", style=ButtonStyle.green)
    async def confirm(self, button, interaction):
        if self.user != interaction.user:
            return

        if self.conf == 1:
            await interaction.send(
                embed=Embed(
                    description="**ALL CURRENT SETUP WILL BE DELETED**, are you sure?",
                    color=Color.orange(),
                ),
                view=ConfirmResetSetup(self.currentp, self.user, 2),
            )
            await self.stop(interaction)
        elif self.conf > 1:
            await self.stop(interaction)
            await interactive_setup([], interaction)

    @ui.button(label="Cancel", style=ButtonStyle.red)
    async def cancel(self, button, interaction):
        if self.user != interaction.user:
            return

        await interaction.send(
            embed=Embed(description="Setup aborted.", color=Color.red())
        )
        await self.stop(interaction)

    async def stop(self, interaction):
        for c in self.children:
            c.disabled = True

        await interaction.message.edit(view=self)
        super().stop()


class PromptResetOrContinue(ui.View):
    def __init__(self, current, user):
        super().__init__()
        self.currentp = current
        self.user = user

    @ui.button(label="Continue", style=ButtonStyle.green)
    async def _continue(self, button, interaction):
        if self.user != interaction.user:
            return

        await self.stop(interaction)
        await interactive_setup(self.currentp, interaction)

    @ui.button(label="Reset", style=ButtonStyle.red)
    async def reset(self, button, interaction):
        if self.user != interaction.user:
            return

        await interaction.send(
            embed=Embed(
                description="**ALL CURRENT SETUP WILL BE DELETED**, are you sure?",
                color=Color.orange(),
            ),
            view=ConfirmResetSetup([], self.user, 2),
        )
        await self.stop(interaction)

    @ui.button(label="Cancel", style=ButtonStyle.red)
    async def cancel(self, button, interaction):
        if self.user != interaction.user:
            return

        await interaction.send(
            embed=Embed(description="Setup aborted.", color=Color.red())
        )
        await self.stop(interaction)

    async def stop(self, interaction):
        for c in self.children:
            c.disabled = True

        await interaction.message.edit(view=self)
        super().stop()


async def intinput(interaction):
    def check(msg):
        return (
            msg.author.id == interaction.user.id
            and msg.channel.id == interaction.channel.id
        )

    mess = await interaction.client.wait_for("message", check=check)
    try:
        price = float(mess.content)
    except ValueError:
        await mess.delete()
        await mess.reply(
            "This is an invalid price. Please send a number (with `.` as decimal separator), without units.",
            delete_after=5,
        )
        return intinput(interaction)

    await mess.delete()
    return price


async def interactive_setup(prices, interaction):
    await interaction.send("Starting interactive setup...")
    labels = interaction.client.labels
    emb = Embed(title="Summary of prices", description="Setting up...")
    emsg = await interaction.send(embed=emb)
    msg = await interaction.send("...")

    settings = {}
    prices = {i["label_id"] for i in prices}

    for idx, label in enumerate(labels):
        if label["id"] in prices:
            continue
        settings[label["id"]] = []
        for wrange in label["weights"]:
            await msg.edit(
                (
                    f"**{label['name']}**\n"
                    f"**Range:** {wrange['min']} lbs - {wrange['max']} lbs\n"
                    f"**Stock price:** {wrange['price']}\n\n"
                    "What price do you want to sell this for?"
                )
            )
            price = await intinput(interaction)
            settings[label["id"]].append(
                {
                    "min_weight": wrange["min"],
                    "max_weight": wrange["max"],
                    "price": price,
                }
            )
            line = f"{wrange['min']} lbs - {wrange['max']} lbs : ${price:.2f}"
            if len(emb.fields) <= idx:
                emb.add_field(name=label["name"], value=line, inline=False)
            else:
                field = emb.fields[idx]
                emb.set_field_at(
                    idx, name=field.name, value=field.value + "\n" + line, inline=False
                )
            await emsg.edit(embed=emb)

    await msg.delete()
    await emsg.delete()
    emb.description = Embed.Empty
    await interaction.client.sql.update_prices(interaction.guild.id, settings)
    await interaction.send("Setup completed.", embed=emb)
