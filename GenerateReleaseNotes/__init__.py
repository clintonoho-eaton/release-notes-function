import azure.functions as func
import os
import logging

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Function started.")

    try:
        payload = req.get_json()
        logging.info(f"Payload received: {payload}")
    except Exception as e:
        logging.error(f"Error parsing JSON: {e}")
        return func.HttpResponse("Invalid JSON payload.", status_code=400)

    try:
        release_name = payload.get("releaseName", "Unnamed Release")
        summary = payload.get("summary", "No summary provided.")
        commits = payload.get("commitMessages", [])
        repo = payload.get("repository", "Unknown Repo")
        tag = payload.get("tag", "No tag")

        formatted_commits = "\n".join(f"- {msg}" for msg in commits)

        prompt = f"""You are an AI assistant helping write professional software release notes.

Release: {release_name}
Repository: {repo}
Tag: {tag}
Summary: {summary}

The following commits were made:
{formatted_commits}

Please write a concise and user-friendly release note.
"""

        logging.info("Prompt generated successfully.")
        return func.HttpResponse(prompt.strip(), status_code=200)

    except Exception as e:
        logging.error(f"Unhandled exception: {e}")
        return func.HttpResponse("Internal Server Error", status_code=500)
