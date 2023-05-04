# Parent Image Detection
A set of tools for collecting parent-image data, and detecting the parent-image of a given Docker image.
Detection will succeed if the parent-image was previously scanned.

In the following text parent image and base image are used interchangeably.

## Prerequisites
The tools are based on Scribe's valint tool (which generates an sbom for a given image). Valint capabilities can be explored [here](https://scribe-security.netlify.app/docs/CLI/valint/). 

Downloading valint:

``` curl -sSfL https://get.scribesecurity.com/install.sh  | sh -s -- -t valint```

## Quick Start

Generate an SBOM, for example:

```valint bom kibana:8.6.2 --output-file kibana-sbom.json```

Get the basic information about the base image of the image described in the sbom:

```python3 get_base_image.py --sbom kibana-sbom.json --image_index small_image_index.json```

Result:
```
INFO:my-logger:Request:kibana-sbom.json

Result:{'repo': 'ubuntu', 'image_tag': 'focal-20230126'}
```

In order to get more detailed information about the parent image, inflate the image_index.tgz file:
    
```tar -xzf image_index.tgz```

And then run:
    
```python3 get_base_image.py --sbom kibana-sbom.json```
    


## Base Image Detection
To find the base image of a given image, create an sbom using valint and then run:
```
    python3 get_base_image.py [options]
    options:
    --sbom          valint generated sbom filename. If no sbom is given the script will act as a service
    --output_file   filename for saving the base-image metadata, defaults to base_image.json
    --image_index   image index filename, defaults to image_index.json
```

When running as service, the following endpoints are supported:
```
/base_image     returns a JSON object describing the base image or an object with an error. 
                Receives and input an ordered list of image layer hashes (as strings)
/healthcheck    returns the JSON object {"Status": "OK"}
/test           returns the object in the data field of a GET request, intended for debug
```

You can check the service by trying:
```
curl -X GET -H "Content-Type:application/json"  -d '[layer1_hash, layer2_hash, ... ]' http://127.0.0.1:5000/base_image

```


## Base Image Database Population

The parent-image population process downloads all images of a repository of a set of parent-images, and creates an index file which is a map - mapping a base-image-id to base-image meta-data.
The base-image-id is a concatenation of the hashes of the layers, ordered from lower layer and up, of the base image.

Defining the base images to download is done via a product.json file. in the following format:
```
[
    {"repo":"ubuntu", "path":"library", "arch":"arm64", "refresh":"index"},
    {"repo":"ubuntu", "path":"library", "arch":"amd64", "refresh":"all"},

    {"repo":"alpine", "path":"library", "arch":"arm64"},
    {"repo":"single-base-layer-test", "path":"scribesecurity", "arch":"arm64"}
]
```

The path parameter is part of the Docker API url; for DockerHub approved or recommended images it is library, and for others it is the DockerHub username.

The refresh parameter enables refreshing the image_index calculation: the "index" option re-calculates the image_index entries based on existing sboms, and the "all" also re-creates the sboms. The index option is much faster since it does not require downloading the image

To run image population run:
```
    python3 get_bimage_index.py [options]
    options:
    --product_list product_list filename, defaults to product_list.json
    --image_index image_index filename, defaults to image_index.json
    --erase_index flag, if exist will erase the image_index file at the beginning of run
```

The script will create folder for each product in the product list, that will containt sboms and a layer synopsis for each of all base image versions,  and files for tracking the which images have been downloaded and which are pending. This allows re-running the script without re-downloading everything.



Another option is to run via docker. Note that this runs docker in docker:
(this example assumes the imaga name is scribesecurity/base-image-tool)
```
docker run -v ${pwd}:/ -v /var/run/docker.sock:/var/run/docker.sock  scribesecurity/base-image-tool
```

The script creates (or updates) the image_index.json file, Which is a dictionary mapping base-image-ids to metadata about the base image.

In case one wants a condensed version - a map from hash concatination to the image tags only, run:

```
    python3 ImgIndexCleaner.py [options]
    options:

    --image_index  image index filename, defaults to image_inded.json
    --outfile      filename for output file, defaults to small_image_index.json
```


## License 
This project is licensed under the AGPL License. The full license can be found in the [LICENSE](agpl-3.0.txt) file.