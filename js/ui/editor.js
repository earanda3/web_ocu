
// Text Editor Modal (for "text" word)
function openTextEditorModal() {
    // Check if modal already exists
    let modal = document.getElementById('text-editor-modal');
    if (modal) {
        modal.style.display = 'block';
        return;
    }

    modal = document.createElement('div');
    modal.id = 'text-editor-modal';
    modal.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        z-index: 2000;
        width: 320px;
        font-family: 'Helvetica', sans-serif;
    `;

    modal.innerHTML = `
        <h3 style="margin-top:0; color:#333;">Editor de Text</h3>
        <textarea id="custom-text-input" placeholder="Escriu aquí..." style="width:100%; height:80px; margin-bottom:15px; padding:8px; border:1px solid #ddd; border-radius:6px; resize:vertical; font-family:inherit;"></textarea>
        <div style="display:flex; justify-content:flex-end; gap:10px;">
            <button id="cancel-text-btn" style="padding:6px 12px; background:#f0f0f0; border:none; border-radius:6px; cursor:pointer;">Cancel·lar</button>
            <button id="create-text-btn" style="padding:6px 12px; background:#333; color:white; border:none; border-radius:6px; cursor:pointer;">Crear</button>
        </div>
    `;

    document.body.appendChild(modal);

    const input = modal.querySelector('#custom-text-input');
    const cancelBtn = modal.querySelector('#cancel-text-btn');
    const createBtn = modal.querySelector('#create-text-btn');

    // Focus input
    setTimeout(() => input.focus(), 100);

    function closeModal() {
        modal.style.display = 'none';
        input.value = '';
    }

    cancelBtn.onclick = closeModal;

    createBtn.onclick = () => {
        const text = input.value.trim();
        if (text) {
            createCustomTextElement(text);
        }
        closeModal();
    };

    // Allow Enter to submit (Shift+Enter for new line)
    input.onkeydown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            createBtn.click();
        }
        if (e.key === 'Escape') {
            closeModal();
        }
    };
}

// Writer Modal (for "lletres" word) - exports as PNG
function openWriterModal() {
    let modal = document.getElementById('writer-modal');
    if (modal) {
        modal.style.display = 'block';
        return;
    }

    modal = document.createElement('div');
    modal.id = 'writer-modal';
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
        max-width: 600px;
        font-family: 'Helvetica', sans-serif;
        display: flex;
        flex-direction: column;
        gap: 16px;
    `;

    modal.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <h3 style="margin:0; color:#333;">Màquina d'Escriure</h3>
            <button id="close-writer-btn" style="background:none; border:none; font-size:20px; cursor:pointer; color:#999;">&times;</button>
        </div>
        
        <div id="writer-canvas-container" style="
            width: 100%;
            height: 300px;
            border: 1px solid #eee;
            border-radius: 8px;
            background: #fafafa;
            position: relative;
            overflow: hidden;
            cursor: text;
        ">
            <div id="writer-content" contenteditable="true" style="
                width: 100%;
                height: 100%;
                padding: 20px;
                outline: none;
                font-family: 'Courier New', monospace;
                font-size: 24px;
                line-height: 1.5;
                color: #333;
                overflow-y: auto;
            "></div>
        </div>
        
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="display:flex; gap:8px;">
                <button class="font-btn active" data-font="'Courier New', monospace" style="font-family:'Courier New', monospace;">Courier</button>
                <button class="font-btn" data-font="'Helvetica', sans-serif" style="font-family:'Helvetica', sans-serif;">Helvetica</button>
                <button class="font-btn" data-font="'Minecraft', monospace" style="font-family:'Minecraft', monospace;">Pixel</button>
            </div>
            <button id="export-writer-btn" style="
                padding: 8px 16px;
                background: #333;
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 500;
            ">Exportar com Imatge</button>
        </div>
        
        <style>
            .font-btn {
                padding: 6px 10px;
                background: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            }
            .font-btn.active {
                background: #eee;
                border-color: #bbb;
            }
        </style>
    `;

    document.body.appendChild(modal);

    const content = modal.querySelector('#writer-content');
    const closeBtn = modal.querySelector('#close-writer-btn');
    const exportBtn = modal.querySelector('#export-writer-btn');
    const fontBtns = modal.querySelectorAll('.font-btn');

    // Font switching
    fontBtns.forEach(btn => {
        btn.onclick = () => {
            fontBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            content.style.fontFamily = btn.dataset.font;
            content.focus();
        };
    });

    // Close
    closeBtn.onclick = () => {
        modal.style.display = 'none';
    };

    // Export to canvas/image
    exportBtn.onclick = () => {
        // Simple HTML2Canvas-like approach using canvas API manually
        // or just creating a text element on the main canvas

        const text = content.innerText;
        if (!text.trim()) return;

        // Create a canvas to render the text
        const exportCanvas = document.createElement('canvas');
        const ctx = exportCanvas.getContext('2d');
        const fontSize = 24;
        const lineHeight = fontSize * 1.5;
        const padding = 20;

        // Measure text
        ctx.font = `${fontSize}px ${getComputedStyle(content).fontFamily}`;
        const lines = text.split('\n');
        let maxWidth = 0;
        lines.forEach(line => {
            const w = ctx.measureText(line).width;
            if (w > maxWidth) maxWidth = w;
        });

        exportCanvas.width = maxWidth + (padding * 2);
        exportCanvas.height = (lines.length * lineHeight) + (padding * 2);

        // Draw background
        ctx.fillStyle = 'white'; // or transparent? Let's do transparent for "sticker" feel
        // ctx.fillRect(0, 0, exportCanvas.width, exportCanvas.height);

        // Draw text
        ctx.font = `${fontSize}px ${getComputedStyle(content).fontFamily}`;
        ctx.fillStyle = '#333';
        ctx.textBaseline = 'top';

        lines.forEach((line, i) => {
            ctx.fillText(line, padding, padding + (i * lineHeight));
        });

        // Convert to image and add to main canvas
        const img = new Image();
        img.src = exportCanvas.toDataURL('image/png');
        img.style.position = 'absolute';

        // Place in center of view
        const vw = window.innerWidth / zoomLevel;
        const vh = window.innerHeight / zoomLevel;
        img.style.left = (vw / 2 - exportCanvas.width / 2 - panX) + 'px';
        img.style.top = (vh / 2 - exportCanvas.height / 2 - panY) + 'px';

        // Add to main canvas
        document.getElementById('canvas').appendChild(img);

        // Make interactive
        if (typeof enhanceImage === 'function') enhanceImage(img);

        // Close modal
        modal.style.display = 'none';
        content.innerText = ''; // Clear content
    };

    // Focus
    setTimeout(() => content.focus(), 100);
}

function createCustomTextElement(text) {
    const el = document.createElement('a');
    el.href = '#';
    el.className = 'custom-text-word';
    el.style.position = 'absolute';
    el.style.fontSize = '24px';
    el.style.color = '#333';
    el.style.cursor = 'move';
    el.style.userSelect = 'none';
    el.style.letterSpacing = '2px';
    el.style.whiteSpace = 'nowrap';

    // Place in center of view
    const vw = window.innerWidth / zoomLevel;
    const vh = window.innerHeight / zoomLevel;
    el.style.left = (vw / 2 - 100 - panX) + 'px';
    el.style.top = (vh / 2 - 20 - panY) + 'px';

    document.getElementById('canvas').appendChild(el);

    // Apply slot machine effect
    if (typeof createWordSlotMachine === 'function') {
        createWordSlotMachine(el, text);
    } else {
        el.textContent = text;
    }

    // Add drag events
    if (typeof addWordDragEvents === 'function') {
        addWordDragEvents(el);
    }

    // Right click to remove
    el.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        el.remove();
    });
}
