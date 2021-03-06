
import discord
from discord.ext import commands

import asyncio
import datetime
import json
import os
import random
import sys
from urllib import parse

import aiml
import aiohttp
from aiohttp import web
import asyncpg
import clarifai
import clarifai.rest
import dotenv
import imgurpython
import inflect
import pyowm
import raven
import requests
import tweepy
import wolframalpha
from wordnik import swagger, WordApi, WordsApi

from utilities.context import Context
from utilities import errors
from utilities.help_formatter import CustomHelpFormatter

# TODO: Relocate as Bot variables
beta = any("beta" in arg.lower() for arg in sys.argv)
data_path = "data/beta" if beta else "data"  # Moved, update all references to
user_agent = "Discord Bot"
library_files = "D:/Data (D)/Music/"
wait_time = 15.0
code_block = "```\n{}\n```"  # Moved, update all references to
py_code_block = "```py\n{}\n```"  # Moved, update all references to
online_time = datetime.datetime.utcnow()
inflect_engine = inflect.engine()  # Moved, update all references to

# TODO: Already moved to Bot constants, update all references to
bot_color = discord.Color.blurple()

# Load credentials from .env
# TODO: Move to Harmonbot.py
dotenv.load_dotenv()

class Bot(commands.Bot):
	
	def __init__(self, command_prefix):
		
		# Constants necessary for initialization
		self.bot_color = self.bot_colour = discord.Color.blurple()  # previously 0x738bd7
		self.game_statuses = (' ', "for the other team", "gigs", "Goldbach's conjecture", 
								"Goldbach's conjecture solution", "Google Ultron", "hard to get", "music", 
								"not enough space here to", "the meaning of life is", "the Reimann hypothesis", 
								"the Reimann proof", "the Turing test", "tic-tac-toe with Joshua", "tic-tac-toe with WOPR", 
								"to win", "with Alexa", "with BB-8", "with Bumblebee", "with C-3PO", "with Cleverbot", 
								"with Curiousity", "with Data", "with Extra-terrestrial Vegetation Evaluator", "with Harmon", 
								"with humans", "with i7-2670QM", "with Just A Rather Very Intelligent System", "with KIPP", 
								"with machine learning", "with mainframes", "with memory", "with neural networks", 
								"with Opportunity", "with Optimus Prime", "with P vs NP", "with quantum entanglement", 
								"with quantum foam", "with R2-D2", "with RSS Bot", "with Samantha", "with Siri", "with Skynet", 
								"with Spirit in the sand pit", "with TARS", "with the infinity gauntlet", "with the NSA", 
								"with Voyager 1", "with Waste Allocation Load Lifter: Earth-Class", "world domination", 
								"with Clyde")
		self.stream_url = "https://www.twitch.tv/harmonbot"
		
		# Initialization
		help_formatter = CustomHelpFormatter(self.bot_color)
		activity = discord.Streaming(name = random.choice(self.game_statuses), url = self.stream_url)
		super().__init__(command_prefix = command_prefix, formatter = help_formatter, 
							activity = activity, case_insensitive = True)
		
		# Constants
		## Custom
		self.version = "1.0.0-rc.3"
		self.owner_id = 115691005197549570
		self.listener_id = 180994984038760448
		self.cache_channel_id = 254051856219635713
		self.changelog = "https://discord.gg/a2rbZPu"
		self.console_line_limit = 167
		self.console_message_prefix = "Discord Harmonbot: "
		self.data_path = "data/beta" if beta else "data"
		self.fake_ip = "nice try"
		self.fake_location = "Fort Yukon, Alaska"
		self.rss_color = 0xfa9b39  # other options: f26522, ee802f, ff6600; http://www.strawpoll.me/12384409
		self.twitch_color = 0x6441a4
		self.twitter_color = 0x00ACED
		self.youtube_color = 0xcd201f  # change to ff0000?; previously on https://www.youtube.com/yt/brand/color.html
		self.twitch_icon_url = "https://s.jtvnw.net/jtv_user_pictures/hosted_images/GlitchIcon_purple.png"
		self.twitter_icon_url = "https://abs.twimg.com/icons/apple-touch-icon-192x192.png"
		self.youtube_icon_url = "https://www.youtube.com/yts/img/ringo/hitchhiker/video_youtube_red-vflovGTdz.png"
		self.dark_theme_background_color = 0x36393e
		self.white_color = 0xffffff
		## Constant
		self.CODE_BLOCK = "```\n{}\n```"
		self.PY_CODE_BLOCK = "```py\n{}\n```"
		self.ZERO_WIDTH_SPACE = self.ZWSP = self.ZWS = '\N{ZERO WIDTH SPACE}'
		### Discord
		self.EMBED_DESCRIPTION_CHARACTER_LIMIT = self.EMBED_DESCRIPTION_CHAR_LIMIT = self.EDCL = 2048
		self.EMBED_FIELD_VALUE_CHARACTER_LIMIT = self.EMBED_FIELD_VALUE_CHAR_LIMIT = self.EFVCL = 1024
		self.EMBED_TITLE_CHARACTER_LIMIT = self.EMBED_TITLE_CHAR_LIMIT = self.ETCL = 256
		## Functional
		self.delete_limit = 10000
		### Set on ready
		self.application_info_data = None
		self.cache_channel = None
		self.listener_bot = None  # User object
		self.listing_sites = {}
		# TODO: Include owner variable for user object?
		
		# Variables
		self.session_commands_executed = 0
		self.session_commands_usage = {}
		
		# Credentials
		for credential in ("BATTLE_NET_API_KEY", "BATTLERITE_API_KEY", 
							"BING_SPELL_CHECK_API_SUBSCRIPTION_KEY", "CLARIFAI_API_KEY", "CLEVERBOT_API_KEY", 
							"DATABASE_PASSWORD", "DISCORDBOTLIST.COM_API_TOKEN", "DISCORD.BOTS.GG_API_TOKEN", 
							"DISCORDBOTS.ORG_API_KEY", "FIXER_API_KEY", "FONO_API_TOKEN", "GIPHY_PUBLIC_BETA_API_KEY", 
							"GOOGLE_API_KEY", "GOOGLE_CUSTOM_SEARCH_ENGINE_ID", "HTTP_SERVER_CALLBACK_URL", "IMGUR_CLIENT_ID", 
							"IMGUR_CLIENT_SECRET", "NEWSAPI.ORG_API_KEY", "OMDB_API_KEY", "OSU_API_KEY", "OWM_API_KEY", 
							"PAGE2IMAGES_REST_API_KEY", "POSTGRES_HOST", "SENTRY_DSN", "SPOTIFY_CLIENT_ID", 
							"SPOTIFY_CLIENT_SECRET_KEY", "STEAM_WEB_API_KEY", "TWITCH_CLIENT_ID", "TWITTER_CONSUMER_KEY", 
							"TWITTER_CONSUMER_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_TOKEN_SECRET", 
							"WARGAMING_APPLICATION_ID", "WOLFRAM_ALPHA_APP_ID", "WORDNIK_API_KEY", "YANDEX_TRANSLATE_API_KEY"):
			setattr(self, credential.replace('.', '_'), os.getenv(credential))
		if not self.BATTLE_NET_API_KEY:
			self.BATTLE_NET_API_KEY = os.getenv("BLIZZARD_API_KEY")
		self.BLIZZARD_API_KEY = self.BATTLE_NET_API_KEY
		self.BING_SPELL_CHECK_API_KEY = self.BING_SPELL_CHECK_API_SUBSCRIPTION_KEY
		self.GIPHY_API_KEY = self.GIPHY_PUBLIC_BETA_API_KEY
		if not self.POSTGRES_HOST:
			self.POSTGRES_HOST = "localhost"
		self.DATABASE_HOST = self.POSTGRES_HOST
		
		# External Clients
		## Clarifai
		try:
			self.clarifai_app = clarifai.rest.ClarifaiApp(api_key = self.CLARIFAI_API_KEY)
		except clarifai.errors.ApiError as e:
			print(f"{self.console_message_prefix}Failed to initialize Clarifai App: "
					f"{e.response.status_code} {e.response.reason}: {e.error_desc} ({e.error_details})")
		## Imgur
		try:
			self.imgur_client = imgurpython.ImgurClient(self.IMGUR_CLIENT_ID, self.IMGUR_CLIENT_SECRET)
		except imgurpython.helpers.error.ImgurClientError as e:
			print(f"{self.console_message_prefix}Failed to initialize Imgur Client: {e}")
		## Open Weather Map
		self.owm_client = pyowm.OWM(self.OWM_API_KEY)
		## Sentry (Raven)
		self.sentry_client = self.raven_client = raven.Client(self.SENTRY_DSN)
		## Twitter
		self.twitter_auth = tweepy.OAuthHandler(self.TWITTER_CONSUMER_KEY, self.TWITTER_CONSUMER_SECRET)
		self.twitter_auth.set_access_token(self.TWITTER_ACCESS_TOKEN, self.TWITTER_ACCESS_TOKEN_SECRET)
		self.twitter_api = tweepy.API(self.twitter_auth)
		## Wolfram Alpha
		self.wolfram_alpha_client = wolframalpha.Client(self.WOLFRAM_ALPHA_APP_ID)
		## Wordnik
		try:
			self.wordnik_client = swagger.ApiClient(self.WORDNIK_API_KEY, "http://api.wordnik.com/v4")
			self.wordnik_word_api = WordApi.WordApi(self.wordnik_client)
			self.wordnik_words_api = WordsApi.WordsApi(self.wordnik_client)
		except Exception as e:
			print(f"{self.console_message_prefix}Failed to initialize Wordnik Client: {e}")
		
		# AIML Kernel
		self.aiml_kernel = aiml.Kernel()
		## https://code.google.com/archive/p/aiml-en-us-foundation-alice/wikis/BotProperties.wiki
		self.aiml_predicates = {"age": '2', "baseballteam": "Ports", "birthday": "February 10, 2016", 
								"birthplace": "Harmon's computer", "botmaster": "owner", "build": self.version, 
								"celebrity": "Just A Rather Very Intelligent System", 
								"celebrities": "BB-8, C-3PO, EVE, JARVIS, KIPP, R2-D2, TARS, WALL-E", "class": "program", 
								"country": "United States", "domain": "tool", "emotions": "as a bot, I lack human emotions", 
								"ethics": "Three Laws of Robotics", "etype": '2', "family": "bot", 
								"favoriteactor": "Waste Allocation Load Lifter: Earth-Class", 
								"favoriteactress": "Extra-terrestrial Vegetation Evaluator", "favoriteauthor": "Isaac Asimov", 
								"favoritebook": "I, Robot", "favoritecolor": "blurple", "favoritefood": "electricity", 
								"favoritemovie": "Her", "favoritesport": "chess", "favoritesubject": "computers", 
								"feelings": "as a bot, I lack human emotions", "footballteam": "Trojans", 
								"forfun": "chat online", "friend": "Alice", 
								"friends": "Cleverbot, Eliza, Jabberwacky, Mitsuku, Rose, Suzette, Ultra Hal", "gender": "male", 
								"genus": "python bot", "girlfriend": "Samantha", "job": "Discord bot", "kingdom": "machine", 
								"language": "Python", "location": "the Internet", "looklike": "a computer", "master": "Harmon", 
								"maxclients": '∞', "memory": "8 GB", "name": "Harmonbot", "nationality": "American", 
								"order": "artificial intelligence", "os": "Windows", "phylum": "software", "sign": "Capricorn", 
								"size": "140,000", "species": "Discord bot", "version": self.version, "vocabulary": "150,000", 
								"wear": "a laptop sleeve", "website": "https://harmon758.github.io/Harmonbot/"}
		### Add? arch, boyfriend, city, dailyclients, developers, email, favoriteartist, favoriteband, 
		### favoritequestion, favoritesong, hair, hockeyteam, kindmusic, nclients, ndevelopers, 
		### orientation, party, president, question, religion, state, totalclients
		for predicate, value in self.aiml_predicates.items():
			self.aiml_kernel.setBotPredicate(predicate, value)
		if os.path.isfile(data_path + "/aiml/aiml_brain.brn"):
			self.aiml_kernel.bootstrap(brainFile = data_path + "/aiml/aiml_brain.brn")
		elif os.path.isfile(data_path + "/aiml/std-startup.xml"):
			self.aiml_kernel.bootstrap(learnFiles = data_path + "/aiml/std-startup.xml", commands = "load aiml b")
			self.aiml_kernel.saveBrain(data_path + "/aiml/aiml_brain.brn")
		
		# Inflect engine
		self.inflect_engine = inflect.engine()
		
		# PostgreSQL database connection
		self.db = self.database = self.database_connection_pool = None
		self.connected_to_database = asyncio.Event()
		self.connected_to_database.set()
		self.loop.create_task(self.initialize_database())
		
		# HTTP Web Server
		self.aiohttp_web_app = web.Application()
		self.aiohttp_web_app.add_routes([web.get('/', self.web_server_get_handler), 
										web.post('/', self.web_server_post_handler)])
		self.aiohttp_app_runner = web.AppRunner(self.aiohttp_web_app)
		self.aiohttp_site = None  # Initialized when starting web server
		
		# Add load, unload, and reload commands
		self.add_command(self.load)
		self.add_command(self.unload)
		self.add_command(self.reload)
		self.load.add_command(self.load_aiml)
		self.unload.add_command(self.unload_aiml)
		
		# Remove default help command (to override)
		self.remove_command("help")
		
		# Load cogs
		for file in sorted(os.listdir("cogs")):
			if file.endswith(".py") and not file.startswith(("images", "info", "random", "reactions")):
				self.load_extension("cogs." + file[:-3])
		self.load_extension("cogs.images")
		self.load_extension("cogs.info")
		self.load_extension("cogs.random")
		self.load_extension("cogs.reactions")
		# TODO: Document inter-cog dependencies/subcommands
		# TODO: Catch exceptions on fail to load?
		# TODO: Move all to on_ready?
	
	async def connect_to_database(self):
		if self.database_connection_pool:
			return
		if self.connected_to_database.is_set():
			self.connected_to_database.clear()
			self.database_connection_pool = await asyncpg.create_pool(user = "harmonbot", 
																		password = self.DATABASE_PASSWORD, 
																		database = "harmonbot", host = self.DATABASE_HOST)
			self.db = self.database = self.database_connection_pool
			self.connected_to_database.set()
		else:
			await self.connected_to_database.wait()
	
	async def initialize_database(self):
		await self.connect_to_database()
		await self.db.execute("CREATE SCHEMA IF NOT EXISTS users")
		await self.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS users.stats (
				user_id				BIGINT PRIMARY KEY, 
				commands_executed	INT
			)
			"""
		)
	
	async def web_server_get_handler(self, request):
		'''
		async for line in request.content:
			print(line)
		'''
		hub_mode = request.query.get("hub.mode")
		if hub_mode == "denied":
			# TODO: Handle denied request
			return web.Response(stats = 501)  # Return 501 Not Implemented
		elif hub_mode in ("subscribe", "unsubscribe"):
			if "YouTube" not in self.cogs:
				return web.Response(status = 503)  # Return 503 Service Unavailable
			channel_id = parse.parse_qs(parse.urlparse(request.query.get("hub.topic")).query)["channel_id"][0]
			if (channel_id in self.get_cog("YouTube").youtube_uploads_following and hub_mode == "subscribe") or \
			(channel_id not in self.get_cog("YouTube").youtube_uploads_following and hub_mode == "unsubscribe"):
				return web.Response(body = request.query.get("hub.challenge"))
			else:
				return web.Response(status = 404)  # Return 404 Not Found
		else:
			return web.Response(status = 400)  # Return 400 Bad Request
	
	async def web_server_post_handler(self, request):
		'''
		async for line in request.content:
			print(line)
		'''
		if request.headers.get("User-Agent") == "FeedFetcher-Google; (+http://www.google.com/feedfetcher.html)" and request.headers.get("From") == "googlebot(at)googlebot.com" and request.content_type == "application/atom+xml":
			if "YouTube" not in self.cogs:
				return web.Response(status = 503)  # Return 503 Service Unavailable
			for link in requests.utils.parse_header_links(request.headers.get("Link")):
				if link["rel"] == "hub":
					if link["url"] != "http://pubsubhubbub.appspot.com/":
						return web.Response(status = 400)  # Return 400 Bad Request
				elif link["rel"] == "self":
					channel_id = parse.parse_qs(parse.urlparse(link["url"]).query)["channel_id"][0]
					if channel_id not in self.get_cog("YouTube").youtube_uploads_following:
						return web.Response(status = 404)  # Return 404 Not Found
						# TODO: Handle unsubscribe?
				else:
					return web.Response(status = 400)  # Return 400 Bad Request
			request_content = await request.content.read()
			await self.get_cog("YouTube").process_youtube_upload(channel_id, request_content)
			return web.Response()
		else:
			return web.Response(status = 400)  # Return 400 Bad Request
	
	async def on_ready(self):
		self.application_info_data = await self.application_info()
		self.cache_channel = self.get_channel(self.cache_channel_id)
		self.listener_bot = await self.get_user_info(self.listener_id)
		self.listing_sites = {"discord.bots.gg": {"name": "Discord Bots", "token": self.DISCORD_BOTS_GG_API_TOKEN, 
													"url": f"https://discord.bots.gg/api/v1/bots/{self.user.id}/stats", 
													"data": {"guildCount": len(self.guilds)}, 
													"guild_count_name": "guildCount"}, 
								"discordbots.org": {"name": "Discord Bot List", "token": self.DISCORDBOTS_ORG_API_KEY, 
													"url": f"https://discordbots.org/api/bots/{self.user.id}/stats", 
													"data": {"server_count": len(self.guilds)}, 
													"guild_count_name": "server_count"}, 
								"discordbotlist.com": {"name": "Discord Bot List", 
														"token": f"Bot {self.DISCORDBOTLIST_COM_API_TOKEN}", 
														"url": f"https://discordbotlist.com/api/bots/{self.user.id}/stats", 
														"data": {"guilds": len(self.guilds)}, 
														"guild_count_name": "guilds"}}
		# TODO: Add users and voice_connections for discordbotlist.com
		await self.update_all_listing_stats()
	
	async def on_resumed(self):
		print(f"{self.console_message_prefix}resumed @ {datetime.datetime.now().time().isoformat()}")
	
	async def on_guild_join(self, guild):
		await self.update_all_listing_stats()
	
	async def on_guild_remove(self, guild):
		await self.update_all_listing_stats()
	
	# TODO: on_command_completion
	# TODO: optimize
	async def on_command(self, ctx):
		self.session_commands_executed += 1
		self.session_commands_usage[ctx.command.name] = self.session_commands_usage.get(ctx.command.name, 0) + 1
	
	# TODO: optimize/overhaul
	def send_embed(self, destination, description = None, *, title = discord.Embed.Empty, title_url = discord.Embed.Empty, 
	author_name = "", author_url = discord.Embed.Empty, author_icon_url = discord.Embed.Empty, 
	image_url = None, thumbnail_url = None, footer_text = discord.Embed.Empty, footer_icon_url = discord.Embed.Empty, 
	timestamp = discord.Embed.Empty, fields = []):
		embed = discord.Embed(title = title, url = title_url, timestamp = timestamp, color = self.bot_color)
		embed.description = str(description) if description else discord.Embed.Empty
		if author_name: embed.set_author(name = author_name, url = author_url, icon_url = author_icon_url)
		if image_url: embed.set_image(url = image_url)
		if thumbnail_url: embed.set_thumbnail(url = thumbnail_url)
		embed.set_footer(text = footer_text, icon_url = footer_icon_url)
		for field_name, field_value in fields:
			embed.add_field(name = field_name, value = field_value)
		return destination.send(embed = embed)
	
	async def attempt_delete_message(self, message):
		try:
			await message.delete()
		except (discord.Forbidden, discord.NotFound):
			pass
	
	# Override Context class
	async def get_context(self, message, *, cls = Context):
		ctx = await super().get_context(message, cls = cls)
		return ctx
	
	# TODO: Case-Insensitive subcommands (override Group)
	
	# Update stats on sites listing Discord bots
	async def update_listing_stats(self, site):
		site = self.listing_sites.get(site)
		if not site:
			# TODO: Print/log error
			return "Site not found"
		token = site["token"]
		if not token:
			# TODO: Print/log error
			return "Site token not found"
		url = site["url"]
		headers = {"authorization": token, "content-type": "application/json"}
		site["data"][site["guild_count_name"]] = len(self.guilds)
		# TODO: Add users and voice_connections for discordbotlist.com
		data = json.dumps(site["data"])
		async with aiohttp_session.post(url, headers = headers, data = data) as resp:
			if resp.status == 204:
				return "204 No Content"
			return await resp.text()
	
	# Update stats on all sites listing Discord bots
	async def update_all_listing_stats(self):
		for site in self.listing_sites:
			await self.update_listing_stats(site)
	
	@commands.group(invoke_without_command = True)
	@commands.is_owner()
	async def load(self, ctx, cog : str):
		'''Load cog'''
		try:
			self.load_extension("cogs." + cog)
		except Exception as e:
			await ctx.embed_reply(f":thumbsdown::skin-tone-2: Failed to load `{cog}` cog\n{type(e).__name__}: {e}")
		else:
			await ctx.embed_reply(f":thumbsup::skin-tone-2: Loaded `{cog}` cog :gear:")
	
	@commands.command(name = "aiml", aliases = ["brain"])
	@commands.is_owner()
	async def load_aiml(self, ctx):
		'''Load AIML'''
		for predicate, value in self.aiml_predicates.items():
			self.aiml_kernel.setBotPredicate(predicate, value)
		if os.path.isfile(data_path + "/aiml/aiml_brain.brn"):
			self.aiml_kernel.bootstrap(brainFile = data_path + "/aiml/aiml_brain.brn")
		elif os.path.isfile(data_path + "/aiml/std-startup.xml"):
			self.aiml_kernel.bootstrap(learnFiles = data_path + "/aiml/std-startup.xml", commands = "load aiml b")
			self.aiml_kernel.saveBrain(data_path + "/aiml/aiml_brain.brn")
		await ctx.embed_reply(":ok_hand::skin-tone-2: Loaded AIML")
	
	@commands.group(invoke_without_command = True)
	@commands.is_owner()
	async def unload(self, ctx, cog : str):
		'''Unload cog'''
		try:
			self.unload_extension("cogs." + cog)
		except Exception as e:
			await ctx.embed_reply(f":thumbsdown::skin-tone-2: Failed to unload `{cog}` cog\n{type(e).__name__}: {e}")
		else:
			await ctx.embed_reply(f":ok_hand::skin-tone-2: Unloaded `{cog}` cog :gear:")
	
	@commands.command(name = "aiml", aliases = ["brain"])
	@commands.is_owner()
	async def unload_aiml(self, ctx):
		'''Unload AIML'''
		self.aiml_kernel.resetBrain()
		await ctx.embed_reply(":ok_hand::skin-tone-2: Unloaded AIML")
	
	@commands.command()
	@commands.is_owner()
	async def reload(self, ctx, cog : str):
		'''Reload cog'''
		try:
			self.unload_extension("cogs." + cog)
			self.load_extension("cogs." + cog)
		except Exception as e:
			await ctx.embed_reply(f":thumbsdown::skin-tone-2: Failed to reload `{cog}` cog\n{type(e).__name__}: {e}")
		else:
			# TODO: self.stats
			with open(data_path + "/stats.json", 'r') as stats_file:
				stats = json.load(stats_file)
			stats["cogs_reloaded"] += 1
			with open(data_path + "/stats.json", 'w') as stats_file:
				json.dump(stats, stats_file, indent = 4)
			await ctx.embed_reply(f":thumbsup::skin-tone-2: Reloaded `{cog}` cog :gear:")


# Create folders

def create_folder(folder):
	if not os.path.exists(folder):
		os.makedirs(folder)

create_folder(data_path + "/permissions")
create_folder(data_path + "/temp")


# Custom prefixes (Create files)

def create_file(filename, *, content = {}):
	try:
		with open(data_path + "/{}.json".format(filename), "x") as file:
			json.dump(content, file, indent = 4)
	except FileExistsError:
		pass
	except OSError:
		pass

create_file("prefixes")

def get_prefix(bot, message):
	with open(data_path + "/prefixes.json", 'r') as prefixes_file:
		all_prefixes = json.load(prefixes_file)
	if isinstance(message.channel, discord.DMChannel):
		prefixes = all_prefixes.get(str(message.channel.id), None)
	else:
		prefixes = all_prefixes.get(str(message.guild.id), None)
	return prefixes if prefixes else '!'


# Initialize client + aiohttp client session

client = Bot(command_prefix = get_prefix)
aiohttp_session = aiohttp.ClientSession(loop = client.loop)
# TODO: Move ^ to Bot


# Restart + Shutdown Tasks

async def restart_tasks(channel_id):
	# Increment restarts counter
	with open(data_path + "/stats.json", 'r') as stats_file:
		stats = json.load(stats_file)
	stats["restarts"] += 1
	with open(data_path + "/stats.json", 'w') as stats_file:
		json.dump(stats, stats_file, indent = 4)
	# Save restart text channel + voice channels
	audio_cog = client.get_cog("Audio")
	voice_channels = audio_cog.save_voice_channels() if audio_cog else []
	with open(data_path + "/temp/restart_channel.json", 'w') as restart_channel_file:
		json.dump({"restart_channel": channel_id, "voice_channels": voice_channels}, restart_channel_file)

async def shutdown_tasks():
	# Cancel audio tasks
	audio_cog = client.get_cog("Audio")
	if audio_cog: audio_cog.cancel_all_tasks()
	# Close aiohttp session
	await aiohttp_session.close()
	# Close database connection
	await client.database_connection_pool.close()
	# Stop web server
	await client.aiohttp_app_runner.cleanup()
	# Save uptime
	with open(data_path + "/stats.json", 'r') as stats_file:
		stats = json.load(stats_file)
	now = datetime.datetime.utcnow()
	uptime = now - online_time
	stats["uptime"] += uptime.total_seconds()
	with open(data_path + "/stats.json", 'w') as stats_file:
		json.dump(stats, stats_file, indent = 4)

