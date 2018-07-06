
from lxml import html
import time
import json
from functools import reduce
import wcUtil
import wcNetwork

#######################
# Global Parameters
#######################

MATCH_ID = '733784'#'737867'

COLUMN_WIDTH = 15

winScores = ['1:0', '2:0', '2:1', '3:0', '3:1', '3:2', '4:0', '4:1', '4:2', '4:3']
drawScores = ['0:0', '1:1', '2:2', '3:3', '4:4']
lossScores = ['0:1', '0:2', '1:2', '0:3', '1:3', '2:3', '0:4', '1:4', '2:4', '3:4']

#######################
# Score Logic
#######################

def queryScoreIndex(matchID:str) -> str:
	url = 'http://odds.500.com/fenxi/bifen-' + matchID + '.shtml'
	parameters = {'cids':5}
	response = wcNetwork.responseOfGet(url, wcNetwork.headerScore, parameters)
	htmlString = response.decode('gb2312')
	return htmlString

def processScoreResponse(htmlString:str) -> ():
	root = html.fromstring(htmlString)
	scores = winScores + drawScores + lossScores
	nodes = root.xpath('//tbody/tr[@class="tr2"]/td/text()')
	lossOdds = list(map(float, nodes[1:-5]))
	drawOdds = list(map(float, nodes[-5:]))
	nodes = root.xpath('//tbody/tr[@class="tr2"]/td/span/text()')
	winOdds = list(map(float, nodes[1:]))
	odds = winOdds+drawOdds+lossOdds
	scoreReturnRate = 1/reduce(lambda s,x:s+1/x, odds, 0)
	probabilities = [scoreReturnRate/odd for odd in odds]
	scoreProbabilities = dict(zip(scores, probabilities))
	originWinProb = sum(probabilities[:len(winScores)])
	originDrawProb = sum(probabilities[len(winScores):-len(lossScores)])
	originLossProb = sum(probabilities[-len(lossScores):])
	return (scoreProbabilities, scoreReturnRate, originWinProb, originDrawProb, originLossProb)

def coordinatedScoreIndex(scoreProbs:{}) -> ():
	winScoresCoordinated = [score.rjust(COLUMN_WIDTH) for score in winScores]
	winScoreProbs = ['{:.2%}'.format(scoreProbabilities[score]).rjust(COLUMN_WIDTH) for score in winScores]
	drawScoresCoordinated = [score.rjust(COLUMN_WIDTH) for score in drawScores]
	drawScoreProbs = ['{:.2%}'.format(scoreProbabilities[score]).rjust(COLUMN_WIDTH) for score in drawScores]
	lossScoresCoordinated = [score.rjust(COLUMN_WIDTH) for score in lossScores]
	lossScoreProbs = ['{:.2%}'.format(scoreProbabilities[score]).rjust(COLUMN_WIDTH) for score in lossScores]
	return (winScoresCoordinated, drawScoresCoordinated, lossScoresCoordinated, winScoreProbs, drawScoreProbs, lossScoreProbs)

#######################
# European Logic
#######################

def queryEuropeanIndex(matchID:str) -> []:
	url = 'http://odds.500.com/fenxi1/json/ouzhi.php'
	parameters = {'fid':matchID, 'cid':5, 'r':1, 'type':'europe', '_':str(int(time.time()*1000))}
	response = wcNetwork.responseOfGet(url, wcNetwork.headerOdds, parameters)
	return json.loads(response)

def processEuropeanResponse(json:[]) -> ():
	latestEuropeanIndex = json[0]
	winOdd = latestEuropeanIndex[0]
	drawOdd = latestEuropeanIndex[1]
	lossOdd = latestEuropeanIndex[2]
	euroReturnRate = latestEuropeanIndex[3]/100
	winProb = euroReturnRate/winOdd
	drawProb = euroReturnRate/drawOdd
	lossProb = euroReturnRate/lossOdd
	initialEuropeanIndex = json[-1]
	initWinOdd = initialEuropeanIndex[0]
	initDrawOdd = initialEuropeanIndex[1]
	initLossOdd = initialEuropeanIndex[2]
	initReturnRate = initialEuropeanIndex[3]/100
	initWinProb = initReturnRate/initWinOdd
	initDrawProb = initReturnRate/initDrawOdd
	initLossProb = initReturnRate/initLossOdd
	return (euroReturnRate, initWinProb, initDrawProb, initLossProb, winProb, drawProb, lossProb)

