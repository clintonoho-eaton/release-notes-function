import logging
import azure.functions as func
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("📩 Dynatrace release event received.")

    try:
        payload = req.get_json()
    except ValueError:
        return func.HttpResponse("Invalid JSON", status_code=400)

    title = payload.get("title", "Unknown Release")
    pipeline = payload.get("customProperties", {}).get("pipeline", "unknown")
    repo = payload.get("customProperties", {}).get("repository", "unknown")

    logging.info(f"🧾 Title: {title}")
    logging.info(f"🏗️ Pipeline: {pipeline}")
    logging.info(f"📁 Repo: {repo}")

    return func.HttpResponse(f"✅ Release '{title}' received.", status_code=200)
