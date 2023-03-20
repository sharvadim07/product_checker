GREETNGS = """Hello {username}, it is product checker bot.
I can generate and store information about your products (e.g. food from the supermarket)
 from their photos.
So I can send notifications about the end of expiry date.

What's user can do:
1. Enter /start command to start bot with greetings message and description;
2. Send <photo> of one of your products with dates of prdouction and expiration;
3. After 1st action or 2nd action use the menu's buttons for communication with bot.

Bot abilities:
- Show all products list with their information;
- Change dates of production and expiration for product;
- Change label for product;
- Delete product;"""

HELP = """What's user can do:
1. Enter /start command to start bot with greetings message and description;
2. Send <photo> of one of your products with dates of prdouction and expiration;
3. After 1st action or 2nd action use the menu's buttons for communication with bot.

Bot abilities:
- Show all products list with their information;
- Change dates of production and expiration for product;
- Change label for product;
- Delete product;"""

PRODUCT_INFO = """Product id: {product_id}
PROD: {date_prod}
EXP: {date_exp}
Minio object_name: {label_path}"""

MYPROD_BUTTON = "My products"
HELP_BUTTON = "Help"

ENTER_PRODEXP_DATE = "Enter new production/expiration date(s):"
SEND_NEW_LABEL_PHOTO = "Send new label photo for product..."

BAD_UPDATE_PRODUCT_DATES = "Not changed. Please retry to edit product..."
BAD_DELETE_PRODUCT_DATES = "Products have not been deleted :("
BAD_SHOW_PRODUCTS = "No products :("
BAD_PHOTO_UPLOAD = "Can't upload your photo :("
PRESS_MENU = "Press menu button..."
ARE_YOU_SURE = "Are you sure?"

DELETE_ALL_PRODUCTS_BUTTON = "Delete all products"
YES_BUTTON = "Yes"
NO_BUTTON = "No"


NAME_MINIO_OBJ = "user_{telegram_user_id}_product_{product_id}_photo"
