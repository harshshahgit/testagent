# assistant_agent/llm_integration.py
import google.generativeai as genai
import os
import json

# Configure the Gemini API key
try:
    GEMINI_API_KEY = os.environ['GEMINI_API_KEY']
    genai.configure(api_key=GEMINI_API_KEY)
    # Initialize the generative model
    # Using gemini-1.5-flash as it's fast and capable for chat/instruction following
    model = genai.GenerativeModel('gemini-1.5-flash')
except KeyError:
    print("ERROR: GEMINI_API_KEY environment variable not set.")
    model = None
except Exception as e:
    print(f"ERROR: Could not configure Gemini API: {e}")
    model = None

def generate_text_with_gemini(prompt: str) -> str | None:
    """
    Generates text using the configured Gemini model.

    Args:
        prompt (str): The prompt to send to the LLM.

    Returns:
        str | None: The LLM's response text, or None if an error occurs or model is not available.
    """
    if not model:
        print("ERROR: Gemini model not initialized. Cannot generate text.")
        return None
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"ERROR: Gemini API call failed: {e}")
        return None

def extract_intent_and_params_with_llm(query: str) -> dict | None:
    """
    Uses Gemini to extract intent and parameters from a user query.
    The LLM is prompted to return a JSON string with 'intent' and 'parameters'.
    """
    if not model:
        return {"intent": "error_model_not_initialized", "parameters": {}, "raw_query": query}

    # More sophisticated prompt engineering might be needed for complex scenarios.
    # This prompt tries to guide the LLM to produce a JSON output.
    prompt = f"""
Analyze the following user query and extract the primary intent and any relevant parameters.
The intent should be one of:
- "check_calendar" (for querying events)
- "create_calendar_event" (for scheduling new events)
- "search_drive_files" (for finding documents)
- "prepare_presentation" (for creating presentations - less focus for now, more complex)
- "unknown_task" (if the query doesn't match known intents)

Parameters should be a dictionary. For calendar events, common parameters are "event_summary", "date_time" (try to interpret relative dates like 'tomorrow', 'next Friday at 2 PM'), "duration", "location", "attendees". For drive search, "file_name" or "query_terms".

Return the result as a JSON object with two keys: "intent" and "parameters".
If parameters are not clearly extractable, provide an empty dictionary or best guess for parameters.

User Query: "{query}"

JSON Output:
"""

    print(f"--- Sending prompt to Gemini for intent/param extraction ---")
    # print(f"Prompt: {prompt}") # Uncomment for debugging prompts

    raw_llm_response = generate_text_with_gemini(prompt)

    if not raw_llm_response:
        print("ERROR: No response from LLM for intent extraction.")
        return {"intent": "error_llm_no_response", "parameters": {}, "raw_query": query}

    print(f"LLM Raw Response (Intent/Params): {raw_llm_response}")

    try:
        # The response might be plain JSON or JSON within backticks (```json ... ```)
        if raw_llm_response.strip().startswith("```json"):
            json_str = raw_llm_response.strip().split("```json")[1].split("```")[0].strip()
        elif raw_llm_response.strip().startswith("{") and raw_llm_response.strip().endswith("}"):
            json_str = raw_llm_response.strip()
        else:
            # Fallback if LLM doesn't produce clean JSON - try to parse it loosely
            # This is a simplistic fallback. Better error handling/parsing is needed for robustness.
            print(f"Warning: LLM response was not clean JSON. Attempting to parse: {raw_llm_response}")
            # A more robust solution would try to find a JSON block or re-prompt.
            # For now, if it's not obvious JSON, we'll treat it as an unknown task or error.
            # Let's try a very naive parse attempt if it looks like it might contain JSON.
            if '{' in raw_llm_response and '}' in raw_llm_response:
                start_index = raw_llm_response.find('{')
                end_index = raw_llm_response.rfind('}')
                if start_index != -1 and end_index != -1 and end_index > start_index:
                    json_str = raw_llm_response[start_index:end_index+1]
                else: # Could not find valid JSON block
                    raise json.JSONDecodeError("Could not find valid JSON block in LLM response", raw_llm_response, 0)
            else: # No JSON structure detected
                 raise json.JSONDecodeError("No JSON structure detected in LLM response", raw_llm_response, 0)


        parsed_response = json.loads(json_str)

        # Basic validation of the parsed structure
        if not isinstance(parsed_response, dict) or "intent" not in parsed_response or "parameters" not in parsed_response:
            print(f"ERROR: LLM response JSON does not have expected structure: {parsed_response}")
            return {"intent": "error_llm_bad_format", "parameters": {}, "raw_query": query, "llm_response": raw_llm_response}

        parsed_response["raw_query"] = query # Add original query for context
        parsed_response["llm_response"] = raw_llm_response # Add raw response for debugging
        return parsed_response

    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse LLM JSON response for intent: {e}. Raw response: {raw_llm_response}")
        return {"intent": "error_llm_json_decode", "parameters": {}, "raw_query": query, "llm_response": raw_llm_response}
    except Exception as e:
        print(f"ERROR: An unexpected error occurred during LLM response processing: {e}")
        return {"intent": "error_processing_llm_response", "parameters": {}, "raw_query": query, "llm_response": raw_llm_response}

if __name__ == '__main__':
    # Test the functions (requires GEMINI_API_KEY to be set)
    if not model:
        print("Skipping llm_integration.py tests as Gemini model is not initialized (GEMINI_API_KEY likely not set).")
    else:
        print("\n--- Testing LLM Integration ---")

        test_queries = [
            "do I have meetings tomorrow from 6-8?",
            "schedule a meeting with John for next Monday at 10am about the project update",
            "fetch the Q3 financial report from my drive",
            "prepare a presentation on Q4 marketing strategy",
            "what is the capital of France?" # Should be unknown_task
        ]

        for t_query in test_queries:
            print(f"\nTesting query: '{t_query}'")
            intent_data = extract_intent_and_params_with_llm(t_query)
            if intent_data:
                print(f"Intent: {intent_data.get('intent')}")
                print(f"Parameters: {intent_data.get('parameters')}")
                # print(f"LLM Raw: {intent_data.get('llm_response')}") # For debugging
            else:
                print("Failed to get intent data from LLM.")
            print("--------------------")
