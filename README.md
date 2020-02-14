# GTC2020 Workshop TrainingData.io Repo

This repos contains sample project for AI-Assited Labeling for Radiology AI using NVIDIA Clara on TrainingData.io

## How to use this Docker image: Quickstart Guide for TrainingDataio/tdviewer

## 1. Use `Dockerfile` to build a docker image
```
docker build -t gtc2020-trainingdataio .
```
## 2 Run a container from this image 
```
docker run -p 8888:8888 9090:9090 8090:8090 8000:8000 --runtime=nvidia gtc2020-trainingdataio /bin/bash
```
Once the container is running,
```
cd /workspace/content
```
## 3. Login to hub.docker.com:
```
docker login hub.docker.com
```

## 4. Login to nvcr.io
```
docker login hub.docker.com
```

## 5. Create a directory on your disk to store TD.io database. For example "/home/user/db"
```
mkdir -p  /path/to/db/directory
```

## 6. Create a directory to place images and videos (dataset assets). For example: "/home/user/images"
```
mkdir -p /path/to/images/directory
```

## 7. Make sure /tmp directory exists and is readable & writable
```
mkdir -p /tmp
```

## 8. Run Docker image providing mount point for database-folder and mount point for images-folder.

```
export DB_MOUNT=/path/to/temp/directory && export IMAGE_MOUNT=/path/to/image/directory && docker-compose -f docker-compose.ngx.yml up -d
```

## 9. Load model in Clara:
curl -X PUT "http://0.0.0.0:5000/admin/model/segmentation_ct_liver_and_tumor"   -H "accept: application/json" -H "Content-Type: application/json" -d '{"path":"nvidia/med/segmentation_ct_liver_and_tumor","version":"1"}'

## 10. Open Webbrower: https://app.trainingdata.io/v1/td/login
Login with oAuth or username & password

## 11. Start AI-Assisted Labeling
      On tab “Labeling Jobs” select “On-Premises Labeling Job”
      Click “Start Labeling”
      Observe http://127.0.0.1 loads in web-browser

## 12. Optional (3D Slicer):
   - Download 3D Slicer: https://trainingdataio.s3.amazonaws.com/SlicerLatest-TDIO-GTC2020Workshop.tgz
   - Extract and open Slicer executable
   - Setup /workspace/content/slicer-plugin as module in Slicer
   - Open the labeling project in "Open in 3D Slicer"
   
# Additional Information
[Manage On-Premises TrainingData Labeling](https://docs.trainingdata.io/v1.0/Premises%20Infrastructure/Docker%20And%20VPN/)

[How to create on-premises datasets?](https://docs.trainingdata.io/v1.0/DataSet/Create%20On-Prem%20Dataset/)

[How to create labeling instructions?](https://docs.trainingdata.io/v1.0/Labelling%20Interface/Builder/)

[How to create labeling jobs?](https://docs.trainingdata.io/v1.0/Projects/Create%20a%20Project/)

[How to distribute labeling jobs among annotators and reviewers?](https://docs.trainingdata.io/v1.0/Collaborators/Add%20Collaborators%20to%20Project/)

[Supported export formats for annotated data?](https://docs.trainingdata.io/v1.0/Export%20Format/COCO/)

## Technical Support

Email: **`support@trainingdata.io`**
