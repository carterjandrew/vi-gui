import sys
import os
import redis
from flask import Flask, request, Response, send_file
from flask_cors import CORS, cross_origin
from minio import Minio
import jsonpickle
import io
import base64
import hashlib
from io import BytesIO
import secrets
import bcrypt

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
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['MAX_CONTENT_LENGTH']=5000*1024*720*10000

@app.route('/', methods=['GET'])
@cross_origin()
def hello():
    return '<h1>API for VIGUI</h1><p> Use a valid endpoint </p>'

# A very very bad way to handle authentication
@app.route('/api/login', methods=['POST'])
@cross_origin()
def login():
    data = request.get_json()
    email = data['email']
    password = data['password']
    passwordStore = redisClient.hget('passwords', email)
    if passwordStore == None:
        return Response("No such user", status=404)
    if not bcrypt.checkpw(password.encode('utf-8'), passwordStore):
        return Response("Incorrect password", status=401)
    token = redisClient.hget('tokenFromEmail', email)
    app.logger.warning(f'TOKEN: {token}')
    token = token.decode('utf-8')
    return Response(jsonpickle.encode({
        'email': email,
        'token': token
    }), status=200)

# A very very bad way to handle sign up for auth
@app.route('/api/signup', methods=['POST'])
@cross_origin()
def signup():
    data = request.get_json()
    email = data['email']
    password = data['password']
    token = redisClient.hget('tokensFromEmail', email)
    if token != None:
        return Response("User allready exists", status=401)
    token = secrets.token_hex(32)
    # Hash the password to keep users info safe
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    # Push email, password, and tokens to redis
    redisClient.hset('emailFromToken', token, email)
    redisClient.hset('passwords', email, hashed_pw)
    redisClient.hset('tokenFromEmail', email, token)
    # Respond to user with authenticated values
    return Response(jsonpickle.encode({
        'email': email,
        'token': token
    }), status=200)

# Get queue items for the worker in rest
@app.route('/api/queue', methods=['GET'])
@cross_origin()
def getQueue():
    try:
        queue_data = redisClient.lrange("toWorker", 0, -1)
        queue = [item.decode('utf-8') for item in queue_data]
        return Response(jsonpickle.encode(queue), status=200)
    except Exception as e:
        return Response("An error occurred", status=500)

# Get queue for jobs being processed and their progress
@app.route('/api/status', methods=['GET'])
@cross_origin()
def getStatus():
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return Response("Not authorized", status=401)
    email = redisClient.hget("emailFromToken", auth_header)
    if not email:
        return Response(f"Bad token: {email}", status=403)
    try:
        queue_data = redisClient.hgetall(f'status_{email}')
        if not queue_data:
            queue_data = {}
        decoded_data = {key.decode('utf-8'): jsonpickle.decode(value.decode('utf-8')) for key, value in queue_data.items()}
        return Response(jsonpickle.encode(decoded_data), status=200)
    except Exception as e:
        app.logger.warning(f'ERROR: {e}')
        return Response("An error occurred", status=500)

# Get all items in the minio buket for debugging purposes
@app.route('/api/minio', methods=['GET'])
@cross_origin()
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
@cross_origin()
def enqueuetrack():
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return Response("Not authorized", status=401)
    email = redisClient.hget("emailFromToken", auth_header)
    if not email:
        return Response(f"Bad token: {email}", status=403)
    try:
        # Make the mino bucket if it does not exist
        if not minioClient.bucket_exists(minioBucket):
            minioClient.make_bucket(minioBucket)
        if request.method == 'POST':
            # Get our JSON data from our post body and decode video
            videoFile = request.files['video'].read()
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
            job = jsonpickle.encode({'id': fileId, 'email': email})
            redisClient.lpush("toWorker", job)
            # Also create entry for status updates
            status_item= {'status': 'Queued', 'progress': 0}
            status_string = jsonpickle.encode(status_item).encode('utf-8')
            redisClient.hset(f'status_{email}', fileId, status_string)
            return Response(jsonpickle.encode({'hash': fileId}), status=200)
        if request.method == 'DELETE':
            return Response('Failed because not implimented', status=500)
    except Exception as e:
        app.logger.warning(f'ERROR: {e}')
        return Response("An error occurred", status=500)

# Route for fetching the videos we have generated
# Will throw and return error if the video has not been processed
@app.route('/api/video/<videoHash>', methods=['GET', 'DELETE'])
@cross_origin()
def fetchVideo(videoHash):
    try:
        objectLocation = f'outputs/{videoHash}.mp4'
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
        app.logger.warning(f'ERROR: {e}')
        return Response("An error occurred", status=500)

# Run server if main
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
