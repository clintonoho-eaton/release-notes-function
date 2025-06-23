import os
import logging
import azure.functions as func
from langchain.chat_models import AzureChatOpenAI
from langchain.schema import HumanMessage

# Azure Function trigger
app = func.FunctionApp()

@app.function_name(name="GenerateReleaseNotes")
@app.route(route="GenerateReleaseNotes", auth_level=func.AuthLevel.ANONYMOUS)
def generate_release_notes(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Processing release notes request.")

    try:
        payload = req.get_json()

        release_name = payload.get("releaseName", "Unnamed Release")
        summary = payload.get("summary", "No summary provided.")
        commits = payload.get("commitMessages", [])
        repo = payload.get("repository", "Unknown Repo")
        tag = payload.get("tag", "No tag")

        # Format commit messages
        formatted_commits = "\n".join(f"- {msg}" for msg in commits)

        # Build the prompt
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

        # Initialize Azure OpenAI LLM via LangChain
        llm = AzureChatOpenAI(
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            openai_api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
            openai_api_version=os.getenv("OPENAI_API_VERSION"),
            temperature=0.0
        )

        # Generate AI response
        response = llm([HumanMessage(content=prompt)])

        return func.HttpResponse(str(response.content), status_code=200)

    except Exception as e:
        logging.error(f"Error generating release notes: {e}")
        return func.HttpResponse(
            f"Error: {str(e)}", status_code=500
        )
