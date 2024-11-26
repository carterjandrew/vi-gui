# Extend the base image
FROM cnstark/pytorch:2.3.0-py3.10.15-cuda12.1.0-ubuntu22.04
LABEL MAINTAINER="Carter Andrew"

# Override the entrypoint
ENTRYPOINT []

# Copy over needed files
WORKDIR /srv
COPY requirements.txt /srv
RUN pip install --no-cache-dir -r requirements.txt
COPY worker.py /srv
COPY uprnet /srv/uprnet

# Run the Flask server
CMD ["python3", "worker.py"]
