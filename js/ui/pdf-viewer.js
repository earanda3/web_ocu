
// Initialize simple PDF viewer
function initPdfViewer() {
    const modal = document.getElementById('pdf-modal');
    const closeBtn = document.querySelector('.pdf-close');
    const downloadBtn = document.getElementById('download-pdf');
    const openExternalBtn = document.getElementById('open-external');

    if (!modal) return;

    // Close modal events
    if (closeBtn) {
        closeBtn.onclick = (e) => {
            e.stopPropagation();
            closePdfPreview();
        };
    }

    // Download button
    if (downloadBtn) {
        downloadBtn.onclick = (e) => {
            e.stopPropagation();
            downloadPDF();
        };
    }

    // Open in new tab button
    if (openExternalBtn) {
        openExternalBtn.onclick = (e) => {
            e.stopPropagation();
            window.open('tao.pdf', '_blank');
        };
    }

    // Keyboard controls
    document.addEventListener('keydown', (e) => {
        if (!modal.classList.contains('show')) return;

        switch (e.key) {
            case 'Escape':
                closePdfPreview();
                break;
            case 'd':
            case 'D':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    downloadPDF();
                }
                break;
        }
    });

    // Initialize drag for the modal
    setupPdfModalDrag(modal);
}

// Advanced PDF Modal drag and resize functionality
function setupPdfModalDrag(modal) {
    const header = modal.querySelector('.pdf-header');
    if (!header) return;

    let isDragging = false;
    let isResizing = false;
    let dragOffset = { x: 0, y: 0 };
    let initialWidth, initialHeight, initialX, initialY;

    // Header drag functionality
    header.addEventListener('mousedown', (e) => {
        if (isResizing) return;

        isDragging = true;
        const rect = modal.getBoundingClientRect();
        dragOffset.x = e.clientX - rect.left;
        dragOffset.y = e.clientY - rect.top;

        document.body.style.cursor = 'grabbing';
        e.preventDefault();
    });

    // Enhanced resize functionality for all 4 corners
    let resizeDirection = null;

    modal.addEventListener('mousedown', (e) => {
        const rect = modal.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        // Detect which corner for resize
        if (x <= 15 && y <= 15) {
            resizeDirection = 'nw';
        } else if (x >= rect.width - 15 && y <= 15) {
            resizeDirection = 'ne';
        } else if (x <= 15 && y >= rect.height - 15) {
            resizeDirection = 'sw';
        } else if (x >= rect.width - 15 && y >= rect.height - 15) {
            resizeDirection = 'se';
        } else {
            resizeDirection = null;
        }

        if (resizeDirection && !isDragging) {
            isResizing = true;
            initialWidth = rect.width;
            initialHeight = rect.height;
            initialX = e.clientX;
            initialY = e.clientY;

            const modalRect = modal.getBoundingClientRect();
            modal.initialLeft = modalRect.left;
            modal.initialTop = modalRect.top;

            document.body.style.cursor = resizeDirection + '-resize';
            e.preventDefault();
            e.stopPropagation();
        }
    });

    // Mouse move handlers
    document.addEventListener('mousemove', (e) => {
        if (isDragging) {
            const x = e.clientX - dragOffset.x;
            const y = e.clientY - dragOffset.y;

            // Keep within viewport bounds
            const maxX = window.innerWidth - modal.offsetWidth;
            const maxY = window.innerHeight - modal.offsetHeight;

            const boundedX = Math.max(0, Math.min(x, maxX));
            const boundedY = Math.max(0, Math.min(y, maxY));

            modal.style.left = boundedX + 'px';
            modal.style.top = boundedY + 'px';
        } else if (isResizing && resizeDirection) {
            const deltaX = e.clientX - initialX;
            const deltaY = e.clientY - initialY;

            let newWidth = initialWidth;
            let newHeight = initialHeight;
            let newLeft = modal.initialLeft;
            let newTop = modal.initialTop;

            switch (resizeDirection) {
                case 'se': // bottom-right
                    newWidth = Math.max(200, initialWidth + deltaX);
                    newHeight = Math.max(250, initialHeight + deltaY);
                    break;
                case 'sw': // bottom-left
                    newWidth = Math.max(200, initialWidth - deltaX);
                    newHeight = Math.max(250, initialHeight + deltaY);
                    newLeft = modal.initialLeft + (initialWidth - newWidth);
                    break;
                case 'ne': // top-right
                    newWidth = Math.max(200, initialWidth + deltaX);
                    newHeight = Math.max(250, initialHeight - deltaY);
                    newTop = modal.initialTop + (initialHeight - newHeight);
                    break;
                case 'nw': // top-left
                    newWidth = Math.max(200, initialWidth - deltaX);
                    newHeight = Math.max(250, initialHeight - deltaY);
                    newLeft = modal.initialLeft + (initialWidth - newWidth);
                    newTop = modal.initialTop + (initialHeight - newHeight);
                    break;
            }

            modal.style.width = newWidth + 'px';
            modal.style.height = newHeight + 'px';
            modal.style.left = newLeft + 'px';
            modal.style.top = newTop + 'px';
        }
    });

    // Mouse up handler
    document.addEventListener('mouseup', () => {
        isDragging = false;
        isResizing = false;
        resizeDirection = null;
        document.body.style.cursor = 'default';
    });

    // Touch support for drag
    header.addEventListener('touchstart', (e) => {
        if (isResizing || e.touches.length > 1) return;

        isDragging = true;
        const touch = e.touches[0];
        const rect = modal.getBoundingClientRect();
        dragOffset.x = touch.clientX - rect.left;
        dragOffset.y = touch.clientY - rect.top;

        e.preventDefault();
    });

    document.addEventListener('touchmove', (e) => {
        if (!isDragging || e.touches.length > 1) return;

        const touch = e.touches[0];
        const x = touch.clientX - dragOffset.x;
        const y = touch.clientY - dragOffset.y;

        const maxX = window.innerWidth - modal.offsetWidth;
        const maxY = window.innerHeight - modal.offsetHeight;

        const boundedX = Math.max(0, Math.min(x, maxX));
        const boundedY = Math.max(0, Math.min(y, maxY));

        modal.style.left = boundedX + 'px';
        modal.style.top = boundedY + 'px';

        e.preventDefault();
    });

    document.addEventListener('touchend', () => {
        isDragging = false;
        isResizing = false;
        resizeDirection = null;
    });
}

