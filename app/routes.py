

from flask import Flask, request, jsonify, render_template, Blueprint, send_from_directory
from langchain_community.llms import Ollama
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.document_loaders import PDFPlumberLoader
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from .prompts import PROMPTS

import os
import shutil
import hashlib
import logging

# Define a blueprint
bp = Blueprint('main', __name__)

# Folder paths
folder_path = "data/db"
pdf_dir = "data/pdf"

# Path to the PDF directory for viewing PDFs
PDF_DIRECTORY = os.path.join(os.path.dirname(__file__), '..', 'data', 'pdf')

# Dictionary to keep track of PDF usage counts
pdf_usage_count = {}
query_usage_count = {}
chat_history = []

# Initialize the Ollama model
cached_llm = Ollama(model="llama3.1")

# Initialize the embedding model
embedding = FastEmbedEmbeddings()

# Initialize text splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=2048,  # Increased chunk size for better context
    chunk_overlap=100,  # Increased overlap to maintain context between chunks
    length_function=len,
    is_separator_regex=False
)

def initialize_vector_store():
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    # Perform a test operation to ensure proper initialization
    try:
        vector_store = Chroma(persist_directory=folder_path, embedding_function=embedding)
        # Example check to validate database
        if not vector_store.get():
            print("Vector store is empty or not properly initialized.")
            # Additional initialization steps if needed
        return vector_store
    except Exception as e:
        print(f"Error initializing vector store: {str(e)}")
        return None

initialize_vector_store()

if not os.path.exists(folder_path):
    print(f"Error: Directory {folder_path} does not exist.")

def file_exists(file_path):
    return os.path.isfile(file_path)