#######################
# Asian Logic
#######################

def queryAsianIndex(matchID:str) -> []:
	url = 'http://odds.500.com/fenxi1/inc/yazhiajax.php'
	parameters = {'fid':matchID, 'id':5, 'r':1, 't':str(int(time.time()*1000))}
	response = wcNetwork.responseOfGet(url, wcNetwork.headerOdds, parameters)
	return json.loads(response)

def processAsianResponse(json:[]) -> ():
	root = html.fromstring(json[0])
	nodes = root.xpath('//td')
	asianUpperOdd = float(nodes[0].text)
	asianLowerOdd = float(nodes[2].text)
	asianUpperCondProb = (asianLowerOdd+1)/(asianUpperOdd+asianLowerOdd+2)
	asianLowerCondProb = (asianUpperOdd+1)/(asianUpperOdd+asianLowerOdd+2)
	asianHandicap = wcUtil.handicapString2number(nodes[1].text)
	asianReturnRate = 1/(1/(asianUpperOdd+1)+1/(asianLowerOdd+1))
	return (asianReturnRate, asianHandicap, asianUpperOdd, asianLowerOdd, asianUpperCondProb, asianLowerCondProb)

#######################
# Conceding Logic
#######################

def queryConcedingIndex(matchID:str) -> []:
	url = 'http://odds.500.com/fenxi1/inc/daxiaoajax.php'
	parameters = {'fid':matchID, 'id':5, 't':str(int(time.time()*1000))}
	response = wcNetwork.responseOfGet(url, wcNetwork.headerOdds, parameters)
	return json.loads(response)

def processConcedingResponse(json:[]) -> ():
	root = html.fromstring(json[0])
	nodes = root.xpath('//td')
	concedingUpperOdd = float(nodes[0].text)
	concedingLowerOdd = float(nodes[2].text)
	concedingUpperCondProb = (concedingLowerOdd+1)/(concedingUpperOdd+concedingLowerOdd+2)
	concedingLowerCondProb = (concedingUpperOdd+1)/(concedingUpperOdd+concedingLowerOdd+2)
	concedingHandicaps = [float(handicap) for handicap in nodes[1].text.strip().split('/')]
	concedingHandicap = sum(concedingHandicaps)/len(concedingHandicaps)
	concedingReturnRate = 1/(1/(concedingUpperOdd+1)+1/(concedingLowerOdd+1))
	return (concedingReturnRate, concedingHandicap, concedingUpperOdd, concedingLowerOdd, concedingUpperCondProb, concedingLowerCondProb)

############################
# Reused Logging Logic
############################

def printConvertedAsianHandicap(isCurrentHandicap:bool, currentHandicap:float, asianReturnRate:float, upperProb:float, lowerProb:float):
	expectedUpperCondProb = upperProb / (upperProb+lowerProb)
	expectedLowerCondProb = lowerProb / (upperProb+lowerProb)
	convertedUpperOdd = asianReturnRate / expectedUpperCondProb - 1
	convertedLowerOdd = asianReturnRate / expectedLowerCondProb - 1
	upperKelly = convertedUpperOdd * upperProb - lowerProb
	lowerKelly = convertedLowerOdd * lowerProb - upperProb
	fillChar = ' '
	seperator = fillChar
	if isCurrentHandicap:
		fillChar = '_'
		seperator = fillChar
	print('{:.2f}'.format(currentHandicap).rjust(COLUMN_WIDTH, fillChar), '{:.2%}'.format(upperProb).rjust(COLUMN_WIDTH, fillChar), '{:.2%}'.format(lowerProb).rjust(COLUMN_WIDTH, fillChar), '{:.2%}'.format(expectedUpperCondProb).rjust(COLUMN_WIDTH, fillChar), '{:.2%}'.format(expectedLowerCondProb).rjust(COLUMN_WIDTH, fillChar), '{:.2f}'.format(convertedUpperOdd).rjust(COLUMN_WIDTH, fillChar), '{:.2f}'.format(convertedLowerOdd).rjust(COLUMN_WIDTH, fillChar), sep=seperator)#, '{:.2f}'.format(upperKelly).rjust(COLUMN_WIDTH), '{:.2f}'.format(lowerKelly).rjust(COLUMN_WIDTH))

