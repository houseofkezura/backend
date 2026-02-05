document.addEventListener('DOMContentLoaded', function() {
    const imageInput = document.getElementById('product-images-input');
    const previewContainer = document.getElementById('image-preview-container');

    if (!imageInput || !previewContainer) return;

    // Store selected files in a DataTransfer object to allow removal
    const dataTransfer = new DataTransfer();

    imageInput.addEventListener('change', function(e) {
        // Clear existing previews if it's a fresh selection (or we can append, but standard file input replaces)
        // However, since we are managing state with DataTransfer, we might want to append.
        // But standard behavior of input[type=file] is replace. Let's stick to standard first to avoid confusion.
        // If the user selects files again, it replaces the current selection in the input.
        
        previewContainer.innerHTML = '';
        dataTransfer.items.clear();

        const files = Array.from(this.files);

        files.forEach(file => {
            if (!file.type.startsWith('image/')) return;

            dataTransfer.items.add(file);

            const reader = new FileReader();
            reader.onload = function(e) {
                createPreviewCard(e.target.result, file.name);
            }
            reader.readAsDataURL(file);
        });
        
        // Sync the input files with our DataTransfer object (though in this simple replace mode it's redundant, 
        // it sets us up for "append" logic if we wanted it later, or "remove" logic)
        imageInput.files = dataTransfer.files;
    });

    function createPreviewCard(src, filename) {
        const div = document.createElement('div');
        div.className = 'relative group w-24 h-24 rounded-lg overflow-hidden border border-gray-200 shadow-sm';
        
        const img = document.createElement('img');
        img.src = src;
        img.alt = filename;
        img.className = 'w-full h-full object-cover';
        
        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'absolute top-1 right-1 bg-red-500 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity';
        removeBtn.innerHTML = '<i class="bx bx-x text-xs"></i>'; // Assuming boxicons is used
        removeBtn.onclick = function() {
            div.remove();
            removeFile(filename);
        };

        div.appendChild(img);
        div.appendChild(removeBtn);
        previewContainer.appendChild(div);
    }

    function removeFile(filename) {
        const newTransfer = new DataTransfer();
        Array.from(imageInput.files).forEach(file => {
            if (file.name !== filename) {
                newTransfer.items.add(file);
            }
        });
        imageInput.files = newTransfer.files;
    }
});
