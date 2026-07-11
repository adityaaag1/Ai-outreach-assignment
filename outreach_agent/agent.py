from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig

from models import Prospect, GapSignal, Draft
from tools.research_tool import research_prospect
from tools.draft_tool import draft_outreach

class AgentState(TypedDict):
    prospect: Prospect
    gaps: List[GapSignal]
    chosen_gap: Optional[GapSignal]
    draft: Optional[Draft]
    status: str

def research_node(state: AgentState) -> AgentState:
    """Runs the research tool."""
    print(f"Agent: Researching {state['prospect'].company}...")
    gaps = research_prospect(state["prospect"].company, state["prospect"].title)
    return {"gaps": gaps}

def evaluate_node(state: AgentState) -> AgentState:
    """Evaluates the gaps found."""
    gaps = state.get("gaps", [])
    if not gaps:
        return {"status": "insufficient_signal", "chosen_gap": None}
    
    # Gaps are already sorted by confidence descending in the tool,
    # but we can do a final check. We want a strong signal.
    # Let's say confidence must be >= 0.5
    best_gap = gaps[0]
    if best_gap.confidence < 0.5:
        return {"status": "insufficient_signal", "chosen_gap": best_gap}
        
    return {"status": "ready_to_draft", "chosen_gap": best_gap}

def draft_node(state: AgentState) -> AgentState:
    """Drafts the message."""
    print(f"Agent: Drafting message based on top gap...")
    chosen_gap = state["chosen_gap"]
    draft = draft_outreach(state["prospect"], chosen_gap)
    return {"draft": draft, "status": "success"}

def route_after_evaluation(state: AgentState) -> str:
    if state["status"] == "ready_to_draft":
        return "draft"
    return END

# Build the graph
workflow = StateGraph(AgentState)

workflow.add_node("research", research_node)
workflow.add_node("evaluate", evaluate_node)
workflow.add_node("draft", draft_node)

workflow.set_entry_point("research")
workflow.add_edge("research", "evaluate")
workflow.add_conditional_edges(
    "evaluate",
    route_after_evaluation,
    {
        "draft": "draft",
        END: END
    }
)
workflow.add_edge("draft", END)

agent_app = workflow.compile()

def run_agent(prospect: Prospect) -> AgentState:
    """Helper to run the agent synchronously."""
    initial_state = {
        "prospect": prospect,
        "gaps": [],
        "chosen_gap": None,
        "draft": None,
        "status": "started"
    }
    
    final_state = agent_app.invoke(initial_state)
    return final_state

if __name__ == "__main__":
    from models import Prospect
    test_prospect = Prospect(
        name="John Smith",
        company="GitLab",
        title="VP of Sales"
    )
    print("Testing agent...")
    res = run_agent(test_prospect)
    print("Status:", res["status"])
    if res["chosen_gap"]:
        print("Gap chosen:", res["chosen_gap"].description)
    if res["draft"]:
        print("Draft subject:", res["draft"].subject)
