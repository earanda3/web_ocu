
// Global Elements
const tao = document.getElementById('tao');
window.tao = tao;
const canvas = document.getElementById('canvas');
window.canvas = canvas;
window.fonts = ['font-minecraft', 'font-oregular', 'font-helvetica', 'font-courier'];
const fonts = window.fonts;
const colorWord = document.getElementById('color-word');
const colorModal = document.getElementById('color-modal');
const bgColorInput = document.getElementById('bg-color-input');
const elColorInput = document.getElementById('el-color-input');
const colorCloseBtn = document.getElementById('color-close');
const colorResetBtn = document.getElementById('color-reset');

// Global State
window.zoomLevel = 1;
window.panX = 0;
window.panY = 0;
window.isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
window.__introHasPlayed = true; // Skip intro - show content directly
window.__introFrozen = false;
window.__slotFrozen = false;
window.__mainIntervals = [];
window.__currentBgColor = '#ffffff';
window.__currentElColor = '#333333';

// Intro content
const INTRO_WORDS_1 = ['Cada', 'Paraula', 'És', 'Un', 'Món'];
const INTRO_WORDS_2 = ['Aquest', 'És', "L'univers", 'ocu'];
const INTRO_FONTS_WEIGHTED = [
    'font-minecraft', 'font-helvetica', 'font-courier', 'font-oregular',
    'font-helvetica', 'font-courier', 'font-oregular',
    'font-minecraft'
];

let introIntervals = [];

// Slot-machine effect for intro (uses custom font list w/out O-Regular)
function createWordSlotMachineCustom(element, text, fontList) {
    element.innerHTML = '';
    const wrapper = document.createElement('span');
    wrapper.className = 'word-wrap in';
    const frag = document.createDocumentFragment();
    Array.from(text).forEach((ch, i) => {
        const span = document.createElement('span');
        span.className = 'letter';
        span.textContent = ch;
        // initial random font from provided list
        const startFont = fontList[Math.floor(Math.random() * fontList.length)];
        span.classList.add(startFont);
        frag.appendChild(span);

        // slot spin per letter (ràpid i esglaonat)
        if (!window.__introFrozen) {
            const intervalId = setInterval(() => {
                if (window.__introFrozen) { return; }
                // remove all known fonts, then add a new one
                fonts.forEach(f => span.classList.remove(f));
                const newFont = fontList[Math.floor(Math.random() * fontList.length)];
                span.classList.add(newFont);
                // tiny squash like a reel tick
                span.style.transform = 'scaleY(0.85)';
                setTimeout(() => { span.style.transform = 'scaleY(1)'; }, 70);
            }, 180 + (i * 20));
            introIntervals.push(intervalId);
        }
    });
    wrapper.appendChild(frag);
    // position context for absolute ghost
    element.style.position = 'relative';
    element.appendChild(wrapper);

    // curtain reveal
    element.classList.remove('reveal');
    void element.offsetWidth;
    element.classList.add('reveal');
    // delayed show for wrapper for smooth entrance
    requestAnimationFrame(() => wrapper.classList.add('show'));
}

function clearIntroIntervals() {
    try { introIntervals.forEach(id => clearInterval(id)); } catch { }
    introIntervals = [];
}

// Global clear for main slot-machine intervals
function clearMainIntervals() {
    try {
        if (window.__mainIntervals && Array.isArray(window.__mainIntervals)) {
            window.__mainIntervals.forEach(id => clearInterval(id));
        }
    } catch { }
    window.__mainIntervals = [];
}

function clearAllSlotIntervals() {
    // Set global freeze so future words don't start spinning
    window.__slotFrozen = true;
    clearIntroIntervals();
    clearMainIntervals();
}

// Spawn a draggable intro word within a central safe area of the viewport
function spawnIntroWord(text, fontList) {
    const el = document.createElement('a');
    el.href = '#';
    el.className = 'intro-free-word';
    el.style.position = 'absolute';
    el.style.fontSize = '24px';
    el.style.color = '#333';
    el.style.cursor = 'move';
    el.style.userSelect = 'none';
    el.style.letterSpacing = '2px';

    // Pick random position within viewport center area, not too close to edges
    const margin = 150;
    const vw = window.innerWidth;
    const vh = window.innerHeight;

    const cx = Math.floor(margin + Math.random() * (vw - margin * 2));
    const cy = Math.floor(margin + Math.random() * (vh - margin * 2));

    el.style.left = cx + 'px';
    el.style.top = cy + 'px';

    // Apply slot machine effect
    createWordSlotMachineCustom(el, text, fontList);

    // Add to canvas
    const canvas = document.getElementById('canvas');
    canvas.appendChild(el);

    // Add drag functionality
    if (typeof addWordDragEvents === 'function') {
        addWordDragEvents(el);
    }

    return el;
}

