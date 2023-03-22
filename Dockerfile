FROM debian:10
LABEL \
name="product_checker_bot docker" \
description="Docker for product_checker telegram bot" \
repo="https://github.com/sharvadim07/product_checker" \
creator="Vadim Sharov" \
version="0.1.0"
# You can set these arguments when you build image
ARG BOT_CONFIG[=./data/config.json]
ARG MINIO_CREDENTIALS[=./data/credentials.json]
WORKDIR /usr/src
ENV WDIR=/usr/src
COPY ./install.sh ./
#CMD [ "/bin/bash" ]
RUN chmod +x ./install.sh && ./install.sh
COPY ${BOT_CONFIG} ./product_checker/data/config.json
COPY ${MINIO_CREDENTIALS} ./product_checker/data/credentials.json
EXPOSE 9000
ENTRYPOINT [ "poetry", "run", "python", "-m product_checker_bot" ]
