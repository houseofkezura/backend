(function () {
	const addColorBtn = document.getElementById("var-color");
	const addVarBtn = document.getElementById("add-var-btn");
	const prodVars = document.getElementById("prod-vars");
	const modalBody = document.querySelector(".modal-body");
	const btnWrap = modalBody.nextElementSibling.querySelector(".btn-wrap");
	const doneBtn = btnWrap.querySelector("#done-modal");
	let editingVarType = false; // Flag to indicate if modal is in edit mode
	let variantsDataStore = []; // Store variant data with pricing/inventory

	const addNewValBox = (type = "custom") => {
		const newValBox = document.createElement("div");
		newValBox.classList.add("val-box");

		newValBox.innerHTML = `
            <div class="val-input-box">
                <input type="text" class="val-input form-control" placeholder="Enter Value">
                ${
					type === "color"
						? '<span class="visual pick-color act-btn"> <i class="bx bx-plus icon"></i> <input type="color" class="the-picker"> </span>'
						: ""
				}
            </div>
            <div class="val-act" hidden>
                <span class="del-val act-btn">
                    <i class="bx bx-trash icon"></i>
                </span>
                <span class="move-val act-btn">
                    <i class="bx bx-move icon"></i>
                </span>
            </div>
        `;

		const valBoxes = modalBody.querySelector(".val-boxes");
		const newValDiv = modalBody.querySelector(".new-val-div");
		newValDiv.appendChild(newValBox);

		const nowValBox = newValDiv.querySelector(".val-box");
		if (nowValBox) {
			let inputHasMoved = false;
			const valInput = nowValBox.querySelector(".val-input");
			const pickColorSpan = nowValBox.querySelector(".pick-color");
			const delValSpan = nowValBox.querySelector(".del-val");
			valInput.addEventListener("input", () => {
				if (
					!inputHasMoved &&
					!nowValBox.nextElementSibling &&
					!nowValBox.closest(".val-boxes")
				) {
					btnWrap.hasAttribute("disabled")
						? toggleDisabled(btnWrap)
						: null;
					nowValBox
						.querySelector(".val-act")
						.removeAttribute("hidden");
					valBoxes.appendChild(nowValBox);
					valInput.focus();
					inputHasMoved = true;
					addNewValBox(type);
				}
				if (pickColorSpan) {
					pickColorSpan.style.backgroundColor = valInput.value;
					pickColorSpan.dataset.visualVal =
						pickColorSpan.style.backgroundColor;
				}
			});

			delValSpan.addEventListener("click", () => {
				nowValBox.remove();
				valBoxes.hasChildNodes() ? null : toggleDisabled(btnWrap);
			});

			if (pickColorSpan) {
				pickColorSpan.addEventListener("click", () => {
					const colorPicker = pickColorSpan.querySelector("input");
					colorPicker.addEventListener("input", () => {
						pickColorSpan.setAttribute(
							"style",
							`background-color:${colorPicker.value}`
						);
						pickColorSpan.dataset.visualVal = colorPicker.value;
					});

					colorPicker.click();
				});
			}
		}
	};

	const addVariationType = (varTypeName, type = "custom") => {
		modalBody.innerHTML = `
            <div class="variation-type" id=${type}>
                <div class="variation-name form-group">
                    <label for="var-name">Name</label>
                    <div class="var-name-input-box">
                        <input type="text" class="variation-type-input form-control" placeholder="Enter Variation Type Name" value="${varTypeName}">
                        ${
							editingVarType
								? '<span class="del-val act-btn"> <i class="bx bx-trash icon"></i> </span>'
								: ""
						}
                    </div>
                </div>

                <div class="variation-vals form-group">
                    <label class="vals-label">Values</label>
                    <div class="val-boxes"></div>
                    <div class="new-val-div"></div>
                </div>
            </div>
        `;
		const delValSpan = modalBody.querySelector(".var-name-input-box .del-val");
		if (delValSpan) {
			delValSpan.addEventListener("click", () => {
				const existingProdVarType = prodVars.querySelector(
					'.prod-var-type[data-editing="true"]'
				);
				existingProdVarType.remove();
				toggleModal();
			});
		}
		toggleDisabled(btnWrap);

		new Sortable(modalBody.querySelector(".val-boxes"), {
			handle: ".move-val",
			animation: 350,
			chosenClass: "sort-chosen",
			dragClass: "dragging",
		});
	};
	function colorVarSetting() {
		addVariationType("Color", (type = "color"));
		addNewValBox("color");
		toggleModal("Color variant type");
	}

	const varSetting = () => {
		addVariationType("");
		addNewValBox();
		toggleModal("Add variant type");
	};

	const validateInputs = () => {
		const varTypeNameInput = modalBody.querySelector(".variation-type-input");
		const valInputs = modalBody.querySelectorAll(".val-boxes .val-input");
		const varTypeName = varTypeNameInput.value.trim();
		const values = Array.from(valInputs).map((valInput) =>
			valInput.value.trim().toLowerCase()
		);

		if (varTypeName === "") {
			showModalAlert("Please enter a variation type name.", "error");
			return false;
		}

		if (values.some((value) => value === "")) {
			showModalAlert(
				"Please enter values for all variation inputs.",
				"error"
			);
			return false;
		}

		const uniqueValues = new Set(values);
		if (uniqueValues.size !== values.length) {
			showModalAlert("Duplicate values are not allowed.", "error");
			return false;
		}
		return true;
	};

	const createProdVarType = (varTypeName, values, type) => {
		const prodVarType = document.createElement("div");
		prodVarType.id = type;
		prodVarType.classList.add("prod-var-type");

		prodVarType.innerHTML = `
                <div class="var-type-info">
                    <label>${varTypeName}</label>
                    <div class="var-type-values"></div>
                </div>
                <div class="var-type-act">
                    <span class="edit-type act-btn btn">
                        Edit
                    </span>
                    <span class="move-type act-btn btn">
                        <i class="bx bx-move icon"></i>
                    </span>
                </div>
        `;

		const varTypeValues = prodVarType.querySelector(".var-type-values");
		values.forEach((value) => {
			const span = document.createElement("span");
			span.textContent = value.Name;
			span.dataset.visualVal = value.Visual;
			varTypeValues.appendChild(span);
		});
		prodVarType.querySelector(".var-type-info").appendChild(varTypeValues);

		return prodVarType;
	};

	const extractValues = () => {
		const varTypeNameInput = modalBody.querySelector(".variation-type-input");
		const valInputs = modalBody.querySelectorAll(".val-input");
		const visuals = modalBody.querySelectorAll(".visual");

		const varTypeName = varTypeNameInput.value.trim();
		const values = Array.from(valInputs)
			.map((valInput, index) => {
				const name = valInput.value.trim();
				const visual =
					visuals.length > 0
						? visuals[index].getAttribute("data-visual-val")
						: "";
				return { Name: name, Visual: visual };
			})
			.filter((value) => value.Name !== ""); // Filter out empty values

		return { varTypeName, values };
	};

	const insertProdVarType = (prodVarType) => {
		prodVars.appendChild(prodVarType);

		new Sortable(prodVars, {
			handle: ".move-type",
			animation: 350,
			chosenClass: "sort-chosen",
			dragClass: "dragging",
		});
	};

	const handleEditButtonClick = (event) => {
		try {
			editingVarType = true;
			const prodVarType = event.target.closest(".prod-var-type");
			const varTypeName = prodVarType.querySelector("label").textContent;
			prodVarType.setAttribute("data-editing", "true");
			const varTypeValues = Array.from(
				prodVarType.querySelectorAll(".var-type-values span")
			).map((span) => {
				const name = span.textContent.trim();
				const visual = span.getAttribute("data-visual-val");
				return { Name: name, Visual: visual };
			});

			addVariationType(varTypeName, (type = prodVarType.id));
			varTypeValues.forEach((value) => {
				addNewValBox(prodVarType.id);
				const lastValBox = modalBody.querySelector(
					".new-val-div .val-box:last-child"
				);
				const valInput = lastValBox.querySelector(".val-input");
				valInput.value = value.Name;
				const valBoxes = modalBody.querySelector(".val-boxes");
				const newValBoxes =
					modalBody.querySelectorAll(".new-val-div .val-box");
				newValBoxes.forEach((newValBox) => {
					newValBox
						.querySelector(".val-act")
						.removeAttribute("hidden");
					const visual = newValBox.querySelector(".visual");
					if (visual) {
						visual.dataset.visualVal = value.Visual;
						visual.setAttribute(
							"style",
							`background-color:${value.Visual}`
						);
					}
					valBoxes.appendChild(newValBox);
				});
			});
			addNewValBox(prodVarType.id);

			modalBody
				.querySelector(".variation-type")
				.setAttribute("data-editing", "true");

			btnWrap.removeAttribute("disabled");
			toggleModal("Edit variant type");
		} catch {
			editingVarType = false;
			toggleAlert("Oops, something went wrong", "error");
		}
	};

	const handleDoneButtonClick = () => {
		if (validateInputs()) {
			const { varTypeName, values } = extractValues();

			if (editingVarType) {
				// Edit mode: Find the existing prodVarType and update its content
				const existingProdVarType = prodVars.querySelector(
					'.prod-var-type[data-editing="true"]'
				);
				existingProdVarType.querySelector("label").textContent =
					varTypeName;
				const varTypeValues =
					existingProdVarType.querySelector(".var-type-values");
				varTypeValues.innerHTML = ""; // Clear existing values
				values.forEach((value) => {
					const span = document.createElement("span");
					span.textContent = value.Name;
					span.dataset.visualVal = value.Visual;
					varTypeValues.appendChild(span);
				});
				existingProdVarType.removeAttribute("data-editing");
			} else {
				// Create new prodVarType
				const type = modalBody.querySelector(".variation-type").id;
				const prodVarType = createProdVarType(
					varTypeName,
					values,
					type
				);
				insertProdVarType(prodVarType);
			}

			toggleModal();
			editingVarType = false; // Reset editing flag
			generateVariants();
		}
	};

	addColorBtn.addEventListener("click", colorVarSetting);
	addVarBtn.addEventListener("click", varSetting);
	doneBtn.addEventListener("click", handleDoneButtonClick);

	// Add event delegation for dynamically added edit buttons
	prodVars.addEventListener("click", (event) => {
		if (event.target.matches(".edit-type")) {
			handleEditButtonClick(event);
		}
	});

	// Function to generate product variants
	const generateVariants = () => {
		const allVariants = document.getElementById("all-variants");
		allVariants.innerHTML = ""; // Clear existing variants
		variantsDataStore = []; // Clear stored data

		const prodVarTypes = document.querySelectorAll(".prod-var-type");
		const varTypeArrays = Array.from(prodVarTypes).map((prodVarType) => {
			const varTypeName = prodVarType.querySelector("label").textContent;
			const varTypeValues = Array.from(
				prodVarType.querySelectorAll(".var-type-values span")
			).map((span) => ({
				name: span.textContent.trim(),
				visual: span.getAttribute("data-visual-val") || ""
			}));
			return { varTypeName, varTypeValues };
		});

		// Recursive function to generate all combinations of variation values
		const generateCombinations = (index, currentCombination, currentAttributes) => {
			if (index === varTypeArrays.length) {
				// Reached the end, create variant
				const variantName = currentCombination.join(" / ");
				const variantId = `variant-${variantsDataStore.length}`;
				
				// Store variant data
				const variantData = {
					name: variantName,
					sku: '',
					price_ngn: 0,
					price_usd: 0,
					quantity: 0,
					low_stock_threshold: 5,
					weight_g: 0,
					attributes: currentAttributes
				};
				variantsDataStore.push(variantData);

				const variant = document.createElement("div");
				variant.classList.add("a-variant");
				variant.dataset.variantId = variantId;
				variant.innerHTML = `
                    <div class="a-variant-info">
                        <label>${variantName}</label>
                        <p class="price text-sm text-gray-500">Click to set price & inventory</p>
                    </div>
                    <i class="bx bxs-chevron-right icon"></i>
                `;
				
				// Add click handler to edit variant details
				variant.addEventListener('click', () => openVariantModal(variantId, variantData));
				
				allVariants.appendChild(variant);
			} else {
				// Continue generating combinations
				const { varTypeName, varTypeValues } = varTypeArrays[index];
				varTypeValues.forEach((valueObj) => {
					const newAttributes = { ...currentAttributes };
					newAttributes[varTypeName.toLowerCase().replace(/\s+/g, '_')] = valueObj.name;
					if (valueObj.visual) {
						newAttributes[`${varTypeName.toLowerCase().replace(/\s+/g, '_')}_visual`] = valueObj.visual;
					}
					
					generateCombinations(index + 1, [
						...currentCombination,
						valueObj.name,
					], newAttributes);
				});
			}
		};

		generateCombinations(0, [], {});
		
		// Update hidden input with variants data
		updateVariantsInput();
	};

	// Open modal to edit variant details (price, inventory, etc.)
	const openVariantModal = (variantId, variantData) => {
		const variantIndex = parseInt(variantId.split('-')[1]);
		
		modalBody.innerHTML = `
			<div class="variant-details-form">
				<div class="form-group">
					<label class="form-label">Variant: ${variantData.name}</label>
				</div>
				
				<div class="form-group">
					<label class="form-label">Price (NGN) <span class="text-red-600">*</span></label>
					<input type="number" class="form-control form-input" id="variant-price-ngn" 
						value="${variantData.price_ngn}" min="0" step="0.01" placeholder="0.00">
				</div>
				
				<div class="form-group">
					<label class="form-label">Price (USD)</label>
					<input type="number" class="form-control form-input" id="variant-price-usd" 
						value="${variantData.price_usd || ''}" min="0" step="0.01" placeholder="0.00">
				</div>
				
				<div class="form-group">
					<label class="form-label">Quantity <span class="text-red-600">*</span></label>
					<input type="number" class="form-control form-input" id="variant-quantity" 
						value="${variantData.quantity}" min="0" placeholder="0">
				</div>
				
				<div class="form-group">
					<label class="form-label">Low Stock Threshold</label>
					<input type="number" class="form-control form-input" id="variant-low-stock" 
						value="${variantData.low_stock_threshold}" min="0" placeholder="5">
				</div>
				
				<div class="form-group">
					<label class="form-label">Weight (grams)</label>
					<input type="number" class="form-control form-input" id="variant-weight" 
						value="${variantData.weight_g || ''}" min="0" placeholder="0">
				</div>
				
				<div class="form-group">
					<label class="form-label">SKU (Optional)</label>
					<input type="text" class="form-control form-input" id="variant-sku" 
						value="${variantData.sku}" placeholder="Auto-generated if blank">
					<p class="form-help">Leave blank to auto-generate from product SKU</p>
				</div>
			</div>
		`;
		
		// Update done button handler
		const newDoneBtn = btnWrap.querySelector("#done-modal");
		const handleVariantSave = () => {
			const priceNgn = parseFloat(document.getElementById('variant-price-ngn').value) || 0;
			const priceUsd = parseFloat(document.getElementById('variant-price-usd').value) || 0;
			const quantity = parseInt(document.getElementById('variant-quantity').value) || 0;
			const lowStock = parseInt(document.getElementById('variant-low-stock').value) || 5;
			const weight = parseInt(document.getElementById('variant-weight').value) || 0;
			const sku = document.getElementById('variant-sku').value.trim();
			
			if (priceNgn <= 0) {
				showModalAlert("Price (NGN) is required and must be greater than 0", "error");
				return;
			}
			
			// Update variant data
			variantsDataStore[variantIndex].price_ngn = priceNgn;
			variantsDataStore[variantIndex].price_usd = priceUsd;
			variantsDataStore[variantIndex].quantity = quantity;
			variantsDataStore[variantIndex].low_stock_threshold = lowStock;
			variantsDataStore[variantIndex].weight_g = weight;
			variantsDataStore[variantIndex].sku = sku;
			
			// Update UI
			const variantElement = document.querySelector(`[data-variant-id="${variantId}"]`);
			if (variantElement) {
				const priceDisplay = variantElement.querySelector('.price');
				priceDisplay.textContent = `₦${priceNgn.toLocaleString()} | Qty: ${quantity}`;
				priceDisplay.classList.remove('text-gray-500');
				priceDisplay.classList.add('text-primary');
			}
			
			updateVariantsInput();
			toggleModal();
			
			// Remove this specific handler
			newDoneBtn.removeEventListener('click', handleVariantSave);
		};
		
		newDoneBtn.addEventListener('click', handleVariantSave);
		toggleModal("Edit Variant Details");
	};

	// Update hidden input with JSON variants data
	const updateVariantsInput = () => {
		let variantsInput = document.getElementById('variants-data-input');
		if (!variantsInput) {
			variantsInput = document.createElement('input');
			variantsInput.type = 'hidden';
			variantsInput.id = 'variants-data-input';
			variantsInput.name = 'variants_data';
			document.getElementById('add-user-form').appendChild(variantsInput);
		}
		variantsInput.value = JSON.stringify(variantsDataStore);
	};

	// Function to load existing variants (called from edit page)
	window.loadExistingVariants = function(variants) {
		variantsDataStore = variants;
		
		const allVariants = document.getElementById("all-variants");
		if (!allVariants) return;
		
		allVariants.innerHTML = ""; // Clear placeholder
		
		variants.forEach((variantData, index) => {
			const variantId = `variant-${index}`;
			
			const variant = document.createElement("div");
			variant.classList.add("a-variant");
			variant.dataset.variantId = variantId;
			variant.innerHTML = `
                <div class="a-variant-info">
                    <label>${variantData.name}</label>
                    <p class="price text-sm ${variantData.price_ngn > 0 ? 'text-primary' : 'text-gray-500'}">
                        ${variantData.price_ngn > 0 ? `₦${variantData.price_ngn.toLocaleString()} | Qty: ${variantData.quantity}` : 'Click to set price & inventory'}
                    </p>
                </div>
                <i class="bx bxs-chevron-right icon"></i>
            `;
			
			// Add click handler to edit variant details
			variant.addEventListener('click', () => openVariantModal(variantId, variantData));
			
			allVariants.appendChild(variant);
		});
		
		// Update hidden input
		updateVariantsInput();
	};

	// Initialize on page load
	document.addEventListener('DOMContentLoaded', () => {
		// If editing existing product with variants, populate variantsDataStore
		const existingVariantsData = document.getElementById('existing-variants-json');
		if (existingVariantsData && existingVariantsData.value) {
			try {
				const variants = JSON.parse(existingVariantsData.value);
				if (variants && variants.length > 0) {
					loadExistingVariants(variants);
				}
			} catch (e) {
				console.error('Failed to parse existing variants data', e);
			}
		}
	});
})();
