
from discord.ext import commands

import clients
import credentials
from utilities import checks

def setup(bot):
	bot.add_cog(Words(bot))

class Words:
	
	def __init__(self, bot):
		self.bot = bot
	
	@commands.command(aliases = ["antonyms"])
	@checks.not_forbidden()
	async def antonym(self, ctx, word : str):
		'''Antonyms of a word'''
		antonyms = self.bot.wordnik_word_api.getRelatedWords(word, relationshipTypes = "antonym", useCanonical = "true", limitPerRelationshipType = 100)
		if not antonyms:
			await ctx.embed_reply(":no_entry: Word or antonyms not found")
			return
		await ctx.embed_reply(', '.join(antonyms[0].words), title = "Antonyms of {}".format(word.capitalize()))
	
	@commands.command()
	@checks.not_forbidden()
	async def define(self, ctx, word : str):
		'''Define a word'''
		definition = self.bot.wordnik_word_api.getDefinitions(word, limit = 1) # useCanonical = True ?
		if not definition:
			await ctx.embed_reply(":no_entry: Definition not found")
			return
		await ctx.embed_reply(definition[0].text, title = definition[0].word.capitalize(), footer_text = definition[0].attributionText)
	
	@commands.command(aliases = ["audiodefine", "pronounce"])
	@checks.not_forbidden()
	async def pronunciation(self, ctx, word : str):
		'''Pronunciation of a word'''
		pronunciation = self.bot.wordnik_word_api.getTextPronunciations(word, limit = 1)
		description = pronunciation[0].raw.strip("()") if pronunciation else "Audio File Link"
		audio_file = self.bot.wordnik_word_api.getAudio(word, limit = 1)
		if audio_file:
			description = "[{}]({})".format(description, audio_file[0].fileUrl)
		elif not pronunciation:
			await ctx.embed_reply(":no_entry: Word or pronunciation not found")
			return
		await ctx.embed_reply(description, title = "Pronunciation of {}".format(word.capitalize()))
	
	@commands.command(aliases = ["rhymes"])
	@checks.not_forbidden()
	async def rhyme(self, ctx, word : str):
		'''Rhymes of a word'''
		rhymes = self.bot.wordnik_word_api.getRelatedWords(word, relationshipTypes = "rhyme", limitPerRelationshipType = 100)
		if not rhymes:
			await ctx.embed_reply(":no_entry: Word or rhymes not found")
			return
		await ctx.embed_reply(', '.join(rhymes[0].words), title = "Words that rhyme with {}".format(word.capitalize()))
	
	@commands.command()
	@checks.not_forbidden()
	async def spellcheck(self, ctx, *, words : str):
		'''Spell check words'''
		async with clients.aiohttp_session.post("https://api.cognitive.microsoft.com/bing/v5.0/spellcheck?Text=" + words.replace(' ', '+'), headers = {"Ocp-Apim-Subscription-Key" : credentials.bing_spell_check_key}) as resp:
			data = await resp.json()
		corrections = data["flaggedTokens"]
		corrected = words
		offset = 0
		for correction in corrections:
			offset += correction["offset"]
			suggestion = correction["suggestions"][0]["suggestion"]
			corrected = corrected[:offset] + suggestion + corrected[offset + len(correction["token"]):]
			offset += (len(suggestion) - len(correction["token"])) - correction["offset"]
		await ctx.embed_reply(corrected)
	
	@commands.command(aliases = ["synonyms"])
	@checks.not_forbidden()
	async def synonym(self, ctx, word : str):
		'''Synonyms of a word'''
		synonyms = self.bot.wordnik_word_api.getRelatedWords(word, relationshipTypes = "synonym", useCanonical = "true", limitPerRelationshipType = 100)
		if not synonyms:
			await ctx.embed_reply(":no_entry: Word or synonyms not found")
			return
		await ctx.embed_reply(', '.join(synonyms[0].words), title = "Synonyms of {}".format(word.capitalize()))
	
	@commands.group(description = "[Language Codes](https://tech.yandex.com/translate/doc/dg/concepts/api-overview-docpage/#languages)\n"
	"Powered by [Yandex.Translate](http://translate.yandex.com/)", invoke_without_command = True)
	@checks.not_forbidden()
	async def translate(self, ctx, *, text : str):
		'''Translate to English'''
		# TODO: From and to language code options?
		await self.process_translate(ctx, text, "en")
	
	@translate.command(name = "from")
	@checks.not_forbidden()
	async def translate_from(self, ctx, from_language_code : str, to_language_code : str, *, text : str):
		'''
		Translate from a specific language to another
		[Language Codes](https://tech.yandex.com/translate/doc/dg/concepts/api-overview-docpage/#languages)
		Powered by [Yandex.Translate](http://translate.yandex.com/)
		'''
		# TODO: Default to_language_code?
		await self.process_translate(ctx, text, to_language_code, from_language_code)
	
	@translate.command(name = "languages", aliases = ["codes", "language_codes"])
	@checks.not_forbidden()
	async def translate_languages(self, ctx, language_code : str = "en"):
		'''Language Codes'''
		async with clients.aiohttp_session.get("https://translate.yandex.net/api/v1.5/tr.json/getLangs?ui={}&key={}".format(language_code, credentials.yandex_translate_api_key)) as resp:
			data = await resp.json()
		if "langs" not in data:
			await ctx.embed_reply(":no_entry: Error: Invalid Language Code")
			return
		await ctx.embed_reply(", ".join(sorted("{} ({})".format(language, code) for code, language in data["langs"].items())))
	
	@translate.command(name = "to")
	@checks.not_forbidden()
	async def translate_to(self, ctx, language_code : str, *, text : str):
		'''
		Translate to a specific language
		[Language Codes](https://tech.yandex.com/translate/doc/dg/concepts/api-overview-docpage/#languages)
		Powered by [Yandex.Translate](http://translate.yandex.com/)
		'''
		await self.process_translate(ctx, text, language_code)
	
	async def process_translate(self, ctx, text, to_language_code, from_language_code = None):
		url = "https://translate.yandex.net/api/v1.5/tr.json/translate?key={}&lang={}&text={}&options=1".format(credentials.yandex_translate_api_key, to_language_code if not from_language_code else "{}-{}".format(from_language_code, to_language_code), text.replace(' ', '+'))
		async with clients.aiohttp_session.get(url) as resp:
			if resp.status == 400: # Bad Request
				await ctx.embed_reply(":no_entry: Error")
				return
			data = await resp.json()
		if data["code"] != 200:
			await ctx.embed_reply(":no_entry: Error: {}".format(data["message"]))
			return
		await ctx.embed_reply(data["text"][0], footer_text = "{}Powered by Yandex.Translate".format("Detected Language Code: {} | ".format(data["detected"]["lang"]) if not from_language_code else ""))