function playIntro() {
    // One-time guard to prevent replaying intro (e.g., on Space key etc.)
    if (window.__introHasPlayed) {
        const overlay = document.getElementById('intro-overlay');
        if (overlay) overlay.remove();
        document.body.classList.remove('intro-active');
        return;
    }
    const overlay = document.getElementById('intro-overlay');
    if (overlay) overlay.remove();
    document.body.classList.add('intro-active');
    window.__introFrozen = false;

    let spawnedEls = [];

    let __introKeydownHandler = null;

    function endIntro() {
        clearIntroIntervals();
        spawnedEls.forEach(el => { try { el.remove(); } catch { } });
        document.body.classList.remove('intro-active');
        window.__introHasPlayed = true;
        if (__introKeydownHandler) {
            try { document.removeEventListener('keydown', __introKeydownHandler, true); } catch { }
            __introKeydownHandler = null;
        }
        // Ensure all interactive words are present
        const ensureFunctions = [
            'ensureStopWord', 'ensureStartWord', 'ensureTextWord', 'ensureUnitatWord',
            'ensureResetWord', 'ensureBorradorWord', 'ensureMinusWord', 'ensureAsteriskWord',
            'ensureSerpWord', 'ensurePixelWord', 'ensureLaberintWord', 'ensurePongWord',
            'ensure3dWord'
        ];

        ensureFunctions.forEach(fnName => {
            if (typeof window[fnName] === 'function') {
                try { window[fnName](); } catch { }
            }
        });
    }


    // Spawn a sequence and hold the last word extraMs longer (others fade out)
    function playSequence(words, extraMs, onDone) {
        let i = 0;
        const base = 1350;
        const localEls = [];
        const spawnNext = () => {
            if (i >= words.length) return;
            const el = spawnIntroWord(words[i], INTRO_FONTS_WEIGHTED);
            localEls.push(el);
            spawnedEls.push(el);
            i++;
            const jitter = Math.floor(Math.random() * 120) - 60;
            setTimeout(spawnNext, Math.max(420, base + jitter));
            if (i === words.length) {
                setTimeout(() => {
                    const last = localEls[localEls.length - 1];
                    localEls.slice(0, -1).forEach(node => {
                        try {
                            node.classList.add('fade-out');
                            setTimeout(() => node.remove(), 450);
                        } catch { }
                    });
                    // Lock last word so it cannot be dragged during solo
                    try {
                        if (last) {
                            last.style.pointerEvents = 'none';
                            last.style.cursor = 'default';
                        }
                    } catch { }
                    const baseHold = 2200; // base solo time for any last word
                    setTimeout(() => {
                        try { if (last) last.classList.add('fade-out'); } catch { }
                        setTimeout(() => {
                            // remove last from DOM as well before continuing
                            try { if (last) last.remove(); } catch { }
                            if (typeof onDone === 'function') onDone();
                        }, 480);
                    }, baseHold + extraMs);
                }, 200);
            }
        };
        spawnNext();
    }

    // Allow skipping intro with Enter (desktop) or double-tap (mobile)
    __introKeydownHandler = (ev) => {
        if (ev.key === 'Enter') {
            ev.preventDefault();
            ev.stopPropagation();
            endIntro();
        }
    };
    document.addEventListener('keydown', __introKeydownHandler, true);

    // Mobile: double-tap to skip intro
    let introLastTouchTime = 0;
    const introTouchHandler = (e) => {
        const now = Date.now();
        const timeDiff = now - introLastTouchTime;
        if (timeDiff < 300 && timeDiff > 0) {
            // Double-tap detected - skip intro
            e.preventDefault();
            endIntro();
            document.removeEventListener('touchstart', introTouchHandler, true);
        }
        introLastTouchTime = now;
    };
    document.addEventListener('touchstart', introTouchHandler, true);

    // Play two parts with adjusted solo timings:
    // Part 1: 'Món' no manté més temps que la resta (reduïm la seva solo time a ~350ms)
    // Part 2: 'ocu' només una mica més que la resta (~700ms)
    playSequence(INTRO_WORDS_1, -1850, () => {
        playSequence(INTRO_WORDS_2, 500, () => {
            endIntro();
        });
    });
}

// Execute intro to load words but end it immediately (no animation visible)
window.addEventListener('load', () => {
    // Set flag to skip intro animation
    window.__introHasPlayed = false;
    
    // Start intro (this loads all the words)
    playIntro();
    
    // End intro immediately after 50ms (just enough time to start)
    setTimeout(() => {
        // Find and trigger Enter key to skip intro
        const event = new KeyboardEvent('keydown', { key: 'Enter' });
        document.dispatchEvent(event);
    }, 50);
});

// Color generation utility
function generateRandomColor() {
    // Generate random RGB values
    const r = Math.floor(Math.random() * 256);
    const g = Math.floor(Math.random() * 256);
    const b = Math.floor(Math.random() * 256);

    // Convert to hex
    return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
}
