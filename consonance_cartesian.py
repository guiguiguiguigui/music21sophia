from __future__ import print_function

from music21 import *
from numpy import *
from scipy import stats
from os import listdir
from os.path import isfile, join
from functools import partial
from collections import defaultdict
import string 


debug = False

systemPrint = print

def debugPrint(*args, **kwargs):
    if debug:
        systemPrint(*args, **kwargs)

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


#returns (count, consonancePos, deviationsNeg, neutral, notInDatabase)
def consonanceOneSong(work):
    count = [0] * 10
    # for Unpaired t-test, we need to have two groups of data: expriment and control 
    consonancePos = [[],[],[],[],[],[],[],[],[],[],[]] 
    consonanceNeg = [[],[],[],[],[],[],[],[],[],[],[]] 

    neutral = [0,[]]
    notInDatabase = [0,[]]

    score = converter.parse(work)
 
    tempStrings = {}
    tempNotes = defaultdict(list)

    for n in justNotes:
        lyricList = n.lyrics

        for i in range(len(lyricList)):

            lyric = lyricList[i].text
            if isinstance(lyric,str):
                lyric = lyric.lower().translate(None, string.punctuation) #rid string of punctuations

            syllabic = lyricList[i].syllabic
            tempNotes[i].append(n.pitches)
            #handles case where sylables are seperated
            if syllabic == "begin":
                tempStrings[i] = lyric
                continue
            elif syllabic == "middle":
                if i in tempStrings.keys(): 
                    tempStrings[i] += lyric
                else:
                    tempStrings[i] = lyric
                continue
            elif syllabic == "end":
                lyric = tempStrings[i]+lyric if i in tempStrings.keys() else lyric
                

            cs = n.getContextByClass('ChordSymbol')
            if not cs:
                continue
            csp = cs.pitches
            newChord = chord.Chord(tuple(n.pitches) + csp)


            if lyric not in dic:
                notInDatabase[0] += 1
                notInDatabase[1] += [songDiv]  
                # print(lyric)
                continue

            neutralWord = True

            for index, val in enumerate(dic[lyric]): 
                consonanceThis = [1] if newChord.isConsonant() else [0]
                if val == 1:
                    neutralWord = False
                    count[index] += 1
                    consonancePos[index] += consonanceThis
                else:
                    consonanceNeg[index] += consonanceThis

            
            if neutralWord:
                neutral[0] += 1
                neutral[1] += [songDiv]

            tempStrings[i] = ""
            tempNotes[i] = []

    return (count, consonancePos, consonanceNeg, neutral, notInDatabase)


def getSentimentConsonanceParallel(mxlfiles):

    wordcount = [0] * 10
    consonance = [0] * 10


    count = 0 
    output = common.runParallel(mxlfiles, consonanceOneSong, update)
    
    for count1, consonance1 in output:
        wordcount = map(sum, zip(wordcount,count1))
        consonance = map(sum, zip(consonance,consonance1))
    

    toPrint = ""

    toPrint += "\nPrinting sentiment-pitch results: \nCorpus Size = "+  str(len(mxlfiles)) #+"\nTotal lyrics wordcount = " +str(totalWords)
    #toPrint += "\nNeutral, sentiment-free words: " + str(neutral) + "\nWords not in our database: "+ str(notInDatabase)
    
    for i in range(10):
    	toPrint += "\nSentiment: " + sentimentIntToString(i) + "\tOccurrence: " + str(wordcount[i])
    	#print(deviations[i])
        if wordcount[i]:
            toPrint += "\n Percentage of consonant notes: \t" + str(round(100*consonance[i]/wordcount[i],2)) +"%"#+  " (p = "+str(stats.kstest(deviations[i],"norm")[1]) +")\n"

    print(toPrint)


#print(consonanceOneSong('../wikifonia/wikifonia-9999.mxl'))
'''
def getTitle(mxl):
    score = converter.parse(mxl)
    return score.metadata.title

count = 0
string = ""

for score in anotherMXL:
    count += 1
    if (count%50 == 0):
        print("--- Finished " + str(count))
    string += getTitle(score) +"\n"

res = open("title_list.txt", "w")
res.write(string)
res.close()
'''
getSentimentConsonanceParallel(anotherMXL)


