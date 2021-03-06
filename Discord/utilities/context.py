
import discord
from discord.ext import commands

import collections
import json

from modules import utilities
from utilities import errors

class Context(commands.Context):
	
	def embed_reply(self, *args, **kwargs):
		return self.embed_say(*args, author_name = self.author.display_name, author_icon_url = self.author.avatar_url, **kwargs)
	
	# TODO: optimize/improve clarity
	async def embed_say(self, description = None, *args, title = discord.Embed.Empty, title_url = discord.Embed.Empty, 
	author_name = "", author_url = discord.Embed.Empty, author_icon_url = discord.Embed.Empty, 
	image_url = None, thumbnail_url = None, footer_text = discord.Embed.Empty, footer_icon_url = discord.Embed.Empty, 
	timestamp = discord.Embed.Empty, fields = [], color = None, in_response_to = True, attempt_delete = True, **kwargs):
		embed = discord.Embed(title = title, url = title_url, timestamp = timestamp, color = color or self.bot.bot_color)
		embed.description = str(description) if description else discord.Embed.Empty
		if author_name: embed.set_author(name = author_name, url = author_url, icon_url = author_icon_url)
		if image_url: embed.set_image(url = image_url)
		if thumbnail_url: embed.set_thumbnail(url = thumbnail_url)
		embed.set_footer(text = footer_text, icon_url = footer_icon_url)
		if footer_text == discord.Embed.Empty and in_response_to: embed.set_footer(text = "In response to: {}".format(self.message.clean_content), icon_url = footer_icon_url)
		elif in_response_to and not args: args = ("In response to: `{}`".format(self.message.clean_content),)
		for field in fields:
			if len(field) >= 3:
				embed.add_field(name = field[0], value = field[1], inline = field[2])
			else:
				embed.add_field(name = field[0], value = field[1])
		if isinstance(self.channel, discord.DMChannel) or getattr(self.channel.permissions_for(self.channel.guild.me), "embed_links", None):
			message = await self.send(*args, embed = embed, **kwargs)
		elif not (title or title_url or image_url or thumbnail_url or footer_text or footer_icon_url or timestamp or fields):
			message = await self.reply(utilities.clean_content(description))
			# TODO: Clean role + user mentions, etc.?
		else:
			raise errors.MissingCapability(["embed_links"])
		if attempt_delete: await self.bot.attempt_delete_message(self.message)
		return message
	
	def reply(self, content, *args, **kwargs):
		return self.send("{0.display_name}:\n{1}".format(self.author, content), **kwargs)
	
	def whisper(self, *args, **kwargs):
		return self.author.send(*args, **kwargs)
	
	# TODO: Improve + Optimize
	def get_permission(self, permission, *, type = "user", id = None):
		try:
			with open(f"{self.bot.data_path}/permissions/{self.guild.id}.json", "x+") as permissions_file:
				json.dump({"name" : self.guild.name}, permissions_file, indent = 4)
		except FileExistsError:
			pass
		else:
			return None
		with open(f"{self.bot.data_path}/permissions/{self.guild.id}.json", 'r') as permissions_file:
			permissions_data = json.load(permissions_file)
		if type == "everyone":
			return permissions_data.get("everyone", {}).get(permission)
		elif type == "role":
			role_setting = permissions_data.get("roles", {}).get(str(id), {}).get(permission)
			if role_setting is not None:
				return role_setting
			return permissions_data.get("everyone", {}).get(permission)
		elif type == "user":
			user_setting = permissions_data.get("users", {}).get(str(id), {}).get(permission)
			if user_setting is not None:
				return user_setting
			user = discord.utils.get(self.guild.members, id = id)
			role_positions = {}
			for role in user.roles:
				role_positions[role.position] = role
			sorted_role_positions = collections.OrderedDict(sorted(role_positions.items(), reverse = True))
			for role_position, role in sorted_role_positions.items():
				role_setting = permissions_data.get("roles", {}).get(str(role.id), {}).get(permission)
				if role_setting is not None:
					return role_setting
			return permissions_data.get("everyone", {}).get(permission)

