import os
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ["MISTRAL_API_KEY"]
model = "mistral-small-latest"

client = Mistral(api_key=api_key)

prompt = """
You are a helpful assistant that provides concise and accurate answers.
Use only one sentence to respond. And do not make up information.
Don't use markdown in your response.
"""

chat_response = client.chat.complete(
    model= model,
    messages = [
        {
            "role": "system",
            "content": prompt,
        },
        {
            "role": "user",
            "content": "What is the best French cheese?",
        },
    ]
)
print(chat_response.choices[0].message.content)