def printConvertedConcedingHandicap(isCurrentHandicap:bool, currentConcedingHandicap:float, concedingReturnRate:float, concedingUpperProb:float, concedingLowerProb:float):
	expectedUpperCondProb = concedingUpperProb / (concedingUpperProb+concedingLowerProb)
	expectedLowerCondProb = concedingLowerProb / (concedingUpperProb+concedingLowerProb)
	convertedUpperOdd = concedingReturnRate / expectedUpperCondProb - 1
	convertedLowerOdd = concedingReturnRate / expectedLowerCondProb - 1
	upperKelly = convertedUpperOdd * concedingUpperProb - concedingLowerProb
	lowerKelly = convertedLowerOdd * concedingLowerProb - concedingUpperProb
	fillChar = ' '
	seperator = fillChar
	if isCurrentHandicap:
		fillChar = '_'
		seperator = fillChar
	print('{:.2f}'.format(currentConcedingHandicap).rjust(COLUMN_WIDTH, fillChar), '{:.2%}'.format(concedingUpperProb).rjust(COLUMN_WIDTH, fillChar), '{:.2%}'.format(concedingLowerProb).rjust(COLUMN_WIDTH, fillChar), '{:.2%}'.format(expectedUpperCondProb).rjust(COLUMN_WIDTH, fillChar), '{:.2%}'.format(expectedLowerCondProb).rjust(COLUMN_WIDTH, fillChar), '{:.2f}'.format(convertedUpperOdd).rjust(COLUMN_WIDTH, fillChar), '{:.2f}'.format(convertedLowerOdd).rjust(COLUMN_WIDTH, fillChar), sep=seperator)#, '{:.2f}'.format(upperKelly).rjust(COLUMN_WIDTH), '{:.2f}'.format(lowerKelly).rjust(COLUMN_WIDTH))


#######################
# Main Interface
#######################

def scoreIndex(matchID:str) -> ():
	return processScoreResponse(queryScoreIndex(matchID))

def europeanIndex(matchID:str) -> ():
	return processEuropeanResponse(queryEuropeanIndex(matchID))

def asianIndex(matchID:str) -> ():
	return processAsianResponse(queryAsianIndex(matchID))

def concedingIndex(matchID:str) -> ():
	return processConcedingResponse(queryConcedingIndex(matchID))

def printWinScoreProb(winScoresCoordinated:[], winScoreProbs:[]):
	print('Win Score'.rjust(COLUMN_WIDTH), *winScoresCoordinated)
	print('Probability'.rjust(COLUMN_WIDTH), *winScoreProbs)
	print()

def printDrawScoreProb(drawScoresCoordinated:[], drawScoreProbs:[]):
	print('Draw Score'.rjust(COLUMN_WIDTH), *drawScoresCoordinated)
	print('Probability'.rjust(COLUMN_WIDTH), *drawScoreProbs)
	print()

def printLossScoreProb(lossScoresCoordinated:[], lossScoreProbs:[]):
	print('Loss Score'.rjust(COLUMN_WIDTH), *lossScoresCoordinated)
	print('Probability'.rjust(COLUMN_WIDTH), *lossScoreProbs)
	print()

def printScoreIndex(scoreReturnRate:float, originWinProb:float, originDrawProb:float, originLossProb:float):
	print('Score Index'.rjust(COLUMN_WIDTH), 'Return Rate'.rjust(COLUMN_WIDTH), 'Orig Win Prob'.rjust(COLUMN_WIDTH), 'Orig Draw Prob'.rjust(COLUMN_WIDTH), 'Orig Loss Prob'.rjust(COLUMN_WIDTH))
	print(''.rjust(COLUMN_WIDTH), '{:.2%}'.format(scoreReturnRate).rjust(COLUMN_WIDTH), '{:.2%}'.format(originWinProb).rjust(COLUMN_WIDTH), '{:.2%}'.format(originDrawProb).rjust(COLUMN_WIDTH), '{:.2%}'.format(originLossProb).rjust(COLUMN_WIDTH))
	print()

