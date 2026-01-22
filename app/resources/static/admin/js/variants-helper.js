/**
 * Variants Helper Functions
 * 
 * This module provides utility functions for working with product variants
 * in the admin interface.
 */

/**
 * Validates variant data before submission
 * @param {Array} variants - Array of variant objects
 * @returns {Object} - {valid: boolean, errors: Array}
 */
function validateVariants(variants) {
	const errors = [];
	
	if (!variants || variants.length === 0) {
		return { valid: true, errors: [] }; // Variants are optional
	}
	
	variants.forEach((variant, index) => {
		if (!variant.price_ngn || variant.price_ngn <= 0) {
			errors.push(`Variant ${index + 1} (${variant.name}): Price (NGN) is required and must be greater than 0`);
		}
		
		if (variant.quantity < 0) {
			errors.push(`Variant ${index + 1} (${variant.name}): Quantity cannot be negative`);
		}
	});
	
	return {
		valid: errors.length === 0,
		errors
	};
}

/**
 * Formats variant data for display
 * @param {Object} variant - Variant object
 * @returns {string} - Formatted display string
 */
function formatVariantDisplay(variant) {
	const parts = [];
	
	if (variant.price_ngn) {
		parts.push(`₦${parseFloat(variant.price_ngn).toLocaleString()}`);
	}
	
	if (variant.price_usd) {
		parts.push(`$${parseFloat(variant.price_usd).toFixed(2)}`);
	}
	
	if (variant.quantity !== undefined) {
		parts.push(`Qty: ${variant.quantity}`);
	}
	
	return parts.join(' | ') || 'Not configured';
}

/**
 * Checks if all variants have required data
 * @param {Array} variants - Array of variant objects
 * @returns {boolean}
 */
function allVariantsConfigured(variants) {
	if (!variants || variants.length === 0) return true;
	
	return variants.every(v => v.price_ngn && v.price_ngn > 0);
}

/**
 * Gets a summary of variants for display
 * @param {Array} variants - Array of variant objects
 * @returns {Object} - Summary statistics
 */
function getVariantsSummary(variants) {
	if (!variants || variants.length === 0) {
		return {
			total: 0,
			configured: 0,
			unconfigured: 0,
			totalInventory: 0
		};
	}
	
	const configured = variants.filter(v => v.price_ngn && v.price_ngn > 0);
	const totalInventory = variants.reduce((sum, v) => sum + (v.quantity || 0), 0);
	
	return {
		total: variants.length,
		configured: configured.length,
		unconfigured: variants.length - configured.length,
		totalInventory
	};
}

// Export for use in other modules if needed
if (typeof module !== 'undefined' && module.exports) {
	module.exports = {
		validateVariants,
		formatVariantDisplay,
		allVariantsConfigured,
		getVariantsSummary
	};
}

