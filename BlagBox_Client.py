# BlagBox - The ultimate Email, Calendar and Contacts Terminal Client
# Blag aka. Alvaro Tejada Galindo
# Senior Developer Advocate
# https://www.linkedin.com/in/atejada/

# Import your dependencies
from dotenv import load_dotenv
import os
from rich.text import Text
from nylas import Client
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import DataTable, Label, Header, Footer, Input, Button, TextArea, Select, Markdown
from textual.screen import Screen
from textual.containers import Container
from textual.binding import Binding
from bs4 import BeautifulSoup
import textwrap
from typing import List, Any
from nylas.models.messages import ListMessagesQueryParams
from nylas.models.messages import UpdateMessageRequest
import pendulum
from textual_datepicker import DateSelect
import datetime

# Load your env variables
load_dotenv()

# Initialize an instance of the Nylas SDK using the client credentials
nylas = Client(
    api_key =  os.environ.get("BLAGBOX_API")
)

# Create the header of the Data Table
ROWS = [("Date", "Subject", "From", "Unread")]

# Global variables
messageid = []
contactid = []

# Get the body of a particular message clean of HTML tags
def get_message(self, message_id: str) -> str:
    body = ""
    message, _ = nylas.messages.find(os.environ.get("BLAGBOX_GRANT_ID"), message_id)
    soup = BeautifulSoup(message.body, 'html.parser')
    clean_text = soup.get_text('\n', strip=True)
    body = "\n".join(textwrap.fill(line, width=75) for line in clean_text.split('\n'))
    
    if message.unread is True:
        request_body = UpdateMessageRequest(unread = False)
        nylas.messages.update(os.environ.get("BLAGBOX_GRANT_ID"), message_id, request_body)
        self.populate_table()
    return body

# Read the first limit messages of our inbox
def get_messages() -> List[Any]:
# Create query parameters
    query_params = ListMessagesQueryParams(
        {'in' : os.environ.get("BLAGBOX_INBOX"), 'limit': os.environ.get("EMAIL_LIMIT")}
    )
    
    messages, _, _ = nylas.messages.list(os.environ.get("BLAGBOX_GRANT_ID"), query_params)
    ROWS.clear()
    ROWS.append(("Date", "Subject", "From", "Unread"))
    for message in messages:
        try:
            _from = message.from_[0]["name"] + " / " + message.from_[0]["email"]
        except Exception:
            _from = message.from_[0]["email"]
        ROWS.append(
            (
                message.date,
                message.subject[0:50],
                _from,
                message.unread,
            )
        )
    return messages

# Read your events
def get_events() -> List[Any]:
    # Get today’s date
    today = pendulum.now()
    start_time = pendulum.local(today.year, today.month, today.day, today.hour, 0, 0).int_timestamp
    end_time = pendulum.local(today.year, today.month, today.day, 22, 0, 0).int_timestamp
    query_params = {"calendar_id": os.environ.get("BLAGBOX_GRANT_ID"), "start":  start_time, "end": end_time}
    try:
        events = nylas.events.list(os.environ.get("BLAGBOX_GRANT_ID"), query_params=query_params).data
    except Exception:
        events = []
    return events

# Read your contacts
def get_contacts() -> List[Any]:
    query_params = {
        "source" : "address_book",
        "group" : os.environ.get("BLAGBOX_CONTACTS")
    }

    try:
        contacts, _, _ = nylas.contacts.list(os.environ.get("BLAGBOX_GRANT_ID"), query_params)
    except Exception:
        contacts = []
    return contacts

# This can be considered the main screen
class EmailApp(App):
    TITLE = "Blag Box - Email, Calendar and Contacts in the Terminal"
# Setup the bindings for the footer 
    BINDINGS = [
        Binding("r", "refresh", "Refresh"),
        Binding("s", "send", "Send", show=False),
        Binding("c", "cancel", "Cancel", show=False),
        Binding("d", "delete", "Delete"),
        Binding("o", "compose", "Compose"),
        Binding("p", "reply", "Reply"),
        Binding("m", "meeting", "Meeting"),
        Binding("k", "contact", "Contact"),
        Binding("q", "quit", "Quit"),
    ]

