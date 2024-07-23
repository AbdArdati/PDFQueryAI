# AI-Powered PDF Query Application 🚀

This repository contains a Flask web application that allows users to upload PDF documents, query their contents, and retrieve answers using an AI language model. The application integrates several functionalities to manage PDFs, handle user queries, and maintain usage statistics.

## High-Level Overview 🌟

The application provides an interface for:
- 📄 **Uploading and managing PDF documents**.
- ❓ **Submitting queries to retrieve information from uploaded PDFs**.
- 📊 **Tracking PDF usage statistics**.
- 🔧 **Performing administrative operations like clearing data and deleting files**.

### Key Features 🔑

1. **PDF Management**:
   - **Upload PDFs**: Users can upload PDF files, which are then processed and stored in a database.
   - **List PDFs**: Users can view a list of uploaded PDF files.
   - **Delete PDFs**: Users can delete specific PDF files from the system.

2. **Query Handling**:
   - **Ask Questions**: Users can submit questions that the application attempts to answer using information from uploaded PDFs.
   - **AI Integration**: Uses a language model to generate answers based on the contents of the PDFs and the provided query.

3. **Statistics and Administration**:
   - **Clear Chat History**: Allows clearing of previous chat interactions.
   - **Clear Database**: Deletes all stored data and PDFs.
   - **PDF Usage Statistics**: Provides statistics on how often each PDF has been queried.

## Low-Level Overview 🔍

### Initialization and Setup

- **Flask Application**: The `Flask` instance is created to handle HTTP requests and route them to appropriate functions.
- **Global Variables**: These include the AI model (`cached_llm`), text embeddings (`embedding`), and a text splitter (`text_splitter`). The application also maintains directories for storing PDFs and vector store data.

### Endpoints and Their Functions

- **`/`**: Serves the main HTML page for user interaction.
  
- **`/ai`**:
  - **Method**: `POST`
  - **Function**: Accepts a JSON request containing a query, passes it to the AI model, and returns the generated response.

- **`/ask_pdf`**:
  - **Method**: `POST`
  - **Function**: Processes queries against uploaded PDFs. It uses a vector store to find relevant documents, generates an answer based on the context, and returns the answer along with sources and usage statistics.

- **`/clear_chat_history`**:
  - **Method**: `POST`
  - **Function**: Clears the chat history stored in the global `chat_history` list.

- **`/clear_db`**:
  - **Method**: `POST`
  - **Function**: Deletes all stored vector data and PDF files from the filesystem, effectively resetting the application’s state.

- **`/list_pdfs`**:
  - **Method**: `GET`
  - **Function**: Lists all PDF files currently available in the storage directory.

- **`/pdf`**:
  - **Method**: `POST`
  - **Function**: Handles PDF uploads. The file is saved, processed, and split into chunks. These chunks are then stored in a vector database for later querying.

- **`/list_documents`**:
  - **Method**: `GET`
  - **Function**: Lists all documents in the vector store.

- **`/delete_pdf`**:
  - **Method**: `POST`
  - **Function**: Deletes a specific PDF file and its associated documents from the vector store.

- **`/delete_document`**:
  - **Method**: `POST`
  - **Function**: Deletes a specific document from the vector store by its ID.

- **`/pdf_usage`**:
  - **Method**: `GET`
  - **Function**: Provides usage statistics on how often each PDF has been queried.

### Internal Functions 🔧

- **`file_exists(filename)`**: Checks if a file with the given name exists in the directory.
  
- **`compute_file_hash(file)`**: Computes the MD5 hash of a file to detect duplicates.
  
- **`perform_ocr(pdf_path)`**: Placeholder function for performing Optical Character Recognition (OCR) on a PDF if it is not structured. This needs to be implemented with an actual OCR library like `pytesseract`.

### Error Handling ⚠️

- The application includes basic error handling for missing data, file operations, and vector store interactions. For example, if a file is not found or an operation fails, the application returns an appropriate error message and HTTP status code.

### Summary 📝

Overall, the application provides a structured way to manage and interact with PDF documents using an AI model. It integrates file management, data processing, and querying capabilities into a Flask web service, allowing users to upload, query, and manage PDFs while also keeping track of usage statistics and providing administrative functionalities.

## Installation Instructions ⚙️

### 1. Download and Install Ollama

To use the `Ollama` model, follow these steps to download and install it based on your operating system:

1. **Visit the Ollama Download Page:**
   Go to [Ollama Download Page](https://ollama.com/download).

2. **Download the Installer:**
   Choose the appropriate installer for your operating system and download it.

3. **Install Ollama:**
   Follow the installation instructions provided on the download page for your specific operating system.

4. **Verify Installation:**
   After installation, verify that Ollama is installed correctly by running the following command in your terminal or command prompt:

   ```bash
   ollama --version

5. **Run the Llama3 Model:**
   Once Ollama is installed, start the llama3 model by running the following command in your terminal or command prompt:

   ```bash
   ollama run llama3
   
### 2. **Clone the Repository**:
    
    git clone https://github.com/AbdArdati/PDFQueryAI.git
    cd PDFQueryAI
   

### 3. **Create a Virtual Environment**:
    
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    

### 4. **Install Dependencies**:
    
    pip install -r requirements.txt
    

### 5. **Run the Application**:
     
    python app.py
     

## License 🛡️

This project is licensed under the Apache 2.0 License. The core components of this application follow the work from [https://github.com/ThomasJay/RAG](https://github.com/ThomasJay/RAG) which is also licensed under Apache 2.0.

```
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```
