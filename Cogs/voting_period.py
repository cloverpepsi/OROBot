from datetime import datetime
import json
import threading
import re
import nltk, random, json, re, os
from nltk.tokenize.treebank import TreebankWordDetokenizer
import discord as dc
from discord.ext import commands as cmd
from __helper import *
import threading

def getScreensFileName():
	return f'DB/screens.json'

def getVotesFileName():
	return f'DB/Private/votes.json'

updateDBLock = threading.Lock()

# list to string
def lts(itemList):
	listAsString = '['
	for i in range(len(itemList)-1):
		listAsString += str(itemList[i])+','
	listAsString += str(itemList[-1])+']'
	return listAsString

# get whether a message should be singular or plural from the size of a list in the message
def sopL(messageString):
	itemListString = re.findall('\[(.*)\]',messageString)[0]
	itemList = itemListString.split(',')
	listReplacement = f'`{itemList[0]}`'
	if len(itemList)==1:
		wordReplacement = r'\1'
	else:
		wordReplacement = r'\2'
		if len(itemList)==2:
			listReplacement += f' and `{itemList[1]}`'
		else:
			listReplacement += ', '
			for i in range(1,len(itemList)-1):
				listReplacement += f'`{itemList[i]}`, '
			listReplacement += f'and `{itemList[-1]}`'
	messageString = re.sub(f'\[{re.escape(itemListString)}\]',listReplacement,
						   messageString)
	messageString = re.sub('{(.*?)/(.*?)}',wordReplacement,messageString)
	return messageString

# screens DB is formatted like {keyword: {A: response, B: response, etc}}
# votes DB is formatted like {userID: {screens: {keywordA: vote, keywordB: vote, etc}, supervoterAccess: false}}

def createVotesDB():
	with open(getVotesFileName(),'w') as f:
		votesDB = {}
		json.dump(votesDB,f,indent=4)

# screens DB is already created
def getScreensDB():
	with open(getScreensFileName(),'r') as f:
		screensDB = json.load(f)
	return screensDB

def getVotesDB():
	with open(getVotesFileName(),'r') as f:
		votesDB = json.load(f)
	return votesDB

def updateVotesDB(newDB):
	with open(getVotesFileName(),'w') as f:
		json.dump(newDB,f,indent=4)

def checkVoteValidity(voteLetters,keysOnScreen):
	message = ''
	# check if vote has repeated letters
	if len(voteLetters)>len(set(voteLetters)):
		repeatedLetters = []
		for c in voteLetters:
			if voteLetters.count(c)>1 and c not in repeatedLetters:
				repeatedLetters.append(c)
		message += sopL(f'Error: {lts(repeatedLetters)} {{is/are}} repeated '
						+'in your vote!')
	# check if vote is missing letters that are on the screen
	missingLetters = []
	for c in keysOnScreen:
		if c not in voteLetters:
			missingLetters.append(c)
	if len(missingLetters)>0:
		if not message:
			message = "Error: "
		else:
			message += " Additionally, "
		message += sopL(f'{lts(missingLetters)} {{is/are}} missing from '
						+'your vote!')
	# check if vote has letters that aren't on the screen
	invalidLetters = []
	for c in voteLetters:
		if c not in keysOnScreen:
			invalidLetters.append(c)
	if len(invalidLetters)>0:
		if not message:
			message = "Error: "
		else:
			message += " Additionally, "
		message += sopL(f"{lts(invalidLetters)} {{is/are}} not {{a /}}"
						+f"character{{/s}} on the screen you're voting on!")
	return message

