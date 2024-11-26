import time
import sys
import os
import redis
from minio import Minio
import jsonpickle
from io import BytesIO
import torch


##
## Configure test vs. production
##

# Initialize the Redis client
redisHost = os.getenv("REDIS_HOST") or "localhost"
redisPort = int(os.getenv("REDIS_PORT") or 6379)

redisClient = redis.StrictRedis(host=redisHost, port=redisPort, db=0)

# Initialize minio client
minioHost = os.getenv("MINIO_HOST") or "minio-proj.minio-ns.svc.cluster.local:9000"
minioUser = os.getenv("MINIO_USER") or "rootuser"
minioPasswd = os.getenv("MINIO_PASSWD") or "rootpass123"
minioBucket = os.getenv("MINIO_BUCKET") or "dmucs-bucket"

minioClient = Minio(minioHost, secure=False, access_key=minioUser, secret_key=minioPasswd)

# Create folders if they do not exist
os.makedirs('inputs', exist_ok=True)
os.makedirs('outputs', exist_ok=True)

while True:
    try:
        work = redisClient.blpop("toWorker", timeout=0)
        if not work: 
            continue
        hash = work[len(work) - 1].decode('utf-8')
        downloadLocation = f'inputs/{hash}.mp4'
        outputsLocation = f'outputs/{hash}.mp4'
        print(f"Found work for item {hash}")
        if not os.path.isfile(downloadLocation):
            minioClient.fget_object(minioBucket, downloadLocation, downloadLocation)
        if os.path.isfile(downloadLocation):
            status_item = {'status': 'Starting', 'progress': 0}
            status_string = jsonpickle.encode(status_item).encode('utf-8')
            redisClient.hset('progress', hash, status_string)
            # Preform work
            for i in range(10):
                status_item = {'status': 'Generating', 'progress': i* 10}
                status_string = jsonpickle.encode(status_item).encode('utf-8')
                redisClient.hset('progress', hash, status_string)
                time.sleep(1)
            # Push to minio

            status_item = {'status': 'Storing', 'progress': 100}
            status_string = jsonpickle.encode(status_item).encode('utf-8')
            redisClient.hset('progress', hash, status_string)

            minioClient.fput_object(
                bucket_name=minioBucket,
                file_path=downloadLocation,
                object_name=downloadLocation,
                content_type='video/mp4'
            )

            status_item = {'status': 'Complete', 'progress': 100}
            status_string = jsonpickle.encode(status_item).encode('utf-8')
            redisClient.hset('progress', hash, status_string)
            # Clean up files
            # os.system(f"rm -rf {outputsLocation}")
            # os.system(f"rm -rf {downloadLocation}")
    except Exception as exp:
        print(f"Exception raised in log loop: {str(exp)}")
    sys.stdout.flush()
    sys.stderr.flush()
