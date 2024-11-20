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
    return '<h1> Music Separation Server</h1><p> Use a valid endpoint </p>'
# Simple test route that adds a message to our logs
@app.route('/api/test/<message>', methods=['GET'])
def enqueueAudio(message):
    # Push to a logging queue (assuming queue name is 'log_queue')
    redisClient.lpush("log_queue", message.encode('utf-8'))
    return Response(f"Message '{message}' pushed to Redis log queue.", status=200)

# Get queue items for the worker in rest
@app.route('/apiv1/queue', methods=['GET'])
def getQueue():
    try:
        queue_data = redisClient.lrange("toWorker", 0, -1)
        queue = [item.decode('utf-8') for item in queue_data]
        return Response(jsonpickle.encode(queue), status=200)
    except Exception as e:
        redisClient.lpush("log_queue", str(e).encode('utf-8'))
        return Response("An error occurred", status=500)

# Simple test for hot-reloading deployment
@app.route('/apiv1/minio', methods=['GET'])
def pushToBucket():
    try:
        if not minioClient.bucket_exists(minioBucket):
            redisClient.lpush("log_queue", "Making bucket".encode('utf-8'))
            minioClient.make_bucket(minioBucket)
        # Convert list_objects result to a list of object names for response
        items = [obj.object_name for obj in minioClient.list_objects(minioBucket, recursive=True)]
        return Response(jsonpickle.encode(items), status=200)
    except Exception as e:
        redisClient.lpush("log_queue", str(e).encode('utf-8'))
        return Response("An error occurred", status=500)

# Simple test for hot-reloading deployment
@app.route('/apiv1/separate', methods=['post'])
def enqueuetrack():
    try:
        if not minioClient.bucket_exists(minioBucket):
            redisClient.lpush("log_queue", "Making bucket".encode('utf-8'))
            minioClient.make_bucket(minioBucket)

        # Get and process the request
        data = request.get_json()
        audioTrack = base64.b64decode(data['mp3'])
        callback = data['callback']
        fileId = hashlib.sha256(audioTrack).hexdigest()[:20]

        # Upload audio track to MinIO
        minioClient.put_object(
            minioBucket,
            f'{fileId}.mp3',
            io.BytesIO(audioTrack),
            length=len(audioTrack),
            content_type='audio/mpeg'
        )

        # Add to Redis queue with encoded data
        queue_item = {'hash': str(fileId), 'callback': callback}
        queue_string = jsonpickle.encode(queue_item).encode('utf-8')
        redisClient.lpush("toWorker", queue_string)
        # TODO: Add second queue for completion consistency
        # Return response
        return Response(jsonpickle.encode({'hash': str(fileId), 'reason': 'Song enqueued for separation'}), status=200)
    except Exception as e:
        redisClient.lpush("log_queue", str(e).encode('utf-8'))
        return Response("An error occurred", status=500)

# Route for fetching processed tracks
@app.route('/apiv1/track/<trackHash>/<trackType>', methods=['GET', 'DELETE'])
def fetchTrack(trackHash, trackType):
    try:
        objectLocation = f'results/{trackHash}/{trackType}.mp3'
        if request.method == 'GET':
            file = minioClient.get_object(minioBucket, objectLocation)
            fileBytes = BytesIO(file.read())
            return send_file(fileBytes, mimetype='audio/mpeg', as_attachment=True, download_name=f"{trackHash}_{trackType}.mp3")
        minioClient.remove_object(minioBucket, objectLocation)
        return Response(f'Deleted track {trackType} for song {trackHash}', status=200)
    except Exception as e:
        redisClient.lpush("log_queue", str(e).encode('utf-8'))
        return Response("An error occurred", status=500)

# Run server if main
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

