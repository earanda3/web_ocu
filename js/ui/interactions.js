
// Helper to safely get canvas element (may be null at parse time)
function getCanvas() {
    return window.canvas || document.getElementById('canvas');
}
// Removed duplicate global variable declarations to prevent SyntaxError with main.js

// Create slot machine effect for a word element
function createWordSlotMachine(element, text) {
    element.innerHTML = '';
    text.split('').forEach((letter, index) => {
        const span = document.createElement('span');
        span.className = 'letter';
        // Convert spaces to non-breaking spaces to preserve them
        span.textContent = letter === ' ' ? '\u00A0' : letter;
        const randomFont = fonts[Math.floor(Math.random() * fonts.length)];
        span.classList.add(randomFont);
        element.appendChild(span);
        // If globally frozen, do not start the interval
        if (window.__slotFrozen) {
            return;
        }
        const id = setInterval(() => {
            fonts.forEach(font => span.classList.remove(font));
            const newFont = fonts[Math.floor(Math.random() * fonts.length)];
            span.classList.add(newFont);
            span.style.transform = 'scaleY(0.8)';
            setTimeout(() => { span.style.transform = 'scaleY(1)'; }, 50);
        }, 200 + (index * 150));
        if (!window.__mainIntervals) window.__mainIntervals = [];
        window.__mainIntervals.push(id);
    });
}

function addWordDragEvents(element) {
    let wordDragging = false;
    let wordOffset = { x: 0, y: 0 };
    let lastTap = 0;

    // Mouse events (desktop)
    element.addEventListener('mousedown', (e) => {
        e.preventDefault();
        e.stopPropagation();
        // Allow scrolling inside PDF viewer; don't start drag from its inner area
        if (element.id === 'pdf-container' && e.target && e.target.closest && e.target.closest('#pdf-js-view')) {
            return;
        }
        wordDragging = true;

        const rect = element.getBoundingClientRect();
        wordOffset.x = e.clientX - rect.left;
        wordOffset.y = e.clientY - rect.top;

        const moveHandler = (e) => {
            if (!wordDragging) return;

            const x = (e.clientX - wordOffset.x) / zoomLevel - panX;
            const y = (e.clientY - wordOffset.y) / zoomLevel - panY;

            element.style.left = x + 'px';
            element.style.top = y + 'px';
        };

        const upHandler = () => {
            wordDragging = false;
            document.removeEventListener('mousemove', moveHandler);
            document.removeEventListener('mouseup', upHandler);
        };

        document.addEventListener('mousemove', moveHandler);
        document.addEventListener('mouseup', upHandler);
    });

    // Touch events (mobile)
    element.addEventListener('touchstart', (e) => {
        // Check for double tap
        const currentTime = new Date().getTime();
        const tapLength = currentTime - lastTap;

        if (tapLength < 500 && tapLength > 0) {
            // Double tap detected
            e.preventDefault();
            e.stopPropagation();

            // If it's the tao element or a file word with download attribute
            if (element.hasAttribute('href') && element.hasAttribute('download')) {
                // Open PDF preview on mobile double-tap
                if (typeof previewPDF === 'function') previewPDF();
                return;
            } else if (element.id === 'currency') {
                // Show currency image
                showCurrencyImage();
                return;
            } else if (element.id === 'about-btn') {
                // Open about page
                window.open('about.html', '_blank');
                return;
            }
        }

        lastTap = currentTime;

        if (e.touches.length > 1) return; // Ignore multi-touch
        // Allow scrolling inside PDF viewer; don't start drag from its inner area
        if (element.id === 'pdf-container' && e.target && e.target.closest && e.target.closest('#pdf-js-view')) {
            return;
        }

        wordDragging = true;

        const touch = e.touches[0];
        const rect = element.getBoundingClientRect();
        wordOffset.x = touch.clientX - rect.left;
        wordOffset.y = touch.clientY - rect.top;

        const touchMoveHandler = (e) => {
            if (!wordDragging || e.touches.length > 1) return;

            const touch = e.touches[0];
            const x = (touch.clientX - wordOffset.x) / zoomLevel - panX;
            const y = (touch.clientY - wordOffset.y) / zoomLevel - panY;

            element.style.left = x + 'px';
            element.style.top = y + 'px';
        };

        const touchEndHandler = () => {
            wordDragging = false;
            element.removeEventListener('touchmove', touchMoveHandler);
            element.removeEventListener('touchend', touchEndHandler);
        };

        element.addEventListener('touchmove', touchMoveHandler, { passive: false });
        element.addEventListener('touchend', touchEndHandler);
    }, { passive: false });
}

// Randomize positions of all elements on canvas
function randomizeAllElements() {
    const rect = canvas.getBoundingClientRect();
    const logicalW = rect.width / zoomLevel;
    const logicalH = rect.height / zoomLevel;

    // Collect movable elements
    const imgs = Array.from(document.querySelectorAll('#canvas img'));
    const words = Array.from(document.querySelectorAll('#canvas a, #currency'));
    const pdf = document.getElementById('pdf-container');

    function logicalSize(el) {
        // Prefer explicit styles for images; fallback to rect/zoom
        let w = parseFloat(el.style.width);
        let h = parseFloat(el.style.height);
        if (!(w > 0) || !(h > 0)) {
            const r = el.getBoundingClientRect();
            w = r.width / zoomLevel;
            h = r.height / zoomLevel;
        }
        return { w, h };
    }

    function placeRandom(el) {
        const { w, h } = logicalSize(el);
        const maxX = Math.max(0, logicalW - w);
        const maxY = Math.max(0, logicalH - h);
        const x = Math.round(Math.random() * maxX);
        const y = Math.round(Math.random() * maxY);
        el.style.left = x + 'px';
        el.style.top = y + 'px';
    }

    imgs.forEach(placeRandom);
    words.forEach(placeRandom);
    if (pdf) placeRandom(pdf);
}

