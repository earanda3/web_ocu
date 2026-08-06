// PDF.js viewer implementation
class PDFViewer {
    constructor(options) {
        this.pdfDoc = null;
        this.pageNum = 1;
        this.pageRendering = false;
        this.pageNumPending = null;
        this.scale = options.scale || 1.5;
        this.canvas = options.canvas;
        this.ctx = this.canvas.getContext('2d');
        this.url = options.url;
        this.container = options.container;
        this.onDocumentLoaded = options.onDocumentLoaded || function() {};
        this.onError = options.onError || function(error) { console.error('PDF error:', error); };
        this.pdfWorkerSrc = options.pdfWorkerSrc || 'lib/pdf.worker.min.js';

        // Set worker source
        pdfjsLib.GlobalWorkerOptions.workerSrc = this.pdfWorkerSrc;
    }

    // Load PDF document
    loadDocument() {
        const loadingTask = pdfjsLib.getDocument(this.url);
        
        loadingTask.promise.then(pdfDoc => {
            this.pdfDoc = pdfDoc;
            this.onDocumentLoaded(pdfDoc.numPages);
            this.renderPage(this.pageNum);
        }).catch(error => {
            this.onError(error);
        });
    }

    // Render a specific page
    renderPage(num) {
        this.pageRendering = true;
        
        this.pdfDoc.getPage(num).then(page => {
            const viewport = page.getViewport({ scale: this.scale });
            this.canvas.height = viewport.height;
            this.canvas.width = viewport.width;

            // Center canvas in container
            if (this.container) {
                const containerWidth = this.container.clientWidth;
                if (viewport.width < containerWidth) {
                    this.canvas.style.marginLeft = ((containerWidth - viewport.width) / 2) + 'px';
                } else {
                    this.canvas.style.marginLeft = '0px';
                }
            }

            const renderContext = {
                canvasContext: this.ctx,
                viewport: viewport
            };

            const renderTask = page.render(renderContext);
            
            renderTask.promise.then(() => {
                this.pageRendering = false;
                
                if (this.pageNumPending !== null) {
                    this.renderPage(this.pageNumPending);
                    this.pageNumPending = null;
                }
            });
        });
    }

    // Queue page rendering if another page is currently rendering
    queueRenderPage(num) {
        if (this.pageRendering) {
            this.pageNumPending = num;
        } else {
            this.renderPage(num);
        }
    }

    // Go to previous page
    previousPage() {
        if (this.pageNum <= 1) {
            return;
        }
        this.pageNum--;
        this.queueRenderPage(this.pageNum);
        return this.pageNum;
    }

    // Go to next page
    nextPage() {
        if (this.pageNum >= this.pdfDoc.numPages) {
            return;
        }
        this.pageNum++;
        this.queueRenderPage(this.pageNum);
        return this.pageNum;
    }

    // Go to a specific page
    goToPage(num) {
        if (num < 1 || num > this.pdfDoc.numPages) {
            return;
        }
        this.pageNum = num;
        this.queueRenderPage(this.pageNum);
        return this.pageNum;
    }

    // Change zoom level
    setZoom(newScale) {
        this.scale = newScale;
        this.queueRenderPage(this.pageNum);
    }

    // Get current page number
    getCurrentPage() {
        return this.pageNum;
    }

    // Get total pages
    getTotalPages() {
        return this.pdfDoc ? this.pdfDoc.numPages : 0;
    }

    // Destroy the viewer
    destroy() {
        if (this.pdfDoc) {
            this.pdfDoc.destroy();
            this.pdfDoc = null;
        }
    }
}
