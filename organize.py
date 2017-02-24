from music21 import *
from os import path,rename,listdir,mkdir
from shutil import copy
from functools import partial
from langid import *

#inputPath = '/Users/Phi/Desktop/2cool4school/music21/new_in'
inputPath = '../wikifonia'
outputPath ='../new_out'


def update(numRun, totalRun, latestOutput):
    for o in latestOutput:
        print("Run %s (%d/%d)" % (o, numRun, totalRun))

def organizeParallel(inputPath, outputPath, categorizeFunctionList):

    mxlfiles = [path.join(inputPath, f) for f in listdir(inputPath) if (path.isfile(path.join(inputPath, f)) and f[-3:] == "mxl")]
    newOrganizeOneSong = partial(organizeOneSong, outputPath=outputPath, categorizeFunctionList=categorizeFunctionList)
    output = common.runParallel(mxlfiles, newOrganizeOneSong, update)
    print("Succecefully organized files from path \"" + inputPath+ "\".")


def organizeOneSong(filePath, outputPath, categorizeFunctionList):
    try:
        score = converter.parse(filePath)
    except Exception:
        return

    for fun in categorizeFunctionList:
        catagorized, folderName = fun(score)
        if catagorized:
            newDir = path.join(outputPath,folderName)
            if not path.isdir(newDir):
                mkdir(newDir)
            copy(filePath,newDir)


def hasLyrics(score):
    ly = text.assembleLyrics(score)
    if len(ly):
        return (True, "has_lyrics")
    else:
        return(True, "no_lyrics")

def hasChords(score):
    chords = []
    for pt in range(len(score.parts)):
        chords += score.parts[pt].recurse().getElementsByClass('Chord').stream()

    if len(chords):
        return (True, "has_chords")
    else:
        return(True, "no_chords")


def catagorizeByLanguage(score):
        ly = text.assembleLyrics(score)
        if not len(ly):
            return(True, "no_lyrics")
        lang = langid.classify(ly)

        if lang:
            return True,lang[0]
        else:
            return False,""


    
    

if __name__ == '__main__':

    organizeParallel(inputPath, outputPath, [catagorizeByLanguage])


