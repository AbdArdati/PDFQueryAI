from flask import Flask, request, jsonify, render_template
from langchain_community.llms import Ollama
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.document_loaders import PDFPlumberLoader
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains.history_aware_retriever import create_history_aware_retriever

import os
import shutil
import hashlib

app = Flask(__name__)


chat_history = []

# Initialize the Ollama model
cached_llm = Ollama(model="llama3")

# Initialize the embedding model
embedding = FastEmbedEmbeddings()

# Initialize text splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1024, chunk_overlap=80, length_function=len, is_separator_regex=False
)

raw_prompt = PromptTemplate.from_template(
    """ 
    <s>[INST] You are a technical assistant good at searching documents. If you do not have an answer from the provided information say so. [/INST] </s>
    [INST] {input}
           Context: {context}
           Answer:
    [/INST]
"""
)

# Ensure the folder paths exist
folder_path = "db"
pdf_dir = "pdf"


def initialize_vector_store():
    if not os.path.exists("db"):
        os.makedirs("db")
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

vector_store = initialize_vector_store()

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

# Dictionary to keep track of PDF usage counts
pdf_usage_count = {}
query_usage_count = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ai", methods=["POST"])
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

@app.route("/ask_pdf", methods=["POST"])
def askPDFPost():
    query_usage_count = {}
    print("POST /ask_pdf called")
    json_content = request.json
    query = json_content.get("query")

    if not query:
        return jsonify({"error": "No 'query' found in JSON request"}), 400

    print(f"query: {query}")

    try:
        print("Loading vector store")
        vector_store = Chroma(persist_directory=folder_path, embedding_function=embedding)
        db_data = vector_store.get()  # Get the data from the vector store

        # Check if there are any documents in the vector store
        if not db_data.get("metadatas"):
            # Return a disclaimer if no documents are available
            return jsonify({
                "answer": "No documents available to process your query.",
                "disclaimer": "The following answer is not based on any available PDF documents.",
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
                    "Given the above conversation, generation a search query to lookup in order to get information relevant to the conversation",
                ),
            ]
        )
        history_aware_retriever = create_history_aware_retriever(
            llm=cached_llm, retriever=retriever, prompt=retriever_prompt
        )
        document_chain = create_stuff_documents_chain(cached_llm, raw_prompt)
        # chain = create_retrieval_chain(retriever, document_chain)
    
        retrieval_chain = create_retrieval_chain(
            # retriever,
            history_aware_retriever,
            document_chain,
        )

        # result = chain.invoke({"input": query})
        result = retrieval_chain.invoke({"input": query})
        chat_history.append(HumanMessage(content=query))
        chat_history.append(AIMessage(content=result["answer"]))

        print(chat_history)

        sources = []

        for doc in result["context"]:
            sources.append(
                {
                    "source": doc.metadata["source"],
                    "page_content": doc.page_content
                }
            )

            # Update PDF usage count total
            pdf_source = doc.metadata.get("source")
            if pdf_source in pdf_usage_count:
                pdf_usage_count[pdf_source] += 1
            else:
                pdf_usage_count[pdf_source] = 1

            # Update query usage count
            if pdf_source in query_usage_count:
                query_usage_count[pdf_source] += 1
            else:
                query_usage_count[pdf_source] = 1

        # Check if any sources were found
        if not sources:
            answer = f"No relevant documents found for the query: {query}. This answer is generated without any PDF context."
        else:
            answer = result["answer"]

        # Convert the result to a JSON serializable format
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

@app.route("/clear_chat_history", methods=["POST"])
def clear_chat_history():
    global chat_history
    chat_history = []
    return jsonify({"status": "Chat history cleared successfully"})


@app.route("/clear_db", methods=["POST"])
def clear_db():
    print("POST /clear_db called")
    try:
        # Clear vector store
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            os.makedirs(folder_path)  # Recreate the folder to maintain structure

        # Clear PDF directory
        if os.path.exists(pdf_dir):
            shutil.rmtree(pdf_dir)
            os.makedirs(pdf_dir)  # Recreate the folder to maintain structure

        return jsonify({"status": "Database and files cleared successfully"})
    except Exception as e:
        print(f"Error during clear_db operation: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/list_pdfs", methods=["GET"])
def list_pdfs():
    print("GET /list_pdfs called")
    try:
        pdf_files = os.listdir(pdf_dir)
        return jsonify({"pdf_files": pdf_files})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/pdf", methods=["POST"])
