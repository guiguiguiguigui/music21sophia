from music21 import *
from numpy import *
from collections import defaultdict
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
    strings = ["anger", "anticipation", "disgust", "fear", "joy", "negative", "positive", "sadness", "surprise", "trust", "neutral", "unknown"]
    return strings.index(sentString)

def sentimentIntToString(sentInt):
    strings = ["anger", "anticipation", "disgust", "fear", "joy", "negative", "positive", "sadness", "surprise", "trust", "neutral", "unknown"]
    return strings[sentInt]


#returns (count, deviationsPos, deviationsNeg, neutral, notInDatabase)
#neutralIndex = 10
#notInDatabaseIndex = 11

def pitchDerivationOneSong(work):
    count = [0] * 10 # number of lyrics with each sentiment

    # for Unpaired t-test, we need to have two groups of data: expriment and control 
    deviationsPos = [[],[],[],[],[],[],[],[],[],[],[]] 
    deviationsNeg = [[],[],[],[],[],[],[],[],[],[],[]] 

    neutral = [0,[]]
    notInDatabase = [0,[]]

    score = converter.parse(work)
    justNotes = score.parts[0].recurse().getElementsByClass('Note').stream()

    '''
    hasBegin = False
    for n in justNotes:
        lyricList = n.lyrics
        for l in lyricList:
            syllabic = l.syllabic
            if syllabic in ('begin', 'middle', 'end'):
                hasBegin = True
                break

    if not hasBegin:
        print("No hasBegin")
        return (count, deviationsPos, deviationsNeg, neutral, notInDatabase)

    '''
    pitch = [p.ps for p in justNotes.pitches]

    avg = mean(pitch)
    stdv = std(pitch)

    tempStrings = {}

    for n in justNotes:
        lyricList = n.lyrics


        for i in range(len(lyricList)):

            #lyric = lyricList[i].text.lower().translate(None, string.punctuation) #rid string of punctuations
            lyric = lyricList[i].text
            if isinstance(lyric,str):
                lyric = lyric.lower().translate(None, string.punctuation) #rid string of punctuations

            syllabic = lyricList[i].syllabic

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

            songDiv =  (n.pitch.ps - avg) / stdv 
           
            if lyric not in dic:
                notInDatabase[0] += 1
                notInDatabase[1] += [songDiv]  
                # print(lyric)
                continue

            neutralWord = True
           
            for index, val in enumerate(dic[lyric]): 
                if val == 1:
                    neutralWord = False
                    count[index] += 1
                    deviationsPos[index] += [songDiv]
                else:
                    deviationsNeg[index] += [songDiv]


            if neutralWord:
                neutral[0] += 1
                neutral[1] += [songDiv]
                
            tempStrings[i] = ""

    return (count, deviationsPos, deviationsNeg, neutral, notInDatabase)


#returns (count, consonancePos, consonanceNeg, neutral, notInDatabase)
def consonanceOneSong(work, returnScore=False, inChordEqConsonant=True):
    count = [0] * 10
    # for Unpaired t-test, we need to have two groups of data: expriment and control 
    consonancePos = [[],[],[],[],[],[],[],[],[],[],[]] 
    consonanceNeg = [[],[],[],[],[],[],[],[],[],[],[]] 

    neutral = [0,[]]
    notInDatabase = [0,[]]
    score = converter.parse(work)
    justNotes = score.parts[0].recurse().getElementsByClass('Note').stream()

 
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
                

            if lyric not in dic:
                notInDatabase[0] += 1
                continue

            cs = n.getContextByClass('ChordSymbol')
            if not cs:
                continue

            neutralWord = True

            if inChordEqConsonant is False:
                csp = cs.pitches
                newChord = chord.Chord(tuple(n.pitches) + csp)
                consonanceThis = [1] if newChord.isConsonant() else [0]
            else:
                # consider consonant if note pitch is in chord, regardless of
                # whether the chord itself is dissonant
                # use pitchClass to not have enharmonic be a problem
                if n.pitch.pitchClass in [p.pitchClass for p in cs.pitches]:
                    consonanceThis = [1]
                else:
                    consonanceThis = [0]

            for index, val in enumerate(dic[lyric]): 
                if val == 1:
                    neutralWord = False
                    count[index] += 1
                    consonancePos[index] += consonanceThis
                else:
                    consonanceNeg[index] += consonanceThis

            
            if neutralWord:
                neutral[0] += 1
                neutral[1] += [consonanceThis]

            # fix up the score for next time...
            if returnScore:
                sentimentLyric = n.lyric + ';'
                for i in range(len(dic[lyric])):
                    if dic[lyric][i] == 1:
                        sentimentLyric += ':' + sentimentIntToString(i)[0:3]

                n.lyric = str(consonanceThis) + '.' + sentimentLyric
            tempStrings[i] = ""
            tempNotes[i] = []

    if returnScore:
        return score
    else:
        return (count, consonancePos, consonanceNeg, neutral, notInDatabase)


