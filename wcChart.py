from pygal.graph.line import Line
from pygal.style import NeonStyle
import os
from lxml import html
import time
import json
import threading
from queue import Queue
import shutil
import wcUtil
import wcNetwork


#######################
# Global Parameters
#######################

matches = \
[
	{
		"channel": None,
		"draw": "3.84",
		"fid": "733784",
		"ghalfscore": None,
		"gid": "12",
		"gname": "西班牙",
		"gscore": None,
		"gsxname": "西班牙",
		"hhalfscore": None,
		"hid": "7",
		"hname": "俄罗斯",
		"hscore": None,
		"hsxname": "俄罗斯",
		"lost": "1.59",
		"status": "1",
		"stime": "2018-07-01 22:00",
		"win": "6.43"
	},
]

teams = {'俄罗斯':'Russia', '埃及':'Egypt', '摩洛哥':'Morocco', '葡萄牙':'Portugal', '法国':'France', '阿根廷':'Argentina', 
'秘鲁':'Peru', '克罗地亚':'Croatia', '哥斯达黎加':'Costa Rica', '德国':'Germany', '巴西':'Brazil', '瑞典':'Sweden', '比利时':'Belgium', 
'突尼斯':'Tunish', '哥伦比亚':'Colombia', '波兰':'Poland', '乌拉圭':'Uruguay', '伊朗':'Iran', '丹麦':'Denmark', '尼日利亚':'Nigeria', 
'塞尔维亚':'Serbia', '韩国':'Korea', '英格兰':'England', '日本':'Japan', '沙特':'Saudi Arab', '西班牙':'Spain', '澳大利亚':'Australia', 
'冰岛':'Iceland', '墨西哥':'Mexico', '瑞士':'Switzerland', '巴拿马':'Panama', '塞内加尔':'Senegal'}

rootDirectory = 'C:\\Users\\Robin\\Desktop\\charts'
groupDirectory = os.path.join(rootDirectory, 'group phase')
knockoutDirectory = os.path.join(rootDirectory, 'knockout phase')
conjunctionDirectory = os.path.join(rootDirectory, 'conjunction')
chartWidth = 2000
chartHeight = 900
		
class ChartGroup(object):
	"""docstring for ChartGroup"""
	def __init__(self, charts:[], faceOff:str):
		super(ChartGroup, self).__init__()
		self.charts = charts
		self.faceOff = faceOff

#######################
# Crawl Europe
#######################

def queryEuropeanIndex(matchID:str) -> []:
	url = 'http://odds.500.com/fenxi1/json/ouzhi.php'
	parameters = {'fid':matchID, 'cid':5, 'r':1, 'type':'europe', '_':str(int(time.time()*1000))}
	response = wcNetwork.responseOfGet(url, wcNetwork.headerOdds, parameters)
	return json.loads(response)

def assembleEuropeanChart(json:[], faceOff:str) -> Line:
	iterator = zip(*reversed(json))
	winOdds = list(next(iterator))
	drawOdds = list(next(iterator))
	lossOdds = list(next(iterator))	
	returnRates = list(next(iterator))
	publishTimes = list(next(iterator))
	winProb = [r/o for r,o in zip(returnRates,winOdds)]
	drawProb = [r/o for r,o in zip(returnRates,drawOdds)]
	lossProb = [r/o for r,o in zip(returnRates,lossOdds)]
	line_chart = Line(
		width=chartWidth,
		height=chartHeight,
		legend_at_bottom=False,
		truncate_label=-1,
		x_label_rotation=-30,
		show_x_guides=True,
		x_title='Date/Time',
		y_title='Odds',
		stroke_style={'width': 2},
		style=NeonStyle(
			label_font_size = 16,
			major_label_font_size = 16,
			title_font_size = 24,
			legend_font_size = 20
		)
	)
	line_chart.title = 'Trends in European Odds for [' + faceOff + ']'
	line_chart.x_labels = publishTimes
	line_chart.add('Win Odds', winOdds)
	line_chart.add('Draw Odds',  drawOdds)
	line_chart.add('Loss Odds',  lossOdds)
	line_chart.add('Return Rates', returnRates, secondary=True)
	return line_chart

def euroPeanChart(matchID:str, faceOff:str) -> Line:
	return assembleEuropeanChart(queryEuropeanIndex(matchID), faceOff)

#######################
# Crawl Asia
#######################

def queryAsianIndex(matchID:str) -> []:
	url = 'http://odds.500.com/fenxi1/inc/yazhiajax.php'
	parameters = {'fid':matchID, 'id':5, 'r':1, 't':str(int(time.time()*1000))}
	response = wcNetwork.responseOfGet(url, wcNetwork.headerOdds, parameters)
	return json.loads(response)

