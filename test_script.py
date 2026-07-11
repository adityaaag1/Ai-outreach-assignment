import os
import sys
from pathlib import Path

# Setup paths
sys.path.append(str(Path(__file__).parent / "outreach_agent"))

from outreach_agent.models import Prospect, GapSignal
from outreach_agent.tools.research_tool import research_prospect, fetch_url_content, ExtractedGaps
from outreach_agent.tools.draft_tool import draft_outreach
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from outreach_agent.config import GROQ_MODEL_NAME

MOCK_BLOG_HTML = """
<html>
<body>
<h1>Acme Corp Q3 Engineering Retrospective</h1>
<p>
Our transition to microservices has resulted in severe deployment bottlenecks, pushing our Q3 feature release back by four weeks. 
The CI/CD pipeline fails roughly 20% of the time due to integration test flakes, which is a major challenge for our team.
</p>
</body>
</html>
"""

def test_extraction_and_drafting():
    print(f"\n======================================")
    print(f"Testing LLM Extraction and Drafting Logic")
    print(f"======================================")
    
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(MOCK_BLOG_HTML, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    
    llm = ChatGroq(model=GROQ_MODEL_NAME, temperature=0)
    structured_llm = llm.with_structured_output(ExtractedGaps)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert B2B sales researcher. 
Your goal is to extract evidence-backed 'gaps', problems, missing capabilities, or pain points from the provided text about the company.
CRITICAL INSTRUCTIONS:
- You MUST extract only gaps with a verbatim quoted source snippet as evidence.
- NEVER infer or hallucinate gaps. If there is no explicit evidence of a problem or gap, return an empty list.
- The source_snippet MUST be an exact substring of the provided text.
- Rank confidence (0.0 to 1.0) based on recency, specificity, and relevance to a B2B product.
"""),
        ("user", "Source URL: {url}\n\nText:\n{text}\n\nExtract gap signals strictly matching the schema.")
    ])
    
    extraction_chain = prompt | structured_llm
    
    url = "https://acmecorp.com/blog/q3-retrospective"
    print("\n[+] Running extraction chain on mock HTML...")
    result = extraction_chain.invoke({"url": url, "text": text})
    
    if not result or not result.gaps:
        print("[-] LLM failed to extract gaps.")
        return
        
    print(f"\n[+] Extracted {len(result.gaps)} gaps successfully.")
    top_gap = sorted(result.gaps, key=lambda x: x.confidence, reverse=True)[0]
    
    print(f"\n[TOP GAP]")
    print(f"Description: {top_gap.description}")
    print(f"Evidence: \"{top_gap.source_snippet}\"")
    print(f"Confidence: {top_gap.confidence}")
    
    print("\n[+] Running drafting chain...")
    prospect = Prospect(name="Jane Doe", title="VP of Engineering", company="Acme Corp")
    
    draft = draft_outreach(prospect, top_gap)
    
    print("\n=== GENERATED DRAFT ===")
    print(f"Subject: {draft.subject}")
    print(f"Body:\n{draft.body}\n")

if __name__ == "__main__":
    test_extraction_and_drafting()
