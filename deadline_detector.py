import boto3
import json
from calendar_tool import create_calendar_event

client = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1"
)

def detect_deadlines_from_messages(messages):
    # Join all messages into one text
    messages_text = "\n".join(messages)
    
    prompt = f"""
    You are analyzing WhatsApp messages from a college student's class group.
    Extract any deadlines, assignments, exams, or important dates mentioned.
    
    Messages:
    {messages_text}
    
    Return ONLY a JSON array like this (no other text):
    [
        {{"title": "DBMS Assignment", "due_date": "2026-03-10", "subject": "DBMS"}},
        {{"title": "OS Exam", "due_date": "2026-03-15", "subject": "OS"}}
    ]
    
    If no deadlines found return empty array: []
    Dates must be in YYYY-MM-DD format.
    """
    
    response = client.invoke_model(
        modelId="us.amazon.nova-lite-v1:0",
        body=json.dumps({
            "messages": [
                {"role": "user", "content": [{"text": prompt}]}
            ]
        })
    )
    
    result = json.loads(response["body"].read())
    text = result["output"]["message"]["content"][0]["text"]
    
    try:
        clean_text = text.strip()
        clean_text = clean_text.replace("```json", "").replace("```", "").strip()
        deadlines = json.loads(clean_text)
        return deadlines
    except:
        print("Could not parse deadlines:", text)
        return []


def is_important_message(message):
    prompt = f"""
    You are analyzing a college Telegram group message.
    Message: "{message}"
    
    Is this message important? Categories:
    1. deadline
    2. class cancelled
    3. exam date
    4. new assignment
    5. professor announcement
    
    Return ONLY JSON like this:
    {{"important": true, "category": "deadline", "summary": "DBMS due March 25"}}
    OR if not important:
    {{"important": false}}
    
    No other text, just JSON.
    """
    
    response = client.invoke_model(
        modelId="us.amazon.nova-lite-v1:0",
        body=json.dumps({
            "messages": [
                {"role": "user", "content": [{"text": prompt}]}
            ]
        })
    )
    
    result = json.loads(response["body"].read())
    text = result["output"]["message"]["content"][0]["text"]
    
    try:
        clean_text = text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except:
        return {"important": False}


def auto_save_deadlines_from_whatsapp(messages):
    print("🔍 Analyzing messages for deadlines...")
    deadlines = detect_deadlines_from_messages(messages)
    
    if not deadlines:
        print("No deadlines found in messages!")
        return
    
    print(f"Found {len(deadlines)} deadlines!")
    
    for deadline in deadlines:
        result = create_calendar_event(
            title=deadline["title"],
            due_date=deadline["due_date"],
            subject=deadline.get("subject", "General")
        )
        print(f"✅ {result}")


if __name__ == "__main__":
    # Test 1 - important message
    result = is_important_message("DBMS assignment due tomorrow!")
    print("Test 1:", result)
    
    # Test 2 - not important
    result = is_important_message("Anyone coming to canteen?")
    print("Test 2:", result)
    
    # Test 3 - class cancelled
    result = is_important_message("Tomorrow's 9am class is cancelled")
    print("Test 3:", result)