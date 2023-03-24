#!/bin/bash 

set -e

# Installation dependencies for product_checker_bot

echo ${WDIR}

# Update
apt update && apt upgrade -y

# Install dependencies with apt
apt install -y build-essential zlib1g-dev \
libncurses5-dev libgdbm-dev libnss3-dev libssl-dev \
libreadline-dev libffi-dev libsqlite3-dev libbz2-dev
apt install -y automake ca-certificates g++ git libtool libleptonica-dev make pkg-config wget curl
apt install -y sqlite3
apt install -y ffmpeg libsm6 libxext6

# Add new repo for tesseract
apt install -y curl
echo "deb https://notesalexp.org/tesseract-ocr-dev/bullseye/ bullseye main" \
| tee /etc/apt/sources.list.d/notesalexp.list > /dev/null
curl -sSL https://notesalexp.org/debian/alexp_key.asc | apt-key add -
apt update
apt install -y tesseract-ocr  

# Clean up
apt clean && rm -rf /var/lib/apt/lists/*

# Python-3.11
cd ${WDIR}
wget https://www.python.org/ftp/python/3.11.1/Python-3.11.1.tgz
tar -xzvf Python-3.11.1.tgz
cd Python-3.11.1
./configure --enable-optimizations #--prefix=${WDIR}/.python3.11
make -j 10
make altinstall

# Poetry
cd ${WDIR}
curl -sSL https://install.python-poetry.org | python3.11 -

#Clone repo
cd ${WDIR}
git clone https://github.com/sharvadim07/product_checker.git

# Poetry install
cd ${WDIR}/product_checker
/root/.local/bin/poetry install

# Fill DB
cd ${WDIR}/product_checker
mkdir -p ./data
cat ./product_checker_bot/db.sql | sqlite3 ./data/db.sqlite3
