# import traceback
from os import listdir

import nextcord
from functions import get_traceback
from nextcord.ext import commands


class ErrorHandler(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        args = ctx.args[2:]
        kwargs = ctx.kwargs
        if type(error) == commands.errors.CommandNotFound:
            print(error)
            pass
        elif type(error) == commands.errors.CommandInvokeError:
            await self.on_command_error(ctx, error.original)
        elif type(error) == commands.errors.ExtensionNotFound:
            await ctx.send(
                embed=nextcord.Embed(
                    color=nextcord.Color.red(),
                    title="Oops, couldn't find this extension",
                    description=f"I couldn't find the extension ``{args[0]}``, please "
                    "retry.",
                )
            )
        elif type(error) == commands.errors.ExtensionNotLoaded:
            if args[0] + ".py" in listdir("./cogs"):
                await ctx.send(
                    embed=nextcord.Embed(
                        color=nextcord.Color.red(),
                        title="Oops, extension isn't loaded",
                        description=f"The extension `{args[0]}` is not loaded, so you "
                        "can't unload nor reload it.",
                    )
                )
            else:
                await ctx.send(
                    embed=nextcord.Embed(
                        color=nextcord.Color.red(),
                        title="Oops, couldn't find this extension",
                        description=f"I couldn't find the extension ``{args[0]}```, "
                        "please retry.",
                    )
                )
        elif type(error) == commands.errors.MissingRequiredArgument:
            await ctx.send(
                embed=nextcord.Embed(
                    color=nextcord.Color.red(),
                    title="Oops, you forgot an argument",
                    description="The command is missing the parameter"
                    f"``{error.param.name}``.\nCommand usage: "
                    f"``{self.client.command_prefix}{ctx.command.name} "
                    f"{ctx.command.signature}``",
                )
            )
        elif type(error) == commands.errors.BadArgument:
            await ctx.send(
                embed=nextcord.Embed(
                    color=nextcord.Color.red(),
                    title="Oops, you provided a bad argument",
                    description=f"This is a frequent error.\nCorrect command usage: "
                    f"``{self.client.command_prefix}{ctx.command.name} "
                    f"{ctx.command.signature}``",
                )
            )
        elif type(error) == nextcord.errors.NotFound:
            print(error.code)
            if error.code == 10013:
                await ctx.send(
                    embed=nextcord.Embed(
                        color=nextcord.Color.red(),
                        title="Oops, user not found",
                        description="The user you were looking for couldn't be found. "
                        "Please make sure you are using a correct ID.",
                    )
                )
            else:
                await ctx.send(
                    embed=nextcord.Embed(
                        color=nextcord.Color.red(),
                        title="Oops, it hasn't been found",
                        description=(
                            error.text
                            if error.text
                            else "No precise error were given, sorry."
                        ),
                    )
                )
        elif type(error) == commands.errors.BotMissingPermissions:
            perms = error.missing_perms
            await ctx.send(
                embed=nextcord.Embed(
                    color=nextcord.Color.red(),
                    title="Oops, I'm missing some permissions",
                    description="I need these permissions to be able to properly run th"
                    f"is command: ``{'``, ``'.join(perms).replace('_', ' ').title()}``",
                )
            )
        elif type(error) == commands.errors.MissingPermissions:
            perms = error.missing_perms
            await ctx.send(
                embed=nextcord.Embed(
                    color=nextcord.Color.red(),
                    title="Oops, you are missing some permissions",
                    description="You need these permissions to be able to run this "
                    f"command: ``{'``, ``'.join(perms).replace('_', ' ').title()}``",
                )
            )
        else:
            print(ctx.invoked_with, ctx, type(error).__name__, error)
            print(args, kwargs)
            print(get_traceback(error))
            emb = nextcord.Embed(
                color=nextcord.Color.red(),
                title="Oops, an uncaught exception occured",
                description=f"`{type(error).__name__}`\n```py\n{error}\n```",
            )
            await ctx.send(embed=emb)


def setup(client):
    client.add_cog(ErrorHandler(client))
