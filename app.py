# app.py
from flask import Flask, render_template, request, jsonify
import sys
import os
import logging # For better logging

# Add assistant_agent to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '.')) # Access assistant_agent package

from assistant_agent.agent import ExecutiveAssistantAgent
from assistant_agent.tools import GoogleCalendarTool, GoogleDriveTool, PresentationTool

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Environment Variable Checks ---
if not os.environ.get('GEMINI_API_KEY'):
    logger.warning("GEMINI_API_KEY environment variable is not set. LLM functionality will likely fail.")
if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
    logger.warning("GOOGLE_APPLICATION_CREDENTIALS environment variable is not set. Google Calendar/Drive tools will likely fail during OAuth or service instantiation.")

app = Flask(__name__)

# --- Initialize Tools and Agent ---
# Global instantiation. For production, consider factory patterns or app context for tools/agent
# if they have per-request state or complex setup. For this demo, global is simpler.
assistant = None
try:
    logger.info("Initializing tools...")
    calendar_tool_instance = GoogleCalendarTool()
    drive_tool_instance = GoogleDriveTool()
    presentation_tool_instance = PresentationTool() # Still a placeholder
    logger.info("Tools initialized (or attempted).")

    logger.info("Initializing ExecutiveAssistantAgent with real tools...")
    assistant = ExecutiveAssistantAgent(
        calendar_tool=calendar_tool_instance,
        drive_tool=drive_tool_instance,
        presentation_tool=presentation_tool_instance
    )
    logger.info("ExecutiveAssistantAgent initialized.")

except ValueError as ve:
    logger.critical(f"CRITICAL ERROR during initialization (likely missing GOOGLE_APPLICATION_CREDENTIALS): {ve}")
    logger.critical("The application's Google Cloud dependent tools will not function. Please check environment variable setup.")
    # assistant remains None or you could set up a fallback dummy agent
except FileNotFoundError as fnfe:
    logger.critical(f"CRITICAL ERROR: Credentials file not found during tool initialization: {fnfe}")
    logger.critical("Ensure GOOGLE_APPLICATION_CREDENTIALS points to a valid file.")
except Exception as e:
    import traceback
    logger.critical(f"CRITICAL ERROR during tool/agent initialization: {e}\n{traceback.format_exc()}")
    # assistant remains None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_query', methods=['POST'])
def process_query():
    if assistant is None:
        logger.error("Attempted to process query, but agent is not initialized due to earlier critical errors.")
        return jsonify({"error": "Agent not initialized due to server-side configuration issues. Please check server logs."}), 500

    try:
        data = request.get_json()
        query = data.get('query')

        if not query:
            logger.warning("Process_query called with no query.")
            return jsonify({"error": "No query provided"}), 400

        logger.info(f"Processing query: '{query}'")
        result = assistant.run_query(query) # Agent processes the query

        # Log the summary of the result for backend visibility
        # logger.info(f"Agent Result for query '{query}': Intent='{result.get('intent')}', Plan Steps={len(result.get('plan', []))}")

        return jsonify(result)

    except Exception as e:
        import traceback
        logger.error(f"Error processing query '{query}': {e}\n{traceback.format_exc()}")
        return jsonify({"error": "An unexpected error occurred on the server."}), 500

if __name__ == '__main__':
    # Note: Flask's default run is single-threaded. For OAuth flows that might block
    # or for handling multiple users, a production server (gunicorn, uWSGI) would be needed.
    logger.info("Starting Flask application...")
    app.run(debug=False, host='0.0.0.0', port=5001) # debug=False for cleaner logs in this stage
