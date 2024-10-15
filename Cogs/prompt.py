import nltk, random, json, re, os
nltk.download('punkt_tab')
from nltk.tokenize.treebank import TreebankWordDetokenizer
import discord as dc
from discord.ext import commands as cmd
from __helper import *

print("Context Index generating...")
try:
	contextIndex = nltk.ContextIndex([word.lower() for word in nltk.corpus.brown.words()])
except:
	nltk.download('brown')
	nltk.download('punkt')
	contextIndex = nltk.ContextIndex([word.lower() for word in nltk.corpus.brown.words()])

print("Done!")
promptList = [x for x in open("DB/sample_prompts.txt",encoding="UTF-8").readlines() if len(x) < 500]

def setup(BOT):
	BOT.add_cog(Prompt(BOT))

def get_prompt(seed):

	random.seed(int(seed))

	prompt = random.choice(promptList).strip()

	tokens = nltk.word_tokenize(prompt)
	for wordx in range(len(tokens)):

		token = tokens[wordx]

		if len(token) == 1:
			continue
		elif not re.match('\w',tokens[wordx]):
			continue

		try:
			tokens[wordx] = random.choice([x for x in contextIndex.similar_words(token,8) if re.match("\w",x)]+[token])
		except:
			print(token, wordx)
			pass

	return TreebankWordDetokenizer().detokenize(tokens).replace(" . ", ". ").replace("’", "'").replace("s '", "s'").replace(" ' ", "'")

class Prompt(cmd.Cog):

	@cmd.slash_command(name="prompt")
	@cmd.cooldown(1, 5, cmd.BucketType.user)
	async def slash_prompt(self, ctx, round_num=1):
		await self.prompt(ctx,round_num=round_num)
		return

	@cmd.command()
	@cmd.cooldown(1,5,cmd.BucketType.user)
	async def prompt(self, ctx, round_num=1):

		round_num = str(round_num)
		short_num = to_sci(round_num) if len(round_num) > 1000 else round_num

		if not is_numerical(round_num) or int(round_num) < 1:
			await ctx.reply("The round number must be a positive integer!")
			return

		if len(round_num) > 4000:
			await ctx.reply("I know we said there were infinite prompts, but we can't allow an index this high due to Discord's limits. Sorry.")
			return

		prompt_dict = json.load(open('DB/prompts.json'))
		print('ok')
		if round_num in prompt_dict.keys():
			prompt = prompt_dict[round_num]
			
		else:
			print('ok2')
			prompt = get_prompt(round_num)
			prompt_dict[round_num] = prompt
			print(prompt_dict)
			open("DB/prompts.json","w").write(json.dumps(prompt_dict,indent="\t"))
			

		await ctx.reply(f'The prompt for R{short_num} is ```{prompt}```')
		return	

	@cmd.slash_command(name="get_prompts")
	@cmd.cooldown(1, 5, cmd.BucketType.user)
	async def slash_get_prompts(self, ctx, min_responses=1, max_responses=999):
		await self.get_prompts(ctx, min_responses, max_responses)
		return

	@cmd.command()
	@cmd.cooldown(1,5,cmd.BucketType.user)
	async def get_prompts(self, ctx, min_responses=1, max_responses=999):

		prompt_dict = json.load(open('DB/prompts.json', 'r'))
		response_dict = json.load(open('DB/Private/responses.json','r'))

		filtered_prompts = []

		for round_num in sorted([int(x) for x in prompt_dict.keys()]):
			round_num = str(round_num)
			if round_num in response_dict.keys():
				respcount = len(response_dict[round_num])
				if respcount >= min_responses and respcount <= max_responses:
					filtered_prompts.append([str(round_num), str(respcount), prompt_dict[round_num]])

		open("prompt_list.txt","w",encoding="utf-8").write("\n".join(["\t".join(x) for x in filtered_prompts]))
		await ctx.reply(f"Here's a list of all prompts with **{min_responses}** to **{max_responses}** responses. (Columns: round #, response count, prompt text)",file=dc.File("prompt_list.txt"))
		os.remove("prompt_list.txt")





