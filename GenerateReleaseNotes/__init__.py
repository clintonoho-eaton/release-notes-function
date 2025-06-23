import logging
import os
import azure.functions as func
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("⚙️ Azure Function triggered")

    try:
        payload = req.get_json()
        logging.info(f"📦 Payload received: {json.dumps(payload)}")
    except Exception as e:
        logging.error(f"❌ Failed to parse JSON: {e}")
        return func.HttpResponse(f"Invalid JSON: {e}", status_code=400)

    # Step 1: Extract fields from payload
    release_name = payload.get("releaseName", "Unnamed Release")
    summary = payload.get("summary", "No summary provided.")
    commits = payload.get("commitMessages", [])
    repo = payload.get("repository", "Unknown Repo")
    tag = payload.get("tag", "No tag")

    logging.info(f"📌 Extracted release info: {release_name}, {repo}, {tag}")

    # Step 2: Initialize Azure OpenAI Client
    try:
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version="2024-12-01-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        logging.info("✅ Azure OpenAI client initialized")
    except Exception as e:
        logging.error(f"❌ Failed to initialize OpenAI client: {e}")
        return func.HttpResponse(f"OpenAI Client Error: {e}", status_code=500)

    # Step 3: Format commits into readable text
    try:
        formatted_commits = "\n".join(f"- {msg}" for msg in commits)
        logging.info("📝 Formatted commit messages")
    except Exception as e:
        logging.error(f"❌ Failed to format commits: {e}")
        return func.HttpResponse(f"Commit formatting error: {e}", status_code=500)

    # Step 4: Construct AI prompt
    prompt = f"""
You are an AI assistant that writes professional software release notes.

Release: {release_name}
Repository: {repo}
Tag: {tag}
Summary: {summary}

The following changes were made:
{formatted_commits}

Please write clear and concise release notes in markdown format.
"""
    logging.info("📤 Prompt constructed successfully")

    # Step 5: Call OpenAI
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You write professional software release notes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        logging.info("✅ OpenAI response received")
        ai_output = response.choices[0].message.content.strip()
        return func.HttpResponse(ai_output, status_code=200, mimetype="text/plain")

    except Exception as e:
        logging.error(f"❌ OpenAI call failed: {e}")
        return func.HttpResponse(f"OpenAI error: {e}", status_code=500)