def runParallel(mxlfiles, oneSongMethod, name):


    wordcount = [0] * 10 # number of occurences of each sentiment
    # for Unpaired t-test, we need to have two groups of data: expriment and control 
    pos = [[],[],[],[],[],[],[],[],[],[],[]] 
    neg = [[],[],[],[],[],[],[],[],[],[],[]] 
    neutral = [0,[]]
    notInDatabase = [0,[]]

    count = 0 
    output = common.runParallel(mxlfiles, oneSongMethod, update)

    def combineList(list1, list2):
        return map(lambda (x,y): x+y, zip(list1, list2))

    for count1, pos1, neg1,  neutral1, notInDatabase1 in output:
        wordcount = combineList(wordcount, count1)
        pos = combineList(pos, pos1)
        neg = combineList(neg, neg1)
        neutral = combineList(neutral, neutral1)
        notInDatabase = combineList(notInDatabase,notInDatabase1)
    
    totalWords= sum(wordcount)+neutral[0]+notInDatabase[0]

    toPrint = ""

    toPrint += "\nPrinting sentiment-"+name+" results: \nCorpus Size = "+  str(len(mxlfiles))+"\nTotal lyrics wordcount = " +str(totalWords)
    toPrint += "\nNeutral, sentiment-free words: " + str(neutral[0]) + "\nWords not in our database: "+ str(notInDatabase[0])
    
    for i in range(10):
        thisPos = pos[i]
        thisNeg = neg[i]
        toPrint += "\nSentiment: " + sentimentIntToString(i) + "\tOccurrence: " + str(wordcount[i])
        print(thisPos)
        print(thisNeg)
        print(neutral[1])
        #print(deviations[i])
        if thisPos:
            # toPrint += "\n" + str(thisDeviation)
            _, pValue = stats.ttest_ind(thisPos, thisNeg, equal_var=False)
            _, pValueN = stats.ttest_ind(thisPos, neutral[1], equal_var=False)
            
            if name == "pitch":
                
                deviationsFromMean = round(mean(thisPos), 4)
                toPrint += "\nStandard deviations away from song average pitch: \t" + str(deviationsFromMean)+  " (p = "+str(pValue) +")\n"
            
            elif name == "consonance":
                posAverage = sum(thisPos)/float(len(thisPos))
                negAverage = sum(thisNeg)/float(len(thisNeg))
                neuAverage = sum(neutral[1])/float(len(neutral[1]))
                percentMoreConsonanceNeg = 100*(posAverage - negAverage)/negAverage
                percentMoreConsonanceNeu = 100*(posAverage - neuAverage)/neuAverage
                toPrint += "\nMore consonant than no such sentiment: " + str(percentMoreConsonanceNeg) + " % (p = "+str(pValue) +")\n"
                toPrint += "More consonant than neutral words: " + str(percentMoreConsonanceNeu) + " % (p = "+str(pValueN) +")\n"



    print(toPrint)

    res = open("pitch-result.txt", "w")
    res.write(toPrint)
    res.close()

#pitchDerivationOneSong('../wikifonia/wikifonia-9999.mxl')

#getSentimentPitchDeviationParallel(anotherMXL)

#runParallel(anotherMXL,pitchDerivationOneSong,"pitch")
if __name__ == '__main__':
    runParallel(anotherMXL[:10],consonanceOneSong,"consonance")

