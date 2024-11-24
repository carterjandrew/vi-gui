import sys
import os
import redis
from flask import Flask, request, Response, send_file
from minio import Minio
import jsonpickle
import io
import base64
import hashlib
from io import BytesIO

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


# Initialize the Flask app
app = Flask(__name__)

@app.route('/', methods=['GET'])
def hello():
    return '<h1>API for VIGUI</h1><p> Use a valid endpoint </p>'

# Get queue items for the worker in rest
@app.route('/api/queue', methods=['GET'])
def getQueue():
    try:
        queue_data = redisClient.lrange("toWorker", 0, -1)
        queue = [item.decode('utf-8') for item in queue_data]
        return Response(jsonpickle.encode(queue), status=200)
    except Exception as e:
        return Response("An error occurred", status=500)

# Get queue for jobs being processed and their progress
@app.route('/api/status', methods=['GET'])
def getStatus():
    try:
        queue_data = redisClient.hgetall("progress")
        decoded_data = {key.decode('utf-8'): value.decode('utf-8') for key, value in queue_data.items()}
        return Response(decoded_data, status=200)
    except Exception as e:
        return Response("An error occurred", status=500)

# Get all items in the minio buket for debugging purposes
@app.route('/api/minio', methods=['GET'])
def pushToBucket():
    try:
        if not minioClient.bucket_exists(minioBucket):
            minioClient.make_bucket(minioBucket)
        # Convert list_objects result to a list of object names for response
        items = [obj.object_name for obj in minioClient.list_objects(minioBucket, recursive=True)]
        return Response(jsonpickle.encode(items), status=200)
    except Exception as e:
        return Response("An error occurred", status=500)

# Method for posting a new job or deleting a existing job
@app.route('/api/jobs', methods=['POST', 'DELETE'])
def enqueuetrack():
    try:
        # Make the mino bucket if it does not exist
        if not minioClient.bucket_exists(minioBucket):
            minioClient.make_bucket(minioBucket)
        if request.method == 'POST':
            # Get our JSON data from our post body and decode video
            data = request.get_json()
            videoFile = base64.b64decode(data['video'])
            # Generate unique ID for the job
            fileId = str(hashlib.sha256(videoFile).hexdigest()[:20])
            # Upload video to our bucket
            minioClient.put_object(
                minioBucket,
                f'inputs/{fileId}.mp4',
                io.BytesIO(videoFile),
                length=len(videoFile),
                content_type='video/mp4'
            )
            # Add job to Redis queue for workers to digest
            redisClient.lpush("toWorker", fileId)
            # Also create entry for status updates
            status_item= {'status': 'Queued', 'progress': 0}
            status_string = jsonpickle.encode(status_item).encode('utf-8')
            redisClient.hset('progress', fileId, status_string)
            return Response(jsonpickle.encode({'hash': fileId}), status=200)
        if request.method == 'DELETE':
            return Response('Failed because not implimented', status=500)
    except Exception as e:
        return Response("An error occurred", status=500)

# Route for fetching the videos we have generated
# Will throw and return error if the video has not been processed
@app.route('/api/video/<videoHash>', methods=['GET', 'DELETE'])
def fetchVideo(videoHash):
    try:
        objectLocation = f'results/{videoHash}.mp4'
        if request.method == 'GET':
            file = minioClient.get_object(minioBucket, objectLocation)
            fileBytes = BytesIO(file.read())
            return send_file(fileBytes, mimetype='video/mp4', as_attachment=True, download_name=f"{videoHash}.mp4")
        # Else we have sent a delete request and we should remove our item
        minioClient.remove_object(minioBucket, objectLocation)
        # TODO: Delete the input as well as the results!!
        # NOTE: Actually do this inside our worker
        return Response(f'Deleted job {videoHash} results', status=200)
    except Exception as e:
        return Response("An error occurred", status=500)

# Run server if main
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
