FROM python:3.9-slim

# Set pip to have cleaner logs and no saved cache
ENV PIP_NO_CACHE_DIR=false \
    PIPENV_HIDE_EMOJIS=1 \
    PIPENV_IGNORE_VIRTUALENVS=1 \
    PIPENV_NOSPIN=1 \
    WEB_CONCURRENCY=2

# Install FFMPEG
RUN apt -y update \
    && apt install -y ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install pipenv
RUN pip install -U pipenv

# Install project dependencies
COPY Pipfile* ./
RUN pipenv install --system --deploy

# Set workdir to root for reltative imports
WORKDIR /

# Copy the source code in last to optimize rebuilding the image
COPY . /app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
