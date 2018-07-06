import os
from PIL import Image

#######################
# String Process
#######################

def handicapString2number(handicapString:str) -> float:
	handicapString = handicapString.strip()
	if handicapString == '平手':
		return 0
	elif handicapString == '平手/半球':
		return -0.25
	elif handicapString == '半球':
		return -0.5
	elif handicapString == '半球/一球':
		return -0.75
	elif handicapString == '一球':
		return -1.0
	elif handicapString == '一球/球半':
		return -1.25
	elif handicapString == '球半':
		return -1.5
	elif handicapString == '球半/两球':
		return -1.75
	elif handicapString == '两球':
		return -2.0
	elif handicapString == '两球/两球半':
		return -2.25
	elif handicapString == '两球半':
		return -2.5
	elif handicapString == '受平手/半球':
		return 0.25
	elif handicapString == '受半球':
		return 0.5
	elif handicapString == '受半球/一球':
		return 0.75
	elif handicapString == '受一球':
		return 1.0
	elif handicapString == '受一球/球半':
		return 1.25
	elif handicapString == '受球半':
		return 1.5
	elif handicapString == '受球半/两球':
		return 1.75
	elif handicapString == '受两球':
		return 2.0
	elif handicapString == '受两球/两球半':
		return 2.25
	elif handicapString == '受两球半':
		return 2.5
	else:
		print('Corrupt handicap:' + handicapString)
		raise Exception('Corrupt handicap.')


#######################
# File Process
#######################

def remove_readonly(func, path, _):
	"Clear the readonly bit and reattempt the removal"
	os.chmod(path, stat.S_IWRITE)
	func(path)

def deleteAndMakeDirectory(directoryPath:str):
	if os.path.exists(directoryPath):
		shutil.rmtree(directoryPath, onerror=remove_readonly)
	try:
		os.mkdir(directoryPath)
	except FileExistsError as e:
		print(directoryPath + 'already exists.')
		raise e

def spliceCharts(chartPaths:[], outcomePath:str, chartWidth:int, chartHeight:int):
	canvas = Image.new('RGB', (chartWidth, chartHeight*len(chartPaths)))
	for i, chartPath in enumerate(chartPaths):
		chart = Image.open(chartPath)
		canvas.paste(chart, (0, chartHeight*i))
	canvas.save(outcomePath)