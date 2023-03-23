FROM debian:11
LABEL \
name="product_checker_bot docker" \
description="Docker for product_checker telegram bot" \
repo="https://github.com/sharvadim07/product_checker" \
creator="Vadim Sharov" \
version="0.1.0"
# You can set these arguments when you build image
ARG BOT_CONFIG
ARG MINIO_CREDENTIALS
WORKDIR /usr/src/
ENV WDIR=/usr/src
COPY ./install.sh ./
#CMD [ "/bin/bash" ]
RUN chmod +x ./install.sh && ./install.sh
COPY ${BOT_CONFIG:-data/config.json} ./product_checker/data/
COPY ${MINIO_CREDENTIALS:-data/credentials.json} ./product_checker/data/
EXPOSE 9000
WORKDIR /usr/src/product_checker
ENTRYPOINT [ "/root/.local/bin/poetry", "run", "python", "-m", "product_checker_bot" ]
