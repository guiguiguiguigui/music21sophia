from music21 import *
from numpy import *
from scipy import stats
from os import listdir
from os.path import isfile, join
import re
from functools import partial


localCorpus = corpus.corpora.LocalCorpus()
#localCorpus.addPath('user/phi/Desktop/2cool4school/music21/wikifonia')
#print(localCorpus.directoryPaths)

#path = '/Users/Phi/Desktop/2cool4school/music21/wikifonia'
path = '../wikifonia'
mxlfiles = [join(path, f) for f in listdir(path) if (isfile(join(path, f)) and f[-3:] == "mxl")]


#anotherPath  = '/Users/Phi/Desktop/2cool4school/music21/new_out/en'
anotherPath  = '../new_out/enOrganized/lyrics_and_chords'
anotherMXL = [join(anotherPath, f) for f in listdir(anotherPath) if (isfile(join(anotherPath, f)) and f[-3:] == "mxl")]
#print mxlfiles
nrcPath = '../scripts/NRC-v0.92.txt'


def update(numRun, totalRun, latestOutput):
    for o in latestOutput:
        print("Run %s (%d/%d)" % (o, numRun, totalRun))

def getDeviationParallel(mxlfiles, word):

    wordCount = 0
    deviations = []
    count = 0 
    getThisDeviationFunction = partial(getDeviationForOneSong, word=word)
    output = common.runParallel(mxlfiles[:500],getThisDeviationFunction, update)
    for oneSongWordCount, oneSongDeviations in output:
        wordCount += oneSongWordCount
        deviations += oneSongDeviations
       

    print("\nPrinting lyric related to song average results:")
    print("The lyric \""+word+"\" appeared "+ str(wordCount) + " times in our courpus of size " + str(len(mxlfiles))+".")
    if deviations:
        print("On average, they are " + str(round(mean(deviations),2))+  " standard deviations away from the average pitch of the song. (p = "+str(stats.kstest(deviations,"norm")[1]) +")" +"\n")



def getDeviationForOneSong(work, word):
    '''
    Takes in a filename (work) and a word to search for (default 'high') and returns two elements: the number
    of times that the word appears and the pitch deviation from the average for that word.

    >>> wc, dev = getDeviationForOneSong('../wikifonia/wikifonia-9999.mxl', 'the')
    >>> wc
    1
    >>> dev
    [-1.3195033341654732]
    '''
    wordCount = 0
    deviations = []
    try:
        score = converter.parse(work)
        lyric = search.lyrics.LyricSearcher(score.parts[0])
        justNotes = score.parts[0].recurse().getElementsByClass('Note')
        if len(justNotes) == 0:
            return (0, [])
        pitch = [p.ps for p in justNotes.pitches]

        avg = mean(pitch)
        stdv = std(pitch)

        words = lyric.search(re.compile(r"\b"+word,re.IGNORECASE))

        if words:
            for parts in words:
                for res in parts.els:
                    wordCount+=1
                    deviations += [ (res.pitch.ps - avg) / stdv ]
    except Exception:
        pass

    return (wordCount, deviations)





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

def sentimentStringToInt(sentString):
    strings = ["anger", "anticipation", "disgust", "fear", "joy", "negative", "positive", "sadness", "surprise", "trust"]
    return strings.index(sentString)

def sentimentIntToString(sentInt):
    strings = ["anger", "anticipation", "disgust", "fear", "joy", "negative", "positive", "sadness", "surprise", "trust"]
    return strings[sentInt]

def getSentimentPitchDeviationParallel(mxlfiles, sentiment="joy"):
    if isinstance(sentiment, int):
        sentInt = sentiment
        sentStr = sentimentIntToString(sentiment)
    elif isinstance(sentiment, str):
        sentInt = sentimentStringToInt(sentiment)
        sentStr = sentiment
    else:
        raise TypeError
    
    wordCount = 0
    deviations = []
    count = 0 
    getThisSentimentFunction = partial(getSentimentPitchDeviationForOneSong, sentiment=sentInt)
    output = common.runParallel(mxlfiles[:50], getThisSentimentFunction, update)
    for oneSongWordCount, oneSongDeviations in output:
        wordCount += oneSongWordCount
        deviations += oneSongDeviations
    
  
    print("\nPrinting sentiment results:")
    print("Lyrics with sentiment of "+sentStr+" appeared "+ str(wordCount) + " times in our courpus of size " + str(len(mxlfiles))+".")
    if deviations:
        print("On average, they are " + str(round(mean(deviations),2))+  " standard deviations away from the average pitch of the song. (p = "+str(stats.kstest(deviations,"norm")[1]) +")" +"\n")

def getSentimentPitchDeviationForOneSong(work, sentiment): 
    '''
    returns (sentimentCount, averageDeviations) of input.

    >>> wc, dev = getSentimentPitchDeviationForOneSong('../wikifonia/wikifonia-9999.mxl',4)
    >>> wc
    7
    >>> dev
    [-0.22069984592803385, -1.3195033341654732, -0.49540071798739366, 0.87810364230940541, 0.87810364230940541, -1.3195033341654732, 0.60340277025004563]
    '''
    dic = parseNRC()
    count = 0
    deviations = []

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

            lyric = lyricList[i].text.lower()

            syllabic = lyricList[i].syllabic

            if syllabic == "begin":
                tempStrings[i] = lyric
                continue
            elif syllabic == "middle":
                tempStrings[i] += lyric
                continue
            elif syllabic == "end":
                lyric = tempStrings[i]+lyric
           
            if lyric not in dic:
                continue  

            if dic[lyric][sentiment] == 1:
                count += 1
                deviations += [ (n.pitch.ps - avg) / stdv ]
                
            tempStrings[i] = ""

    return (count, deviations)
    

def getConsonanceForOneSong(work, sentiment):
    '''
    returns how many notes are consonant of a specific sentiment
    (#of occurance, #of consonance)
    '''
    wordCount = 0
    consonance = 0
    dic = parseNRC()

    score = converter.parse(work)

    for i in score.recurse().getElementsByClass('Note'):
        cs = i.getContextByClass('ChordSymbol')
        csp = cs.pitches
        newChord = chord.Chord(tuple(i.pitches) + csp)
        print(i, newChord, newChord.isConsonant(), i.lyric)

    return (wordCount, consonance)

    #beat strenth???
'''
    tempStrings = {}
    
    for n in justNotes:
        lyricList = n.lyrics

        for i in range(len(lyricList)):

            lyric = lyricList[i].text.lower()

            syllabic = lyricList[i].syllabic

            if syllabic == "begin":
                tempStrings[i] = lyric
                continue
            elif syllabic == "middle":
                tempStrings[i] += lyric
                continue
            elif syllabic == "end":
                lyric = tempStrings[i]+lyric
           
            if lyric not in dic:
                continue  

            if dic[lyric][sentiment] == 1:
                count += 1
                deviations += [ (n.pitch.ps - avg) / stdv ]
                
            tempStrings[i] = ""
'''






if __name__ == '__main__':
    import doctest
    doctest.testmod()
    getConsonanceForOneSong(anotherPath+"/wikifonia-1003.mxl", 0)
    #getSongAverage(mxlfiles)

    #getDeviationParallel(anotherMXL,"high")

    #getDeviationParallel(anotherMXL,"low")

    #getSentimentPitchDeviationParallel(mxlfiles, "joy")


    