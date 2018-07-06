import random
import requests

headerLeague = {
	'Accept': 'application/json, text/javascript, */*',
	'Accept-Language': 'en-US, en; q=0.8, zh-Hans-CN; q=0.5, zh-Hans; q=0.3',
	'Connection': 'close',
	'Host': 'liansai.500.com',
	'Content-Type': 'application/x-www-form-urlencoded',
	'Referer': 'http://liansai.500.com/',
	'X-Requested-With': 'XMLHttpRequest',
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134'
}

headerOdds = {
	'Accept': 'application/json, text/javascript, */*',
	'Accept-Language': 'en-US, en; q=0.8, zh-Hans-CN; q=0.5, zh-Hans; q=0.3',
	'Connection': 'close',
	'Content-Type': 'application/x-www-form-urlencoded',
	'Host': 'odds.500.com',
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134',
	'X-Requested-With': 'XMLHttpRequest'
}

headerScore = {
	'Accept': 'text/html, application/xhtml+xml, application/xml; q=0.9, */*; q=0.8',
	'Accept-Language': 'en-US, en; q=0.8, zh-Hans-CN; q=0.5, zh-Hans; q=0.3',
	'Connection': 'close',
	'Host': 'odds.500.com',
	'Content-Type': 'text/html',
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134',
}

def responseOfGet(url:str, headers:{}, parameters:{}) -> bytes:
	response = requests.get(url, headers=headers, params=parameters)
	while response.status_code != requests.codes.ok:
		print(threading.current_thread().name + ': network access status ' + str(response.status_code) + ' emerge.')
		time.sleep(random.random())
		response = requests.get(url, headers=headers, params=parameters)
	return response.content