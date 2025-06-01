# Personal Executive Assistant Agent (Demo)

This project is a demonstration of a personal executive assistant agent. It can understand simple natural language queries related to calendar management, document retrieval, and presentation preparation. It then plans and (simulates) executing these tasks.

**Note:** This is a simplified version. It uses placeholder functions for actual interactions with services like Google Calendar, Google Drive, or presentation software. Full integration with these services (including OAuth 2.0 authentication and specific API calls) is a major next step.

## Features (Simulated)

*   **Query Understanding:** Interprets user queries to determine intent (e.g., check calendar, fetch document).
*   **Planning:** Creates a basic sequence of actions to fulfill the query.
*   **Execution (Simulated):** Simulates calling tools for Google Calendar, Google Drive, and Presentations.
*   **Web Interface:** A simple web UI to enter queries and view the agent's process and results.

## Project Structure

```
.
├── assistant_agent/        # Core Python code for the agent
│   ├── __init__.py
│   ├── agent.py            # Main ExecutiveAssistantAgent class
│   ├── llm_integration.py  # Placeholders for LLM interactions
│   └── tools.py            # Placeholder tool definitions
├── static/                 # For CSS/JS (if any more advanced UI is built)
│   └── .gitkeep
├── templates/              # HTML templates for Flask
│   └── index.html
├── app.py                  # Flask web server
└── README.md               # This file
```

## Setup and Running

1.  **Clone the repository (if applicable).**

2.  **Create a Python virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    This project uses Flask.
    ```bash
    pip install Flask
    ```

4.  **Run the Flask application:**
    ```bash
    python app.py
    ```
    The application will typically be available at `http://127.0.0.1:5001` or `http://0.0.0.0:5001`. Open this URL in your web browser.

5.  **Using the Agent:**
    Enter queries into the text box on the web page, such as:
    *   `do I have meetings tomorrow from 6-8?`
    *   `fetch documents I need for my visa application from my drive`
    *   `prepare a presentation for my meeting with John`
    *   `schedule a meeting with the team for Friday at 3pm about the launch`

## How it Works (Current Implementation)

1.  The user enters a query in the `index.html` frontend.
2.  JavaScript sends the query to the Flask `app.py` backend (`/process_query`).
3.  `app.py` initializes `ExecutiveAssistantAgent` from `assistant_agent/agent.py`.
4.  The agent's `run_query` method is called:
    *   `understand_query`: Uses simple keyword matching to determine intent (e.g., "check\_calendar", "fetch\_document").
    *   `_extract_params_from_query`: Attempts to pull out key details from the query.
    *   `create_plan`: Generates a list of steps, specifying which (placeholder) tool and action to use.
    *   `execute_plan`: Iterates through the plan. For each step, it prints what it *would* do and calls a placeholder function from `assistant_agent/tools.py`. No actual external services are contacted.
5.  The results (intent, plan, simulated execution log) are returned to the frontend and displayed.

## Next Steps & Extensions

This agent is a foundational example. Here are key areas for improvement and extension:

1.  **Real Tool Integration:**
    *   **Google Calendar:**
        *   Implement OAuth 2.0 for user authentication.
        *   Use the Google Calendar API to list events, create events, etc. Replace the `GoogleCalendarTool` placeholder in `tools.py`.
    *   **Google Drive:**
        *   Implement OAuth 2.0.
        *   Use the Google Drive API to search for files, download files, etc. Replace the `GoogleDriveTool` placeholder.
    *   **Presentation Software:**
        *   Integrate with Google Slides API or other presentation tools (e.g., Microsoft PowerPoint via MS Graph API). Replace the `PresentationTool` placeholder.

2.  **Advanced LLM Integration:**
    *   Replace the rule-based `understand_query` and `create_plan` methods in `agent.py` with calls to a powerful LLM (e.g., via `llm_integration.py`).
    *   Use the prompts defined conceptually (see `Define Initial Prompts` step in development plan) to guide the LLM.
    *   This would involve:
        *   Setting up API keys for an LLM service (OpenAI, Google Gemini, etc.).
        *   Using libraries like `openai` or `google-generativeai`.
        *   More sophisticated prompt engineering for robust intent recognition, slot filling (parameter extraction), and multi-step planning.

3.  **Error Handling and Resilience:**
    *   Improve error handling for API calls.
    *   Add retries or fallback mechanisms.

4.  **State Management:**
    *   For a more personalized experience, manage user-specific settings or context across sessions.

5.  **User Interface (UI) Enhancements:**
    *   Develop a more interactive and richer UI.
    *   Show task progress more dynamically.

6.  **More Tools:**
    *   Add tools for email (Gmail API), task management (Todoist, Asana), communication (Slack), etc.

7.  **Security:**
    *   Properly manage API keys and user credentials (e.g., using environment variables, secure vaults).
    *   Be mindful of data privacy when accessing user data.

This demo provides a starting point for building a more capable and truly helpful personal executive assistant.
