import subprocess
import threading
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import dotenv_values
import mtranslate as mt
import time
import asyncio

# Load environment variables from the .env file.
env_vars = dotenv_values(".env")

# Get the input language setting from the environment variables.
InputLanguage = env_vars.get("InputLanguage", "en")  # Default to 'en' if not set.

# Define the HTML code for the speech recognition interface.
HtmlCode = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Speech Recognition</title>
</head>
<body>
    <button id="start" onclick="startRecognition()">Start Recognition</button>
    <button id="end" onclick="stopRecognition()">Stop Recognition</button>
    <p id="output"></p>
    <script>
        const output = document.getElementById('output');
        let recognition;

        function startRecognition() {
            recognition = window.webkitSpeechRecognition ? new webkitSpeechRecognition() : new SpeechRecognition();
            recognition.lang = 'en';
            recognition.continuous = true;

            recognition.onresult = function(event) {
                const transcript = event.results[event.results.length - 1][0].transcript;
                output.textContent += transcript;
            };

            recognition.onend = function() {
                recognition.start();
            };

            recognition.start();
        }

        function stopRecognition() {
            recognition.stop();
        }
    </script>
</body>
</html>
'''

# Replace the language setting in the HTML code with the input language from the environment variables.
HtmlCode = HtmlCode.replace("recognition.lang = 'en';", f"recognition.lang = '{InputLanguage}';")

# Write the modified HTML code to a file.
with open("DataVoice.html", "w", encoding='utf-8') as f:
    f.write(HtmlCode)

# Get the current working directory.
current_dir = os.getcwd()
# Generate the file path for the HTML file.
Link = f"file:///{current_dir}/DataVoice.html"

# Set Chrome options for the WebDriver.
chrome_options = Options()
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.142.86 Safari/537.36"
chrome_options.add_argument(f"user-agent={user_agent}")
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--use-fake-device-for-media-stream")
# For debugging, comment out headless so the browser UI shows
# chrome_options.add_argument("--headless")

# Initialize the Chrome WebDriver using the ChromeDriverManager.
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Function to set the assistant's status by writing it to a file.
def SetAssistantStatus(Status):
    temp_dir = f"{current_dir}/Frontend/Files"
    os.makedirs(temp_dir, exist_ok=True)  # Create dir if missing
    with open(f'{temp_dir}/Status.data', 'w', encoding='utf-8') as file:
        file.write(Status)

# Function to modify a query to ensure proper punctuation and formatting.
def QueryModifier(query):
    new_query = query.lower().strip()
    query_words = new_query.split()
    question_words = ['how', 'what', 'who', 'where', 'when', 'why', 'which', 'whose', 'whom', 'can you', "what's", "where's", "how's", "can you"]

    # Check if the query is a question and add a question mark if necessary.
    if any(word + " " in new_query for word in question_words):
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        # Add a period if the query is not a question.
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "."
        else:
            new_query += "."

    return new_query.capitalize()

# Universal translator function to translate non-English speech to English.
def UniversalTranslator(Text):
    try:
        english_translation = mt.translate(Text, "en", "auto")
        return english_translation.capitalize()
    except Exception as e:
        print(f"Translation error: {e}")
        return Text

# Function to perform speech recognition using the WebDriver.
def SpeechRecognition():
    driver.get(Link)
    driver.find_element(by=By.ID, value="start").click()

    start_time = time.time()
    timeout = 60  # seconds max to wait

    while True:
        try:
            Text = driver.find_element(by=By.ID, value='output').text

            if Text:
                driver.find_element(by=By.ID, value='end').click()

                if InputLanguage.lower() == 'en' or 'en' in InputLanguage.lower():
                    return QueryModifier(Text)
                else:
                    SetAssistantStatus("Translating .....")
                    return QueryModifier(UniversalTranslator(Text))

            if time.time() - start_time > timeout:
                print("Speech recognition timed out.")
                driver.find_element(by=By.ID, value='end').click()
                return ""

            time.sleep(0.1)

        except Exception as e:
            print(f"Error: {e}")
            break

# Asynchronous function to call the SpeechRecognition in a non-blocking way
async def AsyncSpeechRecognition():
    return await asyncio.to_thread(SpeechRecognition)

# Main execution block.
if __name__ == "__main__":
    while True:
        result = asyncio.run(AsyncSpeechRecognition())
        if result:
            print(f"Recognized Query: {result}")
        else:
            print("No speech recognized.")
