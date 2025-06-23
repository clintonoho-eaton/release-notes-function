import logging
import os
import azure.functions as func
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("⚙️ Azure Function triggered")

    # Step 1: Parse JSON
    try:
        payload = req.get_json()
        logging.info(f"📦 Payload received: {json.dumps(payload)}")
    except Exception as e:
        logging.error(f"[STEP 1 ERROR] Failed to parse JSON: {e}")
        return func.HttpResponse(f"[STEP 1 ERROR] Invalid JSON: {e}", status_code=400)

    # Step 2: Extract fields
    try:
        release_name = payload.get("releaseName", "Unnamed Release")
        summary = payload.get("summary", "No summary provided.")
        commits = payload.get("commitMessages", [])
        repo = payload.get("repository", "Unknown Repo")
        tag = payload.get("tag", "No tag")
        logging.info(f"📌 Extracted: release={release_name}, repo={repo}, tag={tag}")
    except Exception as e:
        logging.error(f"[STEP 2 ERROR] Failed to extract fields: {e}")
        return func.HttpResponse(f"[STEP 2 ERROR] Field extraction failed: {e}", status_code=500)

    # Step 3: Init OpenAI
    try:
        api_key = os.getenv("AZURE_OPENAI_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if not api_key or not endpoint:
            raise ValueError("Missing AZURE_OPENAI_KEY or AZURE_OPENAI_ENDPOINT")

        client = AzureOpenAI(
            api_key=api_key,
            api_version="2024-12-01-preview",
            azure_endpoint=endpoint
        )
        logging.info("✅ Azure OpenAI client initialized")
    except Exception as e:
        logging.error(f"[STEP 3 ERROR] OpenAI client failed: {e}")
        return func.HttpResponse(f"[STEP 3 ERROR] OpenAI init failed: {e}", status_code=500)

    # Step 4: Format commits
    try:
        formatted_commits = "\n".join(f"- {msg}" for msg in commits)
        logging.info("📝 Commits formatted")
    except Exception as e:
        logging.error(f"[STEP 4 ERROR] Commit formatting failed: {e}")
        return func.HttpResponse(f"[STEP 4 ERROR] Commit formatting error: {e}", status_code=500)

    # Step 5: Create prompt
    try:
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
        logging.info("🧠 Prompt created")
    except Exception as e:
        logging.error(f"[STEP 5 ERROR] Prompt creation failed: {e}")
        return func.HttpResponse(f"[STEP 5 ERROR] Prompt generation error: {e}", status_code=500)

    # Step 6: Generate release notes
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You write professional software release notes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        logging.info("🤖 OpenAI returned a response")
        ai_output = response.choices[0].message.content.strip()
        return func.HttpResponse(ai_output, status_code=200, mimetype="text/plain")

    except Exception as e:
        logging.error(f"[STEP 6 ERROR] OpenAI call failed: {e}")
        return func.HttpResponse(f"[STEP 6 ERROR] OpenAI request failed: {e}", status_code=500)