def assembleAsianChart(json:[], faceOff:str) -> Line:
	upperOdds, lowerOdds, publishTimes, handicaps = [], [], [], []
	for htmlString in reversed(json):
		root = html.fromstring(htmlString)
		nodes = root.xpath('//td')
		upper = nodes[0].text
		lower = nodes[2].text
		handicapString = nodes[1].text
		publishTime = nodes[3].text
		upperOdds.append(float(upper))
		handicaps.append(-wcUtil.handicapString2number(handicapString))
		lowerOdds.append(float(lower))
		publishTimes.append(publishTime)
	line_chart = Line(
		width=chartWidth,
		height=chartHeight,
		legend_at_bottom=False,
		truncate_label=-1,
		x_label_rotation=-30,
		show_x_guides=True,
		secondary_range=(-2.5,2.5),
		x_title='Date/Time',
		y_title='Odds',
		stroke_style={'width': 2},
		style=NeonStyle(
			label_font_size = 16,
			major_label_font_size = 16,
			title_font_size = 24,
			legend_font_size = 20
		)
	)
	line_chart.title = 'Trends in Asian Odds & Handicaps for [' + faceOff + ']'
	line_chart.x_labels = publishTimes
	line_chart.y_labels = [f/100 for f in range(45,146,5)]
	line_chart.add('Upper Odds', upperOdds)
	line_chart.add('Lower Odds',  lowerOdds)
	line_chart.add('Handicaps', handicaps, secondary=True)
	line_chart.y_labels_major = [0.75,0.85,0.90,1.00,1.10]
	return line_chart

def asianChart(matchID:str, faceOff:str) -> Line:
	return assembleAsianChart(queryAsianIndex(matchID), faceOff)


#############################
# Crawl Conceding Points
#############################

def queryConcedingIndex(matchID:str) -> []:
	url = 'http://odds.500.com/fenxi1/inc/daxiaoajax.php'
	parameters = {'fid':matchID, 'id':5, 't':str(int(time.time()*1000))}
	response = wcNetwork.responseOfGet(url, wcNetwork.headerOdds, parameters)
	return json.loads(response)

def assembleConcedingChart(json:[], faceOff:str) -> Line:
	upperOdds, lowerOdds, publishTimes, handicaps = [], [], [], []
	for htmlString in reversed(json):
		root = html.fromstring(htmlString)
		nodes = root.xpath('//td')
		upper = nodes[0].text
		lower = nodes[2].text
		publishTime = nodes[3].text
		concedingHandicaps = [float(handicap) for handicap in nodes[1].text.strip().split('/')]
		concedingHandicap = sum(concedingHandicaps)/len(concedingHandicaps)
		handicaps.append(concedingHandicap)
		upperOdds.append(float(upper))
		lowerOdds.append(float(lower))
		publishTimes.append(publishTime)
	line_chart = Line(
		width=chartWidth,
		height=chartHeight,
		legend_at_bottom=False,
		truncate_label=-1,
		x_label_rotation=-30,
		show_x_guides=True,
		secondary_range=(1.0, 3.5),
		x_title='Date/Time',
		y_title='Odds',
		stroke_style={'width': 2},
		style=NeonStyle(
			label_font_size = 16,
			major_label_font_size = 16,
			title_font_size = 24,
			legend_font_size = 20
		)
	)
	line_chart.title = 'Trends in Conceding Odds & Handicaps for [' + faceOff + ']'
	line_chart.x_labels = publishTimes
	line_chart.y_labels = [f/100 for f in range(70,121,5)]
	line_chart.add('Upper Odds', upperOdds)
	line_chart.add('Lower Odds',  lowerOdds)
	line_chart.add('Handicaps', handicaps, secondary=True)
	line_chart.y_labels_major = [0.75,0.85,0.90,1.00,1.10]
	return line_chart

def concedingChart(matchID:str, faceOff:str) -> Line:
	return assembleConcedingChart(queryConcedingIndex(matchID), faceOff)

#############################
# Reusable Chart Group 
#############################

def chartGroups(matches:[]) -> []:
	results = []
	for match in matches:
		matchID = match['fid']
		homeTeam = teams[match['hname']]
		awayTeam = teams[match['gname']]
		homeScore = match['hscore']
		awayScore = match['gscore']
		faceOff = None
		if homeScore and awayScore:
			faceOff = homeTeam + ' ' + homeScore + '-' + awayScore + ' ' + awayTeam
		else:
			faceOff = homeTeam + ' vs ' + awayTeam
		chartEurope = euroPeanChart(matchID, faceOff)
		chartAsia = asianChart(matchID, faceOff)
		chartConcede = concedingChart(matchID, faceOff)
		europeanName = 'EuropeanOdds '+ faceOff + '.png'
		asianName = 'AsianOdds '+ faceOff + '.png'
		concedeName = 'ConcedeOdds '+ faceOff + '.png'
		results.append(ChartGroup([(chartEurope, europeanName), (chartAsia, asianName), (chartConcede, concedeName)], faceOff))
	return results