function randomizeAllWordPositions() {
    const allWords = canvas.querySelectorAll('a');
    const currency = document.getElementById('currency');
    const rect = canvas.getBoundingClientRect();
    const logicalW = rect.width / zoomLevel;
    const logicalH = rect.height / zoomLevel;

    function placeRandom(el) {
        const w = el.offsetWidth || 100;
        const h = el.offsetHeight || 30;
        const maxX = Math.max(0, logicalW - w);
        const maxY = Math.max(0, logicalH - h);
        const x = Math.round(Math.random() * maxX);
        const y = Math.round(Math.random() * maxY);
        el.style.left = x + 'px';
        el.style.top = y + 'px';
    }

    allWords.forEach(placeRandom);
    if (currency) placeRandom(currency);
}

// Auto-placement next to reference image (same size as reference)
let autoImageIndex = 0;
function placeNextToReference(img, force = false) {
    const ref = document.querySelector('#about-btn img');
    if (!ref || img === ref) return;
    // Only apply if not explicitly positioned by user, unless forcing
    if (!force && img.dataset.userMoved === '1') return;

    const refLeft = parseFloat(ref.style.left) || 0;
    const refTop = parseFloat(ref.style.top) || 0;
    const refW = parseFloat(ref.style.width) || ref.clientWidth || 60;
    const refH = parseFloat(ref.style.height) || ref.clientHeight || 40;
    const gap = 10;

    // Do not modify size here; only position next to reference

    // Decide side based on available space
    const c = canvas.getBoundingClientRect();
    const r = ref.getBoundingClientRect();
    const toRight = (r.right + refW + gap) < (c.left + c.width);
    const index = img.dataset.autoIndex ? parseInt(img.dataset.autoIndex, 10) : autoImageIndex++;
    let left;
    if (toRight) {
        left = refLeft + (refW + gap) * (index + 1);
    } else {
        left = refLeft - (refW + gap) * (index + 1);
    }
    img.style.left = Math.max(0, Math.round(left)) + 'px';
    img.style.top = Math.round(refTop) + 'px';
    img.dataset.autoIndex = String(index);
    img.dataset.autoPlaced = '1';
}

function placeElementInSafeArea(el) {
    const zl = window.zoomLevel || 1;
    const vw = Math.floor(window.innerWidth / zl);
    const vh = Math.floor(window.innerHeight / zl);
    const margin = 60;
    const w = el.offsetWidth || 100;
    const h = el.offsetHeight || 40;
    const canvas = window.canvas || document.getElementById('canvas');

    function overlaps(x, y) {
        if (!canvas) return false;
        const siblings = canvas.querySelectorAll('a, img, .stl-viewer-container');
        for (const s of siblings) {
            if (s === el) continue;
            const sl = parseFloat(s.style.left) || 0;
            const st = parseFloat(s.style.top)  || 0;
            const sw = s.offsetWidth  || 80;
            const sh = s.offsetHeight || 30;
            const pad = 24;
            if (x < sl + sw + pad && x + w + pad > sl && y < st + sh + pad && y + h + pad > st) return true;
        }
        return false;
    }

    const maxX = Math.max(margin, vw - w - margin);
    const maxY = Math.max(margin, vh - h - margin);
    let left, top, tries = 0;
    do {
        left = Math.floor(margin + Math.random() * (maxX - margin));
        top  = Math.floor(margin + Math.random() * (maxY - margin));
        tries++;
    } while (overlaps(left, top) && tries < 20);

    el.style.left = left + 'px';
    el.style.top  = top  + 'px';
}

