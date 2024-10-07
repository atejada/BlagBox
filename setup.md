## How to configure your BlagBox

**You need Python3.10 or higher**

1.- Install the following packages

* pip install nylas
* pip install textual
* pip install bs4
* pip install pendulum
* pip install textual_datepicker
* pip install python-dotenv


2.- Create your Nylas account and get the required API Key and Grant Id

Create a [free account](https://dashboard-v3.nylas.com/register)

And check the [Getting Started Guide](https://developer.nylas.com/docs/v3/getting-started/)

3.- Create an .env file with the following information

* BLAGBOX_API = "YOUR_NYLAS_API_KEY"
* BLAGBOX_GRANT_ID = "YOUR_NYLAS_GRANT_ID"
* BLAGBOX_CONTACTS = "myContacts" #Replace with your contacts
* BLAGBOX_INBOX = "INBOX" #Replace with your folder id
* EMAIL_LIMIT = 10

For **BLAGBOX_CONTACTS** follow this [Return all contacts groups](https://developer.nylas.com/docs/api/v3/ecc/#get-/v3/grants/-grant_id-/contacts/groups)

**IMPORTANT** All contacts in a group need to have at least a given name, otherwise the update will fail without a clear explanation. And this is the Nylas API fault, not Blagbox.

For **BLAGBOX_INBOX** follow this [Return all folders](https://developer.nylas.com/docs/api/v3/ecc/#get-/v3/grants/-grant_id-/folders)

4.- Have fun!