def printEuropeanIndex(euroReturnRate:float, initWinProb:float, initDrawProb:float, initLossProb:float, winProb:float, drawProb:float, lossProb:float):
	print('European Index'.rjust(COLUMN_WIDTH), 'Return Rate'.rjust(COLUMN_WIDTH), 'Init Win Prob'.rjust(COLUMN_WIDTH), 'Init Draw Prob'.rjust(COLUMN_WIDTH), 'Init Loss Prob'.rjust(COLUMN_WIDTH), 'Win Prob'.rjust(COLUMN_WIDTH), 'Draw Prob'.rjust(COLUMN_WIDTH), 'Loss Prob'.rjust(COLUMN_WIDTH))
	print(''.rjust(COLUMN_WIDTH), '{:.2%}'.format(euroReturnRate).rjust(COLUMN_WIDTH), '{:.2%}'.format(initWinProb).rjust(COLUMN_WIDTH), '{:.2%}'.format(initDrawProb).rjust(COLUMN_WIDTH), '{:.2%}'.format(initLossProb).rjust(COLUMN_WIDTH), '{:.2%}'.format(winProb).rjust(COLUMN_WIDTH), '{:.2%}'.format(drawProb).rjust(COLUMN_WIDTH), '{:.2%}'.format(lossProb).rjust(COLUMN_WIDTH))
	print()

def printAsianIndex(asianReturnRate:float, asianHandicap:float, asianUpperCondProb:float, asianLowerCondProb:float, asianUpperOdd:float, asianLowerOdd:float):
	print('Asian Index'.rjust(COLUMN_WIDTH), 'Return Rate'.rjust(COLUMN_WIDTH), 'Handicap'.rjust(COLUMN_WIDTH),  'Up Cond Prob'.rjust(COLUMN_WIDTH), 'Low Cond Prob'.rjust(COLUMN_WIDTH), 'Upper Odds'.rjust(COLUMN_WIDTH), 'Lower Odds'.rjust(COLUMN_WIDTH))
	print(''.rjust(COLUMN_WIDTH), '{:.2%}'.format(asianReturnRate).rjust(COLUMN_WIDTH), '{:+.2f}'.format(asianHandicap).rjust(COLUMN_WIDTH), '{:.2%}'.format(asianUpperCondProb).rjust(COLUMN_WIDTH), '{:.2%}'.format(asianLowerCondProb).rjust(COLUMN_WIDTH), '{:.2f}'.format(asianUpperOdd).rjust(COLUMN_WIDTH), '{:.2f}'.format(asianLowerOdd).rjust(COLUMN_WIDTH))
	print()

