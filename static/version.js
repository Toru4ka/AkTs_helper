document.addEventListener("DOMContentLoaded", async () => {
    try {
        const response = await fetch('/version');
        const versionDisplay = document.getElementById('versionDisplay');
        if (response.ok) {
            const version = await response.text();
            versionDisplay.textContent = `Version: ${version}`;
        } else {
            versionDisplay.textContent = 'Version: Unknown';
        }
    } catch (error) {
        console.error('Error fetching version:', error);
        const versionDisplay = document.getElementById('versionDisplay');
        if (versionDisplay) {
            versionDisplay.textContent = 'Version: Error';
        }
    }
});
