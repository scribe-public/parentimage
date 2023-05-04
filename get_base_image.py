import argparse
#from crypt import methods
import sys
import os
#import subprocess
from datetime import datetime
import json
import logging
from functools import cmp_to_key
from get_bimage_index import compare_layer, write_json, get_json

from flask import Flask, jsonify, request

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