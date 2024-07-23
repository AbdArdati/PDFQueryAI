async function uploadPDF() {
    const fileInput = document.getElementById('pdfFile');
    const file = fileInput.files[0];

    if (!file) {
        alert('Please select a PDF file to upload.');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/pdf', {
            method: 'POST',
            body: formData,
        });

        const result = await response.json();
        if (result.status === 'Successfully Uploaded') {
            alert(`Success: ${result.status}\nFilename: ${result.filename}\nLoaded ${result.doc_len} documents\nLoaded len=${result.chunk_len} chunks`);
        } else {
            alert(result.error || 'An error occurred during the upload.');
        }
    } catch (error) {
        alert('An error occurred while uploading the PDF.');
    }
}

async function askAI() {
    const queryInput = document.getElementById('query');
    const query = queryInput.value;
    const responseDiv = document.getElementById('queryResponseAI');

    if (!query) {
        alert('Please enter a query.');
        return;
    }

    // Show loading spinner and message
    responseDiv.innerHTML = '<div class="spinner"></div><p class="loading-message">Fetching response, please wait...</p>';
    
    try {
        const response = await fetch('/ai', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query }),
        });

        const result = await response.json();
        responseDiv.innerHTML = `<p>${result.answer || result.error}</p>`;
    } catch (error) {
        responseDiv.innerHTML = '<p>An error occurred while processing the query.</p>';
    }
}

async function askPDF() {
    const queryInput = document.getElementById('queryPDF');
    const query = queryInput.value;
    const responseDiv = document.getElementById('queryResponse');

    if (!query) {
        alert('Please enter a query.');
        return;
    }

    // Show loading spinner and message
    responseDiv.innerHTML = '<div class="spinner"></div><p class="loading-message">Fetching response, please wait...</p>';

    try {
        const response = await fetch('/ask_pdf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query }),
        });

        const result = await response.json();

        if (result.disclaimer) {
            responseDiv.innerHTML = `<p>${result.disclaimer}</p>`;
        } else {
            responseDiv.innerHTML = `<p>${result.answer || result.error}</p>`;
        }

        // Display PDF usage information if available
        if (result.pdf_usage) {
            displayPDFUsage(result.pdf_usage);
        }

        // Display query usage information if available
        if (result.query_usage) {
            displayQueryUsage(result.query_usage);
        }
    } catch (error) {
        responseDiv.innerHTML = '<p>An error occurred while processing the PDF query.</p>';
    }
}

async function clearChatHistory() {
    fetch('/clear_chat_history', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        const statusElement = document.getElementById('chatHistoryStatus');
        
        if (data.status === "Chat history cleared successfully") {
            statusElement.innerText = 'Chat history cleared successfully.';
        } else {
            statusElement.innerText = 'Failed to clear chat history.';
        }
    
        // Set a timeout to start the fade-out effect after 5 seconds
        setTimeout(() => {
            statusElement.classList.add('fade-out');
        }, 5000);
    })    
    .catch(error => {
        document.getElementById('chatHistoryStatus').innerText = 'An error occurred while clearing chat history.';
        console.error('Error:', error);
    });
}
// async function listPDFs() {
//     try {
//         const response = await fetch('/list_pdfs', {
//             method: 'GET',
//         });

//         const result = await response.json();
//         const pdfList = document.getElementById('pdfList');
//         pdfList.innerHTML = '';

//         if (result.pdf_files && result.pdf_files.length > 0) {
//             result.pdf_files.forEach(pdf => {
//                 const listItem = document.createElement('li');
//                 listItem.textContent = pdf;
//                 const deleteButton = document.createElement('button');
//                 deleteButton.textContent = 'Delete';
//                 deleteButton.onclick = () => deletePDF(pdf);
//                 listItem.appendChild(deleteButton);
//                 pdfList.appendChild(listItem);
//             });
//         } else {
//             pdfList.innerHTML = '<li>No PDFs found.</li>';
//         }
//     } catch (error) {
//         alert('An error occurred while listing PDFs.');
//     }
//}
async function listPDFs() {
    try {
        const response = await fetch('/list_documents', {
            method: 'GET',
        });

        const result = await response.json();
        const pdfList = document.getElementById('pdfList');
        pdfList.innerHTML = '';

        if (response.ok) {
            if (result.documents && result.documents.length > 0) {
                // Use a Set to keep track of seen PDFs and avoid duplicates
                const seenPDFs = new Set();

                result.documents.forEach(doc => {
                    const source = doc.source;

                    // Skip if this PDF has already been listed
                    if (!seenPDFs.has(source)) {
                        seenPDFs.add(source);

                        const listItem = document.createElement('li');
                        listItem.textContent = source;

                        // Add a delete button for each PDF
                        const deleteButton = document.createElement('button');
                        deleteButton.textContent = 'Delete';
                        deleteButton.onclick = () => deletePDF(source);
                        
                        listItem.appendChild(deleteButton);
                        pdfList.appendChild(listItem);
                    }
                });
            } else {
                pdfList.innerHTML = '<li>No documents found.</li>';
            }
        } else {
            alert('An error occurred while listing documents. Please try again later.');
        }
    } catch (error) {
        alert('An error occurred while listing documents. Please try again later.');
    }
}


