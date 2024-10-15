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

		num = str(num)
		short_num = to_sci(num) if len(num) > 1000 else num

		with open('DB/prompts.json','r') as f:
			prompts = json.load(f)

		if not is_numerical(num) or int(num) < 1:
			await ctx.reply("The round number must be a positive integer!")
			return
		if len(num) > 4000:
			await ctx.reply("I know we said there were infinite prompts, but we can't allow an index this high due to Discord's limits. Sorry.")
			return
		if num not in prompts:
			await ctx.reply("This prompt hasn't been generated yet!")
			return

		words = re.split('\s+',response.rstrip())
		if len(words)>10:
			await ctx.reply(f"Your response has {str(len(words))} words, which is above the limit.")
			return
		if len(response) > 1000:
			await ctx.reply(f"Your response is {len(response)} characters long, which is above the limit of 1000.")

		with updateDBLock:
			with open('DB/Private/responses.json','r+') as f:
				responsesDB = json.load(f)

				if num not in responsesDB.keys():
					responsesDB[num] = {}
				currentPromptResponses = responsesDB[num]
				userID = command_user(ctx).id
				IS_EDIT = str(userID) in currentPromptResponses
				print(IS_EDIT)
				currentPromptResponses[str(userID)]=response
			if not IS_EDIT and len(currentPromptResponses)==2:
				channel = self.BOT.get_channel(1290461645172244588)
				await channel.send(f"**========================================**\n# :exclamation: Prompt #{short_num} is now in play!\n**```{prompts[num]}```========================================**")
			elif not IS_EDIT and len(currentPromptResponses)==1:
				channel = self.BOT.get_channel(1290461645172244588)
				await channel.send(f"Prompt #{short_num} has received its first response.\n`{prompts[num]}`")
			json.dump(responsesDB,open('DB/Private/responses.json','w'),indent=4)

		message = (f'Success! Your {"edit" if IS_EDIT else "response"} to the following prompt:\n`{prompts[num]}`\n'
				+f'has been recorded as:\n`{response}`')
		await ctx.reply(message)








