import discord as dc
from discord import *
from discord.ext import commands as cmd
from discord.ext import bridge as bridge
from time import time
import traceback as tb
import os, json
from __helper import *
import re
from datetime import datetime
import threading

PREFIX = "!"
intents = Intents.default()
intents.members = True
intents.message_content = True
updateDBLock = threading.Lock()

BOT = bridge.Bot(command_prefix="!", intents=intents) 
BOT.allowed_mentions = AllowedMentions(replied_user=False)
BOT.remove_command('help')

STARTUP = time()

@BOT.event
async def on_connect():
	print(f"""OROBot connected to Discord at\n{round(time() - STARTUP, 2)}s - {datetime.utcnow()}\n""")

	await BOT.sync_commands()


@BOT.event
async def on_ready():
	print(f"""OROBot logged in at\n{round(time() - STARTUP, 2)}s - {datetime.utcnow()}\n""")


@BOT.event
async def on_command_error(ctx, error): # For prefixed commands
	await error_handler(ctx, error)
from discord.ext import bridge as bridge
@BOT.event
async def on_application_command_error(ctx, error): # For slash commands
	await error_handler(ctx, error)

async def error_handler(ctx, err):
	if type(err) == cmd.errors.CommandNotFound:
		await ctx.respond(f"💀 This command or alias does not exist!", ephemeral=True)
		return
	
	if type(err) == cmd.errors.CommandOnCooldown:
		if is_slash_cmd(ctx):
			await ctx.respond("🐌 **This command is on cooldown right now!**", ephemeral=True)
		else:
			await ctx.message.add_reaction("🐌")
		return
	
	print("-[ERROR]- "*10)
	tb.print_exception(type(err), err, None)

	if type(err).__name__ == "CommandInvokeError":
		err = err.original

	try:
		await ctx.respond(
		f"💀 Uh oh! This command raised an error: **`{type(err).__name__}`**")

	except Exception as e:
		print(f"\nCouldn't inform user of error due to {type(e).__name__}!")

	
	print("-[ERROR]- "*10, '\n')

@BOT.event
async def on_command(ctx):
	print("Text command from", ctx.message.author)
	print(datetime.utcnow(), "-", time())

	try:
		print(ctx.message.channel.name, f"({ctx.message.channel.id})")
		print(ctx.message.guild.name, f"({ctx.message.guild.id})")
	except AttributeError:
		print("Sent in DMs")
	
	print("-->", ctx.message.content, "\n")

@BOT.event
async def on_application_command(ctx):
	print("Slash command from", ctx.user)
	print(datetime.utcnow(), "-", time())

	try:
		print(ctx.channel.name, f"({ctx.channel.id})")
		print(ctx.guild.name, f"({ctx.guild.id})")
	except AttributeError:
		print("Sent in DMs")
	
	print(f"--> /{ctx.command}\n")

print("="*50, '\n')

@BOT.command()
@commands.dm_only()
async def respond(ctx,num,*,response):
	with open('DB/prompts.json','r') as f:
		prompts = json.load(f)
	if num not in prompts:
		await ctx.send("Error! Invalid prompt index!")
		return
	words = re.split('\s+',response.rstrip())
	if len(words)>10:
		await ctx.send(f"Error! Your response has {str(len(words))}, which is above the limit!")
		return
	with updateDBLock:
		with open('DB/Private/responses.json','r+') as f:
			responsesDB = json.load(f)
			currentPromptResponses = responsesDB[num]
			userID = ctx.message.author.id
			currentPromptResponses[userID]=response
			json.dump(responsesDB,f,indent=4)
	message = (f'Success! Your response to the following prompt:\n`{prompts[num]}`\n'
			+f'has been recorded as:\n`{response}`')
	await ctx.send(message)
		

cogs_loaded = []

for cog_name in os.listdir("Cogs"):
	if not cog_name.endswith('py') or cog_name.startswith('__'):
		continue

	BOT.load_extension(f"Cogs.{cog_name[:-3]}")

	cogs_loaded.append(cog_name[:-3].upper())

print(f"Loaded in the following cogs: {', '.join(cogs_loaded)}", '\n')

print("="*50, '\n')

token = open("DB/Private/token.txt",'r').read()
BOT.run(token)

