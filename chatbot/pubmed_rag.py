"""
chatbot/pubmed_rag.py - Live PubMed Citation Fetcher for RAG grounding.

Uses NCBI E-utilities (no API key required for basic use).
Set PUBMED_API_KEY in .env for higher rate limits (10 req/s vs 3 req/s).

Workflow:
  1. extract_medical_keywords(text) -> list of search terms
  2. search_pubmed(query, max_results) -> list of PMIDs
  3. fetch_abstracts(pmids) -> list of ArticleSummary dicts
  4. get_pubmed_citations(user_query, symptoms) -> ready-to-use citations block
"""

import os
import re
import time
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# NCBI E-utilities base URLs
# ---------------------------------------------------------------------------
ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

PUBMED_API_KEY = os.getenv("PUBMED_API_KEY")  # optional — raises rate limit to 10 req/s

HTTP_TIMEOUT = 15
MAX_ABSTRACTS = 3   # Keep context size manageable for Mistral


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_params() -> dict:
    """Return common params for all NCBI calls."""
    params = {"retmode": "json", "tool": "AI-Medical-Assistant", "email": "ai-medical-app@example.com"}
    if PUBMED_API_KEY:
        params["api_key"] = PUBMED_API_KEY
    return params


def extract_medical_keywords(symptoms: str) -> str:
    """
    Build a focused PubMed search query from free-text symptoms.
    Strips generic filler words and keeps medically meaningful terms.
    Returns a query string suitable for PubMed E-search.
    """
    filler = {
        "i", "have", "been", "feeling", "experiencing", "some", "a", "an", "the",
        "and", "or", "but", "with", "my", "me", "of", "in", "is", "are", "was",
        "were", "for", "on", "at", "to", "it", "that", "this", "very", "quite",
        "little", "bit", "much", "more", "less", "please", "help",
    }
    # lowercase, remove punctuation, split
    tokens = re.sub(r"[^\w\s]", " ", symptoms.lower()).split()
    keywords = [t for t in tokens if t not in filler and len(t) > 2]

    # Deduplicate while preserving order
    seen: set = set()
    unique_kw: List[str] = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique_kw.append(kw)

    # Build query: take up to 6 most specific terms
    query_terms = unique_kw[:6]
    return " AND ".join(query_terms) if query_terms else symptoms.strip()


def search_pubmed(query: str, max_results: int = MAX_ABSTRACTS) -> List[str]:
    """
    Run a PubMed E-search and return a list of PMIDs.
    Filters to English, free-full-text-preferred, last 10 years.
    """
    params = _base_params()
    params.update({
        "db": "pubmed",
        "term": f"({query}) AND (English[Language])",
        "retmax": max_results * 3,   # fetch more to allow quality filtering
        "sort": "relevance",
        "datetype": "pdat",
        "reldate": 3650,             # last 10 years
        "retmode": "json",
    })
    try:
        resp = requests.get(ESEARCH_URL, params=params, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        id_list = resp.json().get("esearchresult", {}).get("idlist", [])
        return id_list[:max_results]
    except Exception:
        return []


def fetch_abstracts(pmids: List[str]) -> List[Dict[str, str]]:
    """
    Fetch article titles + abstracts for a list of PMIDs via E-fetch (XML).
    Returns a list of dicts: {pmid, title, abstract, authors, journal, year, url}
    """
    if not pmids:
        return []

    params = _base_params()
    params.update({
        "db": "pubmed",
        "id": ",".join(pmids),
        "rettype": "abstract",
        "retmode": "xml",
    })
    # Remove retmode=json set by _base_params — XML is needed here
    params["retmode"] = "xml"

    try:
        resp = requests.get(EFETCH_URL, params=params, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
    except Exception:
        return []

    articles = []
    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError:
        return []

    for article_node in root.findall(".//PubmedArticle"):
        citation = article_node.find("MedlineCitation")
        if citation is None:
            continue

        pmid_node = citation.find("PMID")
        pmid = pmid_node.text if pmid_node is not None else "N/A"

        article = citation.find("Article")
        if article is None:
            continue

        # Title
        title_node = article.find("ArticleTitle")
        title = "".join(title_node.itertext()) if title_node is not None else "No title"

        # Abstract
        abstract_parts = []
        abstract_node = article.find("Abstract")
        if abstract_node is not None:
            for text_node in abstract_node.findall("AbstractText"):
                label = text_node.get("Label", "")
                content = "".join(text_node.itertext())
                if label:
                    abstract_parts.append(f"{label}: {content}")
                else:
                    abstract_parts.append(content)
        abstract_text = " ".join(abstract_parts) if abstract_parts else "Abstract not available."

        # Authors (first two)
        authors = []
        author_list = article.find("AuthorList")
        if author_list is not None:
            for auth in author_list.findall("Author")[:2]:
                last = auth.findtext("LastName", "")
                initials = auth.findtext("Initials", "")
                if last:
                    authors.append(f"{last} {initials}".strip())
        author_str = ", ".join(authors) + (" et al." if len(authors) >= 2 else "")

        # Journal + Year
        journal_node = article.find("Journal")
        journal_name = ""
        pub_year = ""
        if journal_node is not None:
            journal_name = journal_node.findtext("ISOAbbreviation", "") or journal_node.findtext("Title", "")
            pub_date = journal_node.find("JournalIssue/PubDate")
            if pub_date is not None:
                pub_year = pub_date.findtext("Year", "") or pub_date.findtext("MedlineDate", "")[:4]

        articles.append({
            "pmid": pmid,
            "title": title,
            "abstract": abstract_text[:800],    # truncate to save tokens
            "authors": author_str,
            "journal": journal_name,
            "year": pub_year,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        })

    return articles


def get_pubmed_citations(symptoms: str, max_results: int = MAX_ABSTRACTS) -> Dict:
    """
    Main entry point: given symptoms text returns:
      {
        "citations": [...],      # list of article dicts (for JSON response)
        "context_block": "..."   # formatted text to inject into Mistral prompt
      }

    Returns empty result (no citations) gracefully if PubMed is unreachable.
    """
    if not symptoms or not symptoms.strip():
        return {"citations": [], "context_block": ""}

    query = extract_medical_keywords(symptoms)
    pmids = search_pubmed(query, max_results=max_results)

    if not pmids:
        return {"citations": [], "context_block": ""}

    # Small delay to respect NCBI rate limits (3 req/s without key)
    if not PUBMED_API_KEY:
        time.sleep(0.4)

    articles = fetch_abstracts(pmids)

    if not articles:
        return {"citations": [], "context_block": ""}

    # Build context block for Mistral prompt injection
    lines = ["--- RELEVANT MEDICAL LITERATURE (PubMed) ---"]
    for i, art in enumerate(articles, 1):
        lines.append(
            f"[{i}] {art['authors']} ({art['year']}). \"{art['title']}\". "
            f"{art['journal']}. PMID: {art['pmid']}\n"
            f"    Abstract: {art['abstract']}"
        )
    lines.append("--- END OF LITERATURE ---")
    context_block = "\n\n".join(lines)

    return {
        "citations": [
            {
                "pmid": a["pmid"],
                "title": a["title"],
                "authors": a["authors"],
                "journal": a["journal"],
                "year": a["year"],
                "url": a["url"],
            }
            for a in articles
        ],
        "context_block": context_block,
    }
