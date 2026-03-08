import os
import asyncio
from google import genai
from dotenv import load_dotenv

async def test_hello():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    print("Sending test request...")
    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents="Say hello!"
        )
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_hello())