def pdfPost():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    file_name = file.filename
    save_file = os.path.join(pdf_dir, file_name)

    # Check if the file already exists
    if file_exists(file_name):
        return jsonify({"error": "File already exists."}), 400

    # Compute file hash to check for duplicates
    file_hash = compute_file_hash(file)

    existing_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
    for existing_file in existing_files:
        existing_file_path = os.path.join(pdf_dir, existing_file)
        if compute_file_hash(open(existing_file_path, 'rb')) == file_hash:
            return jsonify({"error": "File with identical content already exists."}), 400

    # Save the file
    file.save(save_file)
    print(f"filename: {file_name}")

    # Load and split the PDF file
    loader = PDFPlumberLoader(save_file)
    try:
        docs = loader.load_and_split()
        is_structured = True
    except Exception as e:
        print(f"Error loading structured text: {e}")
        docs = []
        is_structured = False

    if not docs:
        # Perform OCR if the document is unstructured
        print("Performing OCR")
        text = perform_ocr(save_file)
        docs = [{"page_content": text}]
        is_structured = False

    print(f"Loaded {len(docs)} documents")

    chunks = text_splitter.split_documents(docs)
    print(f"Loaded len={len(chunks)} chunks")

    # Add source metadata to each chunk
    for chunk in chunks:
        chunk.metadata = {"source": file_name}

    # Initialize the vector store
    vector_store = Chroma.from_documents(
        documents=chunks, embedding=embedding, persist_directory=folder_path
    )

    response = {
        "status": "Successfully Uploaded",
        "filename": file_name,
        "doc_len": len(docs),
        "chunk_len": len(chunks),
        "is_structured": is_structured
    }
    return jsonify(response)


@app.route("/list_documents", methods=["GET"])
def list_documents():
    try:
        # Initialize the vector store
        vector_store = Chroma(persist_directory=folder_path, embedding_function=embedding)

        if not vector_store:
            raise RuntimeError("Vector store initialization failed")

        # Get data from the vector store
        db_data = vector_store.get()
        if not db_data or "metadatas" not in db_data:
            return jsonify({"message": "No documents found"}), 200

        # Extract documents
        documents = [{"source": metadata.get("source", "Unknown")} for metadata in db_data["metadatas"]]

        # Return the list of documents
        response = {"documents": documents}
        return jsonify(response), 200

    except Exception as e:
        # Log the error and return a user-friendly message
        print(f"Error listing documents: {e}")
        return jsonify({"error": "Failed to list documents. Please try again later."}), 500

@app.route("/delete_pdf", methods=["POST"])
def delete_pdf():
    json_content = request.json
    file_name = json_content.get("file_name")

    if not file_name:
        return jsonify({"error": "No 'file_name' found in JSON request"}), 400

    try:
        # Construct the file path
        file_path = os.path.join(pdf_dir, file_name)
        print(f"Attempting to delete file at: {file_path}")

        # Check if the file exists
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Successfully deleted file: {file_path}")
        else:
            print(f"File not found: {file_path}")
            return jsonify({"error": "File not found"}), 404

        # Remove the PDF references from the vector store
        vector_store = Chroma(persist_directory=folder_path, embedding_function=embedding)

        # Get all documents from the vector store
        db_data = vector_store.get()  # Get the data from the vector store
        metadatas = db_data.get("metadatas", [])
        
        # Log the number of documents and sample metadata
        print(f"Found {len(metadatas)} documents in vector store")
        if metadatas:
            print(f"Sample metadata: {metadatas[0]}")

        # Create a path pattern to match against
        path_pattern = f'pdf/{file_name}'
        print(f"Looking for documents with source: {path_pattern}")

        # Find and delete documents with the matching source path
        docs_to_delete = [metadata.get("doc_id") for metadata in metadatas if metadata.get("source") == path_pattern]
        print(f"Documents to delete: {docs_to_delete}")

        if docs_to_delete:
            for doc_id in docs_to_delete:
                print(f"Deleting document with ID: {doc_id}")
                vector_store.delete(doc_id)

            # Persist changes to the vector store
            vector_store.persist()
            print(f"Successfully deleted documents and persisted changes.")
        else:
            print(f"No documents found for source: {path_pattern}")
            return jsonify({"status": "No documents found for the provided file name"}), 404

        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Error during deletion: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/delete_document", methods=["POST"])
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

@app.route("/pdf_usage", methods=["GET"])
def get_pdf_usage():
    try:
        # Calculate percentage influence
        total_queries = sum(pdf_usage_count.values())
        pdf_influence = {pdf: {"count": count, "percentage": (count / total_queries * 100) if total_queries > 0 else 0} for pdf, count in pdf_usage_count.items()}
        return jsonify({"pdf_usage": pdf_influence})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def start_app():
    app.run(host="0.0.0.0", port=8080, debug=True)

if __name__ == "__main__":
    start_app()
