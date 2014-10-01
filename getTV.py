import requests
import urllib2
import httplib2
import subprocess
from bs4 import BeautifulSoup

PB_base_url = "http://thepiratebay.se/search/"
PB_sort_url = "/0/7/0"
magnetConverter = "http://magnet2torrent.com/upload/"
latestEpisodes = []
latestEpisode = ''

tvListFile = open('tvList', 'r')
tvList = tvListFile.readlines()
tvListFile.close()

#getNextEpisode takes integer of lastEpisode watched (season*100+episode), 
#boolean of whether to seach in the next season, and a counter that counts
#the number of episodes downloaded in this run
#It returns a string used in the search string for the next episode

def getNextEpisode(lastEpisode, newSeason, counter):
	season = lastEpisode/100
	episode = lastEpisode - season*100
	if (newSeason):
		season = season + 1
		episode = counter
	else:
		episode = episode + counter
	if (season < 10):
		seasonStr = 'S0' + str(season)
	else:
		seasonStr = 'S' + str(season)
	if (episode < 10):
		episodeStr = 'E0' + str(episode)
	else:
		episodeStr = 'E' + str(episode)
	return seasonStr + episodeStr

#getSearchString takes one line from the tvList and returns the search string for next episode
def getSearchString(tv, newSeason, counter):
	tvInfo = tv.split(':')
	tvName = tvInfo[0]
	lastEpisode = int(tvInfo[1])
	return tvName + ' ' + getNextEpisode(lastEpisode, newSeason, counter)

#startDownload calls btc to start the download
def startDownload(torrentPath):
	subprocess.call(["btc", "add", torrentPath])
	print ('start downloading...')

#getTorrentFile takes the magnetLink, converts it to a torrentFile, writes the file to disk.
def getTorrentFile(searchString, magnetLink):
	print('obtaining torrent file...')
	payload = {'magnet': magnetLink}
	r = requests.post(magnetConverter, data=payload)
	torrentPath = 'torrents/' + searchString + '.torrent'
	torrentFile = open(torrentPath, 'w')
	torrentFile.write(r.content)
	torrentFile.close()
	startDownload(torrentPath)
	global latestEpisode
	latestEpisode = searchString

#findNextTorrent finds the torrent magnetlink of the next episode 
def findNextTorrent(tv, newSeason, counter):
	searchString = getSearchString(tv, newSeason, counter)
	pirateBayUrl = PB_base_url +  searchString + PB_sort_url
	print('searching for ' +  searchString)
	
	response = urllib2.urlopen(pirateBayUrl)
	html = response.read()
	soup = BeautifulSoup(html)
	bestLink = soup.find(title="Download this torrent using magnet")
	if (bestLink == None):
		if (newSeason):
			print('No more new episodes')
		else:
			counter = 1
			findNextTorrent(tv, True, counter)
	else:
		magnetLink = bestLink.get('href')
		getTorrentFile(searchString, magnetLink)
		findNextTorrent(tv, newSeason, counter + 1)

#convertStr converts episode number form form 'S01E01' to integer 101
def convertStr(latestEpisode):
	info = latestEpisode.split(' S')
	name = info[0]
	episodeInfo = info[1].split('E')
	season = int(episodeInfo[0])
	episode = int(episodeInfo[1])
	return name + ":" + str(season * 100 + episode) + '\n'

for tv in tvList:
	latestEpisode = ''
	findNextTorrent(tv, False, 1)
	if (latestEpisode == ''):
		latestEpisodes.append(tv)
	else:
		latestEpisodes.append(convertStr(latestEpisode))

#save the newest lastest episodes to tvList
tvListFile = open('tvList', 'w')
tvListFile.writelines(latestEpisodes)