# Class variables
    messages = [Any]
    id_message = 0

# Fill up the Data table
    def populate_table(self) -> None:
        self.messages = get_messages()
        table = self.query_one(DataTable)
        table.clear()
        table.cursor_type = "row"
        rows = iter(ROWS)
        counter = 0
        for row in rows:
            if counter > 0:
                if row[3] is True:
                    styled_row = [
                        Text(str(cell), style="bold #03AC13") for cell in row
                    ]
                    table.add_row(*styled_row)
                else:    
                    table.add_row(*row)
            counter += 1

# Load up the main components of the screen
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield DataTable()
        yield Label("===================================================================================================================================================")
        yield Label("===================================================================================================================================================")
        yield Label(id="message")

# After we load the components, fill up their data
    def on_mount(self) -> None:     
        self.messages = get_messages()
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        rows = iter(ROWS)
        table.add_columns(*next(rows))
        for row in rows:
            if row[3] is True:
                styled_row = [
                    Text(str(cell), style="bold #03AC13") for cell in row
                ]
                table.add_row(*styled_row)
            else:    
                table.add_row(*row)

# When we select a line on our Data table, or read
# an email
    def on_data_table_row_selected(self, event) -> None:
        message = self.query_one("#message", Label)
        self.id_message = self.messages[event.cursor_row].id
        messageid.clear()
        messageid.append(self.id_message)
        message.update(get_message(self, self.id_message))

# We're deleting an email
    def action_delete(self) -> None:
        try:
            nylas.messages.destroy(os.environ.get("BLAGBOX_GRANT_ID"), self.id_message)
            self.populate_table()
        except Exception as e:
            self.notify(e.message)
            self.populate_table()

# We want to Compose a new email
    def action_compose(self) -> None:
        self.push_screen(ComposeEmail())

# We want to refresh by calling in new emails
    def action_refresh(self) -> None:
        self.populate_table()

# We want to reply to an email
    def action_reply(self) -> None:
        if len(messageid) > 0:
            self.push_screen(ReplyScreen())

# We want to schedule a meeting
    def action_meeting(self) -> None:
        if len(messageid) > 0:
            self.push_screen(MeetingScreen())
        else:
            self.push_screen(EventsScreen())

# We want to update a contact
    def action_contact(self) -> None:
        self.push_screen(ContactScreen())

# We want to quit the app -:(
    def action_quit(self) -> None:
       self.exit()

# Events screen. This screen we will be displayed when we are
# listing events
class EventsScreen(Screen):
    BINDINGS = [
        Binding("r", "refresh", "Refresh", show=False),
        Binding("s", "confirm", "Confirm", show=False),
        Binding("c", "cancel", "Cancel"),
        Binding("d", "delete", "Delete", show=False),
        Binding("o", "compose", "Compose", show=False),
        Binding("p", "reply", "Reply", show=False),
        Binding("m", "meeting", "Meeting", show=False),
        Binding("k", "contact", "Contact", show=False),
        Binding("q", "quit", "Quit", show=False),
    ]
# Load up the main components of the screen
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        markdown = ""
        event_date = ""
        participant_details = ""
        today = pendulum.now()
        events = get_events()
        for event in events:
            match event.when.object:
                case 'timespan':
                    start_time = pendulum.from_timestamp(event.when.start_time, today.timezone.name).strftime("%H:%M:%S")
                    end_time = pendulum.from_timestamp(event.when.end_time, today.timezone.name).strftime("%H:%M:%S")
                    event_date = f"{start_time} to {end_time}"
                case 'datespan':
                    event_date = f"{event.when.start_date} to {event.when.end_date}"
                case 'date':
                    event_date = f"{event.when.date}"
            participant_details = ""
            for participant in event.participants:
                participant_details += f"{participant.email} - "
            markdown += "## " + event.title + "  \n" + "### " + event_date + "  \n" + event.description + "  \n" + "  \n" + participant_details[:-3] + "  \n"
        yield Markdown(markdown)

    def action_cancel(self) -> None:
        app.pop_screen()

