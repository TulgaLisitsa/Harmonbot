
if __name__ == "__main__":
	
	print("Starting up Discord Harmonbot...")
	
	import discord
	from discord.ext import commands
	
	import aiohttp
	import asyncio
	import json
	import os
	import re
	import sys
	import traceback
	import youtube_dl
	
	import clients
	import credentials
	from clients import client
	from modules import conversions
	from modules import logging
	from modules import utilities
	from utilities import checks
	from utilities import errors
	from utilities import audio_player
	
	utilities.create_file('f', content = {"total" : 0})
	with open("data/f.json", 'r') as f_file:
		f_counter_info = json.load(f_file)
	
	mention_spammers = []
	
	@client.event
	async def on_ready():
		# data = await client.http.get(client.http.GATEWAY + "/bot")
		# print(data)
		print("Started up Discord {0} ({1})".format(str(client.user), client.user.id))
		if os.path.isfile("data/temp/restart_channel.json"):
			with open("data/temp/restart_channel.json", 'r') as restart_channel_file:
				restart_data = json.load(restart_channel_file)
			os.remove("data/temp/restart_channel.json")
			restart_channel = client.get_channel(restart_data["restart_channel"])
			await client.send_embed(restart_channel, ":thumbsup::skin-tone-2: Restarted")
			for voice_channel in restart_data["voice_channels"]:
				# asyncio.ensure_future(client.cogs["Audio"].start_player(client.get_channel(voice_channel[1])))
				text_channel = client.get_channel(voice_channel[1])
				if text_channel:
					client.cogs["Audio"].players[text_channel.guild.id] = audio_player.AudioPlayer(client, text_channel)
					await client.join_voice_channel(client.get_channel(voice_channel[0]))
		'''
		for folder in os.listdir("data/server_data"):
			with open("data/server_data/{}/settings.json".format(folder), 'r') as settings_file:
				data = json.load(settings_file)
			data["anti-spam"] = False
			with open("data/server_data/{}/settings.json".format(folder), 'w') as settings_file:
				json.dump(data, settings_file, indent = 4)
		'''
		for guild in client.guilds:
			utilities.create_folder("data/server_data/{}".format(guild.id))
			utilities.create_file("server_data/{}/settings".format(guild.id), content = {"anti-spam": False, "respond_to_bots": False})
			if guild.name:
				clean_name = re.sub(r"[\|/\\:\?\*\"<>]", "", guild.name) # | / \ : ? * " < >
				utilities.create_file("server_data/{}/{}".format(guild.id, clean_name))
			# TODO: DM if joined new server
			# TODO: DM if left server
		await clients.random_game_status()
		await clients.set_streaming_status(client)
		# await voice.detectvoice()
	
	@client.event
	async def on_server_join(server):
		utilities.create_folder("data/server_data/{}".format(server.id))
		utilities.create_file("server_data/{}/settings".format(server.id), content = {"anti-spam": False, "respond_to_bots": False})
		me = discord.utils.get(client.get_all_members(), id = clients.owner_id)
		await client.send_embed(me, None, title = "Joined Server", timestamp = server.created_at, thumbnail_url = server.icon_url, fields = (("Name", server.name), ("ID", server.id), ("Owner", str(server.owner)), ("Members", str(server.member_count)), ("Server Region", str(server.region))))
		clean_name = re.sub(r"[\|/\\:\?\*\"<>]", "", server.name) # | / \ : ? * " < >
		utilities.create_file("server_data/{}/{}".format(server.id, clean_name))
	
	@client.event
	async def on_server_remove(server):
		me = discord.utils.get(client.get_all_members(), id = clients.owner_id)
		await client.send_embed(me, None, title = "Left Server", timestamp = server.created_at, thumbnail_url = server.icon_url, fields = (("Name", server.name), ("ID", server.id), ("Owner", str(server.owner)), ("Members", str(server.member_count)), ("Server Region", str(server.region))))
	
	@client.event
	async def on_resumed():
		print("Discord Harmonbot: resumed")
	
	@client.event
	async def on_command(ctx):
		with open("data/stats.json", 'r') as stats_file:
			stats = json.load(stats_file)
		stats["commands_executed"] += 1
		stats["commands_usage"][ctx.command.name] = stats["commands_usage"].get(ctx.command.name, 0) + 1
		with open("data/stats.json", 'w') as stats_file:
			json.dump(stats, stats_file, indent = 4)
		utilities.create_folder("data/user_data/{}".format(ctx.message.author.id))
		utilities.create_file("user_data/{}/stats".format(ctx.message.author.id), content = {"commands_executed": 0, "points": 0, "respects_paid": 0})
		# TODO: Transfer respects paid data?
		clean_name = re.sub(r"[\|/\\:\?\*\"<>]", "", ctx.message.author.name) # | / \ : ? * " < >
		utilities.create_file("user_data/{}/{}".format(ctx.message.author.id, clean_name))
		with open("data/user_data/{}/stats.json".format(ctx.message.author.id), "r") as stats_file:
			stats = json.load(stats_file)
		stats["commands_executed"] += 1
		stats["points"] += 1
		with open("data/user_data/{}/stats.json".format(ctx.message.author.id), 'w') as stats_file:
			json.dump(stats, stats_file, indent = 4)
	
	@client.command(pass_context = True)
	@checks.is_owner()
	async def load(ctx, cog : str):
		'''Loads a cog'''
		try:
			client.load_extension("cogs." + cog)
		except Exception as e:
			await client.embed_reply(":thumbsdown::skin-tone-2: Failed to load `{}` cog\n"
			"{}: {}".format(cog, type(e).__name__, e))
		else:
			await client.embed_reply(":thumbsup::skin-tone-2: Loaded `{}` cog :gear:".format(cog))
			await client.delete_message(ctx.message)
	
	@client.command(pass_context = True)
	@checks.is_owner()
	async def unload(ctx, cog : str):
		'''Unloads a cog'''
		try:
			client.unload_extension("cogs." + cog)
		except Exception as e:
			await client.embed_reply(":thumbsdown::skin-tone-2: Failed to unload `{}` cog\n"
			"{}: {}".format(cog, type(e).__name__, e))
		else:
			await client.embed_reply(":ok_hand::skin-tone-2: Unloaded `{}` cog :gear:".format(cog))
			await client.delete_message(ctx.message)
	
	@client.command(pass_context = True)
	@checks.is_owner()
	async def reload(ctx, cog : str):
		'''Reloads a cog'''
		try:
			client.unload_extension("cogs." + cog)
			client.load_extension("cogs." + cog)
		except Exception as e:
			await client.embed_reply(":thumbsdown::skin-tone-2: Failed to reload `{}` cog\n"
			"{}: {}".format(cog, type(e).__name__, e))
		else:
			with open("data/stats.json", 'r') as stats_file:
				stats = json.load(stats_file)
			stats["cogs_reloaded"] += 1
			with open("data/stats.json", 'w') as stats_file:
				json.dump(stats, stats_file, indent = 4)
			await client.embed_reply(":thumbsup::skin-tone-2: Reloaded `{}` cog :gear:".format(cog))
			await client.delete_message(ctx.message)
	
	# TODO: log message edits
	
	@client.event
	async def on_message(message):
		
		# Log message
		source = "Direct Message" if isinstance(message.channel, discord.DMChannel) else "#{0.channel.name} ({0.channel.id}) [{0.guild.name} ({0.guild.id})]".format(message)
		logging.chat_logger.info("{0.created_at}: [{0.id}] {0.author.display_name} ({0.author.name}) ({0.author.id}) in {1}: {0.content} {0.embeds}".format(message, source))
		
		# Server specific settings
		if message.guild is not None:
			try:
				with open("data/server_data/{}/settings.json".format(message.guild.id), 'r') as settings_file:
					data = json.load(settings_file)
			except FileNotFoundError:
				# TODO: Handle/Fix, create new file with default settings
				data = {}
			if data.get("anti-spam") and len(message.mentions) > 10:
				global mention_spammers
				if message.author.id in mention_spammers:
					# TODO: Handle across different servers
					if message.guild.me.permissions_in(message.channel).kick_members:
						# TODO: Check hierarchy, if able to kick
						await client.send_message(message.author, "You were kicked from {} for spamming mentions".format(message.guild))
						await client.kick(message.author)
						await client.send_message(message.channel, "{} has been kicked for spamming mentions".format(message.author))
					else:
						await client.send_message(message.channel, "I need permission to kick members from the server to enforce anti-spam")
				else:
					await clients.embed_reply(message, ":warning: You will be kicked if you continue spamming mentions")
					mention_spammers.append(message.author.id)
					await asyncio.sleep(3600)
					mention_spammers.remove(message.author.id)
			if not data.get("respond_to_bots") and message.author.bot:
				return
		
		# Commands
		await client.process_commands(message)
		
		# Forward DMs
		if isinstance(message.channel, discord.DMChannel) and message.channel.user.id != clients.owner_id:
			me = discord.utils.get(client.get_all_members(), id = clients.owner_id)
			if message.author == client.user:
				try:
					await client.send_message(me, "To {0.channel.user}: {0.content} `{0.embeds}`".format(message))
				except discord.errors.HTTPException:
					await client.send_message(me, "To {0.channel.user}: `DM too long to forward`".format(message))
			else:
				await client.send_message(me, "From {0.author}: {0.content} `{0.embeds}`".format(message))
		
		# Ignore own and blank messages
		if message.author == client.user or not message.content:
			return
		
		# Other commands
		try:
			prefixes = client.command_prefix(client, message)
		except TypeError:
			prefixes = client.command_prefix
		prefix = discord.utils.find(message.content.startswith, prefixes)
		if prefix:
			command = message.content[len(prefix):]
			if command.startswith("test_on_message"):
				await client.send_message(message.channel, "Hello, World!")
			elif re.match(r"^(\w+)to(\w+)", command, re.I): # conversions
				if command.split()[0] in client.commands:
					return
				elif len(message.content.split()) == 1:
					await clients.embed_reply(message, "Please enter input")
				elif not utilities.is_number(message.content.split()[1]):
					await clients.embed_reply(message, "Syntax error")
				else:
					value = float(message.content.split()[1])
					units = re.match(r"^(\w+)to(\w+)", command, re.I)
					unit1 = units.group(1)
					unit2 = units.group(2)
					converted_temperature_value, temperature_unit1, temperature_unit2 = conversions.temperatureconversion(value, unit1, unit2)
					converted_mass_value = conversions.massconversion(value, unit1, unit2)
					if converted_temperature_value:
						converted_value = converted_temperature_value
						unit1 = temperature_unit1
						unit2 = temperature_unit2
					elif converted_mass_value:
						converted_value = converted_mass_value
					else:
						await clients.embed_reply(message, "Units, {} and/or {}, not found\nSee the conversions command".format(unit1, unit2))
						return
					await clients.embed_reply(message, "{} {} = {} {}".format(value, unit1, converted_value, unit2))
		
		# getprefix
		elif "getprefix" in message.content:
			await client.send_message(message.channel, "Prefixes: {}".format(' '.join(['`"{}"`'.format(prefix) for prefix in prefixes])))
		
		# help DM
		elif message.content.lower() == "help" and isinstance(message.channel, discord.DMChannel):
			await clients.embed_reply(message, "Please see {}help".format(prefixes[0]))
		
		# :8ball:
		elif message.content.startswith("\U0001f3b1") and "Games" in client.cogs:
			await client.send_message(message.channel, "{}: {}".format(message.author.display_name, ":8ball: {}".format(client.cogs["Games"]._eightball())))
		
		# f
		elif message.content.lower() == 'f':
			f_counter_info["total"] += 1
			f_counter_info[message.author.id] = f_counter_info.get(message.author.id, 0) + 1
			with open("data/f.json", 'w') as f_file:
				json.dump(f_counter_info, f_file, indent = 4)
			embed = discord.Embed(color = clients.bot_color)
			embed.description = "{} has paid their respects".format(message.author.display_name)
			embed.description += "\nTotal respects paid so far: {}".format(f_counter_info["total"])
			embed.description += "\nRecorded respects paid by {}: {}".format(message.author.display_name, f_counter_info[message.author.id]) # since 2016-12-20
			try:
				await client.send_message(message.channel, embed = embed)
			except discord.errors.Forbidden: # necessary?
				raise
			except discord.errors.HTTPException:
				await client.send_message(message.channel, embed.description)
		
		# Chatbot
		elif message.raw_mentions and client.user.id == message.raw_mentions[0] and message.clean_content.startswith('@'):
			# Handle @Harmonbot help
			bot_name = message.channel.me.display_name if isinstance(message.channel, discord.DMChannel) else message.guild.me.display_name
			if ' '.join(message.clean_content.split()[:2]).lower() == '@' + bot_name.lower() + " help":
				await clients.embed_reply(message, "Please see {}help".format(prefixes[0]))
				return
			mentionless_message = ' '.join(word for word in message.clean_content.split() if not word.startswith('@'))
			aiml_response = clients.aiml_kernel.respond(mentionless_message)
			# TODO: Handle brain not loaded?
			if aiml_response:
				await clients.embed_reply(message, aiml_response)
			else:
				games_cog = client.get_cog("Games")
				if games_cog:
					cleverbot_response = await games_cog.cleverbot_get_reply(mentionless_message)
					await clients.embed_reply(message, cleverbot_response)
	
	@client.event
	async def on_error(event_method, *args, **kwargs):
		type, value, _traceback = sys.exc_info()
		if type is discord.errors.Forbidden:
			for arg in args:
				if isinstance(arg, commands.context.Context):
					print("Missing Permissions for #{0.channel.name} in {0.guild.name}".format(arg.message))
					return
				elif isinstance(arg, discord.Message):
					print("Missing Permissions for #{0.channel.name} in {0.guild.name}".format(arg))
					return
		print('Ignoring exception in {}'.format(event_method), file = sys.stderr)
		traceback.print_exc()
		logging.errors_logger.error("Uncaught exception\n", exc_info = (type, value, _traceback))
	
	@client.event
	async def on_command_error(error, ctx):
		if isinstance(error, errors.NotOwner): return # not owner
		if isinstance(error, (commands.errors.CommandNotFound, commands.errors.DisabledCommand)): return # disabled or not found
		if isinstance(error, (errors.LichessUserNotFound)): return # handled with local error handler
		if isinstance(error, commands.errors.CommandInvokeError) and isinstance(error.original, youtube_dl.utils.DownloadError): return # handled with local error handler
		embed = discord.Embed(color = clients.bot_color)
		avatar = ctx.message.author.avatar_url or ctx.message.author.default_avatar_url
		embed.set_author(name = ctx.message.author.display_name, icon_url = avatar)
		if isinstance(error, (errors.NotServerOwner, errors.MissingPermissions)): # errors.NotOwner?
			embed.description = ":no_entry: You don't have permission to do that"
		elif isinstance(error, errors.MissingCapability):
			if "embed_links" in error.permissions:
				await ctx.bot.send_message(ctx.message.channel, "I don't have permission to do that here\nI need the permission(s): " + ', '.join(error.permissions))
				return
			embed.description = "I don't have permission to do that here\nI need the permission(s): " + ', '.join(error.permissions)
		elif isinstance(error, errors.PermittedVoiceNotConnected):
			embed.description = "I'm not in a voice channel\nPlease use `{}join` first".format(ctx.prefix)
		elif isinstance(error, errors.NotPermittedVoiceNotConnected):
			embed.description = "I'm not in a voice channel\nPlease ask someone with permission to use `{}join` first".format(ctx.prefix)
		elif isinstance(error, commands.errors.NoPrivateMessage):
			embed.description = "Please use that command in a server"
		elif isinstance(error, commands.errors.MissingRequiredArgument):
			embed.description = str(error).rstrip('.')
		elif isinstance(error, errors.NotPermitted):
			embed.description = ":no_entry: You don't have permission to use that command here"
		elif isinstance(error, commands.errors.BadArgument):
			embed.description = ":no_entry: Error: invalid input"
		elif isinstance(error, commands.errors.CommandInvokeError) and isinstance(error.original, discord.errors.HTTPException) and str(error.original) == "BAD REQUEST (status code: 400): You can only bulk delete messages that are under 14 days old.":
			embed.description = ":no_entry: Error: You can only bulk delete messages that are under 14 days old"
		if embed.description:
			await ctx.bot.send_message(ctx.message.channel, embed = embed) # check embed links permission
		elif isinstance(error, commands.errors.CommandInvokeError) and isinstance(error.original, (discord.errors.Forbidden)):
			print("Missing Permissions for #{0.channel.name} in {0.guild.name}".format(ctx.message))
		else:
			print("Ignoring exception in command {}".format(ctx.command), file = sys.stderr)
			traceback.print_exception(type(error), error, error.__traceback__, file = sys.stderr)
			logging.errors_logger.error("Uncaught exception\n", exc_info = (type(error), error, error.__traceback__))
	
	beta = any("beta" in arg.lower() for arg in sys.argv)
	if beta:
		client.command_prefix = '*'
		token = credentials.beta_token
	else:
		token = credentials.token
	
	try:
		if os.getenv("TRAVIS") and os.getenv("CI"):
			client.loop.create_task(client.start(token))
			client.loop.run_until_complete(asyncio.sleep(10))
		else:
			client.loop.run_until_complete(client.start(token))
	except aiohttp.errors.ClientOSError:
		pass
	finally:
		client.loop.run_until_complete(clients.shutdown_tasks())
		client.loop.close()
		os._exit(0)

