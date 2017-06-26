# encoding=utf8  
from menu import Menu
import os
import pytvmaze
import sys
import pickle
import random
from functools import partial
import sys  
import shutil

reload(sys)  
sys.setdefaultencoding('utf8')

tvm = pytvmaze.TVMaze()

currentShows = []

def showMainMenu():
	menu = Menu(title="MarkovTV")
	menu.set_prompt("Choose an option:")
	menu.set_options([
	("Generate Episodes", showGenerateEpisodeMenu),
	("Register Show", showRegisterShowMenu),
	("Unregister Show", showUnregisterShowMenu),
	("Exit", Menu.CLOSE)
	])
	menu.open()

def showGenerateEpisodeMenu():
	global currentShows

	def addToCurrentShows(showName):
		currentShows.append(showName)
		menu.close()
		showGenerateEpisodeMenu()
		return

	def clearCurrentShows():
		global currentShows
		currentShows = []
		menu.close()
		showGenerateEpisodeMenu()
		return

	menu = Menu(title="Generate Episode : Current={}".format(currentShows))
	menu.set_prompt("Select a show:")

	options = []
	for (dirpath, dirnames, filenames) in os.walk("data"):
		for dirname in dirnames:
			if not dirname in currentShows:
				options.append((dirname, partial(addToCurrentShows, dirname)))
		break
	if len(currentShows) > 0:
		options.append(("Generate", partial(generateEpisodes, currentShows)))
		options.append(("Clear Shows", clearCurrentShows))
	options.append(("Back", Menu.CLOSE))
	menu.set_options(options)
	menu.open()

def showRegisterShowMenu():
	showName = raw_input("Enter a show name: ")
	show = None
	try:
		show = tvm.get_show(show_name=showName, embed="episodes")
	except:
		print "No show with name {}".format(showName)
		raw_input()
		return

	hasData = False
	for season in show:
		for episode in season:
			if episode.summary:
				hasData = True
				break
		if hasData:
			break
			
	if not hasData:
		print "Found show {}, but no episode data...".format(showName)
		raw_input()
		return

	print "... Dumping Input"
	dumpShowInput(show, showName)

	print "... Preparing Chains"
	prepareChains(showName)

	print "Success!"
	raw_input()

def showUnregisterShowMenu():
	menu = Menu(title="Unregister Show")
	menu.set_prompt("Select a show:")

	def showDeletionConfirmation(showName):
		submenu = Menu(title="Removing {}".format(showName))
		submenu.set_prompt("Are you sure?")
		submenu.set_options([
		("No", Menu.CLOSE),
		("Yes", partial(deleteShowData, showName, submenu))
		])
		submenu.open()

	def deleteShowData(showName, submenu):
		shutil.rmtree("data/{}".format(showName))
		submenu.close()
		menu.close()
		showUnregisterShowMenu()
		return

	options = []
	for (dirpath, dirnames, filenames) in os.walk("data"):
		for dirname in dirnames:
			if not dirname in currentShows:
				options.append((dirname, partial(showDeletionConfirmation, dirname)))
		break
	options.append(("Back", Menu.CLOSE))
	menu.set_options(options)
	menu.open()

def markovStr(str):
	return "BEGIN NOW {} END".format(str.encode('utf-8'))

def dumpShowInput(show, showName):
	dirName = "data/{}".format(showName)
	if not os.path.exists(dirName):
		os.makedirs(dirName)

	titles = open("{}/titles.txt".format(dirName), "w")
	summaries = open("{}/summaries.txt".format(dirName), "w")
	for season in show:
		for episode in season:
			if episode.summary:
				print >> titles, markovStr(format(episode))
				print >> summaries, markovStr(episode.summary)

def generate_trigram(words):
    if len(words) < 3:
        return
    for i in xrange(len(words) - 2):
        yield (words[i], words[i+1], words[i+2])

def prepareChains(showName):
	chainTypes = ["titles", "summaries"]
	for chainType in chainTypes:
		chain = {}
		inputFile = open("data/{}/{}.txt".format(showName, chainType), "r")

		for line in inputFile.readlines():
		    words = line.split()
		    for word1, word2, word3 in generate_trigram(words):
		        key = (word1, word2)
		        if key in chain:
		            chain[key].append(word3)
		        else:
		            chain[key] = [word3]
		  
		pickle.dump(chain, open("data/{}/{}.p".format(showName, chainType), "wb" ))

def markov(chain):
	new_review = []
	sword1 = "BEGIN"
	sword2 = "NOW"
	  
	while True:
	    sword1, sword2 = sword2, random.choice(chain[(sword1, sword2)])
	    if sword2 == "END":
	        break
	    new_review.append(sword2)
	  
	return ' '.join(new_review)

def combineChains(chain1, chain2):
	for k, v in chain2.iteritems():
		if k in chain1:
			chain1[k].extend(v)
		else:
			chain1[k] = v
	return chain1

def generateEpisode(showNames):
	showName = showNames[0]
	titles = pickle.load(open("data/{}/titles.p".format(showName)))
	summaries = pickle.load(open("data/{}/summaries.p".format(showName)))

	if len(showNames) > 1:
		for i in range(1, len(showNames)):
			showName2 = showNames[i]
			titles2 = pickle.load(open("data/{}/titles.p".format(showName2)))
			summaries2 = pickle.load(open("data/{}/summaries.p".format(showName2)))
			titles = combineChains(titles, titles2)
			summaries = combineChains(summaries, summaries2)

	return "{}:\n{}".format(markov(titles), markov(summaries))

def generateEpisodes(showNames):
	num_episodes = int(raw_input("Enter number of episodes: "))
	print

	for i in range(num_episodes):
		print generateEpisode(showNames)
		print ""
	raw_input()

showMainMenu()