```
         _________ _______          _________
|\     /|\__   __/(  ____ \|\     /|\__   __/
| )   ( |   ) (   | (    \/| )   ( |   ) (   
| |   | |   | |   | |      | |   | |   | |   
( (   ) )   | |   | | ____ | |   | |   | |   
 \ \_/ /    | |   | | \_  )| |   | |   | |   
  \   /  ___) (___| (___) || (___) |___) (___
   \_/   \_______/(_______)(_______)\_______/
```

# About
This is a video frame interpolator webapp that uses:
## Tech Stack
### Kubernetes
Kubernetes manages all the API backend services, in particular it provides pods for:
### Flask API
Flask provides an API service for handling comminication between the frontend and backend. 
> This means it uses a ingress with kuberenetes
### Redis Service
A Redis service that allows us to use Queues for processing jobs along with key-value stores for checking on jobs progress
### MinIO Object Store
We will be using MINIO as an object store for large video files.
> As these files could be significant in size we have a dedicated ingress for uploading video files. 
### Machine Learning Worker
We will use a pod with access to a GPU along with PyTorch to preform inference on our frames, along with report on job progress
## Flow chart
TODO
