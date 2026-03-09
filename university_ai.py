from openai import OpenAI
from PyPDF2 import PdfReader
import os

# Get API key from environment variable
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Create Groq client
client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# conversation memory
conversation = []

# Load Prospectus
reader = PdfReader("static/brochure/EDUSTACK BROCHURE.pdf")

prospectus_text = ""

for page in reader.pages:
    text = page.extract_text()
    if text:
        prospectus_text += text


system_prompt = f"""
You are the official AI assistant of Edustack University.

Use the university prospectus to answer student questions.

University Prospectus:
{prospectus_text}

Rules:
- Help students with admissions
- Explain courses
- Guide about placements
- Recommend courses if student is confused
- Answer politely
- Keep answers short and clear
"""

def ask_ai(question):

    conversation.append({
        "role": "user",
        "content": question
    })

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            *conversation
        ]
    )

    reply = response.choices[0].message.content

    conversation.append({
        "role": "assistant",
        "content": reply
    })

    return reply