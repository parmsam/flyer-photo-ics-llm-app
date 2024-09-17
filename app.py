from shiny import App, ui, render, reactive
from openai import OpenAI
import os
from datetime import datetime
from icalendar import Calendar, Event
import io
import base64
import json
import uuid

try:
    from setup import api_key1
except ImportError:
    api_key1 = os.getenv("OPENAI_API_KEY")

app_info = """
This app lets you upload a photo of an event flyer and download a calendar file 
(ICS format) with the event information extracted from the flyer.
"""

def create_event(event_data):
    event = Event()
    event.add('summary', event_data.get("event name", "Unnamed Event"))
    event.add('name', event_data.get("event name", "Unnamed Event"))
    event.add('description', event_data.get("description", ""))
    event.add('organizer', event_data.get("organizer", ""))
    event.add('location', event_data.get("location", ""))
    event.add('uid', str(uuid.uuid4()))
    
    # Combine date and time, assuming they're in a compatible format
    start_time = f"{event_data.get('date', '')} {event_data.get('start time', '')}"
    try:
        # Convert 12-hour format to 24-hour format
        event_datetime = datetime.strptime(start_time, "%Y-%m-%d %I:%M %p")
        event.add('dtstart', event_datetime)
    except ValueError:
        # If parsing fails, we'll just not set a start time
        pass
    
    end_time = f"{event_data.get('date', '')} {event_data.get('end time', '')}"
    try:
        # Convert 12-hour format to 24-hour format
        event_end_datetime = datetime.strptime(end_time, "%Y-%m-%d %I:%M %p")
        event.add('dtend', event_end_datetime)
    except ValueError:
        # If parsing fails, we'll just not set an end time
        pass
    
    return event

app_ui = ui.page_fluid(
    ui.panel_title("Event Flyer to Calendar"),
    ui.markdown(app_info),
    ui.row(
        ui.input_password(
            "api_key", 
            "OpenAI API Key",
            value = api_key1,
            width = "30%"
        ),
        ui.input_file(
            "flyer", 
            "Upload Event Flyer", 
            accept=[".jpg", ".png", ".jpeg"],
            width = "30%"
        ),
    ),
    ui.card(
        ui.download_button("download_ics", "Download ICS File"),
        ui.output_text_verbatim("event_info"),
    )
)

def server(input, output, session):
    event_data = reactive.Value(None)
    current_state = reactive.Value("")

    @reactive.Effect
    @reactive.event(input.flyer)
    def process_image():
        # Check if an image is uploaded
        if input.flyer() is None:
            ui.notification_show("Please upload an image first.", type="error")
            return
        elif input.flyer() is not None:
            # Get the uploaded file content
            file_content = input.flyer()[0]["datapath"]
            
            # Check for API key
            api_key = input.api_key()
            if not api_key:
                ui.notification_show("Please enter your OpenAI API key.", type="error")
                return

            # Read and encode the image file
            try:
                with open(file_content, "rb") as image_file:
                    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                ui.notification_show("Image read successfully.", type="info")
            except Exception as e:
                ui.notification_show(f"Error reading the image file: {str(e)}", type="error")
                return
            
            # Process the image with OpenAI API
            try: 
                client = OpenAI(api_key=api_key)
                # get file extension from file path
                image_file_ext = os.path.splitext(file_content)[1][1:]
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system", 
                            "content": """You are a highly proficient assistant 
                            tasked parsing event flyer photos for information. 
                            You parse data and return JSON."""
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text", 
                                    "text": f"""Analyze this event flyer and extract
                                    the event information. Format the response as JSON.
                                    Ensure there are fields for 
                                    "date", "start time", "end time", 
                                    "description", "organizer", "event name", 
                                    and "location" in the JSON response. 
                                    - Ensure that %I:%M %p format is used for times.
                                    - Assume it is this year if no year provided. 
                                    - Nothing else but JSON in the response. Do not include ```json ``` (triple tick marks).
                                    - There might be more than one event on a flyer.
                                    - For the JSON, contain the events inside an array called "events"
                                    - Ensure it is compliant with JSON rules.
                                    """
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"""data:image/{image_file_ext};base64,{base64_image}"""
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=450
                )
                event_data.set(response.choices[0].message.content)
            except Exception as e:
                ui.notification_show(f"Error: {str(e)}", type="error")

    @output
    @render.text
    def event_info():
        if event_data() is not None:
            return f"Extracted Event Information:\n{event_data()}"
        return "Upload an image to extract event information."

    @output
    @render.download(
        filename=lambda: "itinerary.ics"
    )
    async def download_ics():
        if event_data() is not None:
            cal = Calendar()
            try:
                # Parse the JSON data (assuming it's correctly formatted)
                data = json.loads(event_data())
                # Check if data contains multiple events
                if "events" in data:
                    events = data["events"]
                    if isinstance(events, list):
                        for event_item in events:
                            event = create_event(event_item)
                            cal.add_component(event)
                else:
                    # Handle single event case
                    event = create_event(data)
                    cal.add_component(event)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                return
            
            yield cal.to_ical()

app = App(app_ui, server)
