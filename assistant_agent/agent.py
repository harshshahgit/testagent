# assistant_agent/agent.py
import os # For environment variable checks in main block
from .llm_integration import extract_intent_and_params_with_llm, model as gemini_model # Import model for check
from .tools import GoogleCalendarTool, GoogleDriveTool, PresentationTool

class ExecutiveAssistantAgent:
    def __init__(self, calendar_tool=None, drive_tool=None, presentation_tool=None):
        self.calendar_tool = calendar_tool if calendar_tool else GoogleCalendarTool()
        self.drive_tool = drive_tool if drive_tool else GoogleDriveTool()
        self.presentation_tool = presentation_tool if presentation_tool else PresentationTool()

        # This map helps route intents to the correct tool instance's execute method.
        # Note: The execute_plan method currently uses if/elif for tool_name.
        # A direct map to tool instances could also be used if tool_name from plan matches these keys.
        # For now, the existing if/elif in execute_plan is fine.
        self.task_history = []

    def create_plan(self, llm_intent_data: dict) -> list:
        intent = llm_intent_data.get("intent", "unknown_task")
        parameters = llm_intent_data.get("parameters", {})
        original_query = llm_intent_data.get("raw_query", "")

        # print(f"Creating plan for intent: '{intent}' with parameters: {parameters} (from query: '{original_query}')")
        plan = []

        if intent == "check_calendar":
            plan.append({"tool_name": "GoogleCalendarTool", "action": "find_events", "params": parameters, "original_query": original_query})
        elif intent == "create_calendar_event":
            plan.append({"tool_name": "GoogleCalendarTool", "action": "create_event", "params": parameters, "original_query": original_query})
        elif intent == "search_drive_files":
            plan.append({"tool_name": "GoogleDriveTool", "action": "search_files", "params": parameters, "original_query": original_query})
        elif intent == "prepare_presentation": # Still uses placeholder
            plan.append({"tool_name": "PresentationTool", "action": "create_slides", "params": parameters, "original_query": original_query})
        else:
            error_message = llm_intent_data.get("llm_response", original_query)
            plan.append({"tool_name": "UnknownTool", "action": "handle_unknown", "params": {"error_info": error_message}, "original_query": original_query})

        # print(f"Generated plan: {plan}")
        return plan

    def execute_plan(self, plan: list) -> dict:
        # print(f"Executing plan: {plan}")
        results = {"completed": [], "remaining": [], "outputs": []}

        for step_idx, step in enumerate(plan):
            tool_name = step.get("tool_name")
            action = step.get("action")
            params = step.get("params", {})

            tool_to_use = None
            if tool_name == "GoogleCalendarTool":
                tool_to_use = self.calendar_tool
            elif tool_name == "GoogleDriveTool":
                tool_to_use = self.drive_tool
            elif tool_name == "PresentationTool":
                tool_to_use = self.presentation_tool

            output_message = f"Step {step_idx+1}: Tool '{tool_name}', Action '{action}', Params: {params}."
            # print(output_message) # Verbose logging

            tool_output = ""
            step_succeeded = False

            if tool_to_use and hasattr(tool_to_use, 'execute'):
                try:
                    tool_output = tool_to_use.execute(action=action, params=params)
                    step_succeeded = True
                    # For real tools, success might also depend on the content of tool_output
                    # (e.g., not containing "Error:")
                    if isinstance(tool_output, str) and tool_output.startswith("Error:"):
                        step_succeeded = False
                except Exception as e:
                    import traceback
                    print(f"ERROR (Agent.execute_plan): Tool execution failed: {e}\n{traceback.format_exc()}")
                    tool_output = f"Error executing {tool_name}.{action}: {e}"
                    step_succeeded = False
            elif tool_name == "UnknownTool":
                tool_output = f"Cannot execute. Reason: {params.get('error_info', 'Unknown error')}"
                step_succeeded = False
            else:
                tool_output = f"Tool '{tool_name}' not found or not configured correctly."
                step_succeeded = False

            results["outputs"].append(f"{output_message} Result: {tool_output}")
            if step_succeeded:
                results["completed"].append(step)
            else:
                results["remaining"].append(step)

        self.task_history.append({"plan": plan, "results": results})
        # print(f"Execution results: {results}")
        return results

    def run_query(self, query: str) -> dict:
        print(f"\nAGENT: Processing query with LLM: '{query}'")

        llm_intent_data = extract_intent_and_params_with_llm(query)

        if not llm_intent_data or llm_intent_data.get("intent", "").startswith("error_"):
            print(f"AGENT ERROR: LLM processing failed. Intent data: {llm_intent_data}")
            error_response = {
                "query": query,
                "intent": llm_intent_data.get("intent", "error_unknown_llm_failure"),
                "parameters": llm_intent_data.get("parameters", {}),
                "plan": [],
                "execution_summary": {
                    "completed": [],
                    "remaining": [{"tool_name": "LLMProcessing", "action": "understand_query", "params": {"error": llm_intent_data}}],
                    "outputs": [f"Failed to understand query via LLM. Details: {llm_intent_data.get('llm_response', 'No LLM output.')}"]
                },
                "llm_raw_output": llm_intent_data.get("llm_response")
            }
            return error_response

        # print(f"AGENT: LLM Intent Data: {llm_intent_data}")
        intent = llm_intent_data.get("intent")

        plan = self.create_plan(llm_intent_data)
        execution_results = self.execute_plan(plan)

        response = {
            "query": query,
            "intent": intent,
            "parameters": llm_intent_data.get("parameters"),
            "plan": plan,
            "execution_summary": execution_results,
            "llm_raw_output": llm_intent_data.get("llm_response") # For debugging frontend
        }
        # print(f"AGENT: Final response for query '{query}': {response}")
        return response

