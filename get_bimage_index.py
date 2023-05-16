import argparse
import cache
import json
import logging
import os
import requests
import subprocess
import sys
import time

from dirToIndex import getIndexDataFiles, generateNewIndexDict

from functools import cmp_to_key
from datetime import datetime


def get_url(url):
    r = requests.get(url)
    time.sleep(2)
    json_data = r.json()
    if r.status_code == 200:
        return(json_data)
    else:
        log.error("get_url. status code:{}, reason:{}".format(r.status_code, r.reason))


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


def gensbom_image(image_name, gensbom_filename, gensbom_options=['-f']):
    if(os.path.exists(gensbom_filename)):
        return True

    gensbom_command = ["valint","bom", image_name,
        "-vv", #"--external-syft",
        "--output-file", gensbom_filename,
        '-f'] #invalidate cache

    retval = False
    log.info("Running valint on {}".format(image_name))
    try:
        run = subprocess.run(gensbom_command, check=True)
        if run.returncode !=0:
            log.error("valint exit code was: %d" % run.returncode)
        else:
            retval = True

    except:
            log.error("valint caused exception on image {}".format(image_name))

    clean_command = [
                    "docker",
                    "rmi",
                    image_name
                ]

    try:
        run = subprocess.run(clean_command)
        if run.returncode !=0:
            log.error("image removal failed on error: %d" % run.returncode)
        else:
            retval = True
    except:
        log.error("Image removal raised exception on image {}".format(image_name))
    return retval


def get_image_layer_info(gensbom_filename, image_layer_filename):
    sbom = get_json(gensbom_filename)
    if (sbom == None): 
        log.error("Cant get layer info. \nSBOM:{} does not exist.".format(gensbom_filename))
        return False

    image_layers = []
    image_dict = {}
    output_obj = {}

    for c in sbom["components"]:
        if (c["type"] =="container") and (c["group"] == "layer"):
            image_layers.append(c)

    sorted(image_layers, key = cmp_to_key(compare_layer))

    for img in image_layers:
        image_dict[img["hashes"][0]["content"]] = img

    output_obj["image_layers"] = image_layers
    output_obj["image_dict"] = image_dict

    write_json(image_layer_filename, output_obj)

    return True


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


def add_image_layer_index(args, image_layer_filename, image_info, image_index_filename, index_dir_paths):
    image_layer_info = get_json(image_layer_filename)
    if image_layer_info == None:
        log.error("image layer file error on file {}".format(image_layer_filename))
        return False
    
    if args.small_index:
        image_index = get_json(image_index_filename)
        if image_index == None:
            image_index = {}

        id = ""
        for l in image_layer_info["image_layers"]:
            id += l["hashes"][0]["content"]

        small_data = {"repo": image_info['repo'], "image_tag": image_info['image_tag']}

        if id in image_index:
            for im in image_index[id]:
                if im['repo'] == image_info['repo'] and im['image_tag'] == image_info["image_tag"]:
                # if im["image_metadata"]["image_digest"] == image_info["image_digest"]:
                    break
            else:
                image_index[id].append(small_data)
        else:
            image_index[id] = [small_data]
        write_json(image_index_filename, image_index)
    else:
        id = ""
        for l in image_layer_info["image_layers"]:
            id += l["hashes"][0]["content"]

        image_data = {}
        image_data["image_metadata"] = image_info
        image_data["image_layers"] = image_layer_info["image_layers"]

        foundFile = False
        for file in index_dir_paths:
            if foundFile: break
            file_cont = get_json(file)
            if id in file_cont:
                for im in file_cont[id]:
                    if im["image_metadata"]["image_digest"] == image_info["image_digest"]:
                        foundFile = True
                        break
                else: 
                    foundFile = True
                    file_cont[id].append(image_data)
                    break
        if not foundFile:
            folder = 'IndexData/' + image_info['repo'] + '-' + image_info['arch']
            imgDig = image_info['image_digest']
            imgDig = imgDig[7:]
            fileName = folder + '/' + image_info['repo'] + '@' + imgDig + '.json'
            if not os.path.exists(folder):
                os.mkdir(folder)
            digest = ''
            for layer in image_data['image_layers']:
                digest += layer['hashes'][0]['content']
            image_data_reform = {digest:[image_data]}
            write_json(fileName, image_data_reform)
            
    return True


def get_image_obj(repo,res, img):
    image_obj = {
        "repo":repo,
        "image_tag":res["name"],
        "last_updated":res["last_updated"],
        "tag_last_pushed":res["tag_last_pushed"], 
        "arch":img["architecture"],
        "image_digest":img["digest"],
        "image_status":img["status"],
        "image_push_date":img["last_pushed"]
      }
    return image_obj


