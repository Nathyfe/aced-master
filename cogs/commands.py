import config as cfg
import nextcord
import views
from nextcord.ext import commands


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(
        guild_ids=[cfg.MAIN_GUILD, "999707097669316749"],
        default_member_permissions=8,
        force_global=True,
    )
    async def enable(
        self,
        interaction,
        server_id: str = nextcord.SlashOption(
            "server_id", "The ID of the server to enable"
        ),
        api_key: str = nextcord.SlashOption(
            "api_key", "The API Key of the reseller for that server"
        ),
    ):
        if interaction.user.id not in [608745022321328158, 465129603208577044]:
            return await interaction.send("Operation not permitted.")

        try:
            server_id = int(server_id)
        except TypeError:
            return

        await self.bot.sql.enable_server(server_id, api_key)
        await interaction.send(
            "That server has been enabled and the API key has been set."
        )

    @nextcord.slash_command(
        guild_ids=[cfg.MAIN_GUILD],
        default_member_permissions=8,
        force_global=True,
    )
    async def disable(
        self,
        interaction,
        server_id: str = nextcord.SlashOption(
            "server_id", "The ID of the server to disable"
        ),
    ):
        if interaction.user.id not in [608745022321328158, 465129603208577044]:
            return await interaction.send("Operation not permitted.")

        try:
            server_id = int(server_id)
        except TypeError:
            return

        await self.bot.sql.disable_server(server_id)
        await interaction.send("That server has been disabled.")

    @nextcord.slash_command(
        guild_ids=[cfg.TEST_GUILD], force_global=True, dm_permission=False
    )
    async def order(self, interaction):
        p = await self.bot.sql.get_current_guild_prices(interaction.guild.id)
        if not p:
            return await interaction.send("Labels are not set up yet on this server...")
        await interaction.send(
            view=views.SelectLabelType(self.bot, p, interaction.user)
        )

    @nextcord.slash_command(
        guild_ids=[cfg.TEST_GUILD],
        force_global=True,
        dm_permission=False,
        default_member_permissions=8,  # Admins only
    )
    async def setup(self, interaction):
        prices = await self.bot.sql.get_current_guild_prices(interaction.guild.id)
        labels_set = {i["label_id"] for i in prices}
        labels_notset = {i["id"] for i in self.bot.labels if i["id"] not in labels_set}

        if len(labels_notset) == 0:
            await interaction.send(
                embed=nextcord.Embed(
                    description="All prices are currently set. If you click Continue, \
                    **ALL CURRENT PRICES WILL BE DELETED**, and you will need to set them again."
                ),
                view=views.ConfirmResetSetup(prices, interaction.user),
            )
        elif len(labels_set) > 0:
            await interaction.send(
                embed=nextcord.Embed(
                    description="Some labels aren't set on your server, what would you like to do?"
                ),
                view=views.PromptResetOrContinue(prices, interaction.user),
            )
        else:  # Nothing set
            await views.interactive_setup(prices, interaction)

    @nextcord.slash_command(
        guild_ids=[cfg.TEST_GUILD],
        force_global=True,
        dm_permission=False,
        default_member_permissions=8,  # Admins only
    )
    async def userbalance(self, interaction):
        ...

    @userbalance.subcommand()
    async def add(self, interaction, user: nextcord.Member, amount: int):
        await self.bot.sql.add_balance(user.guild.id, user.id, amount)
        await interaction.send(f"Added {amount} to {user.name}.")

    @userbalance.subcommand()
    async def remove(self, interaction, user: nextcord.Member, amount: int):
        a = await self.bot.sql.remove_balance(user.guild.id, user.id, amount)
        if a is False:
            return await interaction.send(
                "Cannot remove {amount} from {user.name}. Insufficient funds on their balance."
            )
        await interaction.send(f"Removed {amount} from {user.name}.")

    @nextcord.slash_command(
        guild_ids=[cfg.TEST_GUILD], force_global=True, dm_permission=False
    )
    async def balance(self, interaction):
        c = await self.bot.sql.get_balance(interaction.guild.id, interaction.user.id)
        bal = c[0]["balance"] if c else 0

        return await interaction.send(f"Your current balance is: `{bal}`.")


def setup(bot):
    bot.add_cog(Commands(bot))
