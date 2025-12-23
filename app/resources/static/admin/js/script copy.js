const main = document.querySelector('#main');

const toggleLoadingBtn = (button) => {
	const btnTxt = button.querySelector(".btn-txt");
	const loadIco = button.querySelector(".load-ico");
	const theIco = loadIco.querySelector(".bx");

	button.disabled = !button.disabled; // disable button to prevent multiple clicks
	btnTxt.classList.toggle("hidden");
	loadIco.classList.toggle("hidden");
	theIco.classList.toggle("bx-spin");
};

const toggleDisabled = (node) => {
	node.hasAttribute("disabled")
		? node.removeAttribute("disabled")
		: node.setAttribute("disabled", true);
};

main.addEventListener('click', e => {
    const collapsibleHead = e.target.closest('.collapsible-header');

    if (collapsibleHead) {
        const collapsible = collapsibleHead.parentNode;
        if (!collapsible.classList.contains('collapsible')) return;

        const collapsibleHeight = `${collapsible.scrollHeight}px`;
        const collapsibleBody = collapsibleHead.nextElementSibling;
        const collapsibleFoot = collapsibleBody.nextElementSibling;
        const collapsibleBodyHeight = collapsibleBody ? `${collapsibleBody.scrollHeight}px` : '0px';
        const collapsibleFootHeight = collapsibleFoot ? `${collapsibleFoot.scrollHeight}px` : '0px';
        const isCollapsed = collapsible.classList.contains('collapsed');

        if (isCollapsed) {
            collapsible.classList.remove('collapsed');
        } else {
            collapsible.style.height = collapsibleHeight;
            collapsibleBody ? collapsibleBody.style.height = collapsibleBodyHeight : {};
            collapsibleFoot ? collapsibleFoot.style.height = collapsibleFootHeight : {};

            setTimeout(() => {
                collapsible.classList.toggle('collapsed');
                collapsible.style.height = '';
                collapsibleBody ? collapsibleBody.style.height = '' : {};
                collapsibleFoot ? collapsibleFoot.style.height = '' : {};
            }, 10);
        }
    }
});

