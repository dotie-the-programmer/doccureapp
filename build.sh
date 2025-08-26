#!/usr/bin/env bash
set -o errexit

# Install dependencies needed for Pillow & mysqlclient
apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    default-libmysqlclient-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