// Create currency slot machine with typography effects
function createCurrencySlotMachine() {
    const currencyElement = document.getElementById('currency');
    if (!currencyElement) return;

    // Currency symbols with typography info
    const currencies = [
        // Major currencies (higher weight) + special O-Regular 'e'
        { symbol: '$', font: 'font-helvetica' },
        { symbol: '$', font: 'font-courier' },
        { symbol: '$', font: 'font-minecraft' },
        { symbol: 'e', font: 'font-oregular' }, // Special O-Regular 'e' as currency
        { symbol: 'e', font: 'font-oregular' },
        { symbol: '€', font: 'font-helvetica' },
        { symbol: '€', font: 'font-courier' },
        { symbol: '€', font: 'font-minecraft' },
        { symbol: '£', font: 'font-helvetica' },
        { symbol: '£', font: 'font-courier' },
        { symbol: '¥', font: 'font-helvetica' },
        { symbol: '¥', font: 'font-minecraft' },
        { symbol: '₩', font: 'font-courier' },
        // Minor currencies
        { symbol: '¢', font: 'font-helvetica' },
        { symbol: '₣', font: 'font-courier' },
        { symbol: '₺', font: 'font-minecraft' },
        { symbol: '₽', font: 'font-helvetica' }
    ];

    function getRandomCurrency() {
        return currencies[Math.floor(Math.random() * currencies.length)];
    }

    function applyCurrencyStyle(element, currencyObj) {
        // Remove all font classes
        fonts.forEach(font => element.classList.remove(font));
        // Apply new font
        element.classList.add(currencyObj.font);
        element.textContent = currencyObj.symbol;
    }

    // Initialize with random currency
    let currentCurrency = getRandomCurrency();
    applyCurrencyStyle(currencyElement, currentCurrency);

    // Slot machine effect - same rhythm as other words
    if (!window.__slotFrozen) {
        const id = setInterval(() => {
            let newCurrency;

            // Make sure we get a different symbol or font
            do {
                newCurrency = getRandomCurrency();
            } while (newCurrency.symbol === currentCurrency.symbol && newCurrency.font === currentCurrency.font);

            // Simple animation like other words
            currencyElement.style.transform = 'scaleY(0.8)';

            setTimeout(() => {
                applyCurrencyStyle(currencyElement, newCurrency);
                currencyElement.style.transform = 'scaleY(1)';
                currentCurrency = newCurrency;
            }, 50);

        }, 400);
        if (!window.__mainIntervals) window.__mainIntervals = [];
        window.__mainIntervals.push(id);
    }

    // Add drag functionality to currency
    addWordDragEvents(currencyElement);

    // Add currency image functionality on right-click
    currencyElement.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        showCurrencyImage();
    });

    // Add click functionality to show QR.png
    currencyElement.addEventListener('click', (e) => {
        e.preventDefault();
        showCurrencyImage();
    });
}

// Function to spawn QR.png as draggable image on canvas
function showCurrencyImage() {
    const img = document.createElement('img');
    img.src = 'QR.png';
    img.alt = 'QR Code';
    img.draggable = false;
    img.style.position = 'absolute';

    // Random size and position like newtro images (50% smaller)
    const vw = Math.floor(window.innerWidth / (window.zoomLevel || 1));
    const vh = Math.floor(window.innerHeight / (window.zoomLevel || 1));
    const w = Math.floor((140 + Math.random() * 280) * 0.5); // 70..210px (50% of original)
    const margin = 60;
    const left = Math.max(margin, Math.floor(Math.random() * (vw - w - margin * 2)));
    const top = Math.max(margin, Math.floor(Math.random() * (vh - 200 - margin * 2)));

    img.style.left = left + 'px';
    img.style.top = top + 'px';
    img.style.width = w + 'px';
    img.style.height = 'auto';

    canvas.appendChild(img);
    img.dataset.userMoved = '1';

    // Add all the same enhancements as newtro images
    try { enhanceImage(img); } catch { }
}

// Real donation system inspired by your code
function openDonationLink() {
    // Configure your payment links here
    const stripeLink = "https://buy.stripe.com/EL_TEULINK"; // Change to your Stripe Payment Link
    const paypalLink = "https://www.paypal.com/donate?business=EL_TEUCORREU_PAYPAL&currency_code=EUR"; // Change to your PayPal link

    // Detect Apple Pay or Google Pay based on device
    const isApplePayAvailable = window.ApplePaySession && ApplePaySession.canMakePayments();
    const isGooglePayAvailable = navigator.userAgent.toLowerCase().includes('android');

    let donationUrl;

    if (isApplePayAvailable || isGooglePayAvailable) {
        donationUrl = stripeLink; // Stripe will show Apple Pay / Google Pay
    } else {
        donationUrl = paypalLink; // Alternative for desktop or non-compatible devices
    }

    // Open donation link in new tab
    window.open(donationUrl, '_blank');

    // Visual feedback
    celebrateDonationClick();
}

function celebrateDonationClick() {
    const currencyElement = document.getElementById('currency');

    // Brief celebration animation
    currencyElement.style.transform = 'scale(1.2)';
    currencyElement.style.filter = 'brightness(1.5)';

    setTimeout(() => {
        currencyElement.style.transform = 'scale(1)';
        currencyElement.style.filter = 'brightness(1)';
    }, 200);
}

// Add About button functionality
function setupAboutButton() {
    const aboutBtn = document.getElementById('about-btn');
    if (!aboutBtn) return;

    // Make the about button draggable
    addWordDragEvents(aboutBtn);

    // Open about page on right-click
    aboutBtn.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        window.open('/about.html', '_blank');
    });

    // Alternative: Ctrl/Cmd + Click to open about page
    aboutBtn.addEventListener('click', (e) => {
        if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            window.open('/about.html', '_blank');
        }
    });

    // Normalize About button container so child img positions relative to #canvas
    aboutBtn.style.display = 'contents'; // no own box; children layout against canvas
}

