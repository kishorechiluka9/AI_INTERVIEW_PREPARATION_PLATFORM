
from langchain_community.vectorstores import FAISS


def create_resume_vector_store(documents, embeddings):
    """Create an in-memory FAISS vector store."""

    if not documents:
        raise ValueError("No documents provided to FAISS.")

    vector_store = FAISS.from_documents(
        documents=documents,
        embedding=embeddings
    )

    return vector_store


def search_resume(vector_store, query, k=4):
    """Retrieve the most relevant resume chunks."""

    if not query or not query.strip():
        raise ValueError("Search query cannot be empty.")

    results = vector_store.similarity_search(
        query=query,
        k=k
    )

    return results
