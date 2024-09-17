# flyer-photo-ics-llm-app

This is a Shiny for Python app that lets you upload a photo of a flyer and get a calender event file (.ics) back. It uses the [OpenAI API](https://github.com/openai/openai-python) for the LLM and the [icalendar](https://pypi.org/project/icalendar/) package to generate the .ics file.

## Setup

The app expects that you have an OpenAI API key that you can paste into the input box. You can get one by visiting the OpenAI API [quickstart page](https://platform.openai.com/docs/quickstart/).  

## Accessing the app

You can clone this repo and run the app locally or publish the app onto [Connect Cloud](https://connect.posit.cloud/). You may need to create a Connect Cloud account to access the app.

## Features

- **Upload Event Flyer Photo**: The app allows users to upload a photo of an event flyer.
- **Parse Event Details**: Utilizes the OpenAI API to parse the event details from the uploaded photo.
- **Download Calendar Event File**: Users can download the parsed event details as a calendar event file (.ics).