// Function to make API requests
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, options);

        // Check if the response status is not OK
        if (!response.ok) {
            const errorText = await response.text(); // Read response text for debugging
            throw new Error(`Failed to fetch from ${url}. Status: ${response.status}. Response: ${errorText}`);
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

// Function to copy text from PDF field and submit to AI
async function copyTextAndSubmit() {
    const pdfText = document.getElementById('queryPDF').value;
    document.getElementById('query').value = pdfText;
    await askAI(); // Call askAI directly since it's defined in this file
}

// Function to ask AI a question
async function askAI() {
    console.log('askAI called'); // Debug log
    const query = document.getElementById('query').value;
    const responseDiv = document.getElementById('queryResponseAI');

    if (!query) {
        alert('Please enter a query.');
        return;
    }

    responseDiv.innerHTML = '<div class="spinner"></div><p class="loading-message">Fetching response, please wait...</p>';

    try {
        const result = await apiRequest('/ai', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query }),
        });

        responseDiv.innerHTML = `<p>${await markdownToHTML(result.answer) || result.error}</p>`;
    } catch (error) {
        responseDiv.innerHTML = `<p>An error occurred while processing the query: ${error.message}</p>`;
    }
}

// Function to ask about PDF
async function askPDF() {
    console.log('askPDF called'); // Debug log
    const query = document.getElementById('queryPDF').value;
    const responseDiv = document.getElementById('queryResponse');
    const promptType = document.getElementById('promptType').value;

    if (!query) {
        alert('Please enter a query.');
        return;
    }

    responseDiv.innerHTML = '<div class="spinner"></div><p class="loading-message">Fetching response, please wait...</p>';

    try {
        const result = await apiRequest('/ask_pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, promptType }),
        });

        if (result.disclaimer) {
            responseDiv.innerHTML = `<p>${result.disclaimer}</p>`;
        } else {
            responseDiv.innerHTML = `<p>${await markdownToHTML(result.answer) || result.error}</p>`;
        }

        if (result.pdf_usage) displayPDFUsage(result.pdf_usage);
        if (result.query_usage) displayQueryUsage(result.query_usage);
    } catch (error) {
        responseDiv.innerHTML = `<p>An error occurred while processing the PDF query: ${error.message}</p>`;
    }
}

// Function to display PDF usage statistics
function displayPDFUsage(pdfUsage) {
    const usageDiv = document.getElementById('pdfUsageStats');
    usageDiv.innerHTML = '<h3>PDF Usage Statistics In Total</h3>';

    if (Object.keys(pdfUsage).length === 0) {
        usageDiv.innerHTML += '<p>No usage statistics available.</p>';
        return;
    }

    usageDiv.innerHTML += '<ul>' + Object.entries(pdfUsage).map(([pdf, data]) => 
        `<li>${pdf}: ${data.count} queries (${data.percentage.toFixed(2)}%)</li>`
    ).join('') + '</ul>';
}

// Function to display query usage statistics
function displayQueryUsage(queryUsage) {
    const usageDiv = document.getElementById('queryUsageStats');
    usageDiv.innerHTML = '<h3>PDF Usage Statistics Per Query</h3>';

    if (Object.keys(queryUsage).length === 0) {
        usageDiv.innerHTML += '<p>No usage statistics available.</p>';
        return;
    }

    usageDiv.innerHTML += '<ul>' + Object.entries(queryUsage).map(([pdf, data]) => 
        `<li>${pdf}: ${data.count} queries (${data.percentage.toFixed(2)}%)</li>`
    ).join('') + '</ul>';
}

// Function to convert markdown to HTML
async function markdownToHTML(markdown) {
    if (!markdown) return '';

    let html = markdown
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold
        .replace(/\n{2,}/g, '</p><p>') // Paragraphs
        .replace(/\n/g, '<br>') // New lines
        .replace(/\t/g, '&nbsp;&nbsp;&nbsp;&nbsp;') // Tabs
        .replace(/^(\d+)\.\s+(.*)$/gm, (match, number, text) => `<p>${number}. ${text}</p>`) // Numbered lists
        .replace(/^\*\s+(.*)$/gm, (match, text) => `<ul><li>${text}</li></ul>`) // Bullet lists
        .replace(/<\/ul>\s*<ul>/g, '</ul><ul>') // Nested lists
        .replace(/<\/li>\s*<li>/g, '</li><li>') // List items
        .replace(/<\/ul>\s*<\/li>/g, '</ul></li>'); // Nested lists closing

    return `<p>${html.replace(/<\/p>\s*<p>/g, '</p><p>').replace(/<p>\s*<\/p>/g, '')}</p>`;
}

// Event listeners for form submission on Enter key press
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOMContentLoaded fired'); // Debug log

    const queryPDFInput = document.getElementById('queryPDF');
    const queryPDFButton = document.getElementById('askPDFButton');
    if (queryPDFInput && queryPDFButton) {
        queryPDFInput.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                queryPDFButton.click();
            }
        });
    } else {
        console.log('queryPDFInput or queryPDFButton is missing'); // Debug log
    }

    const queryInput = document.getElementById('query');
    const queryButton = document.getElementById('askAIButton');
    if (queryInput && queryButton) {
        queryInput.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                queryButton.click();
            }
        });
    } else {
        console.log('queryInput or queryButton is missing'); // Debug log
    }

    const copyPromptButton = document.getElementById('copyPromptButton');
    if (copyPromptButton) {
        copyPromptButton.addEventListener('click', copyTextAndSubmit);
    } else {
        console.log('copyPromptButton is missing'); // Debug log
    }

    // Fetch prompts when the page is loaded
    fetchPrompts();
});

// Function to fetch prompts from the server
async function fetchPrompts() {
    try {
        const prompts = await apiRequest('/prompts');
        const selectElement = document.getElementById('promptType');

        if (selectElement) {
            selectElement.innerHTML = '';
            for (const [key] of Object.entries(prompts)) {
                const option = document.createElement('option');
                option.value = key;
                option.textContent = key;
                selectElement.appendChild(option);
            }
        } else {
            console.error('Prompt type select element is missing in the DOM.');
        }
    } catch (error) {
        console.error('Error fetching prompts:', error);
    }
}