async function deletePDF(fileName) {
    if (!confirm(`Are you sure you want to delete ${fileName}?`)) {
        return;
    }

    try {
        const response = await fetch('/delete_pdf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ file_name: fileName }),
        });

        const result = await response.json();
        if (result.status === 'success') {
            alert('PDF deleted successfully.');
            listPDFs(); // Refresh the list
        } else {
            alert('Failed to delete PDF: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        alert('An error occurred while deleting the PDF.');
    }
}

async function clearDatabase() {
    if (!confirm(`Are you sure you want to delete all PDFs and clear the database?`)) {
        return;
    }
    try {
        const response = await fetch('/clear_db', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const result = await response.json();
        if (response.ok) {
            alert('Database and files cleared successfully');
        } else {
            alert(`Error: ${result.error}`);
        }
    } catch (error) {
        alert(`Network Error: ${error.message}`);
    }
}

async function listPDFUsageOld() {
    try {
        const response = await fetch('/pdf_usage', {
            method: 'GET',
        });

        const result = await response.json();
        const pdfUsageStats = document.getElementById('pdfUsageStats');
        pdfUsageStats.innerHTML = '';

        if (result.pdf_usage && Object.keys(result.pdf_usage).length > 0) {
            Object.entries(result.pdf_usage).forEach(([pdf, { count, percentage }]) => {
                const usageItem = document.createElement('p');
                usageItem.textContent = `${pdf}: Used ${count} times, Influence: ${percentage.toFixed(2)}%`;
                pdfUsageStats.appendChild(usageItem);
            });
        } else {
            pdfUsageStats.innerHTML = '<p>No usage statistics available.</p>';
        }
    } catch (error) {
        alert('An error occurred while fetching PDF usage statistics.');
    }
}

function displayPDFUsage(pdfUsage) {
    const usageDiv = document.getElementById('pdfUsageStats');
    usageDiv.innerHTML = '<h3>PDF Usage Statistics In Total</h3>';

    if (Object.keys(pdfUsage).length === 0) {
        usageDiv.innerHTML += '<p>No usage statistics available.</p>';
        return;
    }

    let usageHTML = '<ul>';
    for (const [pdf, data] of Object.entries(pdfUsage)) {
        usageHTML += `<li>${pdf}: ${data.count} queries (${data.percentage.toFixed(2)}%)</li>`;
    }
    usageHTML += '</ul>';

    usageDiv.innerHTML += usageHTML;
}

function displayQueryUsage(queryUsage) {
    const usageDiv = document.getElementById('queryUsageStats');
    usageDiv.innerHTML = '<h3>PDF Usage Statistics Per Query</h3>';

    if (Object.keys(queryUsage).length === 0) {
        usageDiv.innerHTML += '<p>No usage statistics available.</p>';
        return;
    }

    let usageHTML = '<ul>';
    for (const [pdf, data] of Object.entries(queryUsage)) {
        usageHTML += `<li>${pdf}: ${data.count} queries (${data.percentage.toFixed(2)}%)</li>`;
    }
    usageHTML += '</ul>';

    usageDiv.innerHTML += usageHTML;
}

document.addEventListener('DOMContentLoaded', () => {
    const inputField = document.getElementById('queryPDF');
    const submitButton = document.querySelector('button[onclick="askPDF()"]');

    inputField.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault(); // Prevent the default action
            submitButton.click(); // Programmatically click the Submit button
        }
    });
});