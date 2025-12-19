/**
 * Alert Management Module
 * @module AlertManager
 * @description Handles the display and management of system alerts using Flowbite framework
 */


// Initialize Flowbite dismiss on page load
document.addEventListener("DOMContentLoaded", function () {
	initializeAlerts();
});


/**
 * Initializes all dismissible alerts on the page
 * @function initializeAlerts
 * @description Sets up dismiss functionality for both manual close buttons and auto-dismiss timers
 * @listens DOMContentLoaded
 * @listens turbo:render (if using Turbo/Hotwire)
 * 
 * For each alert element:
 * 1. Creates Flowbite Dismiss instance with cleanup callback
 * 2. Sets up auto-dismiss timer if data-auto-dismiss attribute exists
 * 
 * @example
 * // HTML element requirements
 * <div id="alert-1" data-auto-dismiss="5000">
 *   <button data-dismiss-target="#alert-1">Close</button>
 * </div>
 */
function initializeAlerts() {
	// Initialize Flowbite dismiss
	document.querySelectorAll("[data-dismiss-target]").forEach((button) => {
		const alert = document.querySelector(button.dataset.dismissTarget);
        if (!alert) return;

		
		// Create new Dismiss instance
		const dismiss = new Dismiss(alert, button, {
			transition: "transition-opacity",
			duration: 2000,
			timing: "ease-in-out",
            onHide: () => {
                // Wait for transition to complete before removal
                alert.addEventListener('transitionend', () => {
                    alert.remove();
                }, { once: true });

                // Fallback removal in case transition doesn't fire
                setTimeout(() => {
					if (document.body.contains(alert)) {
						alert.remove();
					}
				}, 500);

                
            }
		});

		// Auto-dismiss logic
        const timeout = parseInt(alert.dataset.autoDismiss) || 5000;

        timeout && setTimeout(() => dismiss.hide(), timeout);
	});
}

/**
 * Creates and displays a new alert message
 * @function toggleAlert
 * @description Dynamically generates and displays alert messages with optional auto-dismiss
 * 
 * @param {string} message - The text content to display in the alert
 * @param {string} [category="info"] - Alert type category (determines styling/icon)
 * @param {Object} [options={}] - Configuration options
 * @param {number} [options.timeout=5000] - Auto-dismiss timeout in milliseconds (0 = no auto-dismiss)
 * @param {boolean} [options.loginLink=false] - Whether to show a login link
 * 
 * @example
 * // Create success alert with 3s auto-dismiss
 * toggleAlert('Operation successful', 'success', { timeout: 3000 });
 * 
 * @example
 * // Create persistent error alert with login link
 * toggleAlert('Session expired', 'error', { 
 *   timeout: 0,
 *   loginLink: true 
 * });
 */
function toggleAlert(message, category = "info", options = {}) {
	const alertBox = document.getElementById("alert-box");
	const alertId = `alert-${Date.now()}`;

	const alertHTML = `
    <div id="${alertId}" class="flex alert-${category} gap-x-4 min-w-96 items-center p-4 rounded-lg bg-gray-800 pointer-events-auto"
        role="alert" data-auto-dismiss="${options.timeout || 5000}">
        
        ${getAlertIcon(category)}

        <span class="sr-only">${category}</span>
        
        <div class="ms-3 text-sm font-medium" id="alert-message-${Date.now()}">
            ${sanitizeHTML(message)}
            ${
				options.loginLink
					? '<a href="/login" class="font-semibold underline hover:no-underline">Login</a>'
					: ""
			}
        </div>

        <button type="button" 
                class="ms-auto -mx-1.5 -my-1.5 rounded-lg focus:ring-2 focus:ring-alert-{{ category }}-solid p-1.5 inline-flex items-center justify-center h-8 w-8 hover:bg-gray-800/10"
                data-dismiss-target="#${alertId}" aria-label="Close">
            <span class="sr-only">Close</span>
            ${getAlertIcon("close")}
        </button>
    </div>
    `;

	// Add to DOM
	alertBox.insertAdjacentHTML("afterbegin", alertHTML);

	initializeAlerts(); // Re-run initialization
}

// Helper function to sanitize messages
function sanitizeHTML(str) {
	const div = document.createElement("div");
	div.textContent = str;
	return div.innerHTML;
}


/**
 * Provides appropriate SVG icons for alert types
 * @function getAlertIcon
 * @description Returns SVG markup for different alert categories
 * 
 * @param {string} category - Alert category type
 * @returns {string} SVG markup string
 * @throws {Error} If unknown category provided, defaults to 'info'
 * 
 * Supported categories:
 * - error: Red X icon
 * - success: Green checkmark
 * - info: Blue info icon
 * - close: Default close icon
 * 
 * @example
 * const icon = getAlertIcon('success');
 */
function getAlertIcon(category) {
	const icons = {
		error: `<svg class="flex-shrink-0 w-4 h-4"" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor"
                    viewBox="0 0 24 24">
                    <path fill-rule="evenodd" d="M2 12C2 6.477 6.477 2 12 2s10 4.477 10 10-4.477 10-10 10S2 17.523 2 12Zm7.707-3.707a1 1 0 0 0-1.414 1.414L10.586 12l-2.293 2.293a1 1 0 1 0 1.414 1.414L12 13.414l2.293 2.293a1 1 0 0 0 1.414-1.414L13.414 12l2.293-2.293a1 1 0 0 0-1.414-1.414L12 10.586 9.707 8.293Z" clip-rule="evenodd"/>
                </svg>
`,
		success: `<svg class="flex-shrink-0 w-4 h-4" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor"
                    viewBox="0 0 24 24">
                    <path fill-rule="evenodd" d="M2 12C2 6.477 6.477 2 12 2s10 4.477 10 10-4.477 10-10 10S2 17.523 2 12Zm13.707-1.293a1 1 0 0 0-1.414-1.414L11 12.586l-1.793-1.793a1 1 0 0 0-1.414 1.414l2.5 2.5a1 1 0 0 0 1.414 0l4-4Z" clip-rule="evenodd"/>
                </svg>
`,
		info: `<svg class="flex-shrink-0 w-4 h-4" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor"
                    viewBox="0 0 20 20">
                    <path
                        d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5ZM9.5 4a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3ZM12 15H8a1 1 0 0 1 0-2h1v-3H8a1 1 0 0 1 0-2h2a1 1 0 0 1 1 1v4h1a1 1 0 0 1 0 2Z" />
                </svg>`,
		close: `<svg class="w-3 h-3" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 14 14">
                    <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m1 1 6 6m0 0 6 6M7 7l6-6M7 7l-6 6" />
                </svg>`,
		// Add other categories
	};
	return icons[category] || icons.info;
}
