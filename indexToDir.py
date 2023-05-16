import os
import json
import logging
import tarfile



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


def getIndexFromTAR():
    tar = tarfile.open("image_index.tar.gz")
    f = tar.extractfile("image_index.json")
    return json.loads(f.read())

def makeDataDirectories(indexJSON):
    for k,v in indexJSON.items():
        image = v[0]["image_metadata"]["repo"]
        arch = v[0]["image_metadata"]["arch"]
        relFold = "IndexData/" + image + "-" + arch
        if not os.path.exists(relFold): 
            os.mkdir(relFold)
        imageDigest = v[0]["image_metadata"]["image_digest"]
        imageDigest = imageDigest[7:]
        fileName = relFold + "/" + image + "@" + imageDigest + ".json"
        recombinedDict = {k: v}
        write_json(fileName, recombinedDict)



def main():
    if not os.path.exists("IndexData"): os.mkdir("IndexData")

    fullIndex = getIndexFromTAR()
    makeDataDirectories(fullIndex)



if __name__ == '__main__':
    main()