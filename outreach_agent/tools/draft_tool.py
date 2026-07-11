import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from config import GROQ_MODEL_NAME, OUR_PRODUCT_DESCRIPTION
from models import Prospect, GapSignal, Draft

class DraftOutput(BaseModel):
    subject: str = Field(description="Subject line of the email draft")
    body: str = Field(description="Body of the email draft")

def draft_outreach(prospect: Prospect, gap: GapSignal, our_product: str = OUR_PRODUCT_DESCRIPTION) -> Draft:
    """
    Drafts a personalized outreach message based on the prospect, the identified gap, 
    and our product description.
    """
    llm = ChatGroq(model=GROQ_MODEL_NAME, temperature=0.4)
    structured_llm = llm.with_structured_output(DraftOutput)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an elite B2B sales copywriter writing a highly personalized, human-sounding outreach email.
CRITICAL RULES:
- Length: Write a comprehensive email, around 150-250 words, structured in short, readable paragraphs.
- Tone: Highly conversational, human, professional. Write as if you are directly speaking to a peer. 
- ANTI-SLOP RULE: STRICTLY AVOID all AI buzzwords and clichés. Do NOT use words like: "leverage", "delve", "testament", "tapestry", "seamless", "innovative", "unlock", "synergy", "game-changer", "landscape", "pivotal", "tailored".
- Do NOT use generic SDR clichés like "I hope this finds you well", "I wanted to reach out", "bumping this", etc.
- Personalization: Deeply weave the prospect's specific role/background into why the identified gap matters to them.
- Reference the specific gap naturally and cite the evidence lightly (don't just paste the quote).
- Explain concretely how our product addresses it — one clear mechanism, no vague value-speak.
- End with a low-friction, natural call to action.
- IMPORTANT: "Our Product" describes the solution WE are selling. The "Prospect Details" describe the person we are writing TO. Do NOT mix these up. Do not imply the prospect works for our company or built our product.
"""),
        ("user", """### PROSPECT DETAILS (The recipient of the email)
Name: {name}
Title: {title}
Company: {company}

### IDENTIFIED GAP (The problem the prospect's company is facing)
Description: {gap_desc}
Evidence snippet: "{gap_evidence}"
Source Type: {gap_type}

### OUR PRODUCT (The solution WE are pitching to the prospect)
{product}
""")
    ])
    
    extraction_chain = prompt | structured_llm
    
    result: DraftOutput = extraction_chain.invoke({
        "name": prospect.name,
        "title": prospect.title,
        "company": prospect.company,
        "gap_desc": gap.description,
        "gap_evidence": gap.source_snippet,
        "gap_type": gap.signal_type.value,
        "product": our_product
    })
    
    return Draft(
        subject=result.subject,
        body=result.body,
        gap_used=gap
    )

if __name__ == "__main__":
    # Test standalone
    from models import SignalType
    
    test_prospect = Prospect(
        name="Jane Doe",
        company="TechCorp",
        title="CTO"
    )
    
    test_gap = GapSignal(
        description="Struggling with slow deployment times and pipeline failures.",
        source_snippet="Our recent engineering blog post highlighted how pipeline failures delayed our Q3 release by two weeks.",
        source_url="https://techcorp.com/blog/q3-retrospective",
        signal_type=SignalType.BLOG_POST,
        confidence=0.9
    )
    
    print("Testing draft_tool...")
    draft = draft_outreach(test_prospect, test_gap)
    print(f"Subject: {draft.subject}")
    print(f"Body:\\n{draft.body}")
