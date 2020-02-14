#!/bin/bash

# launch docker-compose 

export DB_MOUNT=/tmp && export IMAGE_MOUNT=/workspace/content/imageserver && docker-compose -f docker-compose.ngx.yml up -d

# Login to nvcr.io

# pull CT model
curl -X PUT "http://0.0.0.0:5000/admin/model/segmentation_ct_liver_and_tumor"   -H "accept: application/json" -H "Content-Type: application/json" -d '{"path":"nvidia/med/segmentation_ct_liver_and_tumor","version":"1"}'

# source activate rapids && jupyter lab \
#         --ip 0.0.0.0                               `# Run on localhost` \
#         --allow-root                               `# Enable the use of sudo commands in the notebook` \
#         --no-browser                               `# Do not launch a browser by default` \
#         --NotebookApp.token=""                     `# Do not require token to access notebook` \
#         --NotebookApp.password=""                  `# Do not require password to run jupyter server`
