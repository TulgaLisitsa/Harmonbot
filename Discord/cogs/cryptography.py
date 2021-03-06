
from discord.ext import commands

import hashlib
import zlib

from cryptography.hazmat.backends.openssl import backend as openssl_backend
from cryptography.hazmat.primitives import hashes as crypto_hashes
import pygost.gost28147
import pygost.gost28147_mac
import pygost.gost34112012
import pygost.gost341194
import pygost.gost3412

import clients
from modules import ciphers
from utilities import checks

def setup(bot):
	bot.add_cog(Cryptography(bot))

class Cryptography:
	
	def __init__(self, bot):
		self.bot = bot
	
	# TODO: not forbidden global check?
	
	@commands.group(aliases = ["decrpyt"], invoke_without_command = True)
	@checks.not_forbidden()
	async def decode(self, ctx):
		'''Decodes coded messages'''
		await ctx.invoke(self.bot.get_command("help"), ctx.invoked_with)
	
	@decode.group(name = "caesar", aliases = ["rot"], invoke_without_command = True)
	@checks.not_forbidden()
	async def decode_caesar(self, ctx, key : int, *, message : str):
		'''
		Decodes caesar codes
		key: 0 - 26
		'''
		if not 0 <= key <= 26:
			await ctx.embed_reply(":no_entry: Key must be in range 0 - 26")
			return
		await ctx.embed_reply(ciphers.decode_caesar(message, key))
	
	@decode_caesar.command(name = "brute")
	@checks.not_forbidden()
	async def decode_caesar_brute(self, ctx, message : str):
		'''Brute force decode caesar code'''
		await ctx.embed_reply(ciphers.brute_force_caesar(message))
	
	@decode.group(name = "gost", aliases = ["гост"], invoke_without_command = True)
	@checks.not_forbidden()
	async def decode_gost(self, ctx):
		'''
		Russian Federation/Soviet Union GOST
		Межгосударственный стандарт
		From GOsudarstvennyy STandart
		(ГОсударственный СТандарт)
		'''
		await ctx.invoke(self.bot.get_command("help"), "decode", ctx.invoked_with)
	
	@decode_gost.group(name = "28147-89", aliases = ["магма", "magma"], invoke_without_command = True)
	@checks.not_forbidden()
	async def decode_gost_28147_89(self, ctx):
		'''
		GOST 28147-89 block cipher
		Also known as Магма or Magma
		key length must be 32 (256-bit)
		'''
		# TODO: Add decode magma alias
		await ctx.invoke(self.bot.get_command("help"), "decode", "gost", ctx.invoked_with)
	
	@decode_gost_28147_89.command(name = "cbc")
	@checks.not_forbidden()
	async def decode_gost_28147_89_cbc(self, ctx, key : str, *, data : str):
		'''Magma with CBC mode of operation'''
		try:
			await ctx.embed_reply(pygost.gost28147.cbc_decrypt(key.encode("utf-8"), bytearray.fromhex(data)).decode("utf-8"))
		except ValueError as e:
			await ctx.embed_reply(":no_entry: Error: {}".format(e))
	
	@decode_gost_28147_89.command(name = "cfb")
	@checks.not_forbidden()
	async def decode_gost_28147_89_cfb(self, ctx, key : str, *, data : str):
		'''Magma with CFB mode of operation'''
		try:
			await ctx.embed_reply(pygost.gost28147.cfb_decrypt(key.encode("utf-8"), bytearray.fromhex(data)).decode("utf-8"))
		except ValueError as e:
			await ctx.embed_reply(":no_entry: Error: {}".format(e))
	
	@decode_gost_28147_89.command(name = "cnt")
	@checks.not_forbidden()
	async def decode_gost_28147_89_cnt(self, ctx, key : str, *, data : str):
		'''Magma with CNT mode of operation'''
		try:
			await ctx.embed_reply(pygost.gost28147.cnt(key.encode("utf-8"), bytearray.fromhex(data)).decode("utf-8"))
		except ValueError as e:
			await ctx.embed_reply(":no_entry: Error: {}".format(e))
	
	@decode_gost_28147_89.command(name = "ecb")
	@checks.not_forbidden()
	async def decode_gost_28147_89_ecb(self, ctx, key : str, *, data : str):
		'''
		Magma with ECB mode of operation
		data block size must be 8 (64-bit)
		This means the data length must be a multiple of 8
		'''
		try:
			await ctx.embed_reply(pygost.gost28147.ecb_decrypt(key.encode("utf-8"), bytearray.fromhex(data)).decode("utf-8"))
		except ValueError as e:
			await ctx.embed_reply(":no_entry: Error: {}".format(e))
	
	@decode_gost.command(name = "34.12-2015", aliases = ["кузнечик", "kuznyechik"])
	@checks.not_forbidden()
	async def decode_gost_34_12_2015(self, ctx, key : str, *, data : str):
		'''
		GOST 34.12-2015 128-bit block cipher
		Also known as Кузнечик or Kuznyechik
		key length >= 32, data length >= 16
		'''
		# TODO: Add decode kuznyechik alias
		if len(key) < 32:
			await ctx.embed_reply(":no_entry: Error: key length must be at least 32")
			return
		if len(data) < 16:
			await ctx.embed_reply(":no_entry: Error: data length must be at least 16")
			return
		await ctx.embed_reply(pygost.gost3412.GOST3412Kuznechik(key.encode("utf-8")).decrypt(bytearray.fromhex(data)).decode("utf-8"))
	
	@decode.command(name = "morse")
	@checks.not_forbidden()
	async def decode_morse(self, ctx, *, message : str):
		'''Decodes morse code'''
		await ctx.embed_reply(ciphers.decode_morse(message))
	
	@decode.command(name = "qr")
	@checks.not_forbidden()
	async def decode_qr(self, ctx, file_url : str = ""):
		'''
		Decodes QR codes
		Input a file url or attach an image
		'''
		if file_url:
			await self._decode_qr(ctx, file_url)
		if ctx.message.attachments and "filename" in ctx.message.attachments[0]:
			await self._decode_qr(ctx, ctx.message.attachments[0]["url"])
		if not file_url and not (ctx.message.attachments and "filename" in ctx.message.attachments[0]):
			await ctx.embed_reply(":no_entry: Please input a file url or attach an image")
	
	async def _decode_qr(self, ctx, file_url):
		# TODO: use textwrap
		url = "https://api.qrserver.com/v1/read-qr-code/?fileurl={}".format(file_url)
		async with clients.aiohttp_session.get(url) as resp:
			if resp.status == 400:
				await ctx.embed_reply(":no_entry: Error")
				return
			data = await resp.json()
		if data[0]["symbol"][0]["error"]:
			await ctx.embed_reply(":no_entry: Error: {}".format(data[0]["symbol"][0]["error"]))
			return
		decoded = data[0]["symbol"][0]["data"].replace("QR-Code:", "")
		if len(decoded) > ctx.bot.EMBED_DESCRIPTION_CHARACTER_LIMIT:
			await ctx.embed_reply(decoded[:ctx.bot.EDCL - 3] + "...", footer_text = "Decoded message exceeded character limit")
			# EDCL: Embed Description Character Limit
			return
		await ctx.embed_reply(decoded)
	
	@decode.command(name = "reverse")
	@checks.not_forbidden()
	async def decode_reverse(self, ctx, *, message : str):
		'''Reverses text'''
		await ctx.embed_reply(message[::-1])
	
	@commands.group(aliases = ["encrypt"], invoke_without_command = True)
	@checks.not_forbidden()
	async def encode(self, ctx):
		'''Encode messages'''
		await ctx.invoke(self.bot.get_command("help"), ctx.invoked_with)
	
	@encode.command(name = "adler32", aliases = ["adler-32"])
	@checks.not_forbidden()
	async def encode_adler32(self, ctx, *, message : str):
		'''Compute Adler-32 checksum'''
		await ctx.embed_reply(zlib.adler32(message.encode("utf-8")))
	
	@encode.command(name = "blake2b")
	@checks.not_forbidden()
	async def encode_blake2b(self, ctx, *, message : str):
		'''64-byte digest BLAKE2b'''
		digest = crypto_hashes.Hash(crypto_hashes.BLAKE2b(64), backend = openssl_backend)
		digest.update(message.encode("utf-8"))
		await ctx.embed_reply(digest.finalize())
	
	@encode.command(name = "blake2s")
	@checks.not_forbidden()
	async def encode_blake2s(self, ctx, *, message : str):
		'''32-byte digest BLAKE2s'''
		digest = crypto_hashes.Hash(crypto_hashes.BLAKE2s(32), backend = openssl_backend)
		digest.update(message.encode("utf-8"))
		await ctx.embed_reply(digest.finalize())
	
	@encode.command(name = "caesar", aliases = ["rot"])
	@checks.not_forbidden()
	async def encode_caesar(self, ctx, key : int, *, message : str):
		'''
		Encode a message using caesar code
		key: 0 - 26
		'''
		if not 0 <= key <= 26:
			await ctx.embed_reply(":no_entry: Key must be in range 0 - 26")
			return
		await ctx.embed_reply(ciphers.encode_caesar(message, key))
	
	@encode.command(name = "crc32", aliases = ["crc-32"])
	@checks.not_forbidden()
	async def encode_crc32(self, ctx, *, message : str):
		'''Compute CRC32 checksum'''
		await ctx.embed_reply(zlib.crc32(message.encode("utf-8")))
	
	@encode.group(name = "gost", aliases = ["гост"], invoke_without_command = True)
	@checks.not_forbidden()
	async def encode_gost(self, ctx):
		'''
		Russian Federation/Soviet Union GOST
		Межгосударственный стандарт
		From GOsudarstvennyy STandart
		(ГОсударственный СТандарт)
		'''
		await ctx.invoke(self.bot.get_command("help"), "encode", ctx.invoked_with)
	
	@encode_gost.group(name = "28147-89", aliases = ["магма", "magma"], invoke_without_command = True)
	@checks.not_forbidden()
	async def encode_gost_28147_89(self, ctx):
		'''
		GOST 28147-89 block cipher
		Also known as Магма or Magma
		key length must be 32 (256-bit)
		'''
		# TODO: Add encode magma alias
		await ctx.invoke(self.bot.get_command("help"), "encode", "gost", ctx.invoked_with)
	
	@encode_gost_28147_89.command(name = "cbc")
	@checks.not_forbidden()
	async def encode_gost_28147_89_cbc(self, ctx, key : str, *, data : str):
		'''Magma with CBC mode of operation'''
		try:
			await ctx.embed_reply(pygost.gost28147.cbc_encrypt(key.encode("utf-8"), data.encode("utf-8")).hex())
		except ValueError as e:
			await ctx.embed_reply(":no_entry: Error: {}".format(e))
	
	@encode_gost_28147_89.command(name = "cfb")
	@checks.not_forbidden()
	async def encode_gost_28147_89_cfb(self, ctx, key : str, *, data : str):
		'''Magma with CFB mode of operation'''
		try:
			await ctx.embed_reply(pygost.gost28147.cfb_encrypt(key.encode("utf-8"), data.encode("utf-8")).hex())
		except ValueError as e:
			await ctx.embed_reply(":no_entry: Error: {}".format(e))
	
	@encode_gost_28147_89.command(name = "cnt")
	@checks.not_forbidden()
	async def encode_gost_28147_89_cnt(self, ctx, key : str, *, data : str):
		'''Magma with CNT mode of operation'''
		try:
			await ctx.embed_reply(pygost.gost28147.cnt(key.encode("utf-8"), data.encode("utf-8")).hex())
		except ValueError as e:
			await ctx.embed_reply(":no_entry: Error: {}".format(e))
	
	@encode_gost_28147_89.command(name = "ecb")
	@checks.not_forbidden()
	async def encode_gost_28147_89_ecb(self, ctx, key : str, *, data : str):
		'''
		Magma with ECB mode of operation
		data block size must be 8 (64-bit)
		This means the data length must be a multiple of 8
		'''
		try:
			await ctx.embed_reply(pygost.gost28147.ecb_encrypt(key.encode("utf-8"), data.encode("utf-8")).hex())
		except ValueError as e:
			await ctx.embed_reply(":no_entry: Error: {}".format(e))
	
	@encode_gost_28147_89.command(name = "mac")
	@checks.not_forbidden()
	async def encode_gost_28147_89_mac(self, ctx, key : str, *, data : str):
		'''Magma with MAC mode of operation'''
		try:
			mac = pygost.gost28147_mac.MAC(key = key.encode("utf-8"))
			mac.update(data.encode("utf-8"))
			await ctx.embed_reply(mac.hexdigest())
		except ValueError as e:
			await ctx.embed_reply(":no_entry: Error: {}".format(e))
	
	@encode_gost.group(name = "34.11-2012", aliases = ["стрибог", "streebog"], invoke_without_command = True)
	@checks.not_forbidden()
	async def encode_gost_34_11_2012(self, ctx):
		'''
		GOST 34.11-2012 hash function
		Also known as Стрибог or Streebog
		'''
		# TODO: Add encode streebog-256 and encode streebog-512 aliases
		await ctx.invoke(self.bot.get_command("help"), "encode", "gost", ctx.invoked_with)
	
	@encode_gost_34_11_2012.command(name = "256")
	@checks.not_forbidden()
	async def encode_gost_34_11_2012_256(self, ctx, *, data : str):
		'''
		GOST 34.11-2012 256-bit hash function
		Also known as Streebog-256
		'''
		await ctx.embed_reply(pygost.gost34112012.GOST34112012(data.encode("utf-8"), digest_size = 32).hexdigest())
	
	@encode_gost_34_11_2012.command(name = "512")
	@checks.not_forbidden()
	async def encode_gost_34_11_2012_512(self, ctx, *, data : str):
		'''
		GOST 34.11-2012 512-bit hash function
		Also known as Streebog-512
		'''
		await ctx.embed_reply(pygost.gost34112012.GOST34112012(data.encode("utf-8"), digest_size = 64).hexdigest())
	
	@encode_gost.command(name = "34.11-94")
	@checks.not_forbidden()
	async def encode_gost_34_11_94(self, ctx, *, data : str):
		'''GOST 34.11-94 hash function'''
		await ctx.embed_reply(pygost.gost341194.GOST341194(data.encode("utf-8")).hexdigest())
	
	@encode_gost.command(name = "34.12-2015", aliases = ["кузнечик", "kuznyechik"])
	@checks.not_forbidden()
	async def encode_gost_34_12_2015(self, ctx, key : str, *, data : str):
		'''
		GOST 34.12-2015 128-bit block cipher
		Also known as Кузнечик or Kuznyechik
		key length >= 32, data length >= 16
		'''
		# TODO: Add encode kuznyechik alias
		if len(key) < 32:
			await ctx.embed_reply(":no_entry: Error: key length must be at least 32")
			return
		if len(data) < 16:
			await ctx.embed_reply(":no_entry: Error: data length must be at least 16")
			return
		await ctx.embed_reply(pygost.gost3412.GOST3412Kuznechik(key.encode("utf-8")).encrypt(data.encode("utf-8")).hex())
	
	@encode.command(name = "md4")
	@checks.not_forbidden()
	async def encode_md4(self, ctx, *, message : str):
		'''Generate MD4 hash'''
		h = hashlib.new("md4")
		h.update(message.encode("utf-8"))
		await ctx.embed_reply(h.hexdigest())
	
	@encode.command(name = "md5")
	@checks.not_forbidden()
	async def encode_md5(self, ctx, *, message : str):
		'''Generate MD5 hash'''
		await ctx.embed_reply(hashlib.md5(message.encode("utf-8")).hexdigest())
	
	@encode.command(name = "morse")
	@checks.not_forbidden()
	async def encode_morse(self, ctx, *, message : str):
		'''Encode a message in morse code'''
		await ctx.embed_reply(ciphers.encode_morse(message))
	
	@encode.command(name = "qr")
	@checks.not_forbidden()
	async def encode_qr(self, ctx, *, message : str):
		'''Encode a message in a QR code'''
		url = "https://api.qrserver.com/v1/create-qr-code/?data={}".format(message).replace(' ', '+')
		await ctx.embed_reply(image_url = url)
	
	@encode.command(name = "reverse")
	@checks.not_forbidden()
	async def encode_reverse(self, ctx, *, message : str):
		'''Reverses text'''
		await ctx.embed_reply(message[::-1])
	
	@encode.command(name = "ripemd160", aliases = ["ripemd-160"])
	@checks.not_forbidden()
	async def encode_ripemd160(self, ctx, *, message : str):
		'''Generate RIPEMD-160 hash'''
		h = hashlib.new("ripemd160")
		h.update(message.encode("utf-8"))
		await ctx.embed_reply(h.hexdigest())
	
	@encode.command(name = "sha1", aliases = ["sha-1"])
	@checks.not_forbidden()
	async def encode_sha1(self, ctx, *, message : str):
		'''Generate SHA-1 hash'''
		await ctx.embed_reply(hashlib.sha1(message.encode("utf-8")).hexdigest())
	
	@encode.command(name = "sha224", aliases = ["sha-224"])
	@checks.not_forbidden()
	async def encode_sha224(self, ctx, *, message : str):
		'''Generate SHA-224 hash'''
		await ctx.embed_reply(hashlib.sha224(message.encode("utf-8")).hexdigest())
	
	@encode.command(name = "sha256", aliases = ["sha-256"])
	@checks.not_forbidden()
	async def encode_sha256(self, ctx, *, message : str):
		'''Generate SHA-256 hash'''
		await ctx.embed_reply(hashlib.sha256(message.encode("utf-8")).hexdigest())
	
	@encode.command(name = "sha384", aliases = ["sha-384"])
	@checks.not_forbidden()
	async def encode_sha384(self, ctx, *, message : str):
		'''Generate SHA-384 hash'''
		await ctx.embed_reply(hashlib.sha384(message.encode("utf-8")).hexdigest())
	
	@encode.command(name = "sha512", aliases = ["sha-512"])
	@checks.not_forbidden()
	async def encode_sha512(self, ctx, *, message : str):
		'''Generate SHA-512 hash'''
		await ctx.embed_reply(hashlib.sha512(message.encode("utf-8")).hexdigest())
	
	@encode.command(name = "whirlpool")
	@checks.not_forbidden()
	async def encode_whirlpool(self, ctx, *, message : str):
		'''Generate Whirlpool hash'''
		h = hashlib.new("whirlpool")
		h.update(message.encode("utf-8"))
		await ctx.embed_reply(h.hexdigest())

