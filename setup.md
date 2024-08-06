## How to configure your BlagBox

1.- Install the following packages

pip install nylas
pip install textual
pip install bs4
pip install pendulum
pip install textual_datepicker
pip install python-dotenv


2.- Create your Nylas account and get the required API Key and Grant Id

Create a [free account](https://dashboard-v3.nylas.com/register)

And check the [Getting Started Guide](https://developer.nylas.com/docs/v3/getting-started/)

3.- Create an .env file with the following information

BLAGBOX_API = "YOUR_NYLAS_API_KEY"
BLAGBOX_GRANT_ID = "YOUR_NYLAS_GRANT_ID"
BLAGBOX_CONTACTS = "myContacts" #Replace with your contacts
EMAIL_LIMIT = 10

4.- Have fun!
