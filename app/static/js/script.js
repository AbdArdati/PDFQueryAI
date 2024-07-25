async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, options);

        // Check if the response status is not OK
        if (!response.ok) {
            // Attempt to parse the error response
            let errorMessage = `Failed to fetch from ${url}. Status: ${response.status}`;

            try {
                // Try parsing the response as JSON
                const errorData = await response.json();
                errorMessage += `. Response: ${errorData.message || errorData.error || 'Unknown error'}`;
            } catch {
                // If JSON parsing fails, fall back to plain text response
                errorMessage += `. Response: ${await response.text()}`;
            }

            throw new Error(errorMessage);
        }

        // Try parsing JSON, if applicable
        try {
            return await response.json();
        } catch (jsonError) {
            throw new Error(`Failed to parse JSON response from ${url}. Response: ${await response.text()}`);
        }
    } catch (error) {
        console.error('API request error:', error.message);
        throw error; // Re-throw error to be handled by the calling function
    }
}


async function uploadPDF() {
    const fileInput = document.getElementById('pdfFile');
    const file = fileInput.files[0];

    if (!file) return showToast('Please select a PDF file to upload.');

    const formData = new FormData();
    formData.append('file', file);

    try {
        const result = await apiRequest('/pdf', {
            method: 'POST',
            body: formData,
        });

        const { status, filename, doc_len, chunk_len, error } = result;
        if (status === 'Successfully Uploaded') {
            showToast(`Success: ${status}\nFilename: ${filename}\nLoaded ${doc_len} documents\nLoaded len=${chunk_len} chunks`, type = 'success');
            
            // Call listPDFs function after successful upload
            listPDFs();
        } else {
            showToast(error || 'An error occurred during the upload.', type = 'error');
        }
    } catch (error) {
        // Display only the error message for 400 Bad Request
        const errorMessage = error.message.includes('Status: 400') 
            ? `${error.message.split('Response: ')[1]}`
            : `An error occurred while uploading the PDF: ${error.message}`;

        showToast(errorMessage, type = 'error');
    }
}


// Function to clear chat history
async function clearChatHistory() {
    try {
        const data = await apiRequest('/clear_chat_history', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        });

        const statusElement = document.getElementById('chatHistoryStatus');
        statusElement.innerText = data.status === "Chat history cleared successfully" ? 'Chat history cleared successfully.' : 'Failed to clear chat history.';
        statusElement.classList.remove('fade-out');

        setTimeout(() => statusElement.classList.add('fade-out'), 1500);
    } catch (error) {
        const statusElement = document.getElementById('chatHistoryStatus');
        statusElement.innerText = `An error occurred while clearing chat history: ${error.message}`;
        statusElement.classList.remove('fade-out');
    }

}
// Function to list PDFs
async function listPDFs() {
    try {
        const result = await apiRequest('/list_documents');

        const pdfList = document.getElementById('pdfList');
        pdfList.innerHTML = '';

        if (result.documents && result.documents.length > 0) {
            const seenPDFs = new Set();
            result.documents.forEach(doc => {
                const source = doc.source;
                if (!seenPDFs.has(source)) {
                    seenPDFs.add(source);

                    const listItem = document.createElement('div');
                    listItem.className = 'pdf-item'; // Apply the new class
                    listItem.textContent = source;

                    const buttonContainer = document.createElement('div');
                    buttonContainer.className = 'button-container';

                    buttonContainer.appendChild(createButton('View', 'btn view-button', () => window.open(`/pdfs/${source}`, '_blank').focus()));
                    buttonContainer.appendChild(createButton('Delete', 'btn delete-button', () => deletePDF(source)));

                    listItem.appendChild(buttonContainer);
                    pdfList.appendChild(listItem);
                }
            });
        } else {
            pdfList.innerHTML = '<li>No documents found.</li>';
        }
    } catch (error) {
        console.error('Error during listPDFs:', error);
        showToast('An error occurred while listing documents. Please try again later.', type = 'error');
    }
}


// Create a button with text, class, and click handler
function createButton(text, className, onClick) {
    const button = document.createElement('button');
    button.textContent = text;
    button.className = className;
    button.onclick = onClick;
    return button;
}

