import cohere  # Import the Cohere library for AI services.
from rich import print  # type: ignore # Import the Rich library to enhance terminal outputs.
from dotenv import dotenv_values  # type: ignore # Import dotenv to load environment variables from a .env file.

# Load environment variables from the .env file.
env_vars = dotenv_values('.env')

# Retrieve API key.
CohereAPIKey = env_vars.get("CohereAPIKey")

# Create a Cohere client using the provided API key.
co = cohere.Client(api_key=CohereAPIKey)

# Define a list of recognized function keywords for task categorization.
funcs = [
    "exit", "general", "realtime", "open", "close", "play",
    "generate image", "system", "content", "google search",
    "youtube search", "reminder"
]

# Initialize an empty list to store user messages.
messages = []

# Define the preamble that guides the AI model on how to categorize queries.
preamble = """
You are a very accurate Decision-Making Model, which decides what kind of a query is given to you. 
You will decide whether a query is a 'general' query, a 'realtime' query, or is asking to perform tasks.

** Do not answer any query, just decide what kind of query is given to you. **
→ Respond with 'general (query)' if a query can be answered by a llm model (conversational ai).
→ Respond with 'realtime (query)' if a query can not be answered by a llm model (because they do not have real-time data).
→ Respond with 'open (application name or website name)' if a query is asking to open any application like 'open chrome'.
→ Respond with 'close (application name)' if a query is asking to close any application like 'close chrome'.
→ Respond with 'play (song name)' if a query is asking to play any song like 'play afsanay by ys'.
→ Respond with 'generate image (image prompt)' if a query is requesting to generate an image with a prompt.
→ Respond with 'reminder (datetime with message)' if a query is requesting to set a reminder like 'remind me to call John at 6 PM'.
→ Respond with 'system (task name)' if a query is asking to mute, unmute, volume up, volume down, or other system-level tasks.
→ Respond with 'google search (topic)' if a query is asking to search a specific topic on google.
→ Respond with 'youtube search (topic)' if a query is asking to search a specific topic on youtube.
→ Respond with 'content (topic)' if a query is asking to write any type of content like applications, blogs, articles, etc.
→ If the query is asking to perform multiple tasks like 'open facebook, telegram and close whatsapp', 
   respond with 'general (query)' if you can't decide the kind of query or if a query is asking to do something that’s beyond your capability.
→ If the user is saying goodbye or wants to end the conversation like 'bye jarvis', respond with 'bye boss'.
"""

# Define a chat history with predefined user-chatbot interactions for context.
chatHistory = [
    {"role": "User", "message": "how are you?"},
    {"role": "Chatbot", "message": "general how are you?"},
    {"role": "User", "message": "do you like pizza?"},
    {"role": "Chatbot", "message": "general do you like pizza?"},
    {"role": "User", "message": "open chrome and tell me about mahatma gandhi."},
    {"role": "Chatbot", "message": "open chrome, general tell me about mahatma gandhi."},
    {"role": "User", "message": "open chrome and firefox"},
    {"role": "Chatbot", "message": "Open chrome, open firefox"},
    {"role": "User", "message": "what is today's date and by the way remind me that i have a dancing performance on 5th aug at 11pm"},
    {"role": "Chatbot", "message": "general what is today's date, reminder 11:00pm 5th aug dancing performance"},
    {"role": "User", "message": "chat with me."},
    {"role": "Chatbot", "message": "general chat with me."}
]

# Define the main function for decision-making on queries.
def FirstLayerDMM(prompt: str = "test"):
    # Add the user's query to the messages list.
    messages.append({"role": "user", "content": f"{prompt}"})

    # Create a streaming chat session with the Cohere model.
    stream = co.chat_stream(
        model='command-r-plus',
        message=prompt,
        temperature=0.7,
        chat_history=chatHistory,
        prompt_truncation='OFF',
        connectors=[],
        preamble=preamble
    )

    # Initialize an empty string to store the generated response.
    response = ""

    # Iterate over events in the stream and capture text generation events.
    for event in stream:
        if event.event_type == "text-generation":
            response += event.text

    # Clean and split responses into individual tasks.
    response = response.replace("\n", "").split(",")
    response = [i.strip() for i in response]

    # Filter the tasks based on recognized function keywords.
    filtered_response = [task for task in response if any(task.startswith(func) for func in funcs)]

    # Recursively handle unresolved queries.
    if "query" in filtered_response:
        return FirstLayerDMM(prompt=prompt)
    return filtered_response

# Entry point for the script.
if __name__ == "__main__":
    while True:
        user_input = input(">>> ")
        print(FirstLayerDMM(user_input))
