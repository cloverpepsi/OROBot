import discord as dc
from discord.ext import commands as cmd
import os
from time import time

from __helper import *

def setup(BOT):
	BOT.add_cog(Reimport(BOT))

class Reimport(cmd.Cog):


	def __init__(self, BOT):
		self.BOT = BOT

	# Slash version of the command due to incompatibility
	@cmd.slash_command(name="reimport")
	@cmd.cooldown(1, 5, cmd.BucketType.user)
	@cmd.check(is_dev)
	async def slash_reimport(self, ctx, cmd_name, rtype='Cogs'):
		'''
		Choose a bot command file to reload from disk using the `[command_name]` argument.
		'''
		await ctx.response.defer()
		await self.reimport(ctx, cmd_name, rtype=rtype)
		return


	@cmd.command()
	@cmd.cooldown(1, 5, cmd.BucketType.user)
	@cmd.check(is_dev)
	async def reimport(self, ctx, cmd_name, rtype='Cogs'):

		if cmd_name is None:
			await ctx.respond("💀 Include the name of the command to import.")
			return
		
		cmd_name = cmd_name.lower()

		if f"{cmd_name}.py" not in os.listdir(rtype):
			if is_slash_cmd(ctx):
				await ctx.respond("💀 That command does not exist.")
				return
			
			if len(ctx.message.attachments) != 0:
				await ctx.message.attachments[0].save(f"Cogs/{cmd_name}.py")
			else:
				await ctx.respond(
				"💀 That command does not exist. Include a script file to create it!"
				)
				return

			try:
				self.BOT.load_extension(f"{rtype}.{cmd_name}")

			except Exception as e:
				os.remove(f"{rtype}/{cmd_name}.py")

				await ctx.respond(m_line(f"""
				⚠️ **An error ({type(e).__name__}) occured with the new command script!** 
				The import command has been cancelled.
				"""))
				return

			await ctx.respond("✅ **Command file created successfully.**")
			return
		
		else:
			with open(f"{rtype}/{cmd_name}.py", "r", encoding="utf-8") as f:
				backup_cmd = f.read()

			if not is_slash_cmd(ctx) and len(ctx.message.attachments) != 0:
				await ctx.message.attachments[0].save(f"{rtype}/{cmd_name}.py")

			try:
				self.BOT.unload_extension(f"{rtype}.{cmd_name}")
			except dc.errors.ExtensionNotLoaded:
				pass

			try:
				self.BOT.load_extension(f"{rtype}.{cmd_name}")

			except Exception as e:
				with open(f"{rtype}/{cmd_name}.py", "w", encoding="utf-8") as f:
					f.write(backup_cmd)

				self.BOT.load_extension(f"{rtype}.{cmd_name}")

				await ctx.respond(m_line(f"""
				⚠️ **An error ({type(e).__name__}) occured with the new command script!**
				The reimport command has been cancelled.
				"""))
				return
			
			f_name = f"{rtype}/BACKUP_{cmd_name}_{int(time())}.py"

			with open(f_name, 'w', encoding='utf-8') as f:
				f.write(backup_cmd)

			await ctx.respond(m_line("""✅ **Command file updated successfully.** 
			Below is a backup of its previous version."""), file=dc.File(f_name))

			os.remove(f_name)

		return