// Enable Shift+Wheel resize for all images inside #canvas (no frames/handles)
function enableShiftWheelResize(img) {
    // Ensure explicit width/height so resizing is predictable
    const initWidth = img.clientWidth || img.width || 60;
    const ratio = (img.naturalWidth && img.naturalHeight)
        ? (img.naturalHeight / img.naturalWidth)
        : (img.clientHeight && img.clientWidth ? img.clientHeight / img.clientWidth : 1);
    if (!img.style.width) img.style.width = initWidth + 'px';
    if (!img.style.height) img.style.height = Math.max(1, Math.round(initWidth * ratio)) + 'px';

    img.addEventListener('wheel', (e) => {
        if (!(e.shiftKey || e.ctrlKey || e.metaKey)) return; // allow Shift/Ctrl/Cmd
        e.preventDefault();
        e.stopPropagation(); // avoid triggering global canvas zoom
        const current = parseFloat(img.style.width) || img.clientWidth || 60;
        const factor = 1 + (-Math.sign(e.deltaY)) * 0.08; // smooth scaling
        const next = Math.min(3000, Math.max(16, current * factor));
        img.style.width = next + 'px';
        img.style.height = Math.max(1, Math.round(next * ratio)) + 'px';
    }, { passive: false });
    // Prevent native browser drag image ghost
    img.addEventListener('dragstart', (e) => e.preventDefault());
}

// Helper to strip any inline borders/frames that might get added
function cleanImageStyles(img) {
    img.style.border = 'none';
    img.style.borderRadius = '0';
    img.style.outline = 'none';
    img.style.boxShadow = 'none';
    img.style.background = 'transparent';
}

// Convert viewport client coordinates to logical canvas coordinates
function clientToCanvas(clientX, clientY) {
    const canvasRect = canvas.getBoundingClientRect();
    const x = (clientX - canvasRect.left) / zoomLevel - panX;
    const y = (clientY - canvasRect.top) / zoomLevel - panY;
    return { x, y };
}

// Edge/corner drag resize (desktop) and pinch resize (mobile) for images
function enableEdgeDragResize(img) {
    const EDGE = 10; // px from edge considered resizable zone
    let resizing = false;
    let dir = { left: false, right: false, top: false, bottom: false };
    let start = { x: 0, y: 0, left: 0, top: 0, width: 0, height: 0, ratio: 1 };

    function getDir(e) {
        const r = img.getBoundingClientRect();
        const onLeft = (e.clientX - r.left) <= EDGE;
        const onRight = (r.right - e.clientX) <= EDGE;
        const onTop = (e.clientY - r.top) <= EDGE;
        const onBottom = (r.bottom - e.clientY) <= EDGE;
        return { left: onLeft, right: onRight, top: onTop, bottom: onBottom };
    }

    function updateCursor(e) {
        const d = getDir(e);
        let cursor = '';
        if ((d.right && d.bottom) || (d.left && d.top)) cursor = 'nwse-resize';
        else if ((d.right && d.top) || (d.left && d.bottom)) cursor = 'nesw-resize';
        else if (d.left || d.right) cursor = 'ew-resize';
        else if (d.top || d.bottom) cursor = 'ns-resize';
        else cursor = 'move';
        img.style.cursor = cursor;
    }

    img.addEventListener('mousemove', updateCursor);

    img.addEventListener('mousedown', (e) => {
        // capture first to block drag when resizing
    }, { capture: true });

    img.addEventListener('mousedown', (e) => {
        const d = getDir(e);
        if (!(d.left || d.right || d.top || d.bottom)) return; // not on edge -> normal drag
        e.preventDefault();
        e.stopPropagation(); // stop move-drag from starting
        dir = d;
        resizing = true;
        const p = clientToCanvas(e.clientX, e.clientY);
        start.x = p.x; start.y = p.y;
        // Use logical canvas units from styles
        const rect = img.getBoundingClientRect();
        start.left = parseFloat(img.style.left) || ((rect.left - canvas.getBoundingClientRect().left) / zoomLevel - panX);
        start.top = parseFloat(img.style.top) || ((rect.top - canvas.getBoundingClientRect().top) / zoomLevel - panY);
        start.width = parseFloat(img.style.width) || (rect.width / zoomLevel);
        start.height = parseFloat(img.style.height) || (rect.height / zoomLevel);
        start.ratio = (img.naturalWidth && img.naturalHeight) ? (img.naturalHeight / img.naturalWidth) : ((start.height / start.width) || 1);
        document.body.style.cursor = img.style.cursor || 'nwse-resize';
    });

    document.addEventListener('mousemove', (e) => {
        if (!resizing) return;
        e.preventDefault();
        const p = clientToCanvas(e.clientX, e.clientY);
        const dx = p.x - start.x;
        const dy = p.y - start.y;

        let newWidth = start.width;
        let newHeight = start.height;
        let newLeft = start.left;
        let newTop = start.top;

        if (dir.right) newWidth = Math.max(16, start.width + dx);
        if (dir.bottom) newHeight = Math.max(16, start.height + dy);
        if (dir.left) {
            newWidth = Math.max(16, start.width - dx);
            newLeft = start.left + (start.width - newWidth);
        }
        if (dir.top) {
            newHeight = Math.max(16, start.height - dy);
            newTop = start.top + (start.height - newHeight);
        }

        // keep aspect ratio
        if ((dir.left || dir.right) && !(dir.top || dir.bottom)) {
            newHeight = Math.round(newWidth * start.ratio);
        } else if ((dir.top || dir.bottom) && !(dir.left || dir.right)) {
            newWidth = Math.round(newHeight / start.ratio);
        } else {
            // corner drag -> scale by the largest change
            const wFromW = newWidth;
            const wFromH = Math.round(newHeight / start.ratio);
            const w = Math.min(Math.max(16, wFromW), Math.max(16, wFromH));
            newWidth = w;
            newHeight = Math.round(w * start.ratio);
            if (dir.left) newLeft = start.left + (start.width - newWidth);
            if (dir.top) newTop = start.top + (start.height - newHeight);
        }

        img.style.width = newWidth + 'px';
        img.style.height = newHeight + 'px';
        img.style.left = newLeft + 'px';
        img.style.top = newTop + 'px';
    });

    document.addEventListener('mouseup', () => {
        if (resizing) {
            resizing = false;
            document.body.style.cursor = 'auto';
        }
    });
}

