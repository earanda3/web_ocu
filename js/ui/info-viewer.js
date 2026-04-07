/* ================================================================
 * Info Viewer  –  js/ui/info-viewer.js
 * Interactive information window for the ocu universe.
 * Exposes: openInfoViewer(anchorEl?), closeInfoViewer()
 * ================================================================ */

(function () {
    'use strict';

    // ── Load extra fonts (Google Fonts, async) ───────────────────
    if (!document.getElementById('info-viewer-fonts')) {
        const link = document.createElement('link');
        link.id   = 'info-viewer-fonts';
        link.rel  = 'stylesheet';
        link.href = 'https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500&family=Playfair+Display:ital@0;1&family=Courier+Prime&display=swap';
        document.head.appendChild(link);
    }

    // ── CSS ──────────────────────────────────────────────────────
    const CSS = `
#info-modal {
    position: absolute;
    z-index: 620;
    width: 520px;
    height: 580px;
    min-width: 320px;
    min-height: 280px;
    background: #ffffff;
    border: 1px solid rgba(0,0,0,0.09);
    box-shadow: 0 12px 48px rgba(0,0,0,0.13), 0 2px 8px rgba(0,0,0,0.05);
    border-radius: 14px;
    overflow: hidden;
    display: none;
    flex-direction: column;
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    resize: both;
}
#info-modal.show { display: flex; }

.info-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 11px 16px;
    background: #f7f7f7;
    border-bottom: 1px solid rgba(0,0,0,0.06);
    cursor: move;
    user-select: none;
    touch-action: none;
    flex-shrink: 0;
}
.info-header-title {
    font-size: 10px;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: #aaa;
    font-weight: 400;
}
.info-header-close {
    width: 22px;
    height: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    border: none;
    background: rgba(0,0,0,0.07);
    color: #777;
    font-size: 15px;
    cursor: pointer;
    line-height: 1;
    padding: 0;
    transition: background 0.15s, color 0.15s;
    flex-shrink: 0;
}
.info-header-close:hover { background: rgba(0,0,0,0.14); color: #333; }

.info-body {
    flex: 1;
    overflow-y: auto;
    padding: 28px 32px 20px 32px;
    scrollbar-width: thin;
    scrollbar-color: #ddd transparent;
}
.info-body::-webkit-scrollbar { width: 5px; }
.info-body::-webkit-scrollbar-track { background: transparent; }
.info-body::-webkit-scrollbar-thumb { background: #ddd; border-radius: 3px; }

.info-text {
    outline: none;
    line-height: 1.75;
    color: #222;
    min-height: 140px;
    white-space: pre-wrap;
    word-break: break-word;
    cursor: text;
    border-radius: 4px;
    transition: background 0.15s;
}
.info-text:focus { background: rgba(0,0,0,0.015); }
.info-text:empty:before {
    content: attr(data-placeholder);
    color: #ccc;
    pointer-events: none;
}

.info-toolbar {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 16px;
    background: #f7f7f7;
    border-top: 1px solid rgba(0,0,0,0.06);
    flex-shrink: 0;
    flex-wrap: wrap;
}

.info-toolbar select {
    appearance: none;
    -webkit-appearance: none;
    border: 1px solid rgba(0,0,0,0.11);
    border-radius: 7px;
    padding: 4px 26px 4px 10px;
    font-size: 11.5px;
    color: #555;
    background: #fff url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='8' height='5'%3E%3Cpath d='M0 0l4 5 4-5z' fill='%23bbb'/%3E%3C/svg%3E") no-repeat right 9px center;
    cursor: pointer;
    height: 28px;
    min-width: 120px;
    transition: border-color 0.15s;
}
.info-toolbar select:focus { outline: none; border-color: rgba(0,0,0,0.22); }

.info-size-wrap {
    display: flex;
    align-items: center;
    gap: 7px;
}
.info-size-wrap label {
    font-size: 10.5px;
    color: #aaa;
    letter-spacing: 0.5px;
    white-space: nowrap;
}
.info-size-wrap input[type=range] {
    -webkit-appearance: none;
    width: 76px;
    height: 2px;
    background: #ddd;
    border-radius: 2px;
    outline: none;
    cursor: pointer;
}
.info-size-wrap input[type=range]::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 13px;
    height: 13px;
    background: #444;
    border-radius: 50%;
    cursor: pointer;
    transition: background 0.15s;
}
.info-size-wrap input[type=range]::-webkit-slider-thumb:hover { background: #111; }
.info-size-val {
    font-size: 10.5px;
    color: #888;
    min-width: 28px;
    font-variant-numeric: tabular-nums;
}

.info-slot-wrap {
    display: flex;
    align-items: center;
    gap: 7px;
    margin-left: auto;
}
.info-slot-label {
    font-size: 10.5px;
    color: #aaa;
    user-select: none;
    cursor: pointer;
    letter-spacing: 0.5px;
}

/* iOS-style toggle */
.info-toggle {
    position: relative;
    width: 38px;
    height: 21px;
    cursor: pointer;
    flex-shrink: 0;
}
.info-toggle input {
    opacity: 0;
    width: 0;
    height: 0;
    position: absolute;
}
.info-toggle-track {
    position: absolute;
    inset: 0;
    background: #d8d8d8;
    border-radius: 10.5px;
    transition: background 0.2s;
}
.info-toggle input:checked + .info-toggle-track { background: #3a3a3a; }
.info-toggle-thumb {
    position: absolute;
    top: 2.5px;
    left: 2.5px;
    width: 16px;
    height: 16px;
    background: #fff;
    border-radius: 50%;
    box-shadow: 0 1px 4px rgba(0,0,0,0.22);
    transition: transform 0.2s;
    pointer-events: none;
}
.info-toggle input:checked ~ .info-toggle-thumb { transform: translateX(17px); }

.info-reset {
    font-size: 10.5px;
    color: #ccc;
    background: none;
    border: none;
    cursor: pointer;
    padding: 0;
    text-decoration: underline;
    text-underline-offset: 2px;
    transition: color 0.15s;
    white-space: nowrap;
}
.info-reset:hover { color: #999; }
`;

    // Inject CSS once
    if (!document.getElementById('info-viewer-style')) {
        const style = document.createElement('style');
        style.id = 'info-viewer-style';
        style.textContent = CSS;
        document.head.appendChild(style);
    }

    // ── Default text ─────────────────────────────────────────────
    const DEFAULT_TEXT =
`Aquest és l'univers ocu, una plataforma d'art digital
On cada paraula és un món.

Per descobrir-los has de clicar les paraules
Així, trobaràs el que hi ha a l'interior.

Pots interactuar amb els elements que apareixen
Clica els objectes 3D per canviar-los el color
Manipula les Imatges
Descarrega documents
Afegeix paraules
Afegeix arxius
Investiga-ho!

Pots crear una serp amb la lletra "N" per navegar i descobrir l'univers.
Es mou amb les fletxetes.
Pots interactuar amb les paraules xocant-hi
I menjar els elements que hi neixen
per anar més de pressa i créixer.

Pots crear una altra serp amb la lletra "M"
Que es mou amb les lletres W-A-S-D
I jugar amb algú altre al laberint o a veure qui va més de pressa.

Pots jugar al pong amb la lletra "P"
I interactuar amb les paraules
I xocar amb els elements per accelerar la pilota.

Espero que ho gaudeixis
gràcies per la visita <3`;

    // ── Font catalogue ───────────────────────────────────────────
    const FONTS = [
        { label: 'Helvetica',        value: "'Helvetica Neue', Helvetica, Arial, sans-serif" },
        { label: 'Space Grotesk',    value: "'Space Grotesk', sans-serif" },
        { label: 'Playfair Display', value: "'Playfair Display', Georgia, serif" },
        { label: 'Georgia',          value: "Georgia, 'Times New Roman', serif" },
        { label: 'Courier Prime',    value: "'Courier Prime', 'Courier New', monospace" },
        { label: 'O-Regular',        value: "'O-Regular', Helvetica, sans-serif" },
    ];

    // ── DOM refs (set after buildModal) ──────────────────────────
    let modal      = null;
    let textEl     = null;
    let sizeRange  = null;
    let sizeVal    = null;
    let fontSelect = null;
    let slotToggle = null;

    // ── Build modal (idempotent) ─────────────────────────────────
    function buildModal() {
        if (document.getElementById('info-modal')) {
            modal      = document.getElementById('info-modal');
            textEl     = modal.querySelector('.info-text');
            sizeRange  = modal.querySelector('input[type=range]');
            sizeVal    = modal.querySelector('.info-size-val');
            fontSelect = modal.querySelector('select');
            slotToggle = modal.querySelector('.info-toggle input');
            return;
        }

        modal = document.createElement('div');
        modal.id = 'info-modal';

        // ── Header ───────────────────────────────────────────────
        const header = document.createElement('div');
        header.className = 'info-header';

        const titleSpan = document.createElement('span');
        titleSpan.className = 'info-header-title';
        titleSpan.textContent = '· ocu · info ·';

        const closeBtn = document.createElement('button');
        closeBtn.className = 'info-header-close';
        closeBtn.innerHTML = '&times;';
        closeBtn.title = 'Tancar';
        closeBtn.onclick = closeInfoViewer;

        header.appendChild(titleSpan);
        header.appendChild(closeBtn);

        // ── Body (editable text) ─────────────────────────────────
        const body = document.createElement('div');
        body.className = 'info-body';

        textEl = document.createElement('div');
        textEl.className = 'info-text';
        textEl.contentEditable = 'true';
        textEl.setAttribute('data-placeholder', 'Escriu aquí…');
        textEl.spellcheck = false;
        textEl.textContent = DEFAULT_TEXT;
        textEl.style.fontSize = '17px';

        // Prevent drag events from bubbling to canvas pan
        textEl.addEventListener('mousedown', e => e.stopPropagation());
        textEl.addEventListener('touchstart', e => e.stopPropagation(), { passive: true });

        body.appendChild(textEl);

        // ── Toolbar ──────────────────────────────────────────────
        const toolbar = document.createElement('div');
        toolbar.className = 'info-toolbar';

        // Font selector
        fontSelect = document.createElement('select');
        fontSelect.title = 'Tipografia';
        FONTS.forEach(f => {
            const opt = document.createElement('option');
            opt.value = f.value;
            opt.textContent = f.label;
            fontSelect.appendChild(opt);
        });
        fontSelect.oninput = () => { textEl.style.fontFamily = fontSelect.value; };

        // Size wrap
        const sizeWrap = document.createElement('div');
        sizeWrap.className = 'info-size-wrap';

        const sizeLbl = document.createElement('label');
        sizeLbl.textContent = 'Mida';

        sizeRange = document.createElement('input');
        sizeRange.type  = 'range';
        sizeRange.min   = '10';
        sizeRange.max   = '48';
        sizeRange.value = '17';
        sizeRange.oninput = () => {
            textEl.style.fontSize = sizeRange.value + 'px';
            sizeVal.textContent   = sizeRange.value + 'px';
        };

        sizeVal = document.createElement('span');
        sizeVal.className   = 'info-size-val';
        sizeVal.textContent = '17px';

        sizeWrap.appendChild(sizeLbl);
        sizeWrap.appendChild(sizeRange);
        sizeWrap.appendChild(sizeVal);

        // Slot machine toggle
        const slotWrap = document.createElement('div');
        slotWrap.className = 'info-slot-wrap';

        const slotLbl = document.createElement('span');
        slotLbl.className   = 'info-slot-label';
        slotLbl.textContent = 'Slot';

        const toggleLabel = document.createElement('label');
        toggleLabel.className = 'info-toggle';
        toggleLabel.title     = 'Activar/desactivar slot machine';

        slotToggle = document.createElement('input');
        slotToggle.type    = 'checkbox';
        slotToggle.checked = !window.__slotFrozen;
        slotToggle.onchange = () => {
            if (slotToggle.checked) {
                window.__slotFrozen   = false;
                window.__introFrozen  = false;
                if (typeof window.resumeAllSlotMachines === 'function') {
                    window.resumeAllSlotMachines();
                }
            } else {
                window.__slotFrozen  = true;
                window.__introFrozen = true;
                if (typeof window.clearAllSlotIntervals === 'function') {
                    window.clearAllSlotIntervals();
                }
            }
        };

        const toggleTrack = document.createElement('span');
        toggleTrack.className = 'info-toggle-track';
        const toggleThumb = document.createElement('span');
        toggleThumb.className = 'info-toggle-thumb';

        toggleLabel.appendChild(slotToggle);
        toggleLabel.appendChild(toggleTrack);
        toggleLabel.appendChild(toggleThumb);

        slotWrap.appendChild(slotLbl);
        slotWrap.appendChild(toggleLabel);

        // Reset button
        const resetBtn = document.createElement('button');
        resetBtn.className   = 'info-reset';
        resetBtn.textContent = 'reset';
        resetBtn.title       = 'Restaurar valors per defecte';
        resetBtn.onclick = () => {
            textEl.textContent      = DEFAULT_TEXT;
            sizeRange.value         = '17';
            sizeVal.textContent     = '17px';
            textEl.style.fontSize   = '17px';
            fontSelect.selectedIndex = 0;
            textEl.style.fontFamily = FONTS[0].value;
        };

        toolbar.appendChild(fontSelect);
        toolbar.appendChild(sizeWrap);
        toolbar.appendChild(slotWrap);
        toolbar.appendChild(resetBtn);

        modal.appendChild(header);
        modal.appendChild(body);
        modal.appendChild(toolbar);
        document.body.appendChild(modal);

        setupDrag(modal, header);

        // Keyboard close
        document.addEventListener('keydown', e => {
            if (e.key === 'Escape' && modal.classList.contains('show')) {
                closeInfoViewer();
            }
        });
    }

    // ── Drag ─────────────────────────────────────────────────────
    function setupDrag(el, handle) {
        let dragging = false;
        let ox = 0, oy = 0;

        const onStart = (cx, cy) => {
            dragging = true;
            const r = el.getBoundingClientRect();
            ox = cx - r.left;
            oy = cy - r.top;
        };
        const onMove = (cx, cy) => {
            if (!dragging) return;
            const maxX = window.innerWidth  - el.offsetWidth;
            const maxY = window.innerHeight - el.offsetHeight;
            el.style.left = Math.max(0, Math.min(cx - ox, maxX)) + 'px';
            el.style.top  = Math.max(0, Math.min(cy - oy, maxY)) + 'px';
        };
        const onEnd = () => { dragging = false; };

        handle.addEventListener('mousedown', e => {
            if (e.target.closest('.info-header-close')) return;
            onStart(e.clientX, e.clientY);
            e.preventDefault();
        });
        document.addEventListener('mousemove', e => onMove(e.clientX, e.clientY));
        document.addEventListener('mouseup', onEnd);

        handle.addEventListener('touchstart', e => {
            if (e.target.closest('.info-header-close')) return;
            onStart(e.touches[0].clientX, e.touches[0].clientY);
        }, { passive: true });
        document.addEventListener('touchmove', e => {
            if (!dragging) return;
            onMove(e.touches[0].clientX, e.touches[0].clientY);
            e.preventDefault();
        }, { passive: false });
        document.addEventListener('touchend', onEnd);
    }

    // ── Public API ───────────────────────────────────────────────
    function openInfoViewer(anchorEl) {
        buildModal();

        // Position near anchor, or centered
        if (anchorEl && anchorEl.getBoundingClientRect) {
            const r = anchorEl.getBoundingClientRect();
            modal.style.left = Math.max(0, Math.min(r.left + 40, window.innerWidth  - 540)) + 'px';
            modal.style.top  = Math.max(0, Math.min(r.top  + 20, window.innerHeight - 600)) + 'px';
        } else {
            modal.style.left = Math.max(0, Math.round((window.innerWidth  - 520) / 2)) + 'px';
            modal.style.top  = Math.max(0, Math.round((window.innerHeight - 560) / 4)) + 'px';
        }

        // Sync toggle state with current slot status
        if (slotToggle) slotToggle.checked = !window.__slotFrozen;

        modal.classList.add('show');
    }

    function closeInfoViewer() {
        if (modal) modal.classList.remove('show');
    }

    window.openInfoViewer  = openInfoViewer;
    window.closeInfoViewer = closeInfoViewer;

})();
