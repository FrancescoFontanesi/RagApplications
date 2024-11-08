FROM python:3.11.10-slim

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1
# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

# Install pip requirements
RUN pip install --upgrade pip

# Set the working directory in the container
WORKDIR /app

COPY requirements.txt /app/requirements.txt
# Copy the source code into the container.
COPY app.py /app/app.py

RUN pip install -r requirements.txt

CMD python -m flask run --host=0.0.0.0 --port=5000