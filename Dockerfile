FROM ghcr.io/jpconstantineau/docker_arduino_cli:0.34.2

WORKDIR /app
ENV TMPDIR /tmp

RUN apt-get update && apt-get install -y python3 python3-pip python3-venv
RUN pip3 install --upgrade pip

COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

COPY main.py /app/main.py

# TO MOUNT:
    # config.py to /app/config.py -- bind mount (not volume)
    # temporary directory to /tmp -- can be bind or volume
    # /dev/ttyACM0 to /dev/ttyACM0 using '--device' (or respective paths)

# EXPOSE port in config.py

CMD ["python3", "main.py"]