// Pinch resize for mobile
function enablePinchResize(img) {
    let pinch = { active: false, dist: 0, width: 0, height: 0, ratio: 1 };
    img.style.touchAction = 'none'; // allow us to receive pinch events
    img.addEventListener('touchstart', (e) => {
        if (e.touches.length === 2) {
            e.preventDefault();
            const dx = e.touches[0].clientX - e.touches[1].clientX;
            const dy = e.touches[0].clientY - e.touches[1].clientY;
            pinch.dist = Math.hypot(dx, dy);
            const w = parseFloat(img.style.width) || img.clientWidth || 60;
            const naturalRatio = (img.naturalWidth && img.naturalHeight) ? (img.naturalHeight / img.naturalWidth) : null;
            const h = parseFloat(img.style.height) || img.clientHeight || (w * (naturalRatio || 1));
            pinch.width = w; pinch.height = h; pinch.ratio = naturalRatio || (h / w) || 1; pinch.active = true;
        }
    }, { passive: false });

    img.addEventListener('touchmove', (e) => {
        if (!pinch.active || e.touches.length !== 2) return;
        e.preventDefault();
        const dx = e.touches[0].clientX - e.touches[1].clientX;
        const dy = e.touches[0].clientY - e.touches[1].clientY;
        const dist = Math.hypot(dx, dy);
        const scale = dist / (pinch.dist || dist);
        const w = Math.min(3000, Math.max(16, Math.round(pinch.width * scale)));
        const h = Math.max(1, Math.round(w * pinch.ratio));
        img.style.width = w + 'px';
        img.style.height = h + 'px';
    }, { passive: false });

    img.addEventListener('touchend', () => { pinch.active = false; });
}

// Normalize and enhance an image (drag + resize desktop/mobile)
function enhanceImage(img) {
    if (!img || img.dataset.enhanced === '1') return;
    img.dataset.enhanced = '1';
    cleanImageStyles(img);
    // Ensure absolute positioning and numeric left/top
    img.style.position = 'absolute';
    if (!img.style.left || !img.style.top) {
        const r = img.getBoundingClientRect();
        const c = canvas.getBoundingClientRect();
        const left = (r.left - c.left) / zoomLevel - panX;
        const top = (r.top - c.top) / zoomLevel - panY;
        img.style.left = Math.round(left) + 'px';
        img.style.top = Math.round(top) + 'px';
    }
    // Ensure explicit width/height for stable resizing
    const w = img.clientWidth || img.width || 120;
    const ratio = (img.naturalWidth && img.naturalHeight) ? (img.naturalHeight / img.naturalWidth) : 1;
    if (!img.style.width) img.style.width = w + 'px';
    if (!img.style.height) img.style.height = Math.max(1, Math.round((parseFloat(img.style.width) || w) * ratio)) + 'px';
    // Interactions
    enableShiftWheelResize(img);
    enableEdgeDragResize(img);
    enablePinchResize(img);
    addWordDragEvents(img);
    img.addEventListener('dragstart', (e) => e.preventDefault());
    // Mark when the user moves/resizes this image to stop auto-placement
    img.addEventListener('mouseup', () => { img.dataset.userMoved = '1'; });
    img.addEventListener('touchend', () => { img.dataset.userMoved = '1'; });
    // If spawned by the snake, randomize size and place in safe random area, then skip auto-placement
    if (window.__spawnFromSnake) {
        try {
            const minW = 120, maxW = 480;
            const rw = Math.floor(minW + Math.random() * (maxW - minW));
            img.style.width = rw + 'px';
            img.style.height = Math.max(1, Math.round(rw * ratio)) + 'px';
            placeElementInSafeArea(img);
            img.dataset.userMoved = '1';
        } catch { }
    } else {
        // Default placement next to the reference logo and same size
        placeNextToReference(img);
    }
}

// Helper: remove all spawned images except the about cat
function resetAllImages() {
    const aboutImg = document.querySelector('#about-btn img');
    const imgs = Array.from(document.querySelectorAll('#canvas img'));
    imgs.forEach(img => {
        if (aboutImg && img === aboutImg) return; // keep the cat
        img.remove();
    });
    // Optional: reset auto placement index
    autoImageIndex = 0;
    // Also close PDF viewer if open
    const modal = document.getElementById('pdf-modal');
    if (modal && modal.classList.contains('show')) {
        if (typeof closePdfPreview === 'function') closePdfPreview();
    }
}

