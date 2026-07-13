// Pre-flight server check
async function checkServerHealth() {
    const overlay = document.getElementById('loading-overlay');
    if (!overlay) return;

    try {
        // Ping the hypothetical FastAPI backend endpoint
        const response = await fetch('/api/health', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            // 200 OK - Server is awake
            overlay.classList.add('hidden');

            // Initialize graph with empty or default data here
            if (typeof window.initGraph === 'function') {
                window.initGraph({ nodes: [], links: [] });
            }
        } else if (response.status === 503) {
            // Cold start
            console.log("Server cold start detected (503). Retrying...");
            setTimeout(checkServerHealth, 3000);
        } else {
            // Other error
            console.error(`Unexpected server response: ${response.status}`);
            overlay.querySelector('h2').innerText = "Cluster initialization failed.";
            overlay.querySelector('.spinner').style.borderColor = "#ff0000";
        }
    } catch (error) {
        // Timeout or network error
        console.error("Health check failed:", error);
        // We simulate a retry loop in case it's waking up
        setTimeout(checkServerHealth, 3000);
    }
}

// Bind to window and execute on load
window.checkServerHealth = checkServerHealth;

document.addEventListener('DOMContentLoaded', () => {
    // Attempt health check on initial load
    // In a real environment, you might wait to show UI, here we try immediately
    checkServerHealth();
});
