# Extend the base image
FROM xserrat/facebook-demucs
LABEL MAINTAINER="Carter Andrew"

# Override the entrypoint
ENTRYPOINT []

# Copy over needed files
WORKDIR /srv
COPY requirements.txt /srv
RUN pip install --no-cache-dir -r requirements.txt
COPY worker.py /srv

# Run the Flask server
CMD ["python3", "worker.py"]