def get_product_image_list(product):
    path = product["path"]
    repo = product["repo"]
    path_prefix = repo + '-' + product["arch"] + f'/'
    if not os.path.exists(path_prefix):
        os.makedirs(path_prefix)

    repo_images_filename = path_prefix + repo+'-'+product["arch"] + '-image-list.json'
    repo_image_cache = cache.FileCache(repo_images_filename)
    next_url  = f"https://registry.hub.docker.com/v2/repositories/{path}/{repo}/tags?page_size=1024"
    while next_url != None:
        json_data = get_url(next_url)
        for res in json_data["results"]:
            for img in res["images"]:
                if img["architecture"] == product["arch"]:
                    if "digest" in img:
                        if not repo_image_cache.exists(img["digest"]):
                            log.info("Adding {}@{}".format(repo, img["digest"]))
                            repo_image_cache.add(img["digest"], get_image_obj(repo, res, img))
                        else:
                            #place holder fo future to break if all images already exist
                            break

        next_url = json_data["next"]

    repo_image_cache.flush()


def download_image_data(args, product):
    global image_index_filename
    index_dir_paths = getIndexDataFiles()
    repo = product["repo"]
    # Get images to download list
    path_prefix = repo + '-' + product["arch"] + f'/'
    if not os.path.exists(path_prefix):
        log.error("Path: {} does not exist.".format(path_prefix))
        return

    repo_images_filename = path_prefix + repo+'-'+product["arch"] + '-image-list.json'
    image_list = get_json(repo_images_filename)

    downloaded_images_filname = path_prefix + repo+'-'+product["arch"] + '-downloaded-image-list.json'

    if "refresh" in product:
        if product["refresh"] == "index" or product["refresh"] == "all":
            if os.path.exists(downloaded_images_filname):
                os.remove(downloaded_images_filname)
            if product["refresh"] == "all":
                for f in os.listdir(path_prefix):
                    if not f.startswith("valint"):
                        continue
                    os.remove(os.path.join(path_prefix, f))

    downloaded_cache = cache.FileCache(downloaded_images_filname)

    for key, value in image_list.items():
    #for key, value in image_list:
        # key is the digest, value is the object
        if not downloaded_cache.exists(key):
            image_name = repo + '@' + key
            docker_image_name = image_name
            if value["image_status"] == "active":
                if product["path"] != "library":
                    docker_image_name = product["path"] + f"/" + image_name

                gensbom_filename = path_prefix +"valint-" + image_name
                image_layer_filename = path_prefix+'layers-' + image_name
                add_to_cache = False
                if gensbom_image(docker_image_name, gensbom_filename):
                    if get_image_layer_info(gensbom_filename, image_layer_filename):
                        if add_image_layer_index(args, image_layer_filename, value, image_index_filename, index_dir_paths):
                            value["index_status"] = "success"
                            add_to_cache = True
                        else:
                            value["index_status"] = "image index update to file {} failed".format(image_index_filename)
                            log.error(value["index_status"])
                    else:
                        value["index_status"] = "get image layer failed on file {}".format(gensbom_filename)
                        log.error(value["index_status"])
                else:
                        value["index_status"] = "failed to valint image {}".format(docker_image_name)
                        log.error(value["index_status"])
                        add_to_cache = True # TODO: decide how to handle such fails
            else:
                value["index_status"] = "image not active: {}".format(docker_image_name)
                log.error(value["index_status"])
                add_to_cache = True

            if add_to_cache:
                downloaded_cache.add(key, value)
                downloaded_cache.flush() #Flush after handling each image - it is a lot of work


def main(args):
    global image_index_filename # TODO: Remove this variable
    image_index_filename = args.image_index
    if args.erase_index:
        if os.path.exists(image_index_filename):
            os.remove(image_index_filename)

    #image_index = get_json(image_index_filename)

    products = get_json(args.product_list)
    if products == None:
        log.error("Must define product file")
        exit(1)

    for product in products:
        log.info("Handling product:\n{}".format(product))
        get_product_image_list(product)
        download_image_data(args, product)


if __name__ == "__main__":
    log = logging.getLogger("get_bimage_index")
    log.setLevel(logging.DEBUG)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stdout_handler.setFormatter(formatter)
    log.addHandler(stdout_handler)

    file_handler = logging.FileHandler('error.log')
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)
    log.error("New run of get_bimage_index.py")


    parser = argparse.ArgumentParser()
    parser.add_argument('--product_list', type=str, default="product_list.json", required=False)
    parser.add_argument('--image_index', type=str, default="image_index.json", required=False)
    parser.add_argument('--erase_index', action='store_true')
    parser.add_argument('--small_index', action='store_true')
    args = parser.parse_args()
    main(args)