# Meeting screen. This screen we will be displayed when we are
# creating a new meeting
class MeetingScreen(Screen):
    CSS_PATH = "meeting_screen.tcss"
# Setup the bindings for the footer 
    BINDINGS = [
        Binding("r", "refresh", "Refresh", show=False),
        Binding("s", "confirm", "Confirm"),
        Binding("c", "cancel", "Cancel"),
        Binding("d", "delete", "Delete", show=False),
        Binding("o", "compose", "Compose", show=False),
        Binding("p", "reply", "Reply", show=False),
        Binding("m", "meeting", "Meeting", show=False),
        Binding("k", "contact", "Contact", show=False),
        Binding("q", "quit", "Quit", show=False),
    ]
    
# Load up the main components of the screen
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Container(
            DateSelect(
                placeholder="please select",
                format="YYYY-MM-DD",
                date=pendulum.now(),
                picker_mount="#main_container",
                id = "date"
            ),
            Input(placeholder="Meeting Time", id="time"),
            Select(prompt = "Duration", options = [("5", 5), ("15", 15), ("30", 30), ("45", 45), ("60", 60)], id="duration"),
            Input(placeholder="Meeting Title", id="title"),
            Input(placeholder="Meeting Location", id="location"),        
            id="main_container",
        )
        yield TextArea(id="description", text = "Replace with meeting description")
        yield Horizontal(
            Button("Confirm", variant="primary", id="confirm"),
            Label(" "),
            Button("Cancel", variant="primary", id="cancel"),
        )

    def action_confirm(self) -> None:
        message = nylas.messages.find(os.environ.get("BLAGBOX_GRANT_ID"), messageid[0]).data
        date = self.query_one("#date").value
        date_string = date.strftime("%Y-%m-%d")
        year, month, day = map(int, date_string.split("-"))
        time = self.query_one("#time").value
        hours, minutes, seconds = map(int, time.split(":"))
        time_holder = datetime.datetime(year, month, day, hours, minutes, seconds)
        start_time = pendulum.instance(time_holder, pendulum.now().timezone)
        end_time = start_time.add(minutes = self.query_one("#duration").value)
        query_params = {"calendar_id": os.environ.get("BLAGBOX_GRANT_ID")}
        request_body = {
	        "when": { 
		        "start_time": start_time.int_timestamp,
		        "end_time": end_time.int_timestamp,		
	    },
	    "title": self.query_one("#title").value,
	    "location": self.query_one("#location").value,
	    "description": self.query_one("#description").text,
	    "participants": [{
               "name": "",
               "email": message.from_[0]['email'], 
           }]
        }
        
        try:
            nylas.events.create(os.environ.get("BLAGBOX_GRANT_ID"), query_params = query_params, request_body = request_body).data
            self.query_one("#title").value = ""
            self.query_one("#location").value = ""
            self.query_one("#description").text = ""
            app.pop_screen()
        except Exception as e:
            self.notify(e.message)

    def action_cancel(self) -> None:
        app.pop_screen()

# We're pressing a button
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm":
            self.action_confirm()
        if event.button.id == "cancel":
            app.pop_screen()
        
# Contact screen. This screen we will be displayed when we are
# updating a contact
class ContactScreen(Screen):
# Setup the bindings for the footer 
    BINDINGS = [
        Binding("r", "refresh", "Refresh", show=False),
        Binding("u", "update", "Update"),
        Binding("c", "cancel", "Cancel"),
        Binding("d", "delete", "Delete", show=False),
        Binding("o", "compose", "Compose", show=False),
        Binding("p", "reply", "Reply", show=False),
        Binding("m", "meeting", "Meeting", show=False),
        Binding("k", "contact", "Contact", show=False),
        Binding("q", "quit", "Quit", show=False),
    ]
    
