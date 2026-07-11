import sys
from datetime import datetime, timezone
from models import Prospect
from agent import run_agent
from db import log_run
from tools.draft_tool import draft_outreach

def display_gap(gap, index=None):
    prefix = f"[{index}] " if index is not None else ""
    print(f"\n{prefix}Type: {gap.signal_type.value.upper()} (Confidence: {gap.confidence})")
    print(f"Source: {gap.source_url}")
    print(f"Query: {gap.source_query}")
    print(f"Evidence: \"{gap.source_snippet}\"")
    print(f"Gap: {gap.description}")
    print(f"Reasoning: {gap.reasoning}")

def main():
    print("=== AI B2B Outreach Research Agent ===")
    name = input("Prospect Name: ").strip()
    title = input("Prospect Title: ").strip()
    company = input("Prospect Company: ").strip()
    
    if not (name and title and company):
        print("Name, Title, and Company are required.")
        sys.exit(1)
        
    prospect = Prospect(name=name, title=title, company=company)
    
    print("\n[+] Starting agent run...")
    state = run_agent(prospect)
    
    gaps = state.get("gaps", [])
    
    if not gaps:
        print("\n[-] Agent could not find any evidence-backed gaps.")
        reason = input("Enter skip reason (or press enter for 'No gaps found'): ").strip()
        reason = reason or "No gaps found"
        log_run(prospect, datetime.utcnow().isoformat(), [], None, None, "Skip", reason)
        return
        
    print(f"\n[+] Agent found {len(gaps)} potential gap signals.")
    for i, g in enumerate(gaps):
        display_gap(g, i)
        
    status = state.get("status")
    chosen_gap = state.get("chosen_gap")
    draft = state.get("draft")
    
    if status == "insufficient_signal":
        print(f"\n[!] Insufficient signal found for {prospect.name} — skipping draft.")
        print(f"Found signals: {[g.confidence for g in gaps]}")
        log_run(prospect, datetime.utcnow().isoformat(), gaps, chosen_gap, None, "insufficient_signal", None)
        return
        
    elif status == "success" and draft:
        print("\n=== CHOSEN GAP ===")
        display_gap(chosen_gap)
        
        print("\n=== GENERATED DRAFT ===")
        print(f"Subject: {draft.subject}")
        print(f"Body:\n{draft.body}\n")
    
    while True:
        print("\nOptions:")
        print("[A]pprove draft")
        print("[E]dit draft")
        print("[R]egenerate with a different gap")
        print("[S]kip")
        choice = input("Decision [A/E/R/S]: ").strip().upper()
        
        if choice == 'A':
            if not draft:
                print("No draft to approve.")
                continue
            log_run(prospect, datetime.utcnow().isoformat(), gaps, chosen_gap, draft, "Approve", draft.body)
            print("[+] Draft approved and saved to database.")
            break
            
        elif choice == 'E':
            if not draft:
                print("No draft to edit.")
                continue
            print("\nEnter edited body (press Ctrl+D on empty line to finish, or paste single-line if simple):")
            # For simplicity in CLI POC, we'll just read one line or multiple lines if needed.
            # Using a simple input for POC:
            edited_body = input("Edited body: ").strip()
            if edited_body:
                log_run(prospect, datetime.now(timezone.utc).isoformat(), gaps, chosen_gap, draft, "Edit", edited_body)
                print("[+] Edited draft saved to database.")
            else:
                print("[-] Edit cancelled.")
            break
            
        elif choice == 'R':
            try:
                gap_idx = int(input(f"Enter the index of the gap to use (0 to {len(gaps)-1}): ").strip())
                if 0 <= gap_idx < len(gaps):
                    new_gap = gaps[gap_idx]
                    print("\n[+] Regenerating draft with new gap...")
                    draft = draft_outreach(prospect, new_gap)
                    chosen_gap = new_gap
                    print("\n=== GENERATED DRAFT ===")
                    print(f"Subject: {draft.subject}")
                    print(f"Body:\n{draft.body}\n")
                else:
                    print("Invalid index.")
            except ValueError:
                print("Please enter a valid number.")
                
        elif choice == 'S':
            reason = input("Enter skip reason: ").strip()
            log_run(prospect, datetime.utcnow().isoformat(), gaps, chosen_gap, draft, "Skip", reason)
            print("[+] Run logged as skipped.")
            break
            
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
