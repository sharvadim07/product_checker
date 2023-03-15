GREETNGS="""
Hello {username}, it is product checker bot.
I can generate and store information about your products (e.g. food from the supermarket) from their photos. 
So I can send notifications about the end of expiry date.

Bot commands:
/start - Start bot;
<photo> - User sends picture of one of their products with dates of prdouction and expiration. 
User can use the menu's buttons for communication with bot.
Bot abilities:
- Show all products list with their product info;
- Change dates of production and expiration for product;
- Change label for product;
- Delete product;
- Send notification to user when some product about the end of expiry date.
"""

HELP="""
Bot commands:
/start - Start bot;
<photo> - User sends picture of one of their products with dates of prdouction and expiration. 
User can use the menu's buttons for communication with bot.
Bot abilities:
- Show all products list with their product info;
- Change dates of production and expiration for product;
- Change label for product;
- Delete product;
- Send notification to user when some product about the end of expiry date.
"""

PRODUCT_INFO="""
Product id: {product_id}
PROD: {date_prod}
EXP: {date_exp}
Minio object_name: {label_path}
"""

MYPROD_BUTTON_TEXT="My products"
HELP_BUTTON_TEXT="Help"

ENTER_PRODEXP_DATE="Enter new production/expiration date(s):"
SEND_NEW_LABEL_PHOTO="Send new label photo for product..."

_NAME_MINIO_OBJ="user_{telegram_user_id}_product_{product_id}_photo"