// Function to open PDF preview as floating element
function previewPDF(url = 'tao.pdf') {
    const modal = document.getElementById('pdf-modal');
    const pdfView = document.getElementById('pdf-js-view');
    const pdfContainer = document.getElementById('pdf-container');

    // Position the preview near the tao element (or center if not available)
    const tao = document.getElementById('tao');
    const canvas = document.getElementById('canvas');

    if (tao && canvas) {
        const taoRect = tao.getBoundingClientRect();
        const canvasRect = canvas.getBoundingClientRect();

        // Calculate position relative to canvas
        const left = (taoRect.left - canvasRect.left) / zoomLevel - panX + 100;
        const top = (taoRect.top - canvasRect.top) / zoomLevel - panY + 50;

        modal.style.left = left + 'px';
        modal.style.top = top + 'px';
    } else {
        // Center fallback
        modal.style.left = '50%';
        modal.style.top = '50%';
        modal.style.transform = 'translate(-50%, -50%)';
    }

    // Clear previous render (if any) and reset container offsets that could push content off-screen
    if (pdfContainer) {
        pdfContainer.style.position = '';
        pdfContainer.style.left = '';
        pdfContainer.style.top = '';
    }
    pdfView.innerHTML = '';

    // Load and render with PDF.js
    initPdfJsViewer(url);

    // Ensure modal is visible (clear any inline display:none)
    modal.style.display = 'block';
    // Show the modal with animation
    modal.classList.add('show');
}

// Function to close PDF preview
function closePdfPreview() {
    const modal = document.getElementById('pdf-modal');
    const pdfView = document.getElementById('pdf-js-view');
    const pdfContainer = document.getElementById('pdf-container');

    modal.classList.remove('show');

    setTimeout(() => {
        // Clear PDF.js render
        if (pdfView) pdfView.innerHTML = '';
        // Reset PDF.js state
        pdfDoc = null;
        pdfCurrentPage = 1;
        pdfRendering = false;
        pdfPendingPage = null;
        // Reset modal completely so it can be reopened
        modal.style.left = '';
        modal.style.top = '';
        modal.style.width = '';
        modal.style.height = '';
        modal.style.transform = ''; // Clear transform if set
        // Clear any stray offsets on container
        if (pdfContainer) {
            pdfContainer.style.position = '';
            pdfContainer.style.left = '';
            pdfContainer.style.top = '';
        }
        // Let CSS control visibility (base: display:none; .show: display:block)
        modal.style.display = '';
    }, 400);
}

// -----------------------------
// PDF.js simple viewer (single-page fit-width)
// -----------------------------
let pdfDoc = null;
let pdfScale = 1;
let pdfCurrentPage = 1;
let pdfRendering = false;
let pdfPendingPage = null;

// Configure worker
if (window.pdfjsLib) {
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.9.179/pdf.worker.min.js';
}

function initPdfJsViewer(url) {
    const container = document.getElementById('pdf-js-view');
    if (!container) return;

    pdfjsLib.getDocument(url).promise.then((doc) => {
        pdfDoc = doc;
        pdfCurrentPage = 1;
        // Render all pages vertically
        renderAllPages(container);
    }).catch((err) => {
        console.error('PDF load error:', err);
    });
}

function renderAllPages(container) {
    if (!pdfDoc) return;
    container.innerHTML = '';

    const availableWidth = container.clientWidth || 400;

    const renderPage = (num) => {
        if (num > pdfDoc.numPages) return;
        pdfDoc.getPage(num).then((page) => {
            const unscaledViewport = page.getViewport({ scale: 1 });
            const scale = availableWidth / unscaledViewport.width;
            const viewport = page.getViewport({ scale });

            // Wrapper per pàgina
            const pageWrapper = document.createElement('div');
            pageWrapper.style.padding = '12px 0';
            pageWrapper.style.background = 'white';
            pageWrapper.style.display = 'flex';
            pageWrapper.style.justifyContent = 'center';
            pageWrapper.style.alignItems = 'center';

            const canvas = document.createElement('canvas');
            canvas.style.display = 'block';
            canvas.style.background = 'white';
            canvas.width = viewport.width;
            canvas.height = viewport.height;
            pageWrapper.appendChild(canvas);
            container.appendChild(pageWrapper);

            const ctx = canvas.getContext('2d');
            // Fons blanc
            ctx.save();
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.restore();

            const renderContext = { canvasContext: ctx, viewport };
            page.render(renderContext).promise.then(() => {
                renderPage(num + 1);
            });
        });
    };

    renderPage(1);
}

// Direct download function
function downloadPDF(url = 'tao.pdf') {
    const a = document.createElement('a');
    a.href = url;
    a.download = url.split('/').pop();
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}
