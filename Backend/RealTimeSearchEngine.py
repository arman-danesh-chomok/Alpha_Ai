from googlesearch import search  # For performing Google searches
from groq import Groq  # For Groq AI API integration
from json import load, dump  # For reading and writing JSON files
import datetime  # For real-time date and time information
from dotenv import dotenv_values  # For reading environment variables
import os  # For path operations
import logging  # For error logging
from queue import Queue  # For basic concurrency management
import time  # To add delays between searches (in case of rate-limiting)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='chatbot.log'
)

# Load environment variables with validation
def load_environment():
    try:
        env_vars = dotenv_values(".env")
        required_vars = ["Username", "Assistantname", "GroqAPIKey"]
        
        for var in required_vars:
            if not env_vars.get(var):
                raise ValueError(f"Missing required environment variable: {var}")
        
        return env_vars
    except Exception as e:
        logging.error(f"Error loading environment variables: {str(e)}")
        raise

# Initialize environment variables
try:
    env_vars = load_environment()
    Username = env_vars["Username"]
    Assistantname = env_vars["Assistantname"]
    GroqAPIKey = env_vars["GroqAPIKey"]
except Exception as e:
    logging.error(f"Environment setup failed: {str(e)}")
    raise

# Initialize Groq client
client = Groq(api_key=GroqAPIKey)

# System message with proper formatting
System = (
    f"Hello, I am {Username}. You are a very accurate and advanced AI chatbot "
    f"named {Assistantname} which has real-time up-to-date information from the internet.\n"
    "*** Provide Answers In a Professional Way, make sure to add full stops, "
    "commas, question marks, and use proper grammar.***\n"
    "*** Just answer the question from the provided data in a professional way. ***"
)

# Chat log management with proper error handling
def load_or_create_chat_log():
    chat_log_path = os.path.join("Data", "ChatLog.json")
    try:
        os.makedirs(os.path.dirname(chat_log_path), exist_ok=True)
        try:
            with open(chat_log_path, "r") as f:
                return load(f)
        except FileNotFoundError:
            with open(chat_log_path, "w") as f:
                dump([], f)
            return []
    except Exception as e:
        logging.error(f"Chat log operation failed: {str(e)}")
        return []

messages = load_or_create_chat_log()

# Message queue for handling multiple queries
message_queue = Queue()

def GoogleSearch(query, max_retries=3):
    """Perform Google search with error handling and retries"""
    for attempt in range(max_retries):
        try:
            time.sleep(2)  # Delay to prevent hitting rate limits (2 seconds between requests)
            results = list(search(query, num=5, stop=5, pause=2))
            if not results:
                return f"No results found for '{query}'"
            Answer = f"Search results for '{query}':\n[start]\n"
            for url in results:
                Answer += f"URL: {url}\n"
            Answer += "[end]"
            return Answer
        except Exception as e:
            if attempt == max_retries - 1:
                logging.error(f"Google search failed: {str(e)}")
                return f"Search failed after {max_retries} attempts"
            continue

def Information():
    """Get formatted real-time information"""
    current_date_time = datetime.datetime.now()
    return (
        f"Real-time Information:\n"
        f"Day: {current_date_time.strftime('%A')}\n"
        f"Date: {current_date_time.strftime('%d')}\n"
        f"Month: {current_date_time.strftime('%B')}\n"
        f"Year: {current_date_time.strftime('%Y')}\n"
        f"Time: {current_date_time.strftime('%H:%M:%S')}\n"
    )

def clean_message_history(max_history=10):
    """Clean up message history to a manageable size"""
    global messages
    messages = messages[-max_history:] if len(messages) > max_history else messages

def RealtimeSearchEngine(prompt, max_history=10):
    """Enhanced real-time search and response generation"""
    global messages
    
    if not prompt.strip():
        return "Please provide a valid query"

    try:
        # Manage message history
        clean_message_history(max_history)
        messages.append({"role": "user", "content": prompt})

        # Prepare system context
        current_context = [
            {"role": "system", "content": System},
            {"role": "system", "content": GoogleSearch(prompt)},
            {"role": "system", "content": Information()}
        ] + messages

        # Generate response with error handling
        try:
            completion = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=current_context,
                temperature=0.7,
                max_tokens=2048,
                top_p=1,
                stream=True,
                stop=None
            )
        except Exception as e:
            logging.error(f"API call failed: {str(e)}")
            return "Sorry, I encountered an error while processing your request"

        # Process streaming response
        Answer = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content

        # Clean and save response
        Answer = Answer.strip().replace("</s>", "")
        messages.append({"role": "assistant", "content": Answer})

        # Save chat log
        with open(os.path.join("Data", "ChatLog.json"), "w") as f:
            dump(messages, f, indent=4)

        return Answer.strip()

    except Exception as e:
        logging.error(f"RealTimeSearchEngine error: {str(e)}")
        return "An error occurred while processing your request"

if __name__ == "__main__":
    print(f"Chatbot {Assistantname} initialized. Type 'quit' to exit.")
    while True:
        try:
            prompt = input("Enter your query: ").strip()
            if prompt.lower() == 'quit':
                break
            print(RealtimeSearchEngine(prompt))
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            logging.error(f"Main loop error: {str(e)}")
            print("An error occurred. Please try again.")
