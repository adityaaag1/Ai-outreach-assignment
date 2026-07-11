import subprocess
import os
import sys

def test_cli(name, title, company):
    print(f"\n======================================")
    print(f"Testing CLI for {name}, {title} at {company}")
    print(f"======================================")
    
    # We will pass inputs: Name, Title, Company, then 'S' to skip if it reaches the prompt.
    # If it exits on insufficient signal, the extra 'S\n' will just be ignored.
    inputs = f"{name}\n{title}\n{company}\nS\nTest skip\n"
    
    process = subprocess.Popen(
        [sys.executable, 'main.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=os.path.join(os.path.dirname(__file__), 'outreach_agent')
    )
    
    out, _ = process.communicate(input=inputs)
    print(out)

if __name__ == "__main__":
    # Test case 1: Large company
    test_cli("John Smith", "VP of Engineering", "GitLab")
    
    # Test case 2: Small/early-stage company with little presence
    test_cli("Alice Jones", "CTO", "ObscureStartup123xyz")