# Load up the main components of the screen
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        contacts = get_contacts()
        contact_list = []
        for contact in contacts:
            contact_list.append((str(contact.emails[0].email),contact.id))
        yield Select(prompt = "Contacts", options = contact_list, id="contact")
        yield Button("Get contact", variant="primary", id="get")
        yield Input(placeholder= "First Name", id="first_name")
        yield Input(placeholder= "Last Name", id="last_name")
        yield Input(placeholder= "Company Name", id="company")
        yield Input(placeholder= "Job Title", id="job")
        yield Input(placeholder= "Email", id="email")
        yield Input(placeholder= "Phone Number", id="phone")
        yield Horizontal(
            Button("Update", variant="primary", id="update"),
            Label(" "),
            Button("Cancel", variant="primary", id="cancel"),
        )

    def get_contact_details(self, contact_id) -> None:
        contactid.clear()
        contactid.append(contact_id)
        contact, _ = nylas.contacts.find(os.environ.get("BLAGBOX_GRANT_ID"), contact_id)
        self.query_one("#first_name").value = contact.given_name
        self.query_one("#last_name").value = contact.surname
        self.query_one("#company").value = contact.company_name
        self.query_one("#job").value = contact.job_title
        self.query_one("#email").value = contact.emails[0].email
        self.query_one("#phone").value = contact.phone_numbers[0].number
        self.query_one("#phone").text = "Test"

    def action_cancel(self) -> None:
        app.pop_screen()

    def action_update(self) -> None:
        request_body = {
            "given_name" : self.query_one("#first_name").value,
            "surname" : self.query_one("#last_name").value,
            "company_name" : self.query_one("#company").value,
            "job_title" : self.query_one("#job").value,
            "emails" : [{
                "email" :  self.query_one("#email").value,
                "type": "work",
            }],
            "phone_numbers": [
            {
                "number": self.query_one("#phone").value,
                "type": "work"
            }],
        }
        
        try:
            nylas.contacts.update(os.environ.get("BLAGBOX_GRANT_ID"), contactid[0], request_body)
            contactid.clear()
            app.pop_screen()
            self.query_one("#first_name").value = ""
            self.query_one("#last_name").value = ""
            self.query_one("#company").value = ""
            self.query_one("#job").value = ""
            self.query_one("#email").value = ""
            self.query_one("#phone").value = ""
        except Exception as e:
            self.notify(e.message)

# We're pressing a button
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "get":
            self.get_contact_details(self.query_one("#contact").value)
        if event.button.id == "update":
            self.action_update()
        if event.button.id == "cancel":
            app.pop_screen()

# Reply screen. This screen we will be displayed when we are
# replying an email
class ReplyScreen(Screen):
# Setup the bindings for the footer 
    BINDINGS = [
        Binding("r", "refresh", "Refresh", show=False),
        Binding("s", "send", "Send"),
        Binding("c", "cancel", "Cancel"),
        Binding("d", "delete", "Delete", show=False),
        Binding("o", "compose", "Compose Email", show=False),
        Binding("p", "reply", "Reply", show=False),
    ]

# Load up the main components of the screen
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Input(id="email_from")
        yield Input(id="title")
        body = TextArea(id="body")
        body.show_line_numbers = False
        yield body
        yield Horizontal(
            Button("Send!", variant="primary", id="send"),
            Label(" "),
            Button("Cancel", variant="primary", id="cancel"),
        )

# After we load the components, fill up their data
    def on_mount(self) -> None:
        pass
        message = nylas.messages.find(os.environ.get("BLAGBOX_GRANT_ID"), messageid[0]).data
        self.query_one("#body").text = "<br>====<br>" + get_message(self, messageid[0])
        self.query_one("#body").text += "<br><br>Send from The ultimate Email, Calendar and Contacts Terminal Client" 
        self.query_one("#email_from").value = message.from_[0]['email']
        self.query_one("#title").value = "Re: " + message.subject

