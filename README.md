# Personal Executive Assistant Agent

This project implements a personal executive assistant agent capable of understanding natural language queries to manage Google Calendar events and search Google Drive files. It leverages the Gemini Large Language Model for query understanding and directly integrates with Google Calendar and Google Drive APIs for task execution.

**Note:** While Calendar and Drive integrations are functional, the Presentation tool is still a placeholder. Full integration with these services (including OAuth 2.0 authentication and specific API calls) is a major next step for all tools.

## Features (Now with Real Integration for Calendar & Drive)

*   **LLM-Powered Query Understanding:** Uses Google's Gemini model to interpret user queries, extract intent (e.g., check calendar, fetch document), and identify key parameters.
*   **Planning:** Creates a basic sequence of actions to fulfill the query.
*   **Real Google Calendar Integration:**
    *   Checks for existing events.
    *   Creates new calendar events.
    *   Requires OAuth 2.0 authorization.
*   **Real Google Drive Integration:**
    *   Searches for files by name, content keywords, or MIME type.
    *   Requires OAuth 2.0 authorization.
*   **Web Interface:** A simple web UI to enter queries and view the agent's process and results.
*   **Placeholder Presentation Tool:** Includes a non-functional placeholder for future presentation generation capabilities.

## Project Structure

```
.
├── assistant_agent/        # Core Python code for the agent
│   ├── __init__.py
│   ├── agent.py            # Main ExecutiveAssistantAgent class
│   ├── llm_integration.py  # Gemini LLM interaction logic
│   └── tools.py            # Google Calendar/Drive tools and placeholders
├── static/                 # For CSS/JS (if any more advanced UI is built)
│   └── .gitkeep
├── templates/              # HTML templates for Flask
│   └── index.html
├── app.py                  # Flask web server
├── requirements.txt        # Python dependencies
├── token_calendar.json     # (Generated after Calendar OAuth)
├── token_drive.json        # (Generated after Drive OAuth)
└── README.md               # This file
```
*(Note: `credentials.json` should also be in the root but is gitignored).*

## API Key and Credentials Setup

To use the agent with its full capabilities, you **must** configure API keys and authentication:

