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
<photo> - User sends picture of one of their products with dates of prdouction and expiration. 
User can use the menu's buttons for communication with bot.
Bot abilities:
- Show all products list with their product info;
- Change dates of production and expiration for product;
- Change label for product;
- Delete product;
- Send notification to user when some product about the end of expiry date.