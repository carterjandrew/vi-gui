import sys
import os
import redis
from minio import Minio
import jsonpickle
from io import BytesIO
import soundfile as sf
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
os.makedirs('downloads', exist_ok=True)
os.makedirs('outputs', exist_ok=True)

while True:
    try:
        work = redisClient.blpop("toWorker", timeout=0)
        if not work: 
            continue
        item = jsonpickle.decode(work[len(work) - 1].decode('utf-8'))
        hash = item['hash']
        downloadLocation = f'downloads/{hash}.mp3'
        outputsLocation = f'outputs/{hash}'
        redisClient.lpush("log_queue", f"Recived work for item {hash}".encode('utf-8'))
        if not os.path.isfile(downloadLocation):
            minioClient.fget_object(minioBucket, f"{hash}.mp3", downloadLocation)
        if os.path.isfile(f"downloads/{hash}.mp3"):
            redisClient.lpush("log_queue", f"Successfully downloaded track {hash}".encode('utf-8'))
            os.makedirs(outputsLocation, exist_ok=True)
            os.system(f"python3 -m demucs.separate --out {outputsLocation} {downloadLocation} --mp3")
            redisClient.lpush("log_queue", f"Working through item completed!!".encode('utf-8'))
            outputFileLocation = f'{outputsLocation}/mdx_extra_q/{hash}'
            outputContents = os.listdir(outputFileLocation)
            redisClient.lpush("log_queue", f"Outputs in file location: {outputContents}".encode('utf-8'))
            # Push to minio
            for file in outputContents:
                minioLocation = f'results/{hash}/{file}'
                localLocation = f'{outputFileLocation}/{file}'
                minioClient.fput_object(
                    bucket_name=minioBucket,
                    object_name=minioLocation,
                    file_path=localLocation,
                    content_type="audio/mpeg"
                )
                redisClient.lpush("log_queue", f"Worker: Uploaded {file} for {hash} to minio".encode('utf-8'))
            redisClient.lpush("log_queue", f"Worker: Finished uploading objects to minio".encode('utf-8'))
            # Clean up files
            # os.system(f"rm -rf {outputsLocation}")
            # os.system(f"rm -rf {downloadLocation}")
        ##
        ## Work will be a tuple. work[0] is the name of the key from which the data is retrieved
        ## and work[1] will be the text log message. The message content is in raw bytes format
        ## e.g. b'foo' and the decoding it into UTF-* makes it print in a nice manner.
        ##
    except Exception as exp:
        redisClient.lpush('log_queue', f"Error in worker: {exp}".encode('utf-8'))
        print(f"Exception raised in log loop: {str(exp)}")
    sys.stdout.flush()
    sys.stderr.flush()
