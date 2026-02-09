
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.rag.service import RAGService
from backend.core.config import config

def main():
    print(f"Initializing RAG Service (Mock Mode: {config.MOCK_LLM})...")
    rag = RAGService()
    
    # Sample data to seed the knowledge base
    documents = [
        "Product Feature: Our AI agent automates cold outreach by researching prospects and drafting personalized emails.",
        "Case Study: TechStart Inc saw a 40% increase in reply rates using our AI SDR compared to manual outreach.",
        "Pricing: Basic plan is $29/mo, Pro is $99/mo with unlimited leads.",
        "Integration: We integrate seamlessly with Salesforce, HubSpot, and Slack.",
        "Objection Handling: If they say 'too expensive', emphasize the ROI and time saved on manual research (avg 10 hours/week).",
        "Competitor Info: Competitor X lacks our deep research agent which scrapes news and podcasts."
    ]
    
    metadatas = [
        {"category": "product", "source": "manual_seed"},
        {"category": "case_study", "source": "manual_seed"},
        {"category": "pricing", "source": "manual_seed"},
        {"category": "integration", "source": "manual_seed"},
        {"category": "sales_playbook", "source": "manual_seed"},
        {"category": "competitive_intel", "source": "manual_seed"}
    ]
    
    print(f"Ingesting {len(documents)} sample documents...")
    rag.add_documents(documents, metadatas)
    print("Ingestion complete!")

    # Test Query
    test_query = "How much does it cost?"
    print(f"\nTesting Query: '{test_query}'")
    results = rag.query(test_query, n_results=2)
    
    if results:
        for i, r in enumerate(results):
            print(f"Result {i+1}: {r['content']} \n   (Meta: {r['metadata']})")
    else:
        print("No results found.")

if __name__ == "__main__":
    main()
