from music21 import *
from numpy import *
from scipy import stats
from os import listdir
from os.path import isfile, join
from functools import partial
import string 


localCorpus = corpus.corpora.LocalCorpus()

path = '../wikifonia'
mxlfiles = [join(path, f) for f in listdir(path) if (isfile(join(path, f)) and f[-3:] == "mxl")]

anotherPath  = '../wikifonia_en_chords_lyrics'
anotherMXL = [join(anotherPath, f) for f in listdir(anotherPath) if (isfile(join(anotherPath, f)) and f[-3:] == "mxl")]

nrcPath = '../scripts/NRC-v0.92.txt'


def update(numRun, totalRun, latestOutput):
    for o in latestOutput:
        print("Run (%d/%d)" % (numRun, totalRun))


def parseNRC(nrcp = nrcPath):
    '''
    Takes in a NRC text file and parse it into a dictionary mapping each word to a list of ints, 
    indicating the score for each sentiment. The field of the list is as below
    0       1             2       3      4    5         6         7        8         9
    [anger, anticipation, disgust, fear, joy, negative, positive, sadness, surprise, trust]

    '''
    nrc = open(nrcp, 'r')
    wordToEmotions = {}
    for line in nrc:
        entry = line.split("\t")
        if len(entry) != 3:
            continue
        else:
            try:
                wordToEmotions[entry[0]].append(int(entry[2]))
            except KeyError:
                wordToEmotions[entry[0]] = [int(entry[2])]
    nrc.close()
    return wordToEmotions


'''
 0       1             2       3      4    5         6         7        8         9
[anger, anticipation, disgust, fear, joy, negative, positive, sadness, surprise, trust]
'''
dic = parseNRC()

def sentimentStringToInt(sentString):
    strings = ["anger", "anticipation", "disgust", "fear", "joy", "negative", "positive", "sadness", "surprise", "trust"]
    return strings.index(sentString)

def sentimentIntToString(sentInt):
    strings = ["anger", "anticipation", "disgust", "fear", "joy", "negative", "positive", "sadness", "surprise", "trust"]
    return strings[sentInt]


#returns (count, deviations, neutral, notInDatabase)
def pitchDerivationOneSong(work):
    count = [0] * 10
    deviations = [[],[],[],[],[],[],[],[],[],[]] 
    neutral = 0
    notInDatabase = 0

    score = converter.parse(work)
    justNotes = score.parts[0].recurse().getElementsByClass('Note').stream()
    if len(justNotes) == 0:
        return (0, [])

    pitch = [p.ps for p in justNotes.pitches]

    avg = mean(pitch)
    stdv = std(pitch)

    tempStrings = {}

    for n in justNotes:
        lyricList = n.lyrics

        for i in range(len(lyricList)):

            lyric = lyricList[i].text.lower().translate(None, string.punctuation) #rid string of punctuations

            syllabic = lyricList[i].syllabic

            #handles case where sylables are seperated
            if syllabic == "begin":
                tempStrings[i] = lyric
                continue
            elif syllabic == "middle":
                tempStrings[i] += lyric
                continue
            elif syllabic == "end":
                lyric = tempStrings[i]+lyric if i in tempStrings.keys() else lyric
           
            if lyric not in dic:
                notInDatabase += 1  
                continue

            songDiv =  (n.pitch.ps - avg) / stdv 
            neutralWord = True
           
            for index, val in enumerate(dic[lyric]): 
            	if val == 1:
            		neutralWord = False
	                count[index] += 1
	                deviations[index] += [songDiv]

	        if neutralWord:
	        	neutral += 1

                
            tempStrings[i] = ""

    return (count, deviations, neutral, notInDatabase)


def getSentimentPitchDeviationParallel(mxlfiles):

    wordcount = [0] * 10
    deviations = [[],[],[],[],[],[],[],[],[],[]] 
    neutral = 0
    notInDatabase = 0

    count = 0 
    output = common.runParallel(mxlfiles, pitchDerivationOneSong, update)
    
    for count1, deviations1, neutral1, notInDatabase1 in output:
        wordcount = map(sum, zip(wordcount,count1))
        deviations = map(lambda (x,y): x+y, zip(deviations,deviations1))
        neutral += neutral1
        notInDatabase += notInDatabase1
    
    totalWords= sum(wordcount)+neutral+notInDatabase

    toPrint = ""

    toPrint += "\nPrinting sentiment-pitch results: \nCourpus Size = "+  str(len(mxlfiles))+"\nTotal lyrics wordcount = " +str(totalWords)
    toPrint += "\nNeutral, sentiment-free words: " + str(neutral) + "\nWords not in our database: "+ str(notInDatabase)
    
    for i in range(10):
    	toPrint += "\nSentiment: " + sentimentIntToString(i) + "\tOccurrence: " + str(wordcount[i])
    	#print(deviations[i])
    	if deviations[i]:
        	toPrint += "\nStandard deviations away from song average pitch: \t" + str(round(mean(deviations[i]),2))+  " (p = "+str(stats.kstest(deviations[i],"norm")[1]) +")\n"

    print(toPrint)

    res = open("pitch-result.txt", "w")
    res.write(toPrint)
    res.close()

#pitchDerivationOneSong('../wikifonia/wikifonia-9999.mxl')

getSentimentPitchDeviationParallel(anotherMXL[:10])


