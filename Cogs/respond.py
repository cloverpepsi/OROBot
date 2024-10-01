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
			await ctx.reply(f"Error! Your response has {str(len(words))}, which is above the limit!")
			return
		with updateDBLock:
			with open('DB/Private/responses.json','r+') as f:
				responsesDB = json.load(f)

				if str(num) not in responsesDB.keys():
					responsesDB[str(num)] = {}

				currentPromptResponses = responsesDB[str(num)]
				userID = ctx.message.author.id
				currentPromptResponses[str(userID)]=response
			json.dump(responsesDB,open('DB/Private/responses.json','w'),indent=4)

		message = (f'Success! Your response to the following prompt:\n`{prompts[num]}`\n'
				+f'has been recorded as:\n`{response}`')
		await ctx.reply(message)








