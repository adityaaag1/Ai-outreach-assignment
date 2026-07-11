import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from typing import List
from pydantic import BaseModel, Field

from config import GROQ_MODEL_NAME, MAX_SEARCH_RESULTS, SEARCH_TIMEOUT_SECONDS
from models import GapSignal, SignalType

class ExtractedGaps(BaseModel):
    """A list of extracted gap signals."""
    gaps: List[GapSignal] = Field(description="List of gap signals extracted from the source text.")

def fetch_url_content(url: str) -> str:
    """Fetches and parses the text content of a URL."""
    try:
        response = requests.get(url, timeout=SEARCH_TIMEOUT_SECONDS, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
            
        text = soup.get_text(separator=' ', strip=True)
        # Limit text length to avoid token limits (e.g., first 10,000 characters)
        return text[:10000]
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return ""

def research_prospect(company: str, title: str) -> List[GapSignal]:
    """
    Researches a prospect's company using DuckDuckGo to find potential "gaps" 
    or pain points that our product can solve.
    """
    queries = [
        f"{company} careers hiring {title}",
        f"{company} blog OR news 2025 2026",
        f"{company} product problem OR challenge OR launch",
        f"{company} customer reviews complaints"
    ]
    
    urls_to_fetch = []
    with DDGS() as ddgs:
        for query in queries:
            try:
                results = list(ddgs.text(query, max_results=MAX_SEARCH_RESULTS))
                for res in results:
                    if res.get("href"):
                        urls_to_fetch.append((query, res["href"]))
            except Exception as e:
                print(f"Search failed for query '{query}': {e}")
                
    # Deduplicate URLs while keeping the first query that found it
    unique_urls_map = {}
    for q, u in urls_to_fetch:
        if u not in unique_urls_map:
            unique_urls_map[u] = q
    print(f"Found {len(unique_urls_map)} unique URLs to process.")
    
    all_gaps: List[GapSignal] = []
    
    llm = ChatGroq(model=GROQ_MODEL_NAME, temperature=0)
    structured_llm = llm.with_structured_output(ExtractedGaps)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert B2B sales researcher. 
Your goal is to extract evidence-backed 'gaps', problems, missing capabilities, or pain points from the provided text about the company.
CRITICAL INSTRUCTIONS:
- You MUST extract only gaps with a verbatim quoted source snippet as evidence.
- NEVER infer or hallucinate gaps. If there is no explicit evidence of a problem or gap, return an empty list.
- The source_snippet MUST be an exact substring of the provided text.
- Determine the confidence score (0.0 to 1.0) using these exact rules:
  1. Does the snippet name the company or a specific product/feature of theirs? (required for confidence > 0.5)
  2. Is the source dated within the last ~12 months, or otherwise clearly current?
  3. Is the claim specific (a named product, a named hire, a quoted pain point) vs. generic industry language?
  *IMPORTANT*: If a snippet doesn't name the company directly, cap its confidence at 0.3 regardless of other factors.
- Provide a brief 'reasoning' explaining the assigned confidence score based on the above factors.
- Make sure to populate the 'source_query' field with the provided search query.
"""),
        ("user", "Company: {company}\nSource URL: {url}\nSource Query: {query}\n\nText:\n{text}\n\nExtract gap signals strictly matching the schema.")
    ])
    
    extraction_chain = prompt | structured_llm
    
    # Fetch all URLs concurrently
    import concurrent.futures
    url_text_map = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(fetch_url_content, url): url for url in unique_urls_map.keys()}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                text = future.result()
                if text:
                    url_text_map[url] = text
            except Exception as e:
                try:
                    print(f"Failed to fetch {url}: {e}")
                except UnicodeEncodeError:
                    print(f"Failed to fetch {ascii(url)}")
                
    for url, text in url_text_map.items():
        query = unique_urls_map[url]
        try:
            print(f"Analyzing content from: {url}")
        except UnicodeEncodeError:
            print(f"Analyzing content from: {ascii(url)}")
            
        # Relevance Gate
        if company.lower() not in text.lower():
            try:
                print(f"  [-] Discarded {url}: no company mention found.")
            except UnicodeEncodeError:
                print(f"  [-] Discarded {ascii(url)}: no company mention found.")
            continue
            
        try:
            result = extraction_chain.invoke({"company": company, "url": url, "query": query, "text": text})
            if result and result.gaps:
                for gap in result.gaps:
                    # Enforce the URL and query just in case LLM misses it
                    gap.source_url = url
                    gap.source_query = query
                    all_gaps.append(gap)
        except Exception as e:
            try:
                print(f"Failed to extract from {url}: {e}")
            except UnicodeEncodeError:
                print(f"Failed to extract from {ascii(url)}")
            
    # Rank by confidence descending
    all_gaps.sort(key=lambda g: g.confidence, reverse=True)
    return all_gaps

if __name__ == "__main__":
    # Test standalone
    company = "Acme Corp"
    title = "VP of Engineering"
    print(f"Testing research_tool for {company} - {title}")
    gaps = research_prospect(company, title)
    for i, gap in enumerate(gaps):
        print(f"\\n--- Gap {i+1} ---")
        print(f"Description: {gap.description}")
        print(f"Confidence: {gap.confidence}")
        print(f"Type: {gap.signal_type.value}")
        print(f"Source: {gap.source_url}")
        print(f"Snippet: '{gap.source_snippet}'")
