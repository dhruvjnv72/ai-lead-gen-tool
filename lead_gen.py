from groq import Groq
import csv
import time
import requests
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

print("=" * 50)
print("   AI LEAD GEN BOT - Fully Automatic")
print("=" * 50)

city = input("\nWhich city to search in? (e.g. delhi, mumbai): ").lower()

print(f"\n🔍 Searching JustDial for agencies in {city}...\n")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

url = f"https://www.justdial.com/{city}/Digital-Marketing-Companies"

response = requests.get(url, headers=headers, timeout=10)
soup = BeautifulSoup(response.text, "html.parser")

# Extract agency names
agencies = []

# Try to find business names
for tag in soup.find_all(["span", "p", "h2", "h3", "a"], limit=200):
    text = tag.get_text(strip=True)
    if len(text) > 5 and len(text) < 60:
        if any(word in text.lower() for word in ["digital", "media", "marketing", "agency", "studio", "creative", "web", "tech"]):
            if text not in agencies:
                agencies.append(text)
                print(f"🏢 Found: {text}")
        if len(agencies) >= 15:
            break

print(f"\n✅ Found {len(agencies)} agencies!")

if len(agencies) == 0:
    print("⚠️ JustDial blocked us too. Using backup list...")
    agencies = [
        f"Digital Marketing Agency {i+1} in {city.title()}"
        for i in range(10)
    ]

print("⏳ Generating personalized emails...\n")

results = []

for i, agency_name in enumerate(agencies[:10]):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"""Write a cold email to the owner of '{agency_name}' in {city.title()}.
                We offer an AI tool that automatically finds new clients for digital marketing agencies.
                
                Format:
                SUBJECT: [subject line]
                EMAIL: [body under 80 words, friendly and professional]"""
            }
        ],
        model="llama-3.3-70b-versatile",
    )

    response_text = chat_completion.choices[0].message.content

    results.append({
        "agency": agency_name,
        "city": city.title(),
        "email": response_text
    })

    print(f"✅ Email generated for: {agency_name}")
    time.sleep(0.5)

# Save to CSV
with open("auto_leads.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["agency", "city", "email"])
    writer.writeheader()
    writer.writerows(results)

print("\n" + "=" * 50)
print(f"🎉 {len(results)} leads generated automatically!")
print("📁 Check auto_leads.csv!")
print("=" * 50)