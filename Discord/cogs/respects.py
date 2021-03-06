
import discord
from discord.ext import commands

## import astropy.modeling
import matplotlib
import numpy
## import scipy

from utilities import checks

def setup(bot):
	bot.add_cog(Respects(bot))

class Respects:
	
	def __init__(self, bot):
		self.bot = bot
		self.bot.loop.create_task(self.initialize_database())
	
	async def initialize_database(self):
		await self.bot.connect_to_database()
		await self.bot.db.execute("CREATE SCHEMA IF NOT EXISTS respects")
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS respects.stats (
				stat	TEXT PRIMARY KEY, 
				value	BIGINT
			)
			"""
		)
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS respects.users (
				user_id		BIGINT PRIMARY KEY, 
				respects	BIGINT
			)
			"""
		)
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS respects.guilds (
				guild_id	BIGINT PRIMARY KEY, 
				respects	BIGINT
			)
			"""
		)
		await self.bot.db.execute(
			"""
			INSERT INTO respects.stats (stat, value)
			VALUES ('total', 0)
			ON CONFLICT (stat) DO NOTHING
			"""
		)
	
	def __local_check(self, ctx):
		return checks.not_forbidden_predicate(ctx)
	
	@commands.group(aliases = ["respect"], invoke_without_command = True)
	async def respects(self, ctx):
		'''
		Press F to Pay Respects
		https://knowyourmeme.com/memes/press-f-to-pay-respects
		'''
		await ctx.invoke(ctx.bot.get_command("help"), ctx.invoked_with)
	
	@respects.command()
	async def paid(self, ctx):
		'''
		Respects paid
		Record of respects paid by each user began on 2016-12-20
		Record of respects paid by each server began on 2018-09-04
		'''
		user_respects = await ctx.bot.db.fetchval("SELECT respects FROM respects.users WHERE user_id = $1", 
													ctx.author.id) or 0
		if ctx.guild:
			guild_respects = await ctx.bot.db.fetchval("SELECT respects FROM respects.guilds WHERE guild_id = $1", 
														ctx.guild.id) or 0
		total_respects = await ctx.bot.db.fetchval("SELECT value FROM respects.stats WHERE stat = 'total'")
		response = f"You have paid {user_respects:,} respects\n"
		if ctx.guild:
			response += f"This server has paid {guild_respects:,} respects\n"
		response += f"A total of {total_respects:,} respects have been paid"
		await ctx.embed_reply(response)
	
	@respects.command()
	async def pay(self, ctx):
		'''
		Pay Respects
		Can also be triggered with 'f' or 'F'
		'''
		total_respects = await ctx.bot.db.fetchval(
								"""
								UPDATE respects.stats
								SET value = value + 1
								WHERE stat = 'total'
								RETURNING value
								"""
							)
		if ctx.guild:
			guild_respects = await ctx.bot.db.fetchval(
									"""
									INSERT INTO respects.guilds (guild_id, respects)
									VALUES ($1, 1)
									ON CONFLICT (guild_id) DO
									UPDATE SET respects = guilds.respects + 1
									RETURNING respects
									""", 
									ctx.guild.id
								)
		user_respects = await ctx.bot.db.fetchval(
							"""
							INSERT INTO respects.users (user_id, respects)
							VALUES ($1, 1)
							ON CONFLICT (user_id) DO
							UPDATE SET respects = users.respects + 1
							RETURNING respects
							""", 
							ctx.author.id
						)
		suffix = ctx.bot.inflect_engine.ordinal(user_respects)[len(str(user_respects)):]
		response = f"{ctx.author.mention} has paid their respects for the {user_respects:,}{suffix} time\n"
		if ctx.guild:
			response += f"Total respects paid in this server: {guild_respects:,}\n"
		response += f"Total respects paid so far: {total_respects:,}"
		await ctx.embed_reply(response)
	
	@respects.command(aliases = ["statistics"])
	async def stats(self, ctx):
		'''Statistics'''
		total_respects = await ctx.bot.db.fetchval("SELECT value FROM respects.stats WHERE stat = 'total'")
		respects_paid = []
		async with ctx.bot.database_connection_pool.acquire() as connection:
			async with connection.transaction():
				# Postgres requires non-scrollable cursors to be created
				# and used in a transaction.
				async for record in connection.cursor("SELECT * FROM respects.users"):
					respects_paid.append(record["respects"])
		# TODO: Optimize
		filename = ctx.bot.data_path + "/temp/respects.png"
		# TODO: Fit curve
		## n, bins, _ = matplotlib.pyplot.hist(respects_paid, log = True, 
		matplotlib.pyplot.hist(respects_paid, log = True, 
								bins = numpy.logspace(numpy.log10(1), numpy.log10(max(respects_paid)), 50))
		## bin_centers = bins[:-1] + numpy.diff(bins) / 2
		## def func(x, a, b, c):
		##	return a * numpy.exp(-b * x) + c
		## popt, _ = scipy.optimize.curve_fit(func, bin_centers[1:], n[1:], p0 = (1000, 1, 1), maxfev = 100000)
		## t_init = astropy.modeling.models.Gaussian1D()
		## fit_t = astropy.modeling.fitting.LevMarLSQFitter()
		## t = fit_t(t_init, bin_centers, n)
		## x_interval_for_fit = numpy.linspace(bins[0], bins[-1], 10000)
		## matplotlib.pyplot.plot(x_interval_for_fit, func(x_interval_for_fit, *popt), color = "red")
		axes = matplotlib.pyplot.gca()
		axes.set_xscale("log")
		## axes.set_ylim(0.8)
		axes.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
		axes.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
		axes.set_xlabel("Respects Paid")
		axes.set_ylabel("People")
		matplotlib.pyplot.savefig(filename)
		matplotlib.pyplot.clf()
		await ctx.embed_reply(fields = (("Total respects paid", f"{total_respects:,}"), 
										("People who paid respects", f"{len(respects_paid):,}")),
								image_url = "attachment://respects.png", file = discord.File(filename))
	
	@respects.command(aliases = ["most"])
	async def top(self, ctx):
		'''Top respects paid'''
		fields = []
		async with ctx.bot.database_connection_pool.acquire() as connection:
			async with connection.transaction():
				# Postgres requires non-scrollable cursors to be created
				# and used in a transaction.
				async for record in connection.cursor("SELECT * FROM respects.users ORDER BY respects DESC LIMIT 10"):
					user = ctx.bot.get_user(record["user_id"])
					if not user:
						user = await ctx.bot.get_user_info(record["user_id"])
					fields.append((str(user), f"{record['respects']:,}"))
		await ctx.embed_reply(title = "Top Respects Paid", fields = fields)

