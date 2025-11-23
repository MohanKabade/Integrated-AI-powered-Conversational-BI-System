import os
import uuid
from .updated_chatwithpdf import (
    load_and_chunk_documents,
    get_gemini_embeddings,
    store_in_pinecone,
    run_rag_pipeline
)

INDEX_NAME = "llm-chatbot"   # same as in your code


def process_pdf_file(file_storage, upload_folder="uploads"):
    """
    Save PDF/DOC file, chunk it, embed it, store in Pinecone.
    Returns a namespace ID used for future queries.
    """
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, file_storage.filename)
    file_storage.save(file_path)

    # Use a random namespace so each upload is isolated
    namespace = str(uuid.uuid4())

    # 1) Chunk
    chunks = load_and_chunk_documents([file_path])
    texts = [doc.page_content for doc in chunks]

    # 2) Embeddings
    embeddings = get_gemini_embeddings(texts, max_workers=8)

    # 3) Store in Pinecone
    store_in_pinecone(
        chunks,
        embeddings,
        namespace=namespace,
        index_name=INDEX_NAME,
        batch_size=100,
    )

    print("✅ PDF/DOC processed, namespace:", namespace)
    return {
        "message": "PDF/DOC uploaded and processed successfully! Document module activated.",
        "namespace": namespace,
    }


def answer_pdf_question(query, namespace):
    """
    Use RAG pipeline to answer from the uploaded document.
    Always returns text.
    """
    response = run_rag_pipeline(query, namespace=namespace, index_name=INDEX_NAME)
    return {"type": "text", "content": response}
