import json
import argparse


newImgInd = {}


def main(args):
    global indexLoc
    indexLoc = args.image_index
    outFile = args.outfile
    oldImgInd = readFile(indexLoc)
    global newImgInd
    for k,v in oldImgInd.items():
        theHash = k
        for listItem in v:
            for k2,v2 in listItem.items():
                if k2 == "image_metadata":
                    for k3,v3 in v2.items():
                        if k3 == "repo":
                            theRepo = v3
                        elif k3 == "image_tag":
                            theTag = v3
        newImgInd[theHash] = {"repo": theRepo, "image_tag": theTag}
    writeFile(outFile, newImgInd)
    return readFile(outFile)

# def callableMain():
#     global indexLoc
#     oldImgInd = readFile(indexLoc)
#     global newImgInd
#     for k,v in oldImgInd.items():
#         theHash = k
#         for listItem in v:
#             for k2,v2 in listItem.items():
#                 if k2 == "image_metadata":
#                     for k3,v3 in v2.items():
#                         if k3 == "repo":
#                             theRepo = v3
#                         elif k3 == "image_tag":
#                             theTag = v3
#         newImgInd[theHash] = {"repo": theRepo, "image_tag": theTag}
#     global outFile
#     writeFile(outFile, newImgInd)
#     return readFile(outFile)

def readFile(pathToFile):

    with open(pathToFile, 'r') as f:
        data = json.load(f)
    return data

def writeFile(fileName, toWrite):
    with open(fileName, 'w', encoding='utf-8') as f:
        json.dump(toWrite, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('--image_index', type=str, required=False, default="image_index.json")
    parser.add_argument('--outfile', type=str, required=False, default="small_image_index.json")

    args = parser.parse_args()
 
    main(args)
 