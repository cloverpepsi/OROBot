from random import shuffle, choice
import json
import csv

def setup(BOT): return

# gets all Unicode characters that will be used as keyletters
def getUniTable(numResponses):
	uniTable = []
	# in order: upper letters, lower letters, digits, then other latin letters
	uniRanges = [(65,91),(97,123),(48,58)]
	for r in uniRanges:
		for i in range(r[0],r[1]):
			uniTable.append(chr(i))
			if len(uniTable)>=numResponses:
				return uniTable
	numLeft = numResponses-len(uniTable)
	for i in range(192,192+numLeft):
		uniTable.append(chr(i))
	return uniTable

# for a given section of prompts, get a dict of format {keyword: {letter: submitterID}} and a list of rows for the CSV files
def generateSection(promptsInSection,promptsDB,responsesDB):
	CSVRows = []
	responsesPerKeywordDict = {}

	alphabet = "abcdefghijklmnopqrstuvwxyz".upper()

	words = [x.strip().upper() for x in open('DB/words.txt').readlines()]

	for promptID in promptsInSection:
		# TODO: Better keyword generation

		responsesToCurrentPrompt = responsesDB[promptID]
		validKeywords = [x for x in words if x[0] == alphabet[len(responsesToCurrentPrompt.values())-2]]

		keyword = choice(validKeywords)
		words.remove(keyword)
		promptContent = promptsDB[promptID]
		responsesPerKeywordDict[keyword]={}
		CSVRows.append((promptContent, None))
		CSVRows.append(('="["&INDIRECT("B"&ROW()+1)&" "&JOIN("",ARRAY_CONSTRAIN(INDIRECT("B"&(ROW()+2)&":B"),MATCH(TRUE,ARRAYFORMULA(ISBLANK(INDIRECT("B"&(ROW()+1)&":B"))),)-1,1))&"]"', None))
		CSVRows.append((keyword, None))
		# format of responsesToCurrentPrompt: {userID: response content}
	
		userIDList = list(responsesToCurrentPrompt.keys())
		# randomize response order of course
		shuffle(userIDList)
		for i,userID in enumerate(userIDList):
			responseContent = responsesToCurrentPrompt[userID]
			responseContent = responseContent.replace('\n', '//')
			# sanitize formulas
			if responseContent[0] in ['=','+',"'"]:
				responseContent = "'" + responseContent
			CSVRows.append((uniTable[i],responseContent))
			responsesPerKeywordDict[keyword][uniTable[i]] = userID
		CSVRows.append((None,None))
		CSVRows.append((None,None))
	return responsesPerKeywordDict,CSVRows

# get all sections of CSV rows and a dict containing all screens across all prompts
def generateVotingCollections():
	with open('DB/Private/responses.json','r+') as f:
		responsesDB = json.load(f)
	with open('DB/prompts.json','r') as f:
		promptsDB = json.load(f)
	numResponsesDict = {}
	allNumbersOfResponses = []
	# get a dict of format {numResponses: [each prompt ID with that many responses]}
	for promptID in promptsDB:
		promptID = str(promptID)
		try:
			numResponses = len(responsesDB[promptID])
		except:
			numResponses = 0
		if numResponses in numResponsesDict:
			numResponsesDict[numResponses].append(promptID)
		elif numResponses>1:
			allNumbersOfResponses.append(numResponses)
			numResponsesDict[numResponses] = [promptID]
	allNumbersOfResponses.sort()
	global uniTable
	uniTable = getUniTable(max(allNumbersOfResponses))
	sections = []
	fullResponsesPerKeywordDict = {}
	for num in allNumbersOfResponses:
		responsesPerKeywordDict,sectionCSVRows = generateSection(numResponsesDict[num],promptsDB,responsesDB)
		sections.append(sectionCSVRows)

		for key in responsesPerKeywordDict.keys():
			fullResponsesPerKeywordDict[key] = responsesPerKeywordDict[key]
		
	return sections, fullResponsesPerKeywordDict

def ArrayToCSV(CSVFileName,array):
	with open(CSVFileName, 'w', newline='',encoding='utf-8') as csvfile:
		writer = csv.writer(csvfile, delimiter='\t', dialect='excel',
								quotechar='|', quoting=csv.QUOTE_MINIMAL)
		for row in array:
			writer.writerow(row)

def generateVotingFiles(CSVSections,responsesPerKeywordDict):
	for i,section in enumerate(CSVSections):
		ArrayToCSV(f"DB/Section{str(i+1)}",section)
	with open("DB/screens.json","w") as f:
		json.dump(responsesPerKeywordDict,f,indent=4)

def generateAllOfVoting():
	sections,screens = generateVotingCollections()
	generateVotingFiles(sections,screens)

#generateAllOfVoting()
