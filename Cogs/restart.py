import discord as dc
from discord.ext import commands as cmd
import os, sys
from datetime import datetime
from time import time

from __helper import *

def setup(BOT):
	BOT.add_cog(Restart(BOT))

class Restart(cmd.Cog):

	def __init__(self, BOT):
		self.BOT = BOT

	@cmd.command()
	@cmd.cooldown(1, 1, cmd.BucketType.user)
	@cmd.check(is_dev)
	async def shutdown(self, ctx,
		debug = ''):

		file_ref = sys.argv[0]

		debug_arg = 'debug' if debug == 'debug' else ''

		report_guild = f"1_report_guild:{'' if ctx.guild is None else ctx.guild.id}"

		report_chnl = m_line(f"""
		2_report_chnl:{command_user(ctx).id if is_dm(ctx) else ctx.channel.id}""")

		report_time = f"3_report_time:{int(time()*1000)}"

		await self.BOT.change_presence(status=dc.Status.invisible)
		
		await ctx.respond("♻️ **Shutting down!**")
		print(f"Shutting down on command from {command_user(ctx)} at {datetime.utcnow()}")

		sys.exit()

		return