1.  **Gemini API Key (MANDATORY):**
    *   Obtain a `GEMINI_API_KEY` from Google AI Studio (see [Google AI Studio](https://aistudio.google.com/)).
    *   Set it as an environment variable. For example, in Linux/macOS:
        ```bash
        export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
        ```
        (On Windows, use `set GEMINI_API_KEY="YOUR_GEMINI_API_KEY"` in Command Prompt or `$env:GEMINI_API_KEY="YOUR_GEMINI_API_KEY"` in PowerShell).

2.  **Google Cloud Project & APIs (MANDATORY for Calendar/Drive):**
    *   Create a new project or use an existing one in the [Google Cloud Console](https://console.cloud.google.com/).
    *   **Enable the "Google Calendar API" and "Google Drive API"** for this project. You can find these in the "APIs & Services" -> "Library" section.

3.  **OAuth 2.0 Credentials for Google Services (MANDATORY for Calendar/Drive):**
    This agent uses OAuth 2.0 to access your Google Calendar and Drive data on your behalf.
    *   **Create OAuth 2.0 Client ID:**
        *   In the Google Cloud Console, navigate to "APIs & Services" -> "Credentials".
        *   Click "+ CREATE CREDENTIALS" and select "OAuth client ID".
        *   Choose **"Desktop app"** for the "Application type". This is generally the simplest for local development and tools like this one. (If you were deploying a web application, you'd choose "Web application" and configure redirect URIs).
        *   Give it a name (e.g., "Executive Assistant Agent Client").
        *   After creation, **download the credentials JSON file**. It will be named something like `client_secret_CLIENT_ID.json`.
    *   **Place and Rename Credentials File:**
        *   Rename the downloaded JSON file to `credentials.json`.
        *   Place this `credentials.json` file in the root directory of this project.
    *   **Set Environment Variable:**
        *   Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the *absolute path* of this `credentials.json` file. For example:
            ```bash
            export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/project/root/credentials.json"
            ```
            Ensure this path is correct. The application will load this file to initiate the OAuth flow.

4.  **First-Time OAuth Authorization (User Action Required on First Run):**
    *   When you run the application for the first time and it attempts to access Google Calendar or Google Drive, the Google authentication library will typically:
        1.  Print an authorization URL to your console.
        2.  Automatically try to open this URL in your default web browser.
    *   You will need to:
        1.  Log in with the Google account whose Calendar/Drive you want the agent to access.
        2.  Grant the requested permissions (e.g., "View and manage your calendars", "View your Google Drive files").
        3.  After successful authorization, the browser might show an authorization code (if `urn:ietf:wg:oauth:2.0:oob` was used, less common now) or a success message, and the application (via a local server started by `flow.run_local_server()`) will automatically receive the authorization token.
    *   **Token Storage:** Upon successful authorization, the application will save the OAuth tokens in files named `token_calendar.json` and `token_drive.json` in the project's root directory. These token files will be used for subsequent runs, so you won't need to re-authorize every time, unless the tokens expire or are revoked.

5.  **Security (Reminder):**
    *   **Never commit `credentials.json`, `token_calendar.json`, `token_drive.json`, or your actual API keys into your Git repository.**
    *   Ensure your `.gitignore` file includes entries like:
        ```
        credentials.json
        token_*.json
        *.pyc
        __pycache__/
        venv/
        ```

## Setup and Running

1.  **Clone the repository (if applicable).**

2.  **Create a Python virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    Install the required Python packages using `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```
    The key dependencies are:
    - `Flask`: For the web server.
    - `google-generativeai`: For interacting with the Gemini LLM.
    - `google-api-python-client`, `google-auth-httplib2`, `google-auth-oauthlib`: For interacting with Google Calendar and Google Drive APIs.

4.  **Set Environment Variables:**
    Ensure `GEMINI_API_KEY` and `GOOGLE_APPLICATION_CREDENTIALS` are set as described in the "API Key and Credentials Setup" section.

5.  **Run the Flask application:**
    ```bash
    python app.py
    ```
    The application will typically be available at `http://127.0.0.1:5001` or `http://0.0.0.0:5001`.
    *   **Important - First Run:** Pay close attention to the console output when you first run `app.py`. You will likely be prompted (via a URL printed in the console and/or a browser window opening) to authorize the application to access your Google Calendar and Google Drive data. Complete this OAuth 2.0 flow for each service if prompted.
    *   Subsequent runs should use the saved `token_calendar.json` and `token_drive.json` files automatically.

6.  **Using the Agent:**
    Enter queries into the text box on the web page, such as:
    *   `do I have meetings tomorrow from 6-8?`
    *   `fetch documents I need for my visa application from my drive`
    *   `prepare a presentation for my meeting with John` (uses placeholder tool)
    *   `schedule a meeting with the team for Friday at 3pm about the launch`

## How it Works

1.  The user enters a query in the `index.html` frontend.
2.  JavaScript sends the query to the Flask `app.py` backend (`/process_query`).
3.  `app.py` uses an instance of `ExecutiveAssistantAgent` (from `assistant_agent/agent.py`), initialized with real Google Calendar and Drive tools.
4.  The agent's `run_query` method is invoked:
    *   **LLM Interaction:** It calls `extract_intent_and_params_with_llm` (from `assistant_agent/llm_integration.py`), which sends the query to the Gemini LLM via its API. The LLM returns a structured JSON object containing the perceived `intent` and extracted `parameters`.
    *   **Planning:** The `create_plan` method in the agent uses the LLM's output to generate a sequence of steps, each specifying a tool and action (e.g., `GoogleCalendarTool.find_events`, `GoogleDriveTool.search_files`).
    *   **Execution:** The `execute_plan` method iterates through the plan:
        *   For each step, it calls the `execute` method of the corresponding tool instance (e.g., the real `GoogleCalendarTool` or `GoogleDriveTool` in `assistant_agent/tools.py`).
        *   These tool methods make **actual API calls** to Google Calendar or Google Drive using your authorized credentials.
        *   The PresentationTool is still a placeholder and will simulate its actions.
5.  The results (intent, parameters, plan, and actual execution logs/data from tools) are returned to the frontend and displayed.

## Next Steps & Extensions

This agent provides a solid foundation. Here are areas for improvement and extension:

*   **Real PresentationTool Integration:** Replace the placeholder `PresentationTool` with actual integration with Google Slides API or similar.
*   **Refine Date/Time Parsing:** The LLM's date/time understanding is good, but the tools could have more robust parsing for various date/time formats or relative expressions if the LLM output isn't perfectly standardized. Libraries like `dateutil` could be used in the tools.
*   **Error Handling and Resilience:** Enhance error handling for API calls (e.g., retries, more specific error messages to UI).
*   **User Feedback Loop:** Allow users to correct LLM interpretations or failed tool actions.
*   **State Management & Personalization:** Manage user-specific settings or context across sessions (e.g., preferred calendar, default timezone).
*   **UI Enhancements:** Develop a more interactive UI, perhaps showing progress more dynamically or allowing richer interaction with tool results.
*   **More Tools:** Expand capabilities by adding tools for email (Gmail API), task management (Todoist, Asana), communication (Slack), etc.
*   **Security Hardening:** For any deployment, review security practices for API key management, OAuth token storage, and input validation.
*   **Configuration Management:** Move hardcoded settings (like token file names, default LLM models) to a configuration file or environment variables.

This demo provides a starting point for building a more capable and truly helpful personal executive assistant.
