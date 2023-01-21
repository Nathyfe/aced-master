from os import listdir

import config as cfg
import functions as fct
import nextcord
from nextcord.ext import commands


class Developer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(fct.is_dev)
    async def load(self, ctx, extension):
        self.bot.load_extension("cogs." + extension)
        await ctx.send(f"Successfully loaded ``{extension}``.")

    @commands.command()
    @commands.check(fct.is_dev)
    async def unload(self, ctx, extension):
        self.bot.unload_extension("cogs." + extension)
        await ctx.send(f"Successfully unloaded ``{extension}``.")

    @commands.command(aliases=["r"])
    @commands.check(fct.is_dev)
    async def reload(self, ctx, extension="*"):
        if extension == "*":
            reloaded = []
            for cog in listdir("./cogs"):
                if cog.endswith(".py"):
                    self.bot.reload_extension("cogs." + cog[:-3])
                    reloaded.append(cog[:-3])
            await ctx.send(f"Successfully reloaded ``{'``, ``'.join(reloaded)}``.")
        else:
            self.bot.reload_extension("cogs." + extension)
            await ctx.send(f"Successfully reloaded ``{extension}``.")

    @commands.command(name="eval", aliases=["seval"])
    @commands.check(fct.is_dev)
    async def _eval(self, ctx, *, _program):
        program = fct.cleanup_code(_program)
        program = program.replace("\n", "\n  ")
        try:
            res = {
                "ctx": ctx,
                "bot": self.bot,
                "nextcord": nextcord,
                "functions": fct,
                "cfg": cfg,
            }
            if "\n" in program or "return" in program:
                to_run = f"async def evalcode():\n  {program}"
            else:
                to_run = f"async def evalcode():\n  return {program}"

            exec(to_run, res)

            codefunc = res["evalcode"]
            result = await codefunc()
            result = str(result)
            if ctx.invoked_with == "eval":
                if self.bot.ws.token in result:
                    result = result.replace(self.bot.ws.token, "[token]")

                program = program.replace("\n  ", "\n")
                codemb = nextcord.Embed(color=nextcord.Color.green())

                suite = False
                for i in fct.textSlicer(program, 1014):
                    codemb.add_field(
                        name="Input" + (" (cont.)" if suite else ""),
                        value=f"```py\n{i}\n```",
                        inline=False,
                    )
                    suite = True
                suite = False
                for i in fct.textSlicer(result, 1014):
                    codemb.add_field(
                        name="Output" + (" (cont.)" if suite else ""),
                        value=f"```py\n{i}\n```",
                        inline=False,
                    )
                    suite = True
                await ctx.send(embed=codemb)
        except Exception as e:
            program = program.replace("\n  ", "\n")
            codemb = nextcord.Embed(color=nextcord.Color.red())
            suite = False
            for i in fct.textSlicer(program, 1014):
                codemb.add_field(
                    name="Input" + (" (cont.)" if suite else ""),
                    value=f"```py\n{i}\n```",
                    inline=False,
                )
                suite = True
            suite = False
            error = fct.get_traceback(e)
            error.replace("gurvan", "myname")
            for i in fct.textSlicer(error, 1014):
                codemb.add_field(
                    name="Error" + (" (cont.)" if suite else ""),
                    value=f"```py\n{i}\n```",
                    inline=False,
                )
                suite = True
            await ctx.send(embed=codemb)

    @commands.command(aliases=["sd"])
    @commands.check(fct.is_dev)
    async def shutdown(self, ctx):
        await ctx.send("Shutdowning bot...")
        await self.bot.logout()


def setup(bot):
    bot.add_cog(Developer(bot))