# Grab the information and send the reply to the email
    def send_email(self) -> None:
        participants = []
        list_of_emails = self.query_one("#email_from").value.split(";")        
        for i in range(0, len(list_of_emails)):
            participants.append({"name": "", "email": list_of_emails[i]})        
        
        body = {"subject" : self.query_one("#title").value, 
                "body": self.query_one("#body").text,
                "to": participants}
                #"reply_to_message_id": messageid[0]} Not working yet! -:( 
        try:
            nylas.messages.send(os.environ.get("BLAGBOX_GRANT_ID"), request_body = body)
            self.query_one("#email_from").value = ""
            self.query_one("#title").value = ""
            messageid.clear()
            participants.clear()
            app.pop_screen()
        except Exception as e:
            self.notify(e.message)

# This commands should not work on this screen
    def action_delete(self) -> None:
        pass

    def action_compose(self) -> None:
        pass

    def action_refresh(self) -> None:
        pass

    def action_reply(self) -> None:
        pass

# We're pressing a key
    def action_cancel(self) -> None:
        app.pop_screen()

    def action_send(self) -> None:
        self.send_email()

# We're pressing a button
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send":
            self.send_email()
        elif event.button.id == "cancel":
            app.pop_screen()

# Compose screen. This screen we will be displayed when we are
# creating or composing a new email
class ComposeEmail(Screen):
# Setup the bindings for the footer 
    BINDINGS = [
        Binding("r", "refresh", "Refresh", show=False),
        Binding("s", "send", "Send"),
        Binding("c", "cancel", "Cancel"),
        Binding("d", "delete", "Delete", show=False),
        Binding("o", "compose", "Compose Email", show=False),
        Binding("p", "reply", "Reply", show=False),
    ]

# Load up the main components of the screen
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        contacts = get_contacts()
        contact_list = []
        for contact in contacts:
            contact_list.append((str(contact.emails[0].email),contact.emails[0].email))	
        yield Select(prompt = "Email To", options = contact_list, id="email_to")
        yield Input(placeholder="Free Email To", id="free_email_to")
        yield Input(placeholder="Title", id="title")
        body = TextArea(id="body")
        body.show_line_numbers = False
        body.text = "<br><br>Send from my Terminal Email Client"
        yield body
        yield Horizontal(
            Button("Send!", variant="primary", id="send"),
            Label(" "),
            Button("Cancel", variant="primary", id="cancel"),
        )

# Grab the information and send the email
    def send_email(self) -> None:
        participants = []
        body = self.query_one("#body").text
        list_of_emails = self.query_one("#free_email_to").value.split(";")
        for i in range(0, len(list_of_emails)):
            participants.append({"name": "", "email": list_of_emails[i]})        
        if(list_of_emails[0] == ''):
            participants = []
            participants.append({"name": "", "email": self.query_one("#email_to").value})
        body = {"subject" : self.query_one("#title").value, 
                "body": self.query_one("#body").text,
                "to": participants}
        try:
            nylas.messages.send(os.environ.get("BLAGBOX_GRANT_ID"), request_body = body)
            participants.clear()
            app.pop_screen()
        except Exception as e:
            self.notify(e.message)

# This commands should not work on this screen
    def action_delete(self) -> None:
        pass

    def action_compose(self) -> None:
        pass

    def action_refresh(self) -> None:
        pass

    def action_reply(self) -> None:
        pass

# We pressing a key
    def action_cancel(self) -> None:
        app.pop_screen()

    def action_send(self) -> None:
        self.send_email()

# We pressing a button
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send":
            self.send_email()
        elif event.button.id == "cancel":
            app.pop_screen()

# Pass the main class and run the application
if __name__ == "__main__":
    app = EmailApp()
    app.run()
