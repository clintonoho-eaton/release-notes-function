import logging
import azure.functions as func
import json
import os
from openai import AzureOpenAI

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('⚙️ HTTP trigger function received a request.')

    try:
        # ✅ Step 1: Parse JSON body
        try:
            req_body = req.get_json()
        except ValueError:
            raise ValueError("Invalid or missing JSON in request body.")

        # ✅ Step 2: Extract important fields
        event_name = req_body.get("event_name") or req_body.get("tag") or "Unknown Event"
        logging.info(f"📦 Event received: {event_name}")

        # ✅ Step 3: Setup Azure OpenAI client
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2023-05-15",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )

        # ✅ Step 4: Craft the AI prompt
        prompt = f"""
        You are an AI assistant helping generate a release note summary.
        Based on the following deployment tag or event name, write a professional release note:

        Event Name or Tag: {event_name}

        The release note should summarize deployment purpose, changes, or improvements, even if some fields are missing.
        """

        # ✅ Step 5: Generate release note using GPT-4
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),  # e.g., "gpt-4"
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes release changes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=300
        )

        # ✅ Step 6: Parse and return the AI-generated response
        ai_output = response.choices[0].message.content.strip()
        logging.info(f"✅ AI-generated release note: {ai_output}")

        return func.HttpResponse(
            json.dumps({"release_note": ai_output}),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"❌ Internal server error: {str(e)}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