def printAsianHandicap(scoreProbabilities:{}, winProb:float, drawProb:float, lossProb:float, asianReturnRate:float, asianHandicap:float):
	print('Asian Handicap'.rjust(COLUMN_WIDTH), 'Upper Prob'.rjust(COLUMN_WIDTH), 'Lower Prob'.rjust(COLUMN_WIDTH), 'Up Cond Prob'.rjust(COLUMN_WIDTH), 'Low Cond Prob'.rjust(COLUMN_WIDTH), 'Upper Odds'.rjust(COLUMN_WIDTH), 'Lower Odds'.rjust(COLUMN_WIDTH))#, 'Upper Kelly'.rjust(COLUMN_WIDTH), 'Lower Kelly'.rjust(COLUMN_WIDTH))

	#######################
	# Handicap -2.0
	#######################

	currentHandicap = -2.0
	upperProb = winProb - (scoreProbabilities['1:0']+scoreProbabilities['2:1']+scoreProbabilities['3:2']+scoreProbabilities['4:3']) - (scoreProbabilities['2:0']+scoreProbabilities['3:1']+scoreProbabilities['4:2'])
	lowerProb = lossProb + drawProb + (scoreProbabilities['1:0']+scoreProbabilities['2:1']+scoreProbabilities['3:2']+scoreProbabilities['4:3'])
	printConvertedAsianHandicap(asianHandicap==currentHandicap, currentHandicap, asianReturnRate, upperProb, lowerProb)

	#######################
	# Handicap -1.75
	#######################

	currentHandicap = -1.75
	upperProb = winProb - (scoreProbabilities['1:0']+scoreProbabilities['2:1']+scoreProbabilities['3:2']+scoreProbabilities['4:3']) - (scoreProbabilities['2:0']+scoreProbabilities['3:1']+scoreProbabilities['4:2'])/2
	lowerProb = lossProb + drawProb + (scoreProbabilities['1:0']+scoreProbabilities['2:1']+scoreProbabilities['3:2']+scoreProbabilities['4:3'])
	printConvertedAsianHandicap(asianHandicap==currentHandicap, currentHandicap, asianReturnRate, upperProb, lowerProb)

	#######################
	# Handicap -1.5
	#######################

	currentHandicap = -1.5
	upperProb = winProb - (scoreProbabilities['1:0']+scoreProbabilities['2:1']+scoreProbabilities['3:2']+scoreProbabilities['4:3'])
	lowerProb = lossProb + drawProb + (scoreProbabilities['1:0']+scoreProbabilities['2:1']+scoreProbabilities['3:2']+scoreProbabilities['4:3'])
	printConvertedAsianHandicap(asianHandicap==currentHandicap, currentHandicap, asianReturnRate, upperProb, lowerProb)

	#######################
	# Handicap -1.25
	#######################

	currentHandicap = -1.25
	upperProb = winProb - (scoreProbabilities['1:0']+scoreProbabilities['2:1']+scoreProbabilities['3:2']+scoreProbabilities['4:3'])
	lowerProb = lossProb + drawProb + (scoreProbabilities['1:0']+scoreProbabilities['2:1']+scoreProbabilities['3:2']+scoreProbabilities['4:3'])/2
	printConvertedAsianHandicap(asianHandicap==currentHandicap, currentHandicap, asianReturnRate, upperProb, lowerProb)

	#######################
	# Handicap -1.0
	#######################

	currentHandicap = -1.0
	upperProb = winProb - (scoreProbabilities['1:0']+scoreProbabilities['2:1']+scoreProbabilities['3:2']+scoreProbabilities['4:3'])
	lowerProb = lossProb + drawProb
	printConvertedAsianHandicap(asianHandicap==currentHandicap, currentHandicap, asianReturnRate, upperProb, lowerProb)

	#######################
	# Handicap -0.75
	#######################

	currentHandicap = -0.75
	upperProb = winProb - (scoreProbabilities['1:0']+scoreProbabilities['2:1']+scoreProbabilities['3:2']+scoreProbabilities['4:3'])/2
	lowerProb = lossProb + drawProb
	printConvertedAsianHandicap(asianHandicap==currentHandicap, currentHandicap, asianReturnRate, upperProb, lowerProb)

	#######################
	# Handicap -0.5
	#######################

	currentHandicap = -0.5
	upperProb = winProb
	lowerProb = lossProb + drawProb
	printConvertedAsianHandicap(asianHandicap==currentHandicap, currentHandicap, asianReturnRate, upperProb, lowerProb)

	#######################
	# Handicap -0.25
	#######################

	currentHandicap = -0.25
	upperProb = winProb
	lowerProb = lossProb + drawProb / 2
	printConvertedAsianHandicap(asianHandicap==currentHandicap, currentHandicap, asianReturnRate, upperProb, lowerProb)

	#######################
	# Handicap 0
	#######################

	currentHandicap = 0
	upperProb = winProb
	lowerProb = lossProb
	printConvertedAsianHandicap(asianHandicap==currentHandicap, currentHandicap, asianReturnRate, upperProb, lowerProb)

	#######################
	# Handicap 0.25
	#######################

	currentHandicap = 0.25
	upperProb = winProb + drawProb / 2
	lowerProb = lossProb
	printConvertedAsianHandicap(asianHandicap==currentHandicap, currentHandicap, asianReturnRate, upperProb, lowerProb)

	#######################
	# Handicap 0.5
	#######################

	currentHandicap = 0.5
	upperProb = winProb + drawProb
	lowerProb = lossProb
	printConvertedAsianHandicap(asianHandicap==currentHandicap, currentHandicap, asianReturnRate, upperProb, lowerProb)

	#######################
	# Handicap 0.75
	#######################

	currentHandicap = 0.75
	upperProb = winProb + drawProb
	lowerProb = lossProb - (scoreProbabilities['0:1']+scoreProbabilities['1:2']+scoreProbabilities['2:3']+scoreProbabilities['3:4'])/2
	printConvertedAsianHandicap(asianHandicap==currentHandicap, currentHandicap, asianReturnRate, upperProb, lowerProb)

	#######################
	# Handicap 1.0
	#######################

	currentHandicap = 1.0
	upperProb = winProb + drawProb
	lowerProb = lossProb - (scoreProbabilities['0:1']+scoreProbabilities['1:2']+scoreProbabilities['2:3']+scoreProbabilities['3:4'])
	printConvertedAsianHandicap(asianHandicap==currentHandicap, currentHandicap, asianReturnRate, upperProb, lowerProb)

	#######################
	# Handicap 1.25
	#######################

	currentHandicap = 1.25
	upperProb = winProb + drawProb + (scoreProbabilities['0:1']+scoreProbabilities['1:2']+scoreProbabilities['2:3']+scoreProbabilities['3:4'])/2
	lowerProb = lossProb - (scoreProbabilities['0:1']+scoreProbabilities['1:2']+scoreProbabilities['2:3']+scoreProbabilities['3:4'])
	printConvertedAsianHandicap(asianHandicap==currentHandicap, currentHandicap, asianReturnRate, upperProb, lowerProb)

	#######################
	# Handicap 1.5
	#######################

	currentHandicap = 1.5
	upperProb = winProb + drawProb + (scoreProbabilities['0:1']+scoreProbabilities['1:2']+scoreProbabilities['2:3']+scoreProbabilities['3:4'])
	lowerProb = lossProb - (scoreProbabilities['0:1']+scoreProbabilities['1:2']+scoreProbabilities['2:3']+scoreProbabilities['3:4'])
	printConvertedAsianHandicap(asianHandicap==currentHandicap, currentHandicap, asianReturnRate, upperProb, lowerProb)

	#######################
	# Handicap 1.75
	#######################

	currentHandicap = 1.75
	upperProb = winProb + drawProb + (scoreProbabilities['0:1']+scoreProbabilities['1:2']+scoreProbabilities['2:3']+scoreProbabilities['3:4'])
	lowerProb = lossProb - (scoreProbabilities['0:1']+scoreProbabilities['1:2']+scoreProbabilities['2:3']+scoreProbabilities['3:4']) - (scoreProbabilities['0:2']+scoreProbabilities['1:3']+scoreProbabilities['2:4'])/2
	printConvertedAsianHandicap(asianHandicap==currentHandicap, currentHandicap, asianReturnRate, upperProb, lowerProb)

	#######################
	# Handicap 2.0
	#######################

	currentHandicap = 2.0
	upperProb = winProb + drawProb + (scoreProbabilities['0:1']+scoreProbabilities['1:2']+scoreProbabilities['2:3']+scoreProbabilities['3:4'])
	lowerProb = lossProb - (scoreProbabilities['0:1']+scoreProbabilities['1:2']+scoreProbabilities['2:3']+scoreProbabilities['3:4']) - (scoreProbabilities['0:2']+scoreProbabilities['1:3']+scoreProbabilities['2:4'])
	printConvertedAsianHandicap(asianHandicap==currentHandicap, currentHandicap, asianReturnRate, upperProb, lowerProb)

	print('\n\n')



