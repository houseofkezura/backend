(function() {
	("use strict");

	/**
	 * Returns an object containing references to the category UI elements.
	 * This function should be called each time the UI elements are needed
	 * to ensure that the references are up-to-date.
	 */
	function getCategoryUI() {
		return {
			toggleBtn: document.querySelector("[data-category-toggle]"),
			catInputBlock: document.querySelector(
				"[data-category-input-block]"
			),
			newCatInput: document.querySelector("[data-category-input]"),
			selectParentField: document.querySelector("[data-parent-select]"),
			catCheckboxes: document.querySelector("[data-category-checkboxes]"),
			submitBtn: document.querySelector("[data-category-submit]"),
		};
	}

	// Initialize module
	function init() {
		if (!getCategoryUI().toggleBtn) return;

		setupEventListeners();
		getCategoryUI().catInputBlock.hidden = true;
	}

	function setupEventListeners() {
		const categoryUI = getCategoryUI(); // Get a fresh categoryUI object

		// Toggle category input block
		categoryUI.toggleBtn.addEventListener("click", toggleCatInputBlock);

		// Handle form submission
		categoryUI.submitBtn.addEventListener("click", handleSubmit);
	}

	/**
	 * Toggles the visibility of the category input block.
	 * Also updates the aria-expanded attribute of the toggle button.
	 */
	function toggleCatInputBlock() {
		const categoryUI = getCategoryUI(); // Get a fresh categoryUI object
		const isExpanded =
			categoryUI.toggleBtn.getAttribute("aria-expanded") === "true";
		categoryUI.toggleBtn.setAttribute("aria-expanded", !isExpanded);

		// toggle the cat-input-block
		categoryUI.catInputBlock.hidden = isExpanded;
		categoryUI.catInputBlock.classList.toggle("hidden");
	}

	/**
	 * Updates the parent category select field with the provided HTML.
	 * @param {string} selectField - The HTML string containing the new select field.
	 */
	function updateParentSelect(selectField) {
		const selectParentField = document.querySelector(
			"[data-parent-select]"
		); // Re-query the DOM

		if (!selectParentField) {
			console.error("Select element not found in the DOM.");
			return;
		}

		const template = document.createElement("template");
		template.innerHTML = selectField;
		const newSelect = template.content.querySelector("select");

		if (newSelect && selectParentField) {
			selectParentField.parentNode.replaceChild(
				newSelect,
				selectParentField
			);
		} else {
			console.error("New select element not found in the provided HTML.");
		}
	}

	/**
	 * Adds a new category checkbox to the list of categories.
	 *
	 * If the category has a parent, it moves the root parent to the top of the list.
	 * @param {object} newCategory - The new category object.
	 */
	function addCategoryToCheckboxes(newCategory) {
		const categoryUI = getCategoryUI(); // Get a fresh categoryUI object
		const catCheckboxes = categoryUI.catCheckboxes;
		const newCategoryId = newCategory ? newCategory.id : null;
		const newCategoryName = newCategory ? newCategory.name : null;
		const newCategoryParentId = newCategory ? newCategory.parent_id : null;

		const li = document.createElement("li");
		li.setAttribute("data-category", newCategoryId);

		const input = document.createElement("input");
		input.id = `categories-${newCategoryId}`;
		input.name = "categories";
		input.type = "checkbox";
		input.value = newCategoryId;
		if (newCategoryParentId) {
			input.setAttribute("data-parent", newCategoryParentId);
		}
		input.checked = true;

		const label = document.createElement("label");
		label.htmlFor = `categories-${newCategoryId}`;
		label.textContent = newCategoryName;

		li.appendChild(input);
		li.appendChild(label);

		if (newCategoryParentId) {
			const parentItem = document.querySelector(
				`[data-category="${newCategoryParentId}"]`
			);
			if (!parentItem) {
				console.error(
					`Parent item with data-category="${newCategoryParentId}" not found.`
				);
				return;
			}

			// Find the root parent
			let rootParent = parentItem;
			while (rootParent.closest(".is-child")) {
				rootParent = rootParent.closest(".is-child").closest("li");
			}

			// Move the root parent and its descendants to the top
			catCheckboxes.prepend(rootParent);

			// Find the parent category's <ul> element
			let parentList = parentItem?.querySelector("ul");
			if (!parentList && parentItem) {
				parentList = document.createElement("ul");
				parentList.className = newCategoryParentId ? "is-child" : "";
				parentItem.append(parentList);
			}
			parentList?.prepend(li);
		} else {
			catCheckboxes.prepend(li);
		}

		// Scroll the categories list to the top
		catCheckboxes.scrollTop = 0;
	}

	/**
	 * Handles the form submission for adding a new category.
	 * @param {Event} e - The submit event.
	 */
	async function handleSubmit(e) {
		e.preventDefault();
		const categoryUI = getCategoryUI(); // Get a fresh categoryUI object
		const submitBtn = categoryUI.submitBtn;
		if (submitBtn.disabled) return;

		const newCategoryName = categoryUI.newCatInput.value;
		const parentCategoryId = categoryUI.selectParentField.value;

		if (newCategoryName.trim() === "") {
            toggleAlert("New Category field cannot be empty", "error");
			categoryUI.newCatInput.classList.add("error");
			categoryUI.newCatInput.focus();
			return; // Exit the function
		}

		toggleLoadingBtn(submitBtn);

		try {
			const formData = new FormData(); // Create the formData object
			formData.append("name", newCategoryName);
			formData.append("parent_cat", parentCategoryId);

			const response = await fetch(
				"/api/admin/categories?add_select=true",
				{
					method: "POST",
					body: formData,
					headers: {
						"X-Requested-With": "XMLHttpRequest",
					},
				}
			);

			await handleResponse(response);

		} catch (error) {
			toggleAlert("Network error - please try again", "error");
			console.error("Submission error:", error);
		} finally {
			toggleLoadingBtn(submitBtn);
		}
	}

    async function handleResponse(response) {
        if (response.status === 401) {
			// Redirect to login page if unauthorized
			const currentPath =
				window.location.pathname + window.location.search;
			window.location.replace(`/admin/login?next=${currentPath}`);
			return;
		}

        const contentType = response.headers.get("content-type");
		if (!contentType?.includes("application/json")) {
			throw new Error("Invalid server response");
		}

        const responseData = await response.json();

        if (responseData.status === "success" && responseData.data) {
			updateParentSelect(responseData.data.select_field);
			addCategoryToCheckboxes(responseData.data.category);
			resetForm();
			toggleAlert("Category added successfully", "success");
		} else {
			toggleAlert(responseData.message || "Operation failed", "error");
		}
    }

	/**
	 * Resets the form by clearing the new category input field.
	 */
	function resetForm() {
		getCategoryUI().newCatInput.value = "";
	}

	// Initialize the module
	init();

	// document.addEventListener('DOMContentLoaded', function() {
	//     // Get references to the elements
	//     const addCategoryLabel = document.querySelector(
	//         'label[for="new_category_input"]'
	//     );
	//     const catInputBlock = document.querySelector(".cat-input-block");

	//     // Hide the cat-input-block initially
	//     catInputBlock.classList.add("hidden");

	//     // Show the catInputBlock when "Add a new category" label is clicked
	//     addCategoryLabel.addEventListener("click", () => {
	//         catInputBlock.classList.toggle("hidden");
	//     });
	// });

	// const addNewCatBtn = document.querySelector(".add-new-cat");
	// const newCategoryInput = document.getElementById("new-category-input");

	// const updateSelectParentField = (jsonResponse) => {
	//     const parentCat = document.getElementById("parent-cat");
	//     const selectField = jsonResponse.data.select_field;

	//     if (parentCat) {
	//         let tempDiv = document.createElement("div");
	//         tempDiv.innerHTML = selectField;

	//         let newParentCat = tempDiv.getElementsByTagName("select")[0];
	//         parentCat.parentNode.replaceChild(newParentCat, parentCat);
	//     }
	// }

	// const updateCategoryField = (jsonResponse) => {
	//     const categoryList = document.getElementById('categories');
	//     const newCategoryId = 'data' in jsonResponse ? jsonResponse.data.category.id : null;
	//     const newCategoryName = 'data' in jsonResponse ? jsonResponse.data.category.name : null;
	//     const newCategoryParentId = 'category_id' in jsonResponse.data.category ? jsonResponse.data.category.category_id : null;

	//     if (categoryList) {
	//         const newCheckbox = document.createElement('li'); // Create the new checkbox HTML
	//         newCheckbox.innerHTML = `
	//             <input id="categories-${newCategoryId}" name="categories" type="checkbox" value="${newCategoryId}" checked>
	//             <label for="categories-${newCategoryId}">${newCategoryName}</label>
	//             `;

	//         // If the new category is a child category, find its parent category and move it above the new checkbox
	//         if (newCategoryParentId) {
	//             const parentCategoryCheckbox = document.getElementById(`categories-${newCategoryParentId}`);

	//             // Find the parent category's <li> element
	//             const parentCategoryListItem = parentCategoryCheckbox.parentNode;

	//             // Find the parent category's <ul> element
	//             const parentCategoryList = parentCategoryListItem.querySelector('ul');

	//             // Insert the new checkbox as a child of the parent category's <ul> element
	//             parentCategoryList.prepend(newCheckbox);

	//             // Find the last parent ancestor of the new category
	//             let lastParentAncestor = parentCategoryCheckbox;
	//             while (lastParentAncestor.closest('.is-child')) {
	//                 lastParentAncestor = lastParentAncestor.closest('.is-child').closest('li');
	//             }

	//             categoryList.insertBefore(lastParentAncestor, categoryList.querySelector('li'));
	//         } else {
	//             // Insert the new checkbox at the top of the list
	//             categoryList.prepend(newCheckbox);
	//         }
	//     }
	// }

	// function ajaxAddNewCategory(formData) {
	//     let status
	//     // Make the AJAX request to your Flask route
	//     fetch("/api/admin/categories/new?add_select=true", {
	//         method: "POST",
	//         body: formData,
	//         headers: {
	//             "X-Requested-With": "XMLHttpRequest",
	//         },
	//     })
	//         .then((response) => {
	//             if (response.status === 401) {
	//                 // Redirect to login page
	//                 const currentPath =
	//                     window.location.pathname + window.location.search;
	//                 window.location.replace(`/web-admin/login?next=${currentPath}`);
	//             } else if (!response.ok) {
	//                 throw new Error("Network response was not ok");
	//             }
	//             const contentType = response.headers.get("content-type");
	//             if (!contentType?.includes("application/json")) {
	//                 throw new Error("Invalid response format");
	//             }
	//             return response.json();
	//         })
	//         .then((jsonResponse) => {
	//             handleNewCategoryResponse(jsonResponse);
	//         })
	//         .catch((error) => {
	//             msg =
	//                 "Error creating New Category. Please try again. <br> if error persist, please contact technical team";
	//             status = "error";
	//             toggleAlert(msg, status);
	//             throw error;
	//         })
	//         .finally(() => {
	//             toggleLoadingBtn(addNewCatBtn);
	//         });
	// }

	// function handleNewCategoryResponse(jsonResponse) {
	//     let msg = jsonResponse['message'];
	//     let status
	//     if (jsonResponse.status === "success") {
	//         newCategoryInput.value = ""; // Clear input
	//         status = jsonResponse.status;

	//         updateSelectParentField(jsonResponse);
	//         updateCategoryField(jsonResponse);
	//         toggleAlert(msg, status);
	//     } else {
	//         status = "error";
	//         toggleAlert(msg, status);
	//     }
	// }

	// addNewCatBtn.addEventListener('click', (e) => {
	//     e.preventDefault();
	//     if (addNewCatBtn.disabled) return;

	//     // Get the values of newCategoryInput and parentCat fields
	//     const newCategoryValue = newCategoryInput.value;
	//     const parentCat = document.getElementById('parent-cat').value;

	//     const formData = new FormData(); // Create the formData object
	//     formData.append('name', newCategoryValue);
	//     formData.append('parent-cat', parentCat);

	//     if (newCategoryValue.trim() === '') {
	//         toggleAlert('New Category field cannot be empty', 'error')
	//         newCategoryInput.classList.add('error');
	//         newCategoryInput.focus();
	//         return; // Exit the function
	//     }

	//     toggleLoadingBtn(addNewCatBtn);

	//     ajaxAddNewCategory(formData)
	// });
})();