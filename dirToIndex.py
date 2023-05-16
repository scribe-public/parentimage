import os
import json
import logging



def get_json(filename):
    if(os.path.exists(filename)):
        with open(filename, 'r', encoding='utf-8') as f:
            obj = json.load(f)
        return obj
    else:
        logging.warn("In get_json, file {} does not exist".format(filename))
        return(None)
    
def write_json(filename, obj):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=4)

def getIndexDataFiles():
    allFilePaths = []
    for root, dirs, files in os.walk("IndexData/"):
        if not files:
            continue
        folder = root + "/"
        for file in files:
            allFilePaths.append(folder + file)
    return allFilePaths


def generateNewIndexDict(paths):
    indexDict = {}
    for filePath in paths:
        filesInfo = get_json(filePath)
        newk = ""
        newv = ""
        for k,v in filesInfo.items():
            newk = k
            newv = v
        indexDict[newk] = newv
    return indexDict



def main():
    allFiles = getIndexDataFiles()
    newIndexJSONDict = generateNewIndexDict(allFiles)
    
    write_json("generatedIndxOnFiles.json", newIndexJSONDict)



if __name__ == '__main__':
    main()