def compute_file_hash(file):
    """Compute the MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    for chunk in iter(lambda: file.read(4096), b""):
        hash_md5.update(chunk)
    file.seek(0)  # Reset file pointer
    return hash_md5.hexdigest()


if not os.path.exists(folder_path):
    os.makedirs(folder_path)

if not os.path.exists(pdf_dir):
    os.makedirs(pdf_dir)

def preprocess_text(text):
    # Implement text cleaning steps
    text = text.strip().replace('\n', ' ').replace('\r', '')
    return text

class Document:
    def __init__(self, page_content, metadata=None):
        self.page_content = page_content
        self.metadata = metadata or {}

@bp.route('/')
def home():
    return render_template('index.html')

@bp.route('/prompts', methods=['GET'])
def get_prompts():
    try:
        # Convert PromptTemplate objects to a serializable format
        serializable_prompts = {key: str(value) for key, value in PROMPTS.items()}
        return jsonify(serializable_prompts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/pdfManagement")
def pdfManagement():
    try:
        # Fetch the PDF and document statistics
        pdf_files = os.listdir("data/pdf")  # Adjust the path as needed
        vector_store = Chroma(persist_directory="data/db", embedding_function=embedding)
        db_data = vector_store.get()
        document_count = len(db_data.get("metadatas", []))
        
        return render_template("pdfManagement.html", pdf_count=len(pdf_files), doc_count=document_count)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@bp.route("/ai", methods=["POST"])
def aiPost():
    query_usage_count = {}
    print("POST /ai called")
    json_content = request.json
    query = json_content.get("query")

    if not query:
        return jsonify({"error": "No 'query' found in JSON request"}), 400

    print(f"query: {query}")

    response = cached_llm.invoke(query)

    print(response)

    response_answer = {"answer": response}
    return jsonify(response_answer)

@bp.route("/ask_pdf", methods=["POST"])
def askPDFPost():
    query_usage_count = {}
    pdf_usage_count = {}  # Added for tracking PDF usage count
    print("POST /ask_pdf called")

    json_content = request.json
    query = json_content.get("query")
    prompt_type = json_content.get("promptType")  # Get the prompt type

    if not query:
        return jsonify({"error": "No 'query' found in JSON request"}), 400

    print(f"**query**: {query}")
    print(f"**prompt_type**: {prompt_type}")

    # Dynamically select the prompt based on prompt_type
    prompt = PROMPTS.get(prompt_type)
    if not prompt:
        return jsonify({"error": "Unknown prompt type"}), 400

    try:
        print("Loading vector store")
        vector_store = Chroma(persist_directory=folder_path, embedding_function=embedding)
        db_data = vector_store.get()

        if not db_data.get("metadatas"):
            print("Call ended since there are no documents available to process the query.")
            return jsonify({
                "answer": "No documents available to process your query.",
                "disclaimer": "No documents available to process your query. Upload some PDFs to enable document search.",
                "pdf_usage": {},
                "query_usage": {}
            })

        print("Creating retrieval chain")
        retriever = vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": 20,
                "score_threshold": 0.1,
            },
        )

        retriever_prompt = ChatPromptTemplate.from_messages(
            [
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                (
                    "human",
                    "Given the above conversation, generate a search query to lookup in order to get information relevant to the conversation",
                ),
            ]
        )
        history_aware_retriever = create_history_aware_retriever(
            llm=cached_llm, retriever=retriever, prompt=retriever_prompt
        )
        document_chain = create_stuff_documents_chain(cached_llm, prompt)

        retrieval_chain = create_retrieval_chain(
            history_aware_retriever,
            document_chain,
        )

        result = retrieval_chain.invoke({"input": query})
        chat_history.append(HumanMessage(content=query))
        chat_history.append(AIMessage(content=result["answer"]))

        print(chat_history)

        sources = create_context_with_metadata(result.get("context", []))

        # Update PDF usage count and query usage count as before
        for doc in result["context"]:
            pdf_source = doc.metadata.get("source")
            if pdf_source in pdf_usage_count:
                pdf_usage_count[pdf_source] += 1
            else:
                pdf_usage_count[pdf_source] = 1

            if pdf_source in query_usage_count:
                query_usage_count[pdf_source] += 1
            else:
                query_usage_count[pdf_source] = 1

        if not sources:
            answer = f"No relevant documents found for the query: {query}. This answer is generated without any PDF context."
        else:
            answer = result["answer"]

        response_answer = {
            "answer": answer,
            "sources": sources,
            "pdf_usage": {pdf: {"count": count, "percentage": (count / sum(pdf_usage_count.values()) * 100) if sum(pdf_usage_count.values()) > 0 else 0} for pdf, count in pdf_usage_count.items()},
            "query_usage": {pdf: {"count": count, "percentage": (count / sum(query_usage_count.values()) * 100) if sum(query_usage_count.values()) > 0 else 0} for pdf, count in query_usage_count.items()},
            "disclaimer": "This answer is not based on any available PDF documents." if not sources else None
        }

        return jsonify(response_answer)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def create_context_with_metadata(documents):
    contexts = []
    for doc in documents:
        metadata = doc.metadata
        context = f"Document Source: {metadata.get('source', 'Unknown')}\n"
        context += f"Content: {doc.page_content}\n"
        contexts.append({
            "source": metadata.get("source", "Unknown"),
            "page_content": doc.page_content
        })
    return contexts

@bp.route("/clear_chat_history", methods=["POST"])
def clear_chat_history():
    global chat_history
    chat_history = []
    print("Chat history cleared")
    return jsonify({"status": "Chat history cleared successfully"})

@bp.route("/clear_db", methods=["POST"])
def clear_db():
    logging.info("POST /clear_db called")
    try:
        # Clear the vector store (i.e., delete all documents)
        clear_vector_store()

        # Clear the PDF directory if necessary
        clear_directory(pdf_dir)

        # Reinitialize the vector store
        global vector_store
        vector_store = initialize_vector_store()

        return jsonify({"status": "Database and files cleared successfully"})
    except Exception as e:
        logging.error(f"Error during clear_db operation: {str(e)}")
        return jsonify({"error": str(e)}), 500

def clear_directory(directory_path):
    """
    Clears the specified directory by removing it and then recreating it.
    """
    if os.path.exists(directory_path):
        shutil.rmtree(directory_path)
        os.makedirs(directory_path)
        logging.info(f"Directory cleared: {directory_path}")

def clear_vector_store():
    """
    Clears all documents from the vector store.
    """
    try:
        global vector_store
        # Initialize the vector store
        vector_store = Chroma(persist_directory=folder_path, embedding_function=embedding)

        # Get all document IDs from the vector store
        db_data = vector_store.get()  # Get the data from the vector store
        ids = db_data.get("ids", [])

        # Log the number of documents found
        logging.info(f"Found {len(ids)} documents in vector store")

        if ids:
            # Delete all documents by their IDs
            for doc_id in ids:
                if doc_id:
                    vector_store.delete(doc_id)
                    logging.info(f"Deleted document with ID: {doc_id}")

            # Persist changes to the vector store
            vector_store.persist()
            logging.info("Successfully deleted all documents and persisted changes.")
        else:
            logging.info("No documents found in vector store to delete.")
    
    except Exception as e:
        logging.error(f"Error during vector store clearing: {str(e)}")
        raise

    
@bp.route("/list_pdfs", methods=["GET"])
def list_pdfs():
    print("GET /list_pdfs called")
    print(f"pdf_dir: {pdf_dir}")
    print(f"pdf_dir: {pdf_files}")
    try:
        pdf_files = os.listdir(pdf_dir)
        return jsonify({"pdf_files": pdf_files})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@bp.route("/pdf", methods=["POST"])
def pdfPost():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    file_name = file.filename
    save_file = os.path.join(pdf_dir, file_name)

    # Check if the file already exists
    if file_exists(save_file):
        return jsonify({"error": "File already exists."}), 400

    # Compute file hash to check for duplicates
    try:
        file_hash = compute_file_hash(file)
    except Exception as e:
        return jsonify({"error": f"Error computing file hash: {str(e)}"}), 500

    existing_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
    for existing_file in existing_files:
        existing_file_path = os.path.join(pdf_dir, existing_file)
        try:
            if compute_file_hash(open(existing_file_path, 'rb')) == file_hash:
                return jsonify({"error": "File with identical content already exists."}), 400
        except Exception as e:
            return jsonify({"error": f"Error checking existing files: {str(e)}"}), 500

    # Save the file
    try:
        file.save(save_file)
    except Exception as e:
        return jsonify({"error": f"Error saving file: {str(e)}"}), 500

    # Load and preprocess the PDF file
    try:
        loader = PDFPlumberLoader(save_file)
        docs = loader.load_and_split()
        is_structured = True
    except Exception as e:
        print(f"Error loading structured text: {e}")
        docs = []
        is_structured = False

    if not docs:
        # Perform OCR if the document is unstructured
        try:
            print("Performing OCR")
            text = perform_ocr(save_file)
            docs = [Document(page_content=preprocess_text(text), metadata={"source": file_name})]
            is_structured = False
        except Exception as e:
            return jsonify({"error": f"Error during OCR processing: {str(e)}"}), 500
    else:
        # Preprocess text from documents
        docs = [Document(page_content=preprocess_text(doc.page_content), metadata={"source": file_name}) for doc in docs]

    try:
        chunks = text_splitter.split_documents(docs)
        print(f"Loaded len={len(chunks)} chunks")

        # Add source metadata to each chunk
        for chunk in chunks:
            chunk.metadata = {"source": file_name}
        global vector_store
        # Initialize the vector store
        vector_store = Chroma.from_documents(
            documents=chunks, embedding=embedding, persist_directory=folder_path
        )
    except Exception as e:
        return jsonify({"error": f"Error initializing vector store: {str(e)}"}), 500

    response = {
        "status": "Successfully Uploaded",
        "filename": file_name,
        "doc_len": len(docs),
        "chunk_len": len(chunks),
        "is_structured": is_structured
    }
    return jsonify(response)


@bp.route("/list_documents", methods=["GET"])
def list_documents():

    try:
        print("GET /list_pdfs called")
        print(f"pdf_dir: {folder_path}")
        print(f"pdf_dir: {pdf_dir}")
        print(f"folder_path: {folder_path}")
        print(f"embedding function: {embedding}")

        if not os.path.exists(folder_path):
            print(f"The directory {folder_path} does not exist. Initializing vector store...")
            os.makedirs(folder_path, exist_ok=True)  # Ensure the folder exists before initializing

        print("Initializing vector store...")
        initialize_vector_store()
        try:
            vector_store = Chroma(persist_directory=folder_path, embedding_function=embedding)
        except Exception as init_error:
            print(f"Failed to initialize vector store: {init_error}")
            return jsonify({"error": "Failed to initialize vector store"}), 500
        print("Vector store initialized.")

        print("Fetching data from vector store...")
        try:
            db_data = vector_store.get()
        except Exception as fetch_error:
            print(f"Failed to fetch data from vector store: {fetch_error}")
            return jsonify({"error": "Failed to fetch data from vector store"}), 500

        if not db_data or "metadatas" not in db_data or not db_data["metadatas"]:
            print("No documents found in vector store.")
            return jsonify({"message": "No documents found"}), 200

        documents = [{"source": metadata.get("source", "Unknown")} for metadata in db_data["metadatas"]]
        response = {"documents": documents}
        print("Documents extracted:", documents)
        return jsonify(response), 200

    except Exception as e:
        print(f"Error listing documents: {e}")
        return jsonify({"error": "An error occurred while listing documents. Please try again later."}), 500

@bp.route("/delete_pdf", methods=["POST"])
def delete_pdf():
    json_content = request.json
    file_name = json_content.get("file_name")

    if not file_name:
        return jsonify({"error": "No 'file_name' found in JSON request"}), 400

    try:
        # Construct the file path
        file_path = os.path.join(pdf_dir, file_name)
        print(f"Attempting to delete file at: {file_path}")

        # Create a path pattern to match against
        path_pattern = file_name  # Use only file_name for pattern matching
        print(f"Looking for documents with source: {path_pattern}")

        # Remove the PDF references from the vector store
        vector_store = Chroma(persist_directory=folder_path, embedding_function=embedding)

        # Get all documents from the vector store
        db_data = vector_store.get()  # Get the data from the vector store
        print(f"db_data: {db_data}")
        metadatas = db_data.get("metadatas", [])
        ids = db_data.get("ids", [])
        
        # Log the number of documents and sample metadata
        print(f"Found {len(metadatas)} documents in vector store")
        if metadatas:
            print(f"Sample metadata: {metadatas[0]}")

        # Find and delete documents with the matching source path
        docs_to_delete = [id for id, metadata in zip(ids, metadatas) if metadata.get("source").strip().lower() == path_pattern.strip().lower()]
        print(f"Documents to delete: {docs_to_delete}")

        if docs_to_delete:
            for doc_id in docs_to_delete:
                if doc_id is None:
                    print("Encountered None as doc_id, skipping deletion.")
                    continue
                print(f"Deleting document with ID: {doc_id}")
                vector_store.delete(doc_id)

            # Persist changes to the vector store
            vector_store.persist()
            print(f"Successfully deleted documents and persisted changes.")
        else:
            print(f"No documents found for source: {path_pattern}")
            return jsonify({"status": "No documents found for the provided file name"}), 404

        # Check if the file exists
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Successfully deleted file: {file_path}")
        else:
            print(f"File not found: {file_path}")
            return jsonify({"error": "File not found"}), 404
        
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Error during deletion: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route('/pdfs/<path:filename>')
def serve_pdf(filename):
    return send_from_directory(PDF_DIRECTORY, filename)

@bp.route("/delete_document", methods=["POST"])
def delete_document():
    print("POST /delete_document called")
    json_content = request.json
    doc_id = json_content.get("doc_id")

    if not doc_id:
        return jsonify({"error": "No 'doc_id' found in JSON request"}), 400

    try:
        vector_store = Chroma(persist_directory=folder_path, embedding_function=embedding)
        vector_store.delete(doc_id)
        return jsonify({"status": "Document deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def perform_ocr(pdf_path):
    # Placeholder function for OCR processing
    # You can implement this using libraries like pytesseract or other OCR tools
    return "OCR processed text from PDF"

@bp.route("/pdf_usage", methods=["GET"])
def get_pdf_usage():
    try:
        # Calculate percentage influence
        total_queries = sum(pdf_usage_count.values())
        pdf_influence = {pdf: {"count": count, "percentage": (count / total_queries * 100) if total_queries > 0 else 0} for pdf, count in pdf_usage_count.items()}
        return jsonify({"pdf_usage": pdf_influence})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Configure logging
logging.basicConfig(level=logging.INFO, filename='app.log', filemode='a')
