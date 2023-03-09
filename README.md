# product_checker
Generate and store information about the products (food from the supermarket) from their photos. 
Can send notifications about the end of expiry date.

Realized with Telegram app bot.

What is necessesary TODO:

1. Greetings message with description and commands for bot;
2. Product information can include the following fields:
    - id;
    - photo-label;
    - recognized dates (prdouction, expiration)
3. Bot commands:
/start - Start bot;
send picture - User sends picture of one of their products with dates of prdouction and expiration. Bot suggests to send another photo with product label. User can skip this step then the first photo will be used as its label. At the end bot returns product info;
/listprod - Bot returns all products list with their product info;
/showprod <id> - Bot returns info of a product with <id>. If <id> is empty bot returns info about last added product;
/editdateprod <id> - Change dates of production and expiration for product with <id>. If <id> is empty then last product will be changed. Firstly bot returns the date of production to fill, secondly it returns the date of expirtion to fill.
/delprod <id> - Delete product with <id>. If <id> is empty then delete last product;
/changelabelprod <id> - Change label for product with <id>. If <id> is empty then do it for the last product;
/help - Show bot commands.
