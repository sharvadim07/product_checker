#!/bin/bash 

set -e

# Installation dependencies for product_checker_bot

echo ${WDIR}

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
poetry install

# Fill DB
cd ${WDIR}
mkdir -p ./data
cat ./product_checker_bot/db.sql | sqlite3 ./data/db.sqlite3