def printConcedingIndex(concedingReturnRate, concedingHandicap, concedingUpperCondProb, concedingLowerCondProb, concedingUpperOdd, concedingLowerOdd):
	print('Conceding Index'.rjust(COLUMN_WIDTH), 'Return Rate'.rjust(COLUMN_WIDTH), 'Handicap'.rjust(COLUMN_WIDTH),  'Up Cond Prob'.rjust(COLUMN_WIDTH), 'Low Cond Prob'.rjust(COLUMN_WIDTH), 'Upper Odds'.rjust(COLUMN_WIDTH), 'Lower Odds'.rjust(COLUMN_WIDTH))
	print(''.rjust(COLUMN_WIDTH), '{:.2%}'.format(concedingReturnRate).rjust(COLUMN_WIDTH), '{:.2f}'.format(concedingHandicap).rjust(COLUMN_WIDTH), '{:.2%}'.format(concedingUpperCondProb).rjust(COLUMN_WIDTH), '{:.2%}'.format(concedingLowerCondProb).rjust(COLUMN_WIDTH), '{:.2f}'.format(concedingUpperOdd).rjust(COLUMN_WIDTH), '{:.2f}'.format(concedingLowerOdd).rjust(COLUMN_WIDTH))
	print()

def printConcedingHandicap(scoreProbabilities, concedingReturnRate, concedingHandicap):
	print('Conceding Handicap'.rjust(COLUMN_WIDTH), 'Upper Prob'.rjust(COLUMN_WIDTH), 'Lower Prob'.rjust(COLUMN_WIDTH), 'Up Cond Prob'.rjust(COLUMN_WIDTH), 'Low Cond Prob'.rjust(COLUMN_WIDTH), 'Upper Odds'.rjust(COLUMN_WIDTH), 'Lower Odds'.rjust(COLUMN_WIDTH))

	##############################
	# Conceding Handicap 1.5
	##############################

	currentConcedingHandicap = 1.5
	concedingLowerProb = scoreProbabilities['0:0'] + scoreProbabilities['1:0'] + scoreProbabilities['0:1']
	concedingUpperProb = 1 - concedingLowerProb
	printConvertedConcedingHandicap(currentConcedingHandicap==concedingHandicap, currentConcedingHandicap, concedingReturnRate, concedingUpperProb, concedingLowerProb)

	##############################
	# Conceding Handicap 1.75
	##############################

	currentConcedingHandicap = 1.75
	concedingLowerProb = scoreProbabilities['0:0'] + scoreProbabilities['1:0'] + scoreProbabilities['0:1']
	concedingUpperProb = 1 - concedingLowerProb - (scoreProbabilities['2:0'] + scoreProbabilities['0:2'] + scoreProbabilities['1:1'])/2
	printConvertedConcedingHandicap(currentConcedingHandicap==concedingHandicap, currentConcedingHandicap, concedingReturnRate, concedingUpperProb, concedingLowerProb)

	##############################
	# Conceding Handicap 2.0
	##############################

	currentConcedingHandicap = 2.0
	concedingLowerProb = scoreProbabilities['0:0'] + scoreProbabilities['1:0'] + scoreProbabilities['0:1']
	concedingUpperProb = 1 - concedingLowerProb - (scoreProbabilities['2:0'] + scoreProbabilities['0:2'] + scoreProbabilities['1:1'])
	printConvertedConcedingHandicap(currentConcedingHandicap==concedingHandicap, currentConcedingHandicap, concedingReturnRate, concedingUpperProb, concedingLowerProb)

	##############################
	# Conceding Handicap 2.25
	##############################

	currentConcedingHandicap = 2.25
	concedingLowerProb = scoreProbabilities['0:0'] + scoreProbabilities['1:0'] + scoreProbabilities['0:1'] + (scoreProbabilities['2:0'] + scoreProbabilities['0:2'] + scoreProbabilities['1:1'])/2
	concedingUpperProb = 1 - (scoreProbabilities['0:0'] + scoreProbabilities['1:0'] + scoreProbabilities['0:1'] + scoreProbabilities['2:0'] + scoreProbabilities['0:2'] + scoreProbabilities['1:1'])
	printConvertedConcedingHandicap(currentConcedingHandicap==concedingHandicap, currentConcedingHandicap, concedingReturnRate, concedingUpperProb, concedingLowerProb)

	##############################
	# Conceding Handicap 2.5
	##############################

	currentConcedingHandicap = 2.5
	concedingLowerProb = scoreProbabilities['0:0'] + scoreProbabilities['1:0'] + scoreProbabilities['0:1'] + scoreProbabilities['2:0'] + scoreProbabilities['0:2'] + scoreProbabilities['1:1']
	concedingUpperProb = 1 - concedingLowerProb
	printConvertedConcedingHandicap(currentConcedingHandicap==concedingHandicap, currentConcedingHandicap, concedingReturnRate, concedingUpperProb, concedingLowerProb)

	##############################
	# Conceding Handicap 2.75
	##############################

	currentConcedingHandicap = 2.75
	concedingLowerProb = scoreProbabilities['0:0'] + scoreProbabilities['1:0'] + scoreProbabilities['0:1'] + scoreProbabilities['2:0'] + scoreProbabilities['0:2'] + scoreProbabilities['1:1']
	concedingUpperProb = 1 - concedingLowerProb - (scoreProbabilities['3:0'] + scoreProbabilities['0:3'] + scoreProbabilities['2:1'] + scoreProbabilities['1:2'])/2
	printConvertedConcedingHandicap(currentConcedingHandicap==concedingHandicap, currentConcedingHandicap, concedingReturnRate, concedingUpperProb, concedingLowerProb)

	##############################
	# Conceding Handicap 3.0
	##############################

	currentConcedingHandicap = 3.0
	concedingLowerProb = scoreProbabilities['0:0'] + scoreProbabilities['1:0'] + scoreProbabilities['0:1'] + scoreProbabilities['2:0'] + scoreProbabilities['0:2'] + scoreProbabilities['1:1']
	concedingUpperProb = 1 - concedingLowerProb - (scoreProbabilities['3:0'] + scoreProbabilities['0:3'] + scoreProbabilities['2:1'] + scoreProbabilities['1:2'])
	printConvertedConcedingHandicap(currentConcedingHandicap==concedingHandicap, currentConcedingHandicap, concedingReturnRate, concedingUpperProb, concedingLowerProb)

	##############################
	# Conceding Handicap 3.25
	##############################

	currentConcedingHandicap = 3.25
	concedingLowerProb = scoreProbabilities['0:0'] + scoreProbabilities['1:0'] + scoreProbabilities['0:1'] + scoreProbabilities['2:0'] + scoreProbabilities['0:2'] + scoreProbabilities['1:1'] + (scoreProbabilities['3:0'] + scoreProbabilities['0:3'] + scoreProbabilities['2:1'] + scoreProbabilities['1:2'])/2
	concedingUpperProb = 1 - (scoreProbabilities['0:0'] + scoreProbabilities['1:0'] + scoreProbabilities['0:1'] + scoreProbabilities['2:0'] + scoreProbabilities['0:2'] + scoreProbabilities['1:1'] + scoreProbabilities['3:0'] + scoreProbabilities['0:3'] + scoreProbabilities['2:1'] + scoreProbabilities['1:2'])
	printConvertedConcedingHandicap(currentConcedingHandicap==concedingHandicap, currentConcedingHandicap, concedingReturnRate, concedingUpperProb, concedingLowerProb)

	##############################
	# Conceding Handicap 3.5
	##############################

	currentConcedingHandicap = 3.5
	concedingLowerProb = scoreProbabilities['0:0'] + scoreProbabilities['1:0'] + scoreProbabilities['0:1'] + scoreProbabilities['2:0'] + scoreProbabilities['0:2'] + scoreProbabilities['1:1'] + scoreProbabilities['3:0'] + scoreProbabilities['0:3'] + scoreProbabilities['2:1'] + scoreProbabilities['1:2']
	concedingUpperProb = 1 - concedingLowerProb
	printConvertedConcedingHandicap(currentConcedingHandicap==concedingHandicap, currentConcedingHandicap, concedingReturnRate, concedingUpperProb, concedingLowerProb)

	print('\n\n\n')


