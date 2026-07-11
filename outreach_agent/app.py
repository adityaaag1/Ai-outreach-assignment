import streamlit as st
import pandas as pd
import io
import contextlib
import sqlite3
from datetime import datetime, timezone

from models import Prospect, GapSignal
from agent import run_agent
from tools.draft_tool import draft_outreach
from db import log_run, DB_PATH

st.set_page_config(page_title="B2B Outreach Agent", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
.stApp {
    background-color: #2d2d2d;
    color: #cdcdcd;
}
/* Style buttons */
div.stButton > button:first-child {
    background-color: #106da3;
    color: white;
    border: none;
    border-radius: 5px;
}
div.stButton > button:first-child:hover {
    background-color: #4ab1ff;
    color: white;
}
/* Custom gap card */
.gap-card {
    background-color: #383838;
    border-left: 4px solid #4ab1ff;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 20px;
    color: #cdcdcd;
}
.gap-card h4 {
    color: #4ab1ff;
    margin-top: 0;
}
.gap-snippet {
    font-style: italic;
    color: #a0a0a0;
    border-left: 2px solid #555;
    padding-left: 10px;
}
.gap-reasoning {
    margin-top: 10px;
    color: #cdcdcd;
}
</style>
""", unsafe_allow_html=True)

# Custom output redirection to stream prints into Streamlit UI
class StreamlitRedirect:
    def __init__(self, container):
        self.container = container

    def write(self, data):
        # Prevent empty lines from creating unnecessary spacing
        if data.strip():
            self.container.text(data.strip())
            
    def flush(self):
        pass

def init_session_state():
    if 'queue' not in st.session_state:
        st.session_state.queue = []  # List of Prospect dicts
    if 'current_prospect' not in st.session_state:
        st.session_state.current_prospect = None
    if 'pipeline_state' not in st.session_state:
        st.session_state.pipeline_state = None
    if 'edited_body' not in st.session_state:
        st.session_state.edited_body = ""
        
init_session_state()

def run_pipeline(prospect: Prospect):
    st.session_state.current_prospect = prospect
    
    with st.status("Running Research Pipeline...", expanded=True) as status_box:
        # Redirect stdout to capture prints from research_tool
        redirect_io = StreamlitRedirect(status_box)
        with contextlib.redirect_stdout(redirect_io):
            state = run_agent(prospect)
        status_box.update(label="Pipeline Complete", state="complete", expanded=False)
        
    st.session_state.pipeline_state = state
    st.session_state.edited_body = state.get("draft").body if state.get("draft") else ""

def process_next_in_queue():
    if st.session_state.queue:
        next_p_dict = st.session_state.queue.pop(0)
        p = Prospect(
            name=next_p_dict.get("Name", next_p_dict.get("name", "")),
            title=next_p_dict.get("Title", next_p_dict.get("title", "")),
            company=next_p_dict.get("Company", next_p_dict.get("company", ""))
        )
        run_pipeline(p)
    else:
        st.session_state.current_prospect = None
        st.session_state.pipeline_state = None
        st.success("Batch processing complete!")

st.title("AI B2B Outreach Agent")

# ================= SIDEBAR =================
with st.sidebar:
    st.header("Single Prospect")
    with st.form("single_prospect_form"):
        name = st.text_input("Name")
        title = st.text_input("Title")
        company = st.text_input("Company")
        submitted = st.form_submit_button("Run Research")
        if submitted and name and title and company:
            st.session_state.queue = []
            run_pipeline(Prospect(name=name, title=title, company=company))
            
    st.divider()
    st.header("Batch Process (CSV)")
    uploaded_file = st.file_uploader("Upload CSV (Name, Title, Company)", type=["csv"])
    if uploaded_file is not None:
        if st.button("Start Batch"):
            df = pd.read_csv(uploaded_file)
            st.session_state.queue = df.to_dict('records')
            process_next_in_queue()

# ================= MAIN AREA =================
if st.session_state.current_prospect and st.session_state.pipeline_state:
    prospect = st.session_state.current_prospect
    state = st.session_state.pipeline_state
    status = state.get("status")
    gaps = state.get("gaps", [])
    chosen_gap = state.get("chosen_gap")
    draft = state.get("draft")
    
    st.header(f"Results for: {prospect.name} at {prospect.company}")
    
    # 1. Handle Insufficient Signal
    if not gaps or status == "insufficient_signal":
        st.warning(f"**Insufficient signal found for {prospect.name}.** Skipping draft.", icon="⚠️")
        if gaps:
            st.write(f"Found {len(gaps)} signals, but all confidence scores were too low (< 0.5).")
            for g in gaps:
                with st.expander(f"Confidence: {g.confidence} - {g.source_query}"):
                    st.write(f"**Snippet:** {g.source_snippet}")
                    st.write(f"**Reasoning:** {g.reasoning}")
        else:
            st.write("No evidence-backed gaps could be found.")
            
        # Review control for skip
        skip_reason = st.text_input("Reason for skipping", value="Insufficient signal")
        if st.button("Log Skip & Continue"):
            log_run(prospect, datetime.now(timezone.utc).isoformat(), gaps, chosen_gap, None, "insufficient_signal", skip_reason)
            process_next_in_queue()
            st.rerun()
            
    # 2. Handle Success
    elif status == "success" and draft and chosen_gap:
        st.subheader("Selected Gap")
        
        # Improved Data Visualization with custom HTML Card
        st.markdown(f"""
        <div class="gap-card">
            <h4>Signal Confidence: {chosen_gap.confidence}</h4>
            <p><strong>Query used:</strong> {chosen_gap.source_query}</p>
            <p><strong>Evidence Found:</strong></p>
            <div class="gap-snippet">"{chosen_gap.source_snippet}"</div>
            <div class="gap-reasoning">
                <strong>Why it was chosen:</strong> {chosen_gap.reasoning} <br><br>
                <a href="{chosen_gap.source_url}" target="_blank" style="color:#4ab1ff;">View Source Document</a>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("Generated Draft")
        st.write(f"**Subject:** {draft.subject}")
        # Editable text area for the body
        edited_body = st.text_area("Body", value=st.session_state.edited_body, height=200)
        
        st.subheader("Review Controls")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("Approve", type="primary"):
                log_run(prospect, datetime.now(timezone.utc).isoformat(), gaps, chosen_gap, draft, "Approve", draft.body)
                st.success("Approved!")
                process_next_in_queue()
                st.rerun()
                
        with col2:
            if st.button("Save Edit"):
                log_run(prospect, datetime.now(timezone.utc).isoformat(), gaps, chosen_gap, draft, "Edit", edited_body)
                st.success("Edit Saved!")
                process_next_in_queue()
                st.rerun()
                
        with col3:
            if st.button("Regenerate (Next Gap)"):
                # Find the next gap in the sorted gaps list
                current_idx = gaps.index(chosen_gap) if chosen_gap in gaps else -1
                next_idx = current_idx + 1
                if next_idx < len(gaps):
                    new_gap = gaps[next_idx]
                    new_draft = draft_outreach(prospect, new_gap)
                    
                    st.session_state.pipeline_state["chosen_gap"] = new_gap
                    st.session_state.pipeline_state["draft"] = new_draft
                    st.session_state.edited_body = new_draft.body
                    st.rerun()
                else:
                    st.error("No more gaps available to regenerate.")
                    
        with col4:
            with st.popover("Skip"):
                skip_reason = st.text_input("Skip Reason")
                if st.button("Confirm Skip"):
                    log_run(prospect, datetime.now(timezone.utc).isoformat(), gaps, chosen_gap, draft, "Skip", skip_reason)
                    process_next_in_queue()
                    st.rerun()

# ================= SESSION LOG =================
st.divider()
st.subheader("Session Log")
try:
    conn = sqlite3.connect(DB_PATH)
    df_logs = pd.read_sql_query("SELECT timestamp, prospect_name, company, human_decision, final_draft_text FROM runs ORDER BY timestamp DESC LIMIT 20", conn)
    conn.close()
    if not df_logs.empty:
        st.dataframe(df_logs, use_container_width=True)
    else:
        st.write("No logs found.")
except Exception as e:
    st.write("Could not load logs:", e)
