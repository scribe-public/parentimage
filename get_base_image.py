import argparse
#from crypt import methods
import sys
import os
#import subprocess
from datetime import datetime
import json
import logging
from functools import cmp_to_key

from flask import Flask, jsonify, request

def get_json(filename):
    if(os.path.exists(filename)):
        with open(filename, 'r', encoding='utf-8') as f:
            obj = json.load(f)
        return obj
    else:
        log.warn("In get_json, file {} does not exist".format(filename))
        return(None)


def write_json(filename, obj):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=4)


app = Flask(__name__)

@app.route("/test", methods=['GET'])
def test():
    obj = request.get_json() #get_json(force=True)
    return obj
# test by: curl -X GET -H "Content-Type:application/json"  -d '{"My Dict":"My content"}' http://127.0.0.1:5000/test

@app.route("/healthcheck")
def health_check():
    health = {"Status": "OK"}
    return jsonify(health)


@app.route("/base_image")
def get_base_image_endpoint():
    req = request.get_json()
    result = get_base_image(req)
    log.info("Request:{} \nResult:{}".format(req, result))
    return result


def get_base_image(hash_list):
    prefix = ""
    for l in hash_list:
        prefix += l
        if prefix in image_index:
            last = prefix
        else:
            break
    if last in image_index:
        return image_index[last]

    obj = {"Error":"Base image not found"} 
    log.info("Request:{} \nResult:{}".format(hash_list, obj))
    return obj

def get_base_image_by_image_layers_obj(image_layers):
    sorted(image_layers, key = cmp_to_key(compare_layer))
    
    sorted(image_layers, key = cmp_to_key(compare_layer))
    hash_list = []
    for l in image_layers:
        hash_list.append(l["hashes"][0]["content"]) 
    
    return get_base_image(hash_list)

    


def get_base_image_by_sbom(gensbom_filename):
    global image_index
    if(os.path.exists(gensbom_filename)):
        with open(gensbom_filename, 'r', encoding='utf-8') as f:
            sbom = json.load(f)
    else:
        log.error("Cant get layer info. \nSBOM:{} does not exist.".format(gensbom_filename))
        return False
    
    image_layers = []

    for c in sbom["components"]:
        if (c["type"] =="container") and (c["group"] == "layer"):
            image_layers.append(c)
    result = get_base_image_by_image_layers_obj(image_layers)
    log.info("Request:{} \nResult:{}".format(gensbom_filename, result))
    return result

def compare_layer(item1, item2):
    for p in item1["properties"]:
        if p["name"]=="index":
            l1 = p["value"]
            break
    for p in item2["properties"]:
        if p["name"]=="index":
            l2 = p["value"]
            break
    if l1 < l2:
        return -1
    if l1 > l2:
        return 1
    return 0

def main(args):
    global image_index
    image_index = get_json(args.image_index)
    if args.sbom != "":
        obj = get_base_image_by_sbom(args.sbom)
        write_json(args.output_file, obj)
    else:
        # Run as service
        app.run()
        pass

        


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    log = logging.getLogger("my-logger")

    parser = argparse.ArgumentParser()
    parser.add_argument('--sbom', type=str, default="", required=False)
    parser.add_argument('--output_file', type=str, default="base_image.json", required=False)
    parser.add_argument('--image_index', type=str, default="image_index.json", required=False)
    args = parser.parse_args()
    main(args)