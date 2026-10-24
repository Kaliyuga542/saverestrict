FROM python:3.12-slim

WORKDIR /app

# Avoid inheriting invalid Python paths from buildpack environment.
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONHOME= PYTHONPATH=

COPY requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
