# assistant_agent/agent.py

class ExecutiveAssistantAgent:
    def __init__(self, llm_service=None, tools=None):
        self.llm_service = llm_service
        self.tools = tools if tools else [] # In a real scenario, these would be instantiated tool objects
        self.task_history = []

    def understand_query(self, query: str) -> str:
        # Placeholder: Simple keyword matching or rule-based logic
        # In a real scenario, this would involve LLM interaction
        print(f"Understanding query: {query}")
        query_lower = query.lower()
        if "meeting" in query_lower or "calendar" in query_lower:
            if "create" in query_lower or "schedule" in query_lower or "book" in query_lower:
                return "create_calendar_event"
            return "check_calendar"
        elif "document" in query_lower or "drive" in query_lower or "file" in query_lower:
            if "find" in query_lower or "search" in query_lower or "fetch" in query_lower:
                return "fetch_document"
            return "manage_document" # Generic document action
        elif "presentation" in query_lower or "slides" in query_lower:
            if "create" in query_lower or "prepare" in query_lower:
                return "prepare_presentation"
            return "manage_presentation" # Generic presentation action
        return "unknown_task"

    def _extract_params_from_query(self, query: str, intent: str) -> str:
        # Very basic parameter extraction, primarily returns the original query for now.
        # This would be a sophisticated NLP task in a real agent.
        # Example: "do I have meetings tomorrow from 6-8?" -> "tomorrow from 6-8" for check_calendar

        query_lower = query.lower()
        params = query # Default to full query

        # Simple keyword removal to get "pseudo-parameters"
        if intent == "check_calendar":
            triggers = ["do i have meetings", "check meetings for", "any meetings", "meetings"]
            for t in triggers:
                if t in query_lower:
                    params = query_lower.split(t, 1)[-1].strip()
                    break
        elif intent == "fetch_document":
            triggers = ["fetch documents", "find documents", "search for documents", "get files named"]
            for t in triggers:
                if t in query_lower:
                    params = query_lower.split(t, 1)[-1].strip().replace("from my drive", "").strip()
                    break
        elif intent == "prepare_presentation":
            triggers = ["prepare a presentation for", "create a presentation about", "make slides for"]
            for t in triggers:
                if t in query_lower:
                    params = query_lower.split(t, 1)[-1].strip()
                    break
        return params if params else query # ensure we don't return empty string

    def create_plan(self, query: str, intent: str) -> list:
        print(f"Creating plan for query: '{query}' with intent: {intent}")
        plan = []

        # Use the new _extract_params_from_query method
        extracted_params = self._extract_params_from_query(query, intent)

        if intent == "check_calendar":
            plan.append({"tool": "GoogleCalendarTool", "action": "find_events", "params": extracted_params, "original_query": query})
        elif intent == "create_calendar_event":
            plan.append({"tool": "GoogleCalendarTool", "action": "create_event", "params": extracted_params, "original_query": query})
        elif intent == "fetch_document":
            plan.append({"tool": "GoogleDriveTool", "action": "search_files", "params": extracted_params, "original_query": query})
        elif intent == "prepare_presentation":
            plan.append({"tool": "PresentationTool", "action": "create_slides", "params": extracted_params, "original_query": query})
        elif intent == "manage_document": # Catch-all for other doc actions
             plan.append({"tool": "GoogleDriveTool", "action": "generic_file_op", "params": extracted_params, "original_query": query})
        elif intent == "manage_presentation": # Catch-all for other pres actions
             plan.append({"tool": "PresentationTool", "action": "generic_presentation_op", "params": extracted_params, "original_query": query})
        else:
            plan.append({"tool": "UnknownTool", "action": "handle_unknown", "params": query, "original_query": query})

        print(f"Generated plan: {plan}")
        return plan

    def execute_plan(self, plan: list) -> dict:
        print(f"Executing plan: {plan}")
        results = {"completed": [], "remaining": [], "outputs": []}

        # In a real agent, you'd instantiate and call methods on tool objects from self.tools
        # For now, we simulate based on tool name and action.
        # from .tools import GoogleCalendarTool, GoogleDriveTool, PresentationTool # Assuming tools.py is in the same package

        for step_idx, step in enumerate(plan):
            tool_name = step.get("tool")
            action = step.get("action")
            params = step.get("params")
            original_query = step.get("original_query", "")

            output_message = f"Step {step_idx+1}: Attempting to use {tool_name} with action '{action}' for parameters '{params}' (from query: '{original_query}')."
            print(output_message)

            tool_output = ""
            step_succeeded = False

            # Simulate calling the placeholder tools from tools.py
            # This part is conceptual. A real agent would have tool instances.
            if tool_name == "GoogleCalendarTool":
                # calendar_tool = GoogleCalendarTool() # Conceptually
                # tool_output = calendar_tool.execute(action=action, params=params) # Conceptually
                tool_output = f"Placeholder: GoogleCalendarTool action '{action}' executed for '{params}'."
                step_succeeded = True
            elif tool_name == "GoogleDriveTool":
                # drive_tool = GoogleDriveTool() # Conceptually
                # tool_output = drive_tool.execute(action=action, params=params) # Conceptually
                tool_output = f"Placeholder: GoogleDriveTool action '{action}' executed for '{params}'."
                step_succeeded = True
            elif tool_name == "PresentationTool":
                # presentation_tool = PresentationTool() # Conceptually
                # tool_output = presentation_tool.execute(action=action, params=params) # Conceptually
                tool_output = f"Placeholder: PresentationTool action '{action}' executed for '{params}'."
                step_succeeded = True
            else:
                tool_output = f"Placeholder: Unknown tool '{tool_name}'. Cannot execute action '{action}' for '{params}'."
                step_succeeded = False

            results["outputs"].append(f"{output_message} Result: {tool_output}")
            if step_succeeded:
                results["completed"].append(step)
            else:
                results["remaining"].append(step)

        self.task_history.append({"plan": plan, "results": results})
        print(f"Execution results: {results}")
        return results

    def run_query(self, query: str) -> dict:
        print(f"\nRunning query: '{query}'")
        intent = self.understand_query(query)
        print(f"Detected intent: {intent}")
        plan = self.create_plan(query, intent)
        execution_results = self.execute_plan(plan)

        response = {
            "query": query,
            "intent": intent,
            "plan": plan,
            "execution_summary": execution_results
        }
        print(f"Final response for query '{query}': {response}")
        return response

if __name__ == '__main__':
    # Example Usage (for testing)
    agent = ExecutiveAssistantAgent()

    queries = [
        "do I have meetings tomorrow from 6-8?",
        "check my calendar for any appointments next Monday",
        "schedule a meeting with marketing team for next Friday at 2 PM about Q3 results",
        "fetch documents I need for my visa application from my drive",
        "find the Q2 sales report in my Google Drive",
        "prepare a presentation for my meeting with John",
        "create slides for the project Alpha update",
        "what's the weather like?", # Unknown
        "book a flight to London" # Unknown,
        # new intent if we expand
    ]

    for q in queries:
        result = agent.run_query(q)
        print(f"--- Query: {q} ---")
        print(f"Intent: {result['intent']}")
        print("Plan:")
        for step in result['plan']:
            print(f"  - Tool: {step['tool']}, Action: {step['action']}, Params: '{step['params']}'")
        print("Execution Outputs:")
        for output_msg in result['execution_summary']['outputs']:
            print(f"  - {output_msg}")
        print("---------------------\n")
