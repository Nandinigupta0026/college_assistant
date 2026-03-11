import boto3
import json
from datetime import datetime
from calendar_tool import create_calendar_event, get_upcoming_events

client = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1"
)

# Simple local storage for now
deadlines = []

# Step 1 — Define your tools
tools = [
    {
        "toolSpec": {
            "name": "save_deadline",
            "description": "Save an assignment or exam deadline for the student",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Name of assignment or exam"
                        },
                        "due_date": {
                            "type": "string",
                            "description": "Due date in YYYY-MM-DD format"
                        },
                        "subject": {
                            "type": "string",
                            "description": "Subject name"
                        }
                    },
                    "required": ["title", "due_date"]
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "list_deadlines",
            "description": "Show all saved deadlines and assignments",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {}
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "create_calendar_event",
            "description": "Add an assignment, exam or event to Google Calendar",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "due_date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format"
                        },
                        "subject": {"type": "string"}
                    },
                    "required": ["title", "due_date"]
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "get_upcoming_events",
            "description": "Get all upcoming events and deadlines from Google Calendar",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {}
                }
            }
        }
    }
]

# Step 2 — Define actual functions
def save_deadline(title, due_date, subject="General"):
    deadlines.append({
        "title": title,
        "due_date": due_date,
        "subject": subject
    })
    return f"Saved! {title} due on {due_date}"

def list_deadlines():
    if not deadlines:
        return "No deadlines saved yet!"
    result = "Your deadlines:\n"
    for d in deadlines:
        result += f"- {d['title']} ({d['subject']}) → {d['due_date']}\n"
    return result

# Step 3 — Handle tool calls
def handle_tool_call(tool_name, tool_input):
    if tool_name == "save_deadline":
        # Now save to Google Calendar instead of local list!
        return create_calendar_event(
            tool_input.get("title"),
            tool_input.get("due_date"),
            tool_input.get("subject", "General")
        )
    elif tool_name == "list_deadlines":
        return get_upcoming_events()
    elif tool_name == "create_calendar_event":
        return create_calendar_event(**tool_input)
    elif tool_name == "get_upcoming_events":
        return get_upcoming_events()

# Step 4 — Ask Nova with tools
conversation_history = []

def ask_nova(user_message):
    conversation_history.append({
        "role": "user",
        "content": [{"text": user_message}]
    })

    response = client.invoke_model(
        modelId="us.amazon.nova-lite-v1:0",
        body=json.dumps({
            "system": [
                {
                    "text": "You are a helpful personal assistant for a college student. Use tools when needed to save and retrieve information."
                }
            ],
            "messages": conversation_history,
            "toolConfig": {"tools": tools}
        })
    )

    result = json.loads(response["body"].read())
    output = result["output"]["message"]

    # Check if Nova wants to use a tool
    for block in output["content"]:
        if block.get("toolUse"):
            tool_name = block["toolUse"]["name"]
            tool_input = block["toolUse"]["input"]
            tool_use_id = block["toolUse"]["toolUseId"]

            print(f"⚙️ Nova is using tool: {tool_name}")

            # Run the actual function
            tool_result = handle_tool_call(tool_name, tool_input)

            # Add tool result back to conversation
            conversation_history.append({
                "role": "assistant",
                "content": output["content"]
            })
            conversation_history.append({
                "role": "user",
                "content": [{
                    "toolResult": {
                        "toolUseId": tool_use_id,
                        "content": [{"text": tool_result}]
                    }
                }]
            })

            # Get Nova's final reply
            final_response = client.invoke_model(
                modelId="us.amazon.nova-lite-v1:0",
                body=json.dumps({
                    "system": [{"text": "You are a helpful college assistant."}],
                    "messages": conversation_history,
                    "toolConfig": {"tools": tools}
                })
            )
            final_result = json.loads(final_response["body"].read())
            final_text = final_result["output"]["message"]["content"][0]["text"]

            conversation_history.append({
                "role": "assistant",
                "content": [{"text": final_text}]
            })
            return final_text

    # No tool used — normal reply
    nova_reply = output["content"][0]["text"]
    conversation_history.append({
        "role": "assistant",
        "content": [{"text": nova_reply}]
    })
    return nova_reply


# Fixed code ✅
if __name__ == "__main__":
    print("🎓 College Assistant Ready! Type 'quit' to exit\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == "quit":
            print("Bye! 👋")
            break
        reply = ask_nova(user_input)
        print(f"Nova: {reply}\n")