# app.py
from flask import Flask, render_template, request, jsonify
import sys
import os

# Add assistant_agent to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'assistant_agent'))

from agent import ExecutiveAssistantAgent
# Placeholder for actual tools, will be refined later
# from tools import get_tools

app = Flask(__name__)

# Initialize the agent
# In a real app, you might manage agent instances differently (e.g., per user session)
# For now, we are not passing any specific llm_service or tools,
# as the agent uses its internal placeholders.
assistant = ExecutiveAssistantAgent()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_query', methods=['POST'])
def process_query():
    try:
        data = request.get_json()
        query = data.get('query')

        if not query:
            return jsonify({"error": "No query provided"}), 400

        # Agent processes the query
        # The current agent.run_query() returns a dictionary with plan, results, etc.
        result = assistant.run_query(query)

        # The result from agent.run_query is already a dictionary
        # and can be directly returned as JSON.
        # It includes 'query', 'intent', 'plan', and 'execution_summary'.
        # The 'execution_summary' contains 'completed', 'remaining', and 'outputs'.
        return jsonify(result)

    except Exception as e:
        app.logger.error(f"Error processing query: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
