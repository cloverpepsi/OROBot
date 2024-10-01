import nltk, random, json, re
from nltk.tokenize.treebank import TreebankWordDetokenizer
import discord as dc
from discord.ext import commands as cmd
from __helper import *
import threading

updateDBLock = threading.Lock()

def setup(BOT):
	BOT.add_cog(Respond(BOT))

class Respond(cmd.Cog):
	def __init__(self, BOT):
		self.BOT = BOT
	@cmd.slash_command(name="respond")
	@cmd.cooldown(1, 5, cmd.BucketType.user)
	async def slash_respond(self, ctx, num, response):
		await self.respond(ctx,num=num, response=response)
		return

	@cmd.command()
	@cmd.cooldown(1,5,cmd.BucketType.user)
	@cmd.dm_only()
	async def respond(self,ctx,num,*,response):
		with open('DB/prompts.json','r') as f:
			prompts = json.load(f)
		if str(num) not in prompts:
			await ctx.reply("Error! Invalid prompt index!")
			return
		words = re.split('\s+',response.rstrip())
		if len(words)>10:
			await ctx.reply(f"Error! Your response has {str(len(words))} words, which is above the limit!")
			return
		with updateDBLock:
			with open('DB/Private/responses.json','r+') as f:
				responsesDB = json.load(f)

				if str(num) not in responsesDB.keys():
					responsesDB[str(num)] = {}
				currentPromptResponses = responsesDB[str(num)]
				userID = ctx.message.author.id
				IS_EDIT = str(userID) in currentPromptResponses
				print(IS_EDIT)
				currentPromptResponses[str(userID)]=response
			if not IS_EDIT and len(currentPromptResponses)==2:
				channel = self.BOT.get_channel(1290461645172244588)
				await channel.send(f"**========================================**\n# :exclamation: Prompt #{str(num)} is now in play!\n**```{prompts[num]}```========================================**")
			elif not IS_EDIT and len(currentPromptResponses)==1:
				channel = self.BOT.get_channel(1290461645172244588)
				await channel.send(f"Prompt #{str(num)} has received its first response.\n`{prompts[num]}`")
			json.dump(responsesDB,open('DB/Private/responses.json','w'),indent=4)

		message = (f'Success! Your {"edit" if IS_EDIT else "response"} to the following prompt:\n`{prompts[num]}`\n'
				+f'has been recorded as:\n`{response}`')
		await ctx.reply(message)








