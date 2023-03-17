GREETNGS = """
Hello {username}, it is product checker bot.
I can generate and store information about your products (e.g. food from the supermarket) from their photos. 
So I can send notifications about the end of expiry date.

</b>What's user can do:</b>
1. Enter /start command to start bot with greetings message and description;
2. Send <photo> of one of your products with dates of prdouction and expiration;
3. After 1st action or 2nd action use the menu's buttons for communication with bot.

</b>Bot abilities:</b>
- Show all products list with their information;
- Change dates of production and expiration for product;
- Change label for product;
- Delete product;
"""

HELP = """
</b>What's user can do:</b>
1. Enter /start command to start bot with greetings message and description;
2. Send <photo> of one of your products with dates of prdouction and expiration;
3. After 1st action or 2nd action use the menu's buttons for communication with bot.

</b>Bot abilities:</b>
- Show all products list with their information;
- Change dates of production and expiration for product;
- Change label for product;
- Delete product;
"""

PRODUCT_INFO = """
Product id: {product_id}
PROD: {date_prod}
EXP: {date_exp}
Minio object_name: {label_path}
"""

MYPROD_BUTTON_TEXT = "My products"
HELP_BUTTON_TEXT = "Help"

ENTER_PRODEXP_DATE = "Enter new production/expiration date(s):"
SEND_NEW_LABEL_PHOTO = "Send new label photo for product..."

BAD_UPDATE_PRODUCT_DATES = "Not changed. Please retry to edit product..."
PRESS_MENU_BUTTON = "Press menu button..."

NAME_MINIO_OBJ = "user_{telegram_user_id}_product_{product_id}_photo"