if __name__ == '__main__':
    print("--- Running ExecutiveAssistantAgent Tests (agent.py) ---")

    # Check if LLM is available (basic check based on llm_integration.py's model variable)
    if not gemini_model:
        print("WARNING (Agent Test): Gemini model not initialized in llm_integration.py. LLM calls will fail.")
        print("Ensure GEMINI_API_KEY is set. Skipping agent tests that rely on LLM.")
    elif not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        print("WARNING (Agent Test): GOOGLE_APPLICATION_CREDENTIALS not set.")
        print("Real tool execution (Calendar, Drive) will fail OAuth or service instantiation.")
        print("Skipping agent tests that rely on Google Cloud services.")
    else:
        print("Info (Agent Test): GEMINI_API_KEY and GOOGLE_APPLICATION_CREDENTIALS seem to be available.")
        print("Attempting to instantiate real tools for testing...")

        try:
            # Instantiate real tools
            # These will attempt OAuth flow if token_*.json is not present or invalid.
            # This requires user interaction in the console if run for the first time.
            print("Instantiating GoogleCalendarTool...")
            calendar_tool_instance = GoogleCalendarTool()
            print("Instantiating GoogleDriveTool...")
            drive_tool_instance = GoogleDriveTool()
            # Presentation tool is still a placeholder
            presentation_tool_instance = PresentationTool()

            agent = ExecutiveAssistantAgent(
                calendar_tool=calendar_tool_instance,
                drive_tool=drive_tool_instance,
                presentation_tool=presentation_tool_instance
            )

            queries = [
                "do I have any meetings today?",
                "schedule a meeting with the marketing team for next Friday at 2 PM about Q4 planning",
                "find my document named 'project_proposal.pdf' in Google Drive",
                "search for spreadsheets about sales figures from last quarter",
                "prepare a presentation for the client update next week" # Uses placeholder
            ]

            for q_idx, q in enumerate(queries):
                print(f"\n--- Test Query {q_idx+1}/{len(queries)}: {q} ---")
                result = agent.run_query(q)
                print(f"AGENT TEST - Intent: {result.get('intent')}")
                print(f"AGENT TEST - Parameters: {result.get('parameters')}")
                print("AGENT TEST - Plan:")
                if result.get('plan'):
                    for step in result['plan']:
                        print(f"  - Tool: {step.get('tool_name')}, Action: {step.get('action')}, Params: {step.get('params')}")
                else:
                    print("  - No plan generated.")
                print("AGENT TEST - Execution Outputs:")
                if result.get('execution_summary') and result['execution_summary'].get('outputs'):
                    for output_msg in result['execution_summary']['outputs']:
                        print(f"  - {output_msg}")
                else:
                    print("  - No execution outputs.")
                print("-----------------------------")

        except Exception as e:
            import traceback
            print(f"ERROR (Agent Test): An error occurred during agent testing with real tools: {e}\n{traceback.format_exc()}")
            print("This might be due to OAuth issues, API errors, or problems with tool instantiation.")
