To configure this module, you need to set several things in both PrestaShop and Odoo:

Steps in Ebisumart

Steps in Odoo:

* Go to Connectors > Ebisumart > Backends.
* Create a new record to register an Ebisumart backend.
    * Name - Backend Name
    * Ebisumart No - The number of Ebisumart
    * App Code - The code of your application
    * Password - Password for your application
    * Root Ebisumart URL - Specify the root URL for the shop management tool (https://support.ebisumart.com/category/APP/APP_INSTALL.html)
    * Ebisumart Access URL - Specify the URL for API access (https://support.ebisumart.com/category/APPDA/APPDA.html#APPDA_ACCESS_URL)
    * Redirect URI - Specify the URL of the Odoo environment for redirecting from Ebisumart when requesting authorization (e.g., odoo_web_url/ebisumart/auth)
    * Sale Partner - Assign the partner that will be used as the customer for imported sale orders.
    * Coupon Product - Assign the coupon product to be used in the order line when the Ebisumart order includes a coupon
* After filling in the details, click the Authorization button. This will initiate the OAuth process to obtain the token information needed for secure API communication with Ebisumart.
* Go to Accounting > Configuration > Journals and select the appropriate journal. 
* Choose the Ebisumart Payment Type that you will use, such as Credit Card or Payment Slip, to assign journal for imported orders.
* Set the timezone of the OdooBot user to match the timezone of your Ebisumart shop. This ensures that dates and times are correctly mapped during the synchronization process, avoiding any discrepancies in Odoo.