// Function to arrange words alphabetically in a vertical list
function arrangeWordsAlphabetically() {
    const allWords = canvas.querySelectorAll('a');
    const currency = document.getElementById('currency');
    const wordsData = [];

    // Collect all words except margin elements
    allWords.forEach(word => {
        const id = word.id;
        if (id !== 'reset-word' && id !== 'borrador-word' && id !== 'minus-word' && id !== 'asterisk-word') {
            const text = word.textContent.trim().toLowerCase();
            if (text) {
                wordsData.push({ element: word, text: text });
            }
        }
    });

    // Also include currency element
    if (currency) {
        const currencyText = currency.textContent.trim().toLowerCase();
        if (currencyText) {
            wordsData.push({ element: currency, text: currencyText });
        }
    }

    // Sort alphabetically
    wordsData.sort((a, b) => a.text.localeCompare(b.text));

    // Arrange in vertical list starting from top-left
    const startX = 80;
    const startY = 80;
    const lineHeight = 35; // Vertical spacing between words

    wordsData.forEach((wordData, index) => {
        const word = wordData.element;
        word.style.display = 'block'; // Make sure it's visible
        word.style.left = startX + 'px';
        word.style.top = (startY + index * lineHeight) + 'px';
    });
}

// --- ENSURE WORD FUNCTIONS ---

window.ensureResetWord = function () {
    let resetWord = document.getElementById('reset-word');
    if (resetWord) return;
    resetWord = document.createElement('a');
    resetWord.id = 'reset-word';
    resetWord.href = '#';
    resetWord.style.position = 'absolute';
    resetWord.style.left = 'calc(100vw + 20px)';
    resetWord.style.top = '20px';
    resetWord.style.fontSize = '24px';
    resetWord.style.letterSpacing = '2px';
    resetWord.style.color = '#333';
    resetWord.style.cursor = 'move';
    resetWord.style.userSelect = 'none';
    const canvas = getCanvas();
    if (!canvas) return;
    canvas.appendChild(resetWord);
    createWordSlotMachine(resetWord, 'reset');
    addWordDragEvents(resetWord);
    // reset cancels grouping by redistributing randomly AND restores hidden words
    function resetAndRestoreWords() {
        // First restore visibility of all hidden words
        const allWords = canvas.querySelectorAll('a');
        const currency = document.getElementById('currency');
        allWords.forEach(word => {
            word.style.display = 'block';
        });
        // Also restore currency element
        if (currency) currency.style.display = 'block';
        // Then randomize positions
        randomizeAllWordPositions();
    }
    resetWord.addEventListener('click', (e) => { e.preventDefault(); resetAndRestoreWords(); });
    resetWord.addEventListener('contextmenu', (e) => { e.preventDefault(); resetAndRestoreWords(); });
}

window.ensureMinusWord = function () {
    let minusWord = document.getElementById('minus-word');
    if (minusWord) return;
    minusWord = document.createElement('a');
    minusWord.id = 'minus-word';
    minusWord.href = '#';
    minusWord.style.position = 'absolute';
    minusWord.style.left = 'calc(100vw + 20px)';
    minusWord.style.top = 'calc(100vh - 120px)';
    minusWord.style.fontSize = '24px';
    minusWord.style.letterSpacing = '2px';
    minusWord.style.color = '#333';
    minusWord.style.cursor = 'move';
    minusWord.style.userSelect = 'none';
    const canvas = getCanvas();
    if (!canvas) return;
    canvas.appendChild(minusWord);
    createWordSlotMachine(minusWord, '-');
    addWordDragEvents(minusWord);

    // Right-click hides all words except margin ones
    minusWord.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        // Hide all words except margin elements (reset, borrador, minus, asterisk)
        const allWords = canvas.querySelectorAll('a');
        const currency = document.getElementById('currency');
        allWords.forEach(word => {
            const id = word.id;
            if (id !== 'reset-word' && id !== 'borrador-word' && id !== 'minus-word' && id !== 'asterisk-word') {
                word.style.display = 'none';
            }
        });
        // Also hide currency element
        if (currency) currency.style.display = 'none';
    });

    // Mobile: double-tap hides words
    // (Handled by addWordDragEvents if implemented there, or here)
    // For now, sticking to the extracted logic which had explicit double tap handlers
    // But addWordDragEvents handles double tap for some elements. Let's add explicit here if needed.
    // The original code had addMobileDoubleTap. I should probably include that helper or integrate it.
    // addWordDragEvents handles double tap for specific IDs.
}

window.ensureSerpWord = function () {
    let serpWord = document.getElementById('serp-word');
    if (serpWord) return;
    serpWord = document.createElement('a');
    serpWord.id = 'serp-word';
    serpWord.href = '#';
    serpWord.style.position = 'absolute';
    serpWord.style.left = 'calc(100vw + 20px)';
    serpWord.style.top = 'calc(100vh - 40px)';
    serpWord.style.fontSize = '24px';
    serpWord.style.letterSpacing = '2px';
    serpWord.style.color = '#333';
    serpWord.style.cursor = 'move';
    serpWord.style.userSelect = 'none';
    const canvas = getCanvas();
    if (!canvas) return;
    canvas.appendChild(serpWord);
    createWordSlotMachine(serpWord, 'serp');
    addWordDragEvents(serpWord);

    // Right-click toggles snake
    serpWord.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        if (typeof toggleSnake === 'function') toggleSnake();
    });
}

