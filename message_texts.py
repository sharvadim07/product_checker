GREETNGS="""
Hello {username}, it is product checker bot.
I can generate and store information about your products (e.g. food from the supermarket) from their photos. 
So I can send notifications about the end of expiry date.

Bot commands:
/start - Start bot;
<send picture> - User sends picture of one of their products with dates of prdouction and expiration. Bot suggests to send another photo with product label. User can skip this step then the first photo will be used as its label. At the end bot returns product info;
/listprod - Bot returns all products list with their product info;
/showprod <id> - Bot returns info of a product with <id>. If <id> is empty bot returns info about last added product;
/editdateprod <id> - Change dates of production and expiration for product with <id>. If <id> is empty then last product will be changed. Firstly bot returns the date of production to fill, secondly it returns the date of expirtion to fill.
/delprod <id> - Delete product with <id>. If <id> is empty then delete last product;
/changelabelprod <id> - Change label for product with <id>. If <id> is empty then do it for the last product;
/help - Show bot commands.
"""

HELP="""
Bot commands:
/start - Start bot;
<send picture> - User sends picture of one of their products with dates of prdouction and expiration. Bot suggests to send another photo with product label. User can skip this step then the first photo will be used as its label. At the end bot returns product info;
/listprod - Bot returns all products list with their product info;
/showprod <id> - Bot returns info of a product with <id>. If <id> is empty bot returns info about last added product;
/editdateprod <id> - Change dates of production and expiration for product with <id>. If <id> is empty then last product will be changed. Firstly bot returns the date of production to fill, secondly it returns the date of expirtion to fill.
/delprod <id> - Delete product with <id>. If <id> is empty then delete last product;
/changelabelprod <id> - Change label for product with <id>. If <id> is empty then do it for the last product;
/help - Show bot commands.
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