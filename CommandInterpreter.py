from AppOpener import open as appopen
from webbrowser import open as webopen
from pywhatkit import search, playonyt  # type: ignore
from dotenv import dotenv_values
from bs4 import BeautifulSoup
from rich import print
from groq import Groq
import subprocess
import requests
import keyboard
import asyncio
import os


# Load environment variables
env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")

# Initialize Groq client
client = Groq(api_key=GroqAPIKey)

# For Google scraping
useragent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'

# For content generation memory
messages = []

# Setup for system role
username = os.environ.get("Username", "Assistant")
SystemChatBot = [{
    "role": "system",
    "content": f"Hello, I am {username}, You're a content writer. You have to write content like letters, articles, and blogs in a professional manner."
}]

# ========== Core Functionalities ==========

def ContentWriterAI(prompt):
    messages.append({"role": "user", "content": prompt})
    try:
        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=SystemChatBot + messages,
            max_tokens=2048,
            temperature=0.7,
            top_p=1,
            stream=True,
            stop=None
        )
        Answer = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content

        Answer = Answer.replace("</s>", "")
        messages.append({"role": "assistant", "content": Answer})
        return Answer
    except Exception as e:
        print(f"[red]Error generating content:[/red] {e}")
        return "An error occurred while generating content."

def PlayYoutube(query):
    try:
        playonyt(query)
        return f"Playing {query} on YouTube."
    except Exception as e:
        print(f"[red]Error playing video:[/red] {e}")
        return "Could not play video."

def OpenApp(app):
    try:
        appopen(app, match_closest=True, output=True, throw_error=True)
        return f"Opening {app}."
    except Exception as e:
        print(f"[red]Error opening app {app}:[/red] {e}")
        return f"Could not open {app}."

def extract_links(html):
    if html is None:
        return []
    soup = BeautifulSoup(html, 'html.parser')
    links = soup.find_all('a', {'jsname': 'UWckNb'})
    return [link.get('href') for link in links]

def search_google(query):
    url = f"https://www.google.com/search?q={query}"
    headers = {"User-Agent": useragent}
    try:
        response = requests.get(url, headers=headers)
        return response.text if response.status_code == 200 else None
    except Exception as e:
        print(f"[red]Error retrieving Google search results:[/red] {e}")
        return None

# ========== Main Executor ==========

async def TranslateAndExecute(commands: list[str]):
    funcs = []

    for command in commands:
        if isinstance(command, str):
            command = command.lower().strip()

            # Google search
            if command.startswith("google search "):
                query = command.removeprefix("google search ")
                html = search_google(query)
                if html:
                    links = extract_links(html)
                    if links:
                        webopen(links[0])
                    else:
                        print("[yellow]No links found in the search results.[/yellow]")
                else:
                    print("[red]Failed to retrieve HTML for search.[/red]")

            # Open YouTube
            elif command == "open youtube":
                webopen("https://www.youtube.com")
                print("[green]Opening YouTube...[/green]")

            # Close YouTube (force closes Chrome)
            elif command == "close youtube":
                os.system("taskkill /f /im chrome.exe")  # Warning: closes all Chrome instances
                print("[green]Closing YouTube (Chrome)...[/green]")

            # Play YouTube
            elif command.startswith("play "):
                funcs.append(asyncio.to_thread(PlayYoutube, command.removeprefix("play ")))

            # Content generation
            elif command.startswith("content "):
                funcs.append(asyncio.to_thread(ContentWriterAI, command.removeprefix("content ")))

            # App opening
            elif command.startswith("open "):
                funcs.append(asyncio.to_thread(OpenApp, command.removeprefix("open ")))

            else:
                print(f"[yellow]No function found for:[/yellow] {command}")
        else:
            print(f"[yellow]Skipping invalid command (not a string):[/yellow] {command}")

    try:
        return await asyncio.gather(*funcs)
    except Exception as e:
        print(f"[red]Error executing commands:[/red] {e}")
        return None
