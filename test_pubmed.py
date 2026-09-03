from chatbot.pubmed_rag import get_pubmed_citations
res = get_pubmed_citations("headache AND fever")
for c in res['citations']:
    print(c['title'])