window.ensureAsteriskWord = function () {
    let asteriskWord = document.getElementById('asterisk-word');
    if (asteriskWord) return;
    asteriskWord = document.createElement('a');
    asteriskWord.id = 'asterisk-word';
    asteriskWord.href = '#';
    asteriskWord.style.position = 'absolute';
    asteriskWord.style.left = 'calc(100vw + 20px)';
    asteriskWord.style.top = 'calc(100vh - 80px)';
    asteriskWord.style.fontSize = '24px';
    asteriskWord.style.letterSpacing = '2px';
    asteriskWord.style.color = '#333';
    asteriskWord.style.cursor = 'move';
    asteriskWord.style.userSelect = 'none';
    const canvas = getCanvas();
    if (!canvas) return;
    canvas.appendChild(asteriskWord);
    createWordSlotMachine(asteriskWord, '*');
    addWordDragEvents(asteriskWord);

    // Right-click arranges words alphabetically in a list
    asteriskWord.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        arrangeWordsAlphabetically();
    });
}

window.ensureBorradorWord = function () {
    let borradorWord = document.getElementById('borrador-word');
    if (borradorWord) return;
    borradorWord = document.createElement('a');
    borradorWord.id = 'borrador-word';
    borradorWord.href = '#';
    borradorWord.style.position = 'absolute';
    borradorWord.style.left = 'calc(100vw + 20px)';
    borradorWord.style.top = '60px';
    borradorWord.style.fontSize = '24px';
    borradorWord.style.letterSpacing = '2px';
    borradorWord.style.color = '#333';
    borradorWord.style.cursor = 'move';
    borradorWord.style.userSelect = 'none';
    const canvas = getCanvas();
    if (!canvas) return;
    canvas.appendChild(borradorWord);
    createWordSlotMachine(borradorWord, 'borrador');
    addWordDragEvents(borradorWord);
    // borrador clears images, pixels and closes pdfs
    function clearPixels() {
        try { canvas.querySelectorAll('.hazard-pixel').forEach(n => n.remove()); } catch { }
        try { if (hazardPatternTimer) { clearInterval(hazardPatternTimer); hazardPatternTimer = null; } } catch { }
    }
    borradorWord.addEventListener('click', (e) => { e.preventDefault(); resetAllImages(); clearPixels(); if (typeof clearAllMazes === 'function') clearAllMazes(); });
    borradorWord.addEventListener('contextmenu', (e) => { e.preventDefault(); resetAllImages(); clearPixels(); if (typeof clearAllMazes === 'function') clearAllMazes(); });
}

window.ensurePongWord = function () {
    let pongWord = document.getElementById('pong-word');
    if (pongWord) return;
    pongWord = document.createElement('a');
    pongWord.id = 'pong-word';
    pongWord.href = '#';
    pongWord.textContent = 'pong';
    pongWord.style.position = 'absolute';
    pongWord.style.fontSize = '24px';
    pongWord.style.letterSpacing = '2px';
    pongWord.style.color = '#333';
    pongWord.style.cursor = 'move';
    pongWord.style.userSelect = 'none';
    const canvas = getCanvas();
    if (!canvas) return;
    const c = canvas.getBoundingClientRect();
    canvas.appendChild(pongWord);
    createWordSlotMachine(pongWord, 'pong');
    addWordDragEvents(pongWord);

    // Right-click starts Pong game
    pongWord.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        if (typeof startPongGame === 'function') startPongGame(e.clientX, e.clientY);
    });
}

window.ensureStopWord = function () {
    let stopWord = document.getElementById('stop-word');
    if (stopWord) return; // already exists
    stopWord = document.createElement('a');
    stopWord.id = 'stop-word';
    stopWord.href = '#';
    stopWord.style.position = 'absolute';
    stopWord.style.fontSize = '24px';
    stopWord.style.letterSpacing = '2px';
    stopWord.style.color = '#333';
    stopWord.style.cursor = 'move';
    stopWord.style.userSelect = 'none';
    const canvas = getCanvas();
    if (!canvas) return;
    canvas.appendChild(stopWord);
    createWordSlotMachine(stopWord, 'stop!');
    addWordDragEvents(stopWord);
    placeElementInSafeArea(stopWord);
    // Right-click to freeze ALL slot machines (like other context actions)
    stopWord.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        window.__slotFrozen = true;
        window.__introFrozen = true; // stop any remaining intro timers just in case
        clearAllSlotIntervals();
        // Visual feedback: dim STOP a bit
        try { stopWord.style.opacity = '0.65'; } catch { }
    });
}

window.ensureStartWord = function () {
    let startWord = document.getElementById('start-word');
    if (startWord) return;
    startWord = document.createElement('a');
    startWord.id = 'start-word';
    startWord.href = '#';
    startWord.style.position = 'absolute';
    startWord.style.fontSize = '24px';
    startWord.style.letterSpacing = '2px';
    startWord.style.color = '#333';
    startWord.style.cursor = 'move';
    startWord.style.userSelect = 'none';
    const canvas = getCanvas();
    if (!canvas) return;
    canvas.appendChild(startWord);
    createWordSlotMachine(startWord, 'start');
    addWordDragEvents(startWord);
    placeElementInSafeArea(startWord);

    startWord.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        // Unfreeze
        window.__slotFrozen = false;
        // Restart slot machines for all words
        document.querySelectorAll('#canvas a').forEach(el => {
            if (el.id === 'stop-word') { el.style.opacity = '1'; return; }
            // Re-init slot machine if it has text content
            const text = el.textContent.trim();
            if (text && text.length > 0) {
                createWordSlotMachine(el, text);
            }
        });
    });
}

