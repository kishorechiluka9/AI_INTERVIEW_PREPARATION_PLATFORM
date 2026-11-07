
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


def split_resume_into_chunks(resume_text: str):
    """Split extracted resume text into smaller chunks."""

    if not resume_text or not resume_text.strip():
        raise ValueError("Resume text is empty.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    chunks = splitter.split_text(resume_text)

    if not chunks:
        raise ValueError("No resume chunks generated.")

    documents = []

    for index, chunk in enumerate(chunks):
        doc = Document(
            page_content=chunk,
            metadata={
                "source": "resume",
                "chunk_id": index
            }
        )
        documents.append(doc)

    return documents