// Function to copy text from PDF field and submit to AI
async function copyTextAndSubmit() {
    const pdfText = document.getElementById('queryPDF').value;
    document.getElementById('query').value = pdfText;
    document.querySelector('.query-section button[onclick="askAI()"]').click();
}

// Function to delete a PDF
async function deletePDF(fileName) {
    if (!confirm(`Are you sure you want to delete ${fileName}?`)) return;

    try {
        const result = await apiRequest('/delete_pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_name: fileName }),
        });

        if (result.status === 'success') {
            showToast('PDF deleted successfully.', type = 'success');
            listPDFs();
        } else {
            showToast('Failed to delete PDF: ' + (result.error || 'Unknown error'), type = 'error');
        }
    } catch (error) {
        showToast('An error occurred while deleting the PDF: ' + error.message, type = 'error');
    }
}

// Function to clear the database
async function clearDatabase() {
    if (!confirm('Are you sure you want to delete all PDFs and clear the database?')) return;

    try {
        const result = await apiRequest('/clear_db', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        showToast(result.error ? `Error: ${result.error}` : 'Database and files cleared successfully', type = 'success');

        // Call listPDFs function after successful database clearance
        if (!result.error) {
            listPDFs();
        }
    } catch (error) {
        showToast('Network Error: ' + error.message, type = 'error');
    }
}


async function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.textContent = message;

    // Apply base styles
    toast.style.position = 'fixed';
    toast.style.top = '5%'; // Center vertically
    toast.style.left = '50%'; // Center horizontally
    toast.style.transform = 'translate(-50%, -50%)';
    toast.style.padding = '25px 30px';
    toast.style.borderRadius = '12x';
    toast.style.color = '#fff';
    toast.style.fontFamily = 'Arial, sans-serif';
    toast.style.fontSize = '24px';
    toast.style.zIndex = '1000';
    toast.style.boxShadow = '0 2px 4px rgba(0,0,0,0.3)';
    toast.style.transition = 'opacity 0.5s ease, top 0.5s ease'; // Add transition for top property

    // Style based on type
    switch (type) {
        case 'success':
            toast.style.backgroundColor = '#4CAF50'; // Green
            break;
        case 'error':
            toast.style.backgroundColor = '#F44336'; // Red
            break;
        case 'warning':
            toast.style.backgroundColor = '#FFC107'; // Yellow
            break;
        case 'info':
        default:
            toast.style.backgroundColor = '#2196F3'; // Blue
            break;
    }

    // Append toast to the body
    document.body.appendChild(toast);

    // Animate toast appearance
    toast.style.opacity = '1';

    // Remove the toast after a timeout
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.top = '45%'; // Move up slightly before disappearing
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 500); // Allow time for fade-out animation
    }, 3000); // Toast disappears after 3 seconds
}

function handleNavigation(event) {
    // Check if the spinner is still visible
    var spinner = document.querySelector('.spinner');
    if (spinner) {
        // Show a confirmation dialog to the user
        var confirmNavigation = confirm("You have an ongoing process. If you leave now, you may not get the answer you are waiting for. Do you want to continue?");
        if (!confirmNavigation) {
            // Prevent the default action if the user does not confirm
            event.preventDefault();
        }
    }
}

// Select all response containers and resize handles
const responseContainers = document.querySelectorAll('.response-container');
const resizeHandles = document.querySelectorAll('.resize-handle');

resizeHandles.forEach((resizeHandle, index) => {
    let isResizing = false;
    let startY, startHeight;

    resizeHandle.addEventListener('mousedown', (event) => {
        isResizing = true;
        startY = event.clientY;
        startHeight = parseInt(document.defaultView.getComputedStyle(responseContainers[index].querySelector('.response')).height, 10);

        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', stopResizing);
    });

    function handleMouseMove(event) {
        if (isResizing) {
            let newHeight = startHeight + (event.clientY - startY);

            if (newHeight < 100) { // Optional: Minimum height constraint
                newHeight = 100;
            }
            responseContainers[index].querySelector('.response').style.height = `${newHeight}px`;
        }
    }

    function stopResizing() {
        isResizing = false;
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', stopResizing);
    }
});