window.ensureTextWord = function () {
    let textWord = document.getElementById('text-word');
    if (textWord) return;
    textWord = document.createElement('a');
    textWord.id = 'text-word';
    textWord.href = '#';
    textWord.style.position = 'absolute';
    textWord.style.fontSize = '24px';
    textWord.style.letterSpacing = '2px';
    textWord.style.color = '#333';
    textWord.style.cursor = 'move';
    textWord.style.userSelect = 'none';
    const canvas = getCanvas();
    if (!canvas) return;
    canvas.appendChild(textWord);
    createWordSlotMachine(textWord, 'text');
    addWordDragEvents(textWord);
    placeElementInSafeArea(textWord);

    textWord.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        if (typeof openTextEditorModal === 'function') openTextEditorModal();
    });
}

window.ensureUnitatWord = function () {
    let unitatWord = document.getElementById('unitat-word');
    if (unitatWord) return;
    unitatWord = document.createElement('a');
    unitatWord.id = 'unitat-word';
    unitatWord.href = '#';
    unitatWord.style.position = 'absolute';
    unitatWord.style.fontSize = '24px';
    unitatWord.style.letterSpacing = '2px';
    unitatWord.style.color = '#333';
    unitatWord.style.cursor = 'move';
    unitatWord.style.userSelect = 'none';
    const canvas = getCanvas();
    if (!canvas) return;
    canvas.appendChild(unitatWord);
    createWordSlotMachine(unitatWord, 'unitat');
    addWordDragEvents(unitatWord);
    placeElementInSafeArea(unitatWord);

    // Group all words in center
    unitatWord.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        const allWords = canvas.querySelectorAll('a');
        const currency = document.getElementById('currency');
        const vw = window.innerWidth / zoomLevel;
        const vh = window.innerHeight / zoomLevel;
        const cx = vw / 2 - panX;
        const cy = vh / 2 - panY;

        allWords.forEach(word => {
            if (word.id.includes('snake')) return; // skip snake hud
            // Move towards center with some random scatter
            const scatter = 100;
            const tx = cx + (Math.random() * scatter - scatter / 2);
            const ty = cy + (Math.random() * scatter - scatter / 2);
            word.style.left = tx + 'px';
            word.style.top = ty + 'px';
        });
        if (currency) {
            currency.style.left = cx + 'px';
            currency.style.top = cy + 'px';
        }
    });
}

window.ensurePixelWord = function () {
    let el = document.getElementById('pixel-word');
    if (el) return el;
    el = document.createElement('a');
    el.id = 'pixel-word';
    el.href = '#';
    el.style.position = 'absolute';
    el.style.fontSize = '24px';
    el.style.letterSpacing = '2px';
    el.style.color = '#333';
    el.style.cursor = 'move';
    const canvas = getCanvas();
    if (!canvas) return el;
    canvas.appendChild(el);
    // Place in safe area initially
    try { placeElementInSafeArea(el); } catch { }
    // Slot machine effect and draggable behavior
    try { createWordSlotMachine(el, 'pixel'); } catch { el.textContent = 'pixel'; }
    try { addWordDragEvents(el); } catch { }
    // Right-click could also spawn hazards
    el.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (typeof spawnLoosePixels === 'function') spawnLoosePixels(28);
    });
    return el;
}

window.ensureLaberintWord = function () {
    let el = document.getElementById('laberint-word');
    if (el) return el;
    el = document.createElement('a');
    el.id = 'laberint-word';
    el.href = '#';
    el.style.position = 'absolute';
    el.style.fontSize = '24px';
    el.style.letterSpacing = '2px';
    el.style.color = '#333';
    el.style.cursor = 'move';
    const canvas = getCanvas();
    if (!canvas) return el;
    canvas.appendChild(el);
    try { placeElementInSafeArea(el); } catch { }
    try { createWordSlotMachine(el, 'laberint'); } catch { el.textContent = 'laberint'; }
    try { addWordDragEvents(el); } catch { }

    el.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        if (typeof spawnMaze === 'function') spawnMaze({ complexity: 1 });
    });
    return el;
}

window.ensure3dWord = function () {
    let el = document.getElementById('3d-word');
    if (el) return el;
    el = document.createElement('a');
    el.id = '3d-word';
    el.href = '#';
    el.style.position = 'absolute';
    el.style.fontSize = '24px';
    el.style.letterSpacing = '2px';
    el.style.color = '#333';
    el.style.cursor = 'move';
    el.style.userSelect = 'none';
    const canvas = getCanvas();
    if (!canvas) return el;
    canvas.appendChild(el);
    try { placeElementInSafeArea(el); } catch { }
    try { createWordSlotMachine(el, '3d'); } catch { el.textContent = '3d'; }
    try { addWordDragEvents(el); } catch { }

    el.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        if (typeof openStlViewer === 'function') {
            const demoFile = prompt('Introdueix la ruta de l\'arxiu STL:', 'model.stl');
            if (demoFile) {
                openStlViewer(demoFile);
            }
        }
    });
    return el;
}
