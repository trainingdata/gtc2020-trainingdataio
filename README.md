# GTC2020 TrainingData.io Repo

This repos contains sample project for AI-Assited Labeling for Radiology AI using NVIDIA Clara on TrainingData.io

## How to use this Docker image: Quickstart Guide for TrainingDataio/tdviewer

## 1. Login to hub.docker.com:
```
docker login hub.docker.com
```

## 2. Login to nvcr.io
```
docker login hub.docker.com
```

## 3. Create a directory on your disk to store TD.io database. For example "/home/user/db"
```
mkdir -p  /path/to/db/directory
```

## 4. Create a directory to place images and videos (dataset assets). For example: "/home/user/images"
```
mkdir -p /path/to/images/directory
```

## 5. Make sure /tmp directory exists and is readable & writable
```
mkdir -p /tmp
```

## 6. Run Docker image providing mount point for database-folder and mount point for images-folder.

```
export DB_MOUNT=/path/to/temp/directory && export IMAGE_MOUNT=/path/to/image/directory && docker-compose -f docker-compose.ngx.yml up -d
```

## 7. Load model in Clara:
curl -X PUT "http://0.0.0.0:5000/admin/model/segmentation_ct_liver_and_tumor"   -H "accept: application/json" -H "Content-Type: application/json" -d '{"path":"nvidia/med/segmentation_ct_liver_and_tumor","version":"1"}'

## 8. Open Webbrower: https://app.trainingdata.io/v1/td/login
Login with user: bgenereaux@nvidia.com
           pass: p@$$12345

## 9. Start AI-Assisted Labeling
      On tab “Labeling Jobs” select “On-Premises Labeling Job”
      Click “Start Labeling”
      Observe http://127.0.0.1 loads in web-browser

# Additional Information
[Manage On-Premises TrainingData Labeling](https://docs.trainingdata.io/v1.0/Premises%20Infrastructure/Docker%20And%20VPN/)

[How to create on-premises datasets?](https://docs.trainingdata.io/v1.0/DataSet/Create%20On-Prem%20Dataset/)

[How to create labeling instructions?](https://docs.trainingdata.io/v1.0/Labelling%20Interface/Builder/)

[How to create labeling jobs?](https://docs.trainingdata.io/v1.0/Projects/Create%20a%20Project/)

[How to distribute labeling jobs among annotators and reviewers?](https://docs.trainingdata.io/v1.0/Collaborators/Add%20Collaborators%20to%20Project/)

[Supported export formats for annotated data?](https://docs.trainingdata.io/v1.0/Export%20Format/COCO/)

## Technical Support

Email: **`support@trainingdata.io`**


############### DELETE IN ABSOLUTE END#####################
This repo gives a simple example of what a contributor would provide to the DLI so that DLI can port the content to the DLI Platform.

# Docker Instructions

Use `Dockerfile` to build a docker image with `docker build -t gtc_example_repo .`.

Run a container from this image with `docker run -p 8888:8888 --runtime=nvidia gtc_example_repo`.

Once the container is running, visit the content in your browser at `localhost:8888`.