#############################
# Crawl Group Matches
#############################

def queryGroupIndex(groupName:str) -> []:
	url = 'http://liansai.500.com/index.php'
	parameters = {'c':'score', 'a':'getmatch', 'stid':'12379', 'round':groupName}
	response = wcNetwork.responseOfGet(url, wcNetwork.headerLeague, parameters)
	return json.loads(response)

def assembleGroupCharts(json:[], plotQueue:Queue):
	for group in chartGroups(json):
		for chart, name in group.charts:
			plotQueue.put((chart, os.path.join(groupDirectory, groupName, name)))
	
def crawlGroup(matchQueue:Queue, plotQueue:Queue):
	wcUtil.deleteAndMakeDirectory(os.path.join(groupDirectory, groupName))
	groupName = matchQueue.get()
	assembleGroupCharts(queryGroupIndex(groupName), plotQueue)
	print(threading.current_thread().name+' has done its job.')
	matchQueue.task_done()

#############################
# Crawl Knockout Matches
#############################

def queryKnockoutIndex() -> []:
	url = 'http://liansai.500.com/index.php'
	parameters = {'c':'match', 'a':'getmatch', 'sid':'4667'}
	response = wcNetwork.responseOfGet(url, wcNetwork.headerLeague, parameters)
	return json.loads(response)

def crawlKnockout():
	url = 'http://liansai.500.com/index.php?c=match&a=getmatch&sid=4667'
	json = queryKnockoutIndex()
	for group in chartGroups(json):
		for chart, name in group.charts:
			chart.render_to_png(os.path.join(knockoutDirectory, name))

#######################
# Main Interface
#######################

def generateConjunctiveChartsUponGroupTeams(teams:{}):
	for groupName, teamName in teams.items():
		qualifiedChartPaths = []
		directoryPath = os.path.join(groupDirectory, groupName)
		for chartName in os.listdir(directoryPath):
			chartPath = os.path.join(directoryPath, chartName)
			_, ext = os.path.splitext(chartName)
			if os.path.isfile(chartPath) and ext.lower()=='.png' and teamName in chartName:
				qualifiedChartPaths.append(chartPath)
		outcomePath = os.path.join(conjunctionDirectory, teamName+'.png')
		wcUtil.spliceCharts(qualifiedChartPaths, outcomePath, chartWidth, chartHeight)

def generateConjunctiveChartsBetweenKnockoutTeams(team1:str, team2:str):
	qualifiedChartPaths = []
	for chartName in os.listdir(knockoutDirectory):
		chartPath = os.path.join(knockoutDirectory, chartName)
		_, ext = os.path.splitext(chartName)
		if os.path.isfile(chartPath) and ext.lower()=='.png' and \
		team1 in chartName and team2 in chartName:
			qualifiedChartPaths.append(chartPath)
	outcomePath = os.path.join(conjunctionDirectory, team1 + ' vs ' + team2 + '.png')
	wcUtil.spliceCharts(qualifiedChartPaths, outcomePath, chartWidth, chartHeight)

def generateGroupCharts():
	wcUtil.deleteAndMakeDirectory(groupDirectory)
	groupNames = 'ABCDEFGH'
	matchQueue = Queue()
	plotQueue = Queue()
	for groupName in groupNames:
		matchQueue.put(groupName)
		thread = threading.Thread(target=crawlGroup, args=(matchQueue, plotQueue))
		thread.start()
	matchQueue.join()
	while not plotQueue.empty():
		chart, chartPath = plotQueue.get()
		chart.render_to_png(chartPath)
		plotQueue.task_done()

def generateknockoutCharts():
	wcUtil.deleteAndMakeDirectory(knockoutDirectory)
	crawlKnockout()

def generateKnockoutChartsWithMatches(matches:[]):
	for group in chartGroups(matches):
			chartPaths = []
			for chart, name in group.charts:
				path = os.path.join(knockoutDirectory, name)
				chartPaths.append(path)
				chart.render_to_png(path)
			outcomePath = os.path.join(conjunctionDirectory, group.faceOff + '.png')
			wcUtil.spliceCharts(chartPaths, outcomePath, chartWidth, chartHeight)


#######################
# Main Logic
#######################

generateKnockoutChartsWithMatches(matches)
