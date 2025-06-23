import logging
import os
import azure.functions as func
from openai import AzureOpenAI
import json

# Set up Azure OpenAI client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-12-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

def build_prompt(payload):
    # Extract useful info from the incoming event
    release_name = payload.get("releaseName", "Unnamed Release")
    summary = payload.get("summary", "No summary provided.")
    commits = payload.get("commitMessages", [])
    repo = payload.get("repository", "Unknown Repo")
    tag = payload.get("tag", "No tag")

    # Format commit messages
    formatted_commits = "\n".join(f"- {msg}" for msg in commits)

    # Build the prompt for the AI
    prompt = f"""
You are an AI assistant helping write professional software release notes.

Release: {release_name}
Repository: {repo}
Tag: {tag}
Summary: {summary}

The following commits were made:
{formatted_commits}

Please write a concise and user-friendly release note.
"""
    return prompt.strip()

# Azure Function entry point
app = func.FunctionApp()

@app.function_name(name="GenerateReleaseNotes")
@app.route(route="generate-release-notes", methods=["POST"])
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Azure Function triggered to generate release notes.")

    try:
        payload = req.get_json()
    except ValueError:
        return func.HttpResponse("Invalid JSON input.", status_code=400)

    prompt = build_prompt(payload)

    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        ai_output = response.choices[0].message.content
        return func.HttpResponse(json.dumps({"release_note": ai_output}), mimetype="application/json")

    except Exception as e:
        logging.error(f"Error generating release note: {e}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
