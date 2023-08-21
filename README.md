# product_checker

The app realized as Telegram bot.

This bot can generate and store information about the products 
using automatic dates recognition (e.g. food from the supermarket) from their photos. 
So it can send notifications about their shelf life end of expiry date.

## What's user can do:
1. Enter /start command to start bot with greetings message and description;
2. Send photo of one of your products with dates of production and expiration;
3. After 1st action or 2nd action use the menu's buttons for communication with bot.

## Bot abilities:
- Recognise dates of production and expiration from photo of product where these dates printed;
- Show all products list with their information;
- Sort products list by their expiration;
- Change dates of production and expiration for product;
- Change label for product;
- Delete product/all products;
- Send notification to user when some product about the end of expiry date;
- Ability to add bot in group chat (please add grants for sending mesages for it);

## Developed with using:
- Python telegram bot;
- Tesseract;
- MinIO S3 storage.

## Deploy
- Configure Minio S3 storage server;
- Build docker image and set required arguments BOT_CONFIG and MINIO_CREDENTIALS (example of these files in ./example_config);
- Run docker container;

## TODO:
- Testing and debugging;
