import logging
import azure.functions as func
import json
import os
from openai import AzureOpenAI

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('📥 Function triggered.')

    try:
        # Step 1: Try parsing the body
        try:
            req_body = req.get_json()
            logging.info(f"📦 Parsed request body: {req_body}")
        except Exception as e:
            logging.error(f"❌ Error parsing JSON: {e}")
            return func.HttpResponse(f"Bad request: Invalid JSON. {e}", status_code=400)

        # Step 2: Extract event name
        event_name = req_body.get("event_name") or req_body.get("tag")
        if not event_name:
            logging.warning("⚠️ Missing 'event_name' or 'tag' in payload.")
            event_name = "Unknown Event"

        logging.info(f"📝 Event Name: {event_name}")

        # Step 3: Set up OpenAI client
        try:
            client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_KEY"),
                api_version="2024-12-01-preview",
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
            logging.info("✅ OpenAI client initialized.")
        except Exception as e:
            logging.error(f"❌ Failed to initialize AzureOpenAI client: {e}")
            return func.HttpResponse(f"AzureOpenAI client error: {e}", status_code=500)

        # Step 4: Build the prompt
        prompt = f"""
        You are an AI assistant helping generate a release note summary.
        Based on the following deployment tag or event name, write a professional release note:

        Event Name or Tag: {event_name}

        The release note should summarize deployment purpose, changes, or improvements, even if some fields are missing.
        """

        # Step 5: Make OpenAI request
        try:
            response = client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes release changes."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=300
            )
            ai_output = response.choices[0].message.content.strip()
            logging.info(f"✅ AI Output: {ai_output}")
        except Exception as e:
            logging.error(f"❌ OpenAI API error: {e}")
            return func.HttpResponse(f"OpenAI API call failed: {e}", status_code=500)

        # Step 6: Return success response
        return func.HttpResponse(
            json.dumps({"release_note": ai_output}),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"❌ Unknown server error: {e}")
        return func.HttpResponse(f"Server error: {e}", status_code=500)Get
