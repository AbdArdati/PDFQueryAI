<p align="center">
  <img src="https://github.com/AbdArdati/PDFQueryAI/blob/main/app/static/images/full_logo_cropped.png">
</p>

# AskItRight: AI-Powered PDF Query Application 🚀

This repository contains a Flask web application that allows users to upload PDF documents, query their contents, and retrieve answers using an AI language model. The application integrates several functionalities to manage PDFs, handle user queries, and maintain usage statistics.

## High-Level Overview 🌟

The application provides an interface for:
- 📄 **Uploading and managing PDF documents**.
- ❓ **Submitting queries to retrieve information from uploaded PDFs**.
- 📊 **Tracking PDF usage statistics**.
- 🔧 **Performing administrative operations like clearing data and deleting files**.
- 🔍 **Viewing PDF files**
- 📝 **Prompt templates management**

### Key Features 🔑

1. **PDF Management**:
   - **Upload PDFs**: 📤 Users can upload PDF files through the upload interface. These files are processed and stored in the system.
   - **List PDFs**: 📋 Users can view a list of all uploaded PDF files through the available PDFs interface.
   - **Delete PDFs**: 🗑️ Users can remove specific PDF files using the delete functionality available in the PDF management interface.
   - **View PDFs**: 👁️ Users can open and view the content of PDF files in a new browser tab directly from the list of PDFs.

2. **Query Handling**:
   - **Ask Questions to PDF**: 🤔 Users can submit questions about the content of uploaded PDFs using the query interface. The application uses the AI model to provide answers based on the PDF contents.
   - **AI Integration**: 🤖 The Ollama3.1 model is used to generate answers to queries from the content of the PDFs. This functionality is accessible through the AI query interface.
  - **Prompt Templates**: 📝 Users can view and select from various prompt templates to guide the AI's responses, ensuring they are tailored to specific needs. (Currently in progress, with frontend Create, Update, and Delete to be implemented.)

3. **Statistics and Administration**:
   - **Clear Chat History**: 🧹 Users can clear previous chat interactions using the clear chat history button in the query section.
   - **Clear Database**: 🚮 Deletes all stored PDFs and related data, effectively resetting the application’s state. This action is available in the database management section.
   - **PDF Usage Statistics**: 📈 Provides information on how frequently each PDF has been queried, viewable through the statistics dashboard.

### HTML Interfaces Overview 🖥️

1. **Document Interaction Dashboard**:
   - **Homepage**: 🏠 Features interfaces for asking questions about PDF content and interacting with the Ollama3.1 AI model. It also displays query and PDF usage statistics.
   - **PDF Query Section**: ❓ Allows users to submit questions about PDFs and view responses.
   - **AI Query Section**: 🤖 Provides functionality to query the Ollama3.1 AI model independently of PDFs.
   - **Statistics Section**: 📊 Displays usage statistics for both queries and PDFs.

2. **PDF Management and Statistics**:
   - **Upload and List PDFs**: 📤📋 An interface to upload new PDFs, view a list of all uploaded PDFs, and access each PDF file.
   - **Database Management**: 🗑️ Provides options to clear the database and manage stored PDFs.
   - **Statistics Dashboard**: 📈 Shows statistics related to the total number of PDFs and documents in the vector store.

### Examples

| Image | Description |
|-------|-------------|
| <img src="https://github.com/AbdArdati/PDFQueryAI/blob/main/app/static/images/Home_Example_1.png" alt="Home Example" width="400" /> | This screenshot shows the functionality of using PDFs with the 'Essay Expert' prompt template. At the top, the system leverages PDF content for detailed responses, while the lower section illustrates responses generated without PDFs. |
| <img src="https://github.com/AbdArdati/PDFQueryAI/blob/main/app/static/images/Home_Example_2.png" alt="Home Example" width="400" /> | This example demonstrates the advanced capabilities of the 'Essays Expert' prompt template. The screenshot highlights how the system utilises PDF content to generate comprehensive responses at the top, while the lower section shows the output generated without PDFs, illustrating the impact of including detailed content. |
| <img src="https://github.com/AbdArdati/PDFQueryAI/blob/main/app/static/images/Home_Example_3.png" alt="Home Example" width="400" /> | This screenshot reveals the limitations of the current app, indicating that it may struggle with queries beyond the scope of the provided documents. It underscores the need for further improvements and extensive testing to enhance the model's accuracy and robustness. |
| <img src="https://github.com/AbdArdati/PDFQueryAI/blob/main/app/static/images/PDF_Management_Eaxmple.png" alt="Home Example" width="400" /> | This screenshot demonstrates the PDF Management & Statistics Dashboard, showcasing how users can view detailed statistics related to the uploaded PDFs and documents within the system. |

## Installation Instructions ⚙️

### System Requirements 🖥️

For Ollama3.1 8B, ensure your system has at least 16 GB of RAM, and reasonable disk space for a reasonable performance; a GPU is recommended for models with 70B parameters or higher.

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
   ollama run llama3.1
   ```
  When you run `ollama run llama3.1`, it defaults to using configuration 8b unless you specify otherwise.

### 2. **Clone the Repository**:
    
    git clone https://github.com/AbdArdati/PDFQueryAI.git
    cd PDFQueryAI 

### 3. **Create a Virtual Environment**:
    
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`

### 4. **Install Dependencies**:
    
    pip install -r requirements.txt

### 5. **Run the Application**:
     
    python app.py

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

### Release Information 🚀

**Current Version:** `v1.0.0-beta`

**Release Date:** `25/07/2024`

**Description:** This is the beta release of AskItRight. It includes features for uploading, managing, and querying PDF documents using an AI model, as well as basic statistics and administrative functionalities.

**Changelog:**
- Initial beta release with core functionalities.
- Added PDF upload, query, and management features.
- Integrated AI model for querying PDF content.
- Implemented basic statistics and database management features.

### Summary 📝

Overall, the application provides a structured way to manage and interact with PDF documents using an AI model. It integrates file management, data processing, and querying capabilities into a Flask web service, allowing users to upload, query, and manage PDFs while also keeping track of usage statistics and providing administrative functionalities.


### Disclaimer 📝
Please be aware that this application is provided "as is," without any guarantee of functionality or reliability. It's important to note that the codebase may not adhere to best practices in terms of tidiness and organisation, and there is significant room for improvement and bug fixes. While I try to enhance the application, I plan to release a new version in the future as time permits. 

The developers disclaim all responsibility for bugs or issues, stating use is at one's own risk. Users are encouraged to contribute but the developers are not liable for any damages from using the application.

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

---
**Developed by Abd Alsattar Ardati for the sake of exploring, learning, and sharing.**  
Visit my [website](https://abd.ardati.org) for more information or contact me at abd.alsattar.ardati @ gmail.