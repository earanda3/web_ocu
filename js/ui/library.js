
// Library Feature: Fetch and display PDFs from the server

function ensureLibraryWord() {
    let libWord = document.getElementById('library-word');
    if (libWord) return;

    libWord = document.createElement('a');
    libWord.id = 'library-word';
    libWord.href = '#';
    libWord.style.position = 'absolute';
    libWord.style.fontSize = '24px';
    libWord.style.letterSpacing = '2px';
    libWord.style.color = '#333';
    libWord.style.cursor = 'move';
    libWord.style.userSelect = 'none';

    // Position it somewhere reasonable
    const vw = window.innerWidth / (window.zoomLevel || 1);
    const vh = window.innerHeight / (window.zoomLevel || 1);
    libWord.style.left = (vw - 200 - (window.panX || 0)) + 'px';
    libWord.style.top = (100 - (window.panY || 0)) + 'px';

    document.getElementById('canvas').appendChild(libWord);

    if (typeof createWordSlotMachine === 'function') {
        createWordSlotMachine(libWord, 'biblioteca');
    } else {
        libWord.textContent = 'biblioteca';
    }

    if (typeof addWordDragEvents === 'function') {
        addWordDragEvents(libWord);
    }

    // Click opens library modal
    libWord.addEventListener('click', (e) => {
        e.preventDefault();
        if (!libWord.dataset.dragging) {
            openLibraryModal();
        }
    });

    // Right click also opens it
    libWord.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        openLibraryModal();
    });
}

function openLibraryModal() {
    let modal = document.getElementById('library-modal');
    if (modal) {
        modal.style.display = 'block';
        fetchPdfList(); // Refresh list
        return;
    }

    modal = document.createElement('div');
    modal.id = 'library-modal';
    modal.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.2);
        z-index: 2000;
        width: 90vw;
        max-width: 500px;
        max-height: 80vh;
        display: flex;
        flex-direction: column;
        font-family: 'Helvetica', sans-serif;
    `;

    modal.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
            <h3 style="margin:0; color:#333; font-size: 20px;">Biblioteca PDF</h3>
            <button id="close-library-btn" style="background:none; border:none; font-size:24px; cursor:pointer; color:#999;">&times;</button>
        </div>
        <div id="library-list" style="
            flex: 1;
            overflow-y: auto;
            border: 1px solid #eee;
            border-radius: 8px;
            padding: 8px;
        ">
            <div style="text-align:center; color:#999; padding:20px;">Carregant...</div>
        </div>
    `;

    document.body.appendChild(modal);

    const closeBtn = modal.querySelector('#close-library-btn');
    closeBtn.onclick = () => {
        modal.style.display = 'none';
    };

    // Close on click outside
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.style.display = 'none';
    });

    fetchPdfList();
}

function fetchPdfList() {
    const listContainer = document.querySelector('#library-list');
    if (!listContainer) return;

    listContainer.innerHTML = '<div style="text-align:center; color:#999; padding:20px;">Carregant...</div>';

    fetch('/api/pdfs')
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(files => {
            if (!files || files.length === 0) {
                listContainer.innerHTML = '<div style="text-align:center; color:#999; padding:20px;">Cap PDF trobat.</div>';
                return;
            }

            listContainer.innerHTML = '';
            const ul = document.createElement('ul');
            ul.style.listStyle = 'none';
            ul.style.padding = '0';
            ul.style.margin = '0';

            files.forEach(file => {
                const li = document.createElement('li');
                li.style.padding = '10px';
                li.style.borderBottom = '1px solid #f5f5f5';
                li.style.cursor = 'pointer';
                li.style.display = 'flex';
                li.style.alignItems = 'center';
                li.style.gap = '10px';
                li.style.transition = 'background 0.2s';

                li.onmouseover = () => li.style.background = '#f9f9f9';
                li.onmouseout = () => li.style.background = 'transparent';

                // Icon
                const icon = document.createElement('span');
                icon.innerHTML = '📄';
                icon.style.fontSize = '18px';

                // Name
                const name = document.createElement('span');
                name.textContent = file.name;
                name.style.flex = '1';
                name.style.fontWeight = '500';
                name.style.color = '#333';

                // Size (optional)
                if (file.size) {
                    const size = document.createElement('span');
                    size.textContent = formatBytes(file.size);
                    size.style.fontSize = '12px';
                    size.style.color = '#999';
                    li.appendChild(size);
                }

                li.prepend(name);
                li.prepend(icon);

                li.onclick = () => {
                    if (typeof previewPDF === 'function') {
                        previewPDF(file.name); // Assuming file.name is the relative URL or filename
                        document.getElementById('library-modal').style.display = 'none';
                    }
                };

                ul.appendChild(li);
            });

            listContainer.appendChild(ul);
        })
        .catch(err => {
            console.error('Error fetching PDFs:', err);
            listContainer.innerHTML = '<div style="text-align:center; color:#e53935; padding:20px;">Error carregant la llista.</div>';
        });
}

function formatBytes(bytes, decimals = 1) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}
