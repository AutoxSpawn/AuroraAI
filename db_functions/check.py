from openai import OpenAI
import os
from dotenv import load_dotenv


load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

models = client.models.list()

print("\n✅ Available models with your API key:")
for model in models:
    print(model.id)