def addVote(userID,keyword,letters):
	# remove brackets
	keyword = re.sub("[\[\]]","",keyword)
	letters = re.sub("[\[\]]","",letters)
	keyword = keyword.upper()
	# make sure keyword exists
	allScreens = getScreensDB()
	if keyword not in allScreens:
		return f'Error: `{keyword}` is not a valid keyword!'
	with updateDBLock:
		votesDB = getVotesDB()
		# check if user has voted previously; if so, make some additional checks
		if userID in votesDB:
			# check if user has access to the supervoter channel; reject their vote if so
			if votesDB[userID]["supervoterAccess"]:
				return (f"Error: You are in the Supervoter channel! You cannot change your votes anymore.")
			# check if user has already voted on this screen; if so, change the text at the end
			alreadyVotedOnScreen = keyword in votesDB[userID]['screens']
		else:
			alreadyVotedOnScreen = False
		keysOnScreen = [keyletter for keyletter in allScreens[keyword]]
		if len(keysOnScreen)<=26:
			letters = letters.upper()
		message = checkVoteValidity(letters,keysOnScreen)
		# if no errors have been raised, add vote to the DB
		if not message:
			# add user to vote DB if they're not there yet
			if userID not in votesDB:
				votesDB[userID] = {'screens':{},'supervoterAccess':False}
			votesDB[userID]['screens'][keyword] = letters
			updateVotesDB(votesDB)
			message=f"Success! Your vote of `{keyword} {letters}` has been logged!"
			if alreadyVotedOnScreen:
				message=f"Success! Your vote on screen `{keyword}` has been edited to `{letters}`!"
			# check if they've voted on all screens in the section
			if len(votesDB[userID]['screens'])==len(allScreens):
				message+=f"\nYou have voted on every screen!"
				message+=f"\nYou can access the supervoter channel with `!supervoter`."
	return message

def deleteVote(userID,keyword):
	# make sure keyword exists
	allScreens = getScreensDB()
	if keyword not in allScreens:
		return f'Error: `{keyword}` is not a valid keyword!'
	with updateDBLock:
		votesDB = getVotesDB()
		# make sure user has already sent at least one vote 
		if userID not in votesDB:
			return 'Error! You have not sent any votes yet!'
		# make sure user has already voted on this particular screen
		if keyword not in votesDB[userID]['screens']:
			return f'Error! You have not voted on screen {keyword} yet!'
		# check if user has access to the supervoter channel; reject their deletion if so
		if votesDB[userID]["supervoterAccess"]:
			return (f"Error: You are in the Supervoter channel! You cannot change your votes anymore.")
		del votesDB[userID]['screens'][keyword] 
		if len(votesDB[userID]['screens']) == 0:
			del votesDB[userID]
		updateVotesDB(votesDB)
		return f"Success! Your vote on screen `{keyword}` has been deleted!"
	
def clearVotes(userID):
	with updateDBLock:
		votesDB = getVotesDB()
		# make sure user has already sent at least one vote 
		if userID not in votesDB:
			return 'Error! You have not sent any votes yet!'
		# check if user has access to the supervoter channel; reject their deletion if so
		if votesDB[userID]["supervoterAccess"]:
			return (f"Error: You are in the Supervoter channel! You cannot change your votes anymore.")
		del votesDB[userID]
		updateVotesDB(votesDB)
		return "Success! All your votes have been deleted!"

def viewVotes(userID):
	votesDB = getVotesDB()
	# make sure user has already sent at least one vote
	if userID not in votesDB:
		return 'Error! You have not sent any votes yet!'
	message = "Here is a list of your votes:"
	userVotes = votesDB[userID]['screens']
	for keyword in userVotes:
		message += f'\n`{keyword} {userVotes[keyword]}`'
	return message

def hasSupervoted(userID):
	votesDB = getVotesDB()
	screensDB = getScreensDB()
	if userID not in votesDB:
		return "Error! You have not sent any votes!"
	screensUserHasVotedOn = [screen for screen in votesDB[userID]['screens']]
	if not all([keyword in screensUserHasVotedOn for keyword in screensDB]):
		return f"Error! You have not yet voted on every screen!"
	return ""



def setup(BOT):
	BOT.add_cog(Vote(BOT))

class Vote(cmd.Cog):

	def __init__(self, BOT):
		self.BOT = BOT

	@cmd.command()
	@cmd.cooldown(1,1,cmd.BucketType.user)
	@cmd.dm_only()
	async def vote(self, ctx, *, votes):
		
		allVotes = [re.sub("[\\[\\]]", "", x) for x in re.findall("\\[.+?\\]", votes)]
		response = []
		for vote in allVotes:
			response.append(addVote(command_user(ctx).id, vote.split(" ")[0], vote.split(' ')[1]))
			
		await ctx.reply("\n".join(response))
		
		

