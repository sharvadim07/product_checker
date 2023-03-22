FROM debian:10
LABEL \
name="product_checker_bot docker" \
description="Docker for product_checker telegram bot" \
repo="https://github.com/sharvadim07/product_checker" \
creator="Vadim Sharov" \
version="0.1.0"
ARG BOT_CONFIG[=./data/config.json]
ARG MINIO_CREDENTIALS[=./data/credentials.json]
WORKDIR /usr/src
ENV WDIR=/usr/src
# Update
RUN apt update && apt upgrade -y
# Install dependencies with apt
RUN \
apt install -y build-essential zlib1g-dev \
libncurses5-dev libgdbm-dev libnss3-dev libssl-dev \
libreadline-dev libffi-dev libsqlite3-dev wget libbz2-dev
RUN apt install -y git wget curl pkg-config sqlite3 tesseract-ocr
# Clean up
RUN apt clean && rm -rf /var/lib/apt/lists/*
COPY ./install.sh ./
# ENV PATH="/usr/local/bin:$PATH"
# ENV PATH="/root/.local/bin:$PATH"
#CMD [ "/bin/bash" ]
RUN chmod +x ./install.sh && ./install.sh
COPY ${BOT_CONFIG} ./product_checker/data/config.json
COPY ${MINIO_CREDENTIALS} ./product_checker/data/credentials.json
EXPOSE 9000
ENTRYPOINT [ "poetry", "run", "python", "-m product_checker_bot" ]
