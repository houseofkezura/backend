// For admin UI interactions (toggles, etc.)
// Extend as needed for the in-house admin UI.

const main = document.querySelector("#main");

const toggleLoadingBtn = (button) => {
	const btnTxt = button.querySelector(".btn-txt");
	const loadIco = button.querySelector(".load-ico");
	const theIco = loadIco.querySelector(".bx");

	button.disabled = !button.disabled; // disable button to prevent multiple clicks
	btnTxt.classList.toggle("hidden");
	loadIco.classList.toggle("hidden");
	theIco.classList.toggle("bx-spin");
};

const toggleModal = (title = "") => {
	const modalBox = document.querySelector(".modal-box");
	modalBox.querySelector(".modal-title").textContent = title;
	document.querySelector("html").classList.toggle("stop-scroll");
	modalBox.classList.toggle("hidden");
};

const toggleDisabled = (node) => {
	node.hasAttribute("disabled")
		? node.removeAttribute("disabled")
		: node.setAttribute("disabled", true);
};

const showModalAlert = (message, type = "info") => {
	const modalBody = document.querySelector(".modal-body");
	if (!modalBody) return;
	
	// Remove existing alert if any
	const existingAlert = modalBody.querySelector(".modal-alert");
	if (existingAlert) existingAlert.remove();
	
	// Create alert element
	const alert = document.createElement("div");
	alert.className = `modal-alert p-3 mb-4 rounded-lg text-sm ${
		type === "error" ? "bg-red-100 text-red-800 border border-red-200" :
		type === "success" ? "bg-green-100 text-green-800 border border-green-200" :
		type === "warning" ? "bg-yellow-100 text-yellow-800 border border-yellow-200" :
		"bg-blue-100 text-blue-800 border border-blue-200"
	}`;
	alert.textContent = message;
	
	// Insert at top of modal body
	modalBody.insertBefore(alert, modalBody.firstChild);
	
	// Auto-remove after 5 seconds
	setTimeout(() => alert.remove(), 5000);
};

main.addEventListener("click", (e) => {
	const collapsibleHead = e.target.closest(".collapsible-header");
	const modal = e.target.closest(".modal-box");
	const closeModal = e.target.closest(".close-modal");
	const cancelModal = e.target.closest("#cancel-modal");

	if (collapsibleHead) {
		const collapsible = collapsibleHead.parentNode;
		if (!collapsible.classList.contains("collapsible")) return;

		const collapsibleHeight = `${collapsible.scrollHeight}px`;
		const collapsibleBody = collapsibleHead.nextElementSibling;
		const collapsibleFoot = collapsibleBody.nextElementSibling;
		const collapsibleBodyHeight = collapsibleBody
			? `${collapsibleBody.scrollHeight}px`
			: "0px";
		const collapsibleFootHeight = collapsibleFoot
			? `${collapsibleFoot.scrollHeight}px`
			: "0px";
		const isCollapsed = collapsible.classList.contains("collapsed");

		if (isCollapsed) {
			collapsible.classList.remove("collapsed");
		} else {
			collapsible.style.height = collapsibleHeight;
			collapsibleBody
				? (collapsibleBody.style.height = collapsibleBodyHeight)
				: {};
			collapsibleFoot
				? (collapsibleFoot.style.height = collapsibleFootHeight)
				: {};

			setTimeout(() => {
				collapsible.classList.toggle("collapsed");
				collapsible.style.height = "";
				collapsibleBody ? (collapsibleBody.style.height = "") : {};
				collapsibleFoot ? (collapsibleFoot.style.height = "") : {};
			}, 10);
		}
	}
	if (e.target == modal || closeModal || cancelModal) {
		toggleModal();
	}
});