#######################
# Main Logic
#######################

scoreProbabilities, scoreReturnRate, originWinProb, originDrawProb, originLossProb = scoreIndex(MATCH_ID)
euroReturnRate, initWinProb, initDrawProb, initLossProb, winProb, drawProb, lossProb = europeanIndex(MATCH_ID)
asianReturnRate, asianHandicap, asianUpperOdd, asianLowerOdd, asianUpperCondProb, asianLowerCondProb = asianIndex(MATCH_ID)
concedingReturnRate, concedingHandicap, concedingUpperOdd, concedingLowerOdd, concedingUpperCondProb, concedingLowerCondProb = concedingIndex(MATCH_ID)
winScoresCoordinated, drawScoresCoordinated, lossScoresCoordinated, winScoreProbs, drawScoreProbs, lossScoreProbs = coordinatedScoreIndex(scoreProbabilities)

printWinScoreProb(winScoresCoordinated, winScoreProbs)
printDrawScoreProb(drawScoresCoordinated, drawScoreProbs)
printLossScoreProb(lossScoresCoordinated, lossScoreProbs)
printScoreIndex(scoreReturnRate, originWinProb, originDrawProb, originLossProb)
printEuropeanIndex(euroReturnRate, initWinProb, initDrawProb, initLossProb, winProb, drawProb, lossProb)
printAsianIndex(asianReturnRate, asianHandicap, asianUpperCondProb, asianLowerCondProb, asianUpperOdd, asianLowerOdd)
printAsianHandicap(scoreProbabilities, winProb, drawProb, lossProb, asianReturnRate, asianHandicap)
printConcedingIndex(concedingReturnRate, concedingHandicap, concedingUpperCondProb, concedingLowerCondProb, concedingUpperOdd, concedingLowerOdd)
printConcedingHandicap(scoreProbabilities, concedingReturnRate, concedingHandicap)