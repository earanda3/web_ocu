
let snakeActive = false;
let snake = [];
let snakeDir = 'right';
let snakeTimer = null;
let snakeLayer = null;
let snakeScore = 0;
let lastHudScore = -1;
let snakeHighScore = 0;
try { snakeHighScore = parseInt(localStorage.getItem('snakeHighScore') || '0'); } catch { }

const SNAKE_SIZE = 10;
const SNAKE_BASE_MS = 85;
const SNAKE_MIN_MS = 30;

function getSnakeSpeed() {
    // Speed up as length grows (or score grows). Start with base, subtract a bit per 3 segments.
    const grow = Math.max(0, snake.length - 4);
    const step = Math.floor(grow / 3);
    return Math.max(SNAKE_MIN_MS, SNAKE_BASE_MS - step * 5);
}

// HUD helpers
let snakeHud = null;
let snakeStartTime = null;
let snakeTimeTimer = null;

function formatTime(ms) {
    const total = Math.max(0, Math.floor(ms / 1000));
    const m = Math.floor(total / 60);
    const s = total % 60;
    const mm = String(m).padStart(2, '0');
    const ss = String(s).padStart(2, '0');
    return `${mm}:${ss}`;
}

function updateHudWord(el, text) {
    if (!el) return;
    const spans = el.querySelectorAll('span.letter');
    if (spans.length === text.length) {
        for (let i = 0; i < spans.length; i++) spans[i].textContent = text[i];
    } else {
        try { createWordSlotMachine(el, text); } catch { el.textContent = text; }
    }
}

function ensureSnakeHud() {
    if (!snakeHud) {
        snakeHud = document.createElement('div');
        snakeHud.id = 'snake-hud';
        // Smaller than other words (24px) -> use 18px-20px
        snakeHud.innerHTML = `
            <a id="punts-word" href="#" style="display:block; font-size: 18px; letter-spacing: 2px; cursor: default; user-select: none;"></a>
            <a id="punts2-word" href="#" style="display:block; margin-top: 2px; font-size: 18px; letter-spacing: 2px; cursor: default; user-select: none;"></a>
            <a id="temps-word" href="#" style="display:block; margin-top: 4px; font-size: 16px; letter-spacing: 2px; cursor: default; user-select: none;"></a>
        `;
        document.body.appendChild(snakeHud);
        // Build slot machine effect for the HUD words
        const punts = snakeHud.querySelector('#punts-word');
        if (punts) {
            try { createWordSlotMachine(punts, '0'); } catch { punts.textContent = '0'; }
        }
        const punts2 = snakeHud.querySelector('#punts2-word');
        if (punts2) {
            try { createWordSlotMachine(punts2, '0'); } catch { punts2.textContent = '0'; }
            // Color to match snake 2 body
            try { punts2.style.color = 'blue'; } catch { }
        }
        const temps = snakeHud.querySelector('#temps-word');
        if (temps) {
            try { createWordSlotMachine(temps, '00:00'); } catch { temps.textContent = '00:00'; }
        }
        // Apply current color immediately for snake1 score and time
        if (window.__currentElColor) {
            try { punts.style.color = window.__currentElColor; } catch { }
            try { temps.style.color = window.__currentElColor; } catch { }
        }
    }
}

function updateSnakeHud() {
    ensureSnakeHud();
    // Update live score and time
    const punts = snakeHud.querySelector('#punts-word');
    const temps = snakeHud.querySelector('#temps-word');
    if (snakeScore !== lastHudScore) {
        // On score change, rerun slot-machine effect for feedback
        try { createWordSlotMachine(punts, String(snakeScore)); }
        catch { updateHudWord(punts, String(snakeScore)); }
        lastHudScore = snakeScore;
    } else {
        updateHudWord(punts, String(snakeScore));
    }
    if (snakeStartTime) {
        updateHudWord(temps, formatTime(Date.now() - snakeStartTime));
    }
    snakeHud.classList.remove('hidden');
}

function hideSnakeCurrentScoreKeepHi() {
    ensureSnakeHud();
    // Keep HUD visible; nothing else to do
}

function ensureSnakeLayer() {
    if (!snakeLayer) {
        snakeLayer = document.createElement('div');
        snakeLayer.id = 'snake-layer';
        canvas.appendChild(snakeLayer);
    }
}

function spawnSnake() {
    ensureSnakeLayer();
    ensureSnakeHud();
    // Start at the absolute center of the screen viewport, not canvas coordinates
    const viewportCenterX = Math.round(window.innerWidth / 2);
    const viewportCenterY = Math.round(window.innerHeight / 2);

    // Convert viewport center to canvas coordinates accounting for zoom and pan
    const canvasX = Math.round(viewportCenterX / zoomLevel) - panX;
    const canvasY = Math.round(viewportCenterY / zoomLevel) - panY;

    // Ensure snake spawns aligned to grid for clean movement
    const gridAlignedX = Math.round(canvasX / SNAKE_SIZE) * SNAKE_SIZE;
    const gridAlignedY = Math.round(canvasY / SNAKE_SIZE) * SNAKE_SIZE;

    snake = [
        { x: gridAlignedX - 3 * SNAKE_SIZE, y: gridAlignedY },
        { x: gridAlignedX - 2 * SNAKE_SIZE, y: gridAlignedY },
        { x: gridAlignedX - SNAKE_SIZE, y: gridAlignedY },
        { x: gridAlignedX, y: gridAlignedY }
    ];
    snakeDir = 'right';
    snakeScore = 0;
    updateSnakeHud();
    renderSnake();
    // Do not start time here; the timer starts only after colliding with the PIXEL word
}

function destroySnake() {
    snake = [];
    if (snakeLayer) snakeLayer.innerHTML = '';
    if (snakeTimer) { clearInterval(snakeTimer); snakeTimer = null; }
    if (snakeTimeTimer) { clearInterval(snakeTimeTimer); snakeTimeTimer = null; }

    // Clean up pixel mode goal
    try {
        if (pixelModeGoal && pixelModeGoal.parentNode) {
            pixelModeGoal.parentNode.removeChild(pixelModeGoal);
        }
        if (pixelGoalTimer) {
            clearInterval(pixelGoalTimer);
            pixelGoalTimer = null;
        }
        pixelModeGoal = null;
    } catch { }

    // Persist HI
    try {
        if (snakeScore > snakeHighScore) {
            snakeHighScore = snakeScore;
            localStorage.setItem('snakeHighScore', String(snakeHighScore));
        }
    } catch { }
    updateSnakeHud();
    hideSnakeCurrentScoreKeepHi();
    // Hide D-pad
    removeDpadOverlay();
}

function toggleSnake() {
    // If awaiting reset, clear the flag and reset
    if (window.__snakeAwaitingReset) {
        try { snakeScore = 0; } catch { }
        try { snakeStartTime = null; } catch { }
        try { updateSnakeHud(); } catch { }
        window.__snakeAwaitingReset = false;
    }

    snakeActive = !snakeActive;
    if (snakeActive) {
        spawnSnake();
        if (snakeTimer) clearInterval(snakeTimer);
        snakeTimer = setInterval(moveSnakeTick, getSnakeSpeed());
        // Show D-pad on mobile
        if (isMobile) {
            createDpadOverlay();
        }
    } else {
        destroySnake();
        // Hide D-pad
        removeDpadOverlay();
    }
}

function renderSnake() {
    if (!snakeLayer) return;
    const frag = document.createDocumentFragment();
    snakeLayer.innerHTML = '';
    const segColor = (window.__currentElColor || '#333');
    for (let i = 0; i < snake.length; i++) {
        const seg = snake[i];
        const px = document.createElement('div');
        px.className = 'snake-pixel';
        px.style.left = seg.x + 'px';
        px.style.top = seg.y + 'px';
        // Use current elements color for all segments (head included)
        px.style.background = segColor;
        frag.appendChild(px);
    }
    snakeLayer.appendChild(frag);
}

// Helpers: maze interactions for the snake
function getElementCanvasPosition(el) {
    // Returns {left, top} in canvas coordinate space (numbers)
    const left = parseFloat(el.style.left || '0');
    const top = parseFloat(el.style.top || '0');
    return { left: isNaN(left) ? 0 : left, top: isNaN(top) ? 0 : top };
}

function snakeMazeCheck(x, y) {
    // x,y are snake head (top-left) in canvas coords. Sample near center.
    if (!window.__mazes || !window.__mazes.length) return null;
    const cx = x + Math.floor(SNAKE_SIZE / 2);
    const cy = y + Math.floor(SNAKE_SIZE / 2);
    for (const m of window.__mazes) {
        const el = m.el;
        if (!el || !el.getContext) continue;
        const pos = getElementCanvasPosition(el);
        const sc = (m.scale || 1);
        const lx = (cx - pos.left) / sc;
        const ly = (cy - pos.top) / sc;
        if (lx < 0 || ly < 0 || lx >= el.width || ly >= el.height) continue;
        // Check goal proximity first using stored metadata if available
        const gx = m.goalX != null ? m.goalX : (el.width - Math.round(m.cellSize * 0.5));
        const gy = m.goalY != null ? m.goalY : (el.height - Math.round(m.cellSize * 0.5));
        const gr = m.goalR != null ? m.goalR : Math.max(1, Math.floor(Math.max(2, Math.round(m.cellSize * 0.28)) / 2));
        const dd = Math.hypot(lx - gx, ly - gy);
        if (dd <= gr + Math.max(0, Math.floor(SNAKE_SIZE * 0.25))) {
            // Reached exit -> remove current maze and spawn next with increased complexity
            try {
                const next = Math.min(10, (m.complexity || 1) + 1);
                window.__mazeProgress = next;
                // Remove current canvas, portal and metadata entry
                if (m._observer && m._observer.disconnect) m._observer.disconnect();
                if (m.portalTimer) { try { clearInterval(m.portalTimer); } catch { } }
                if (m.portalEl && m.portalEl.parentNode) m.portalEl.parentNode.removeChild(m.portalEl);
                if (m.el && m.el.parentNode) m.el.parentNode.removeChild(m.el);
                const idx = window.__mazes.indexOf(m);
                if (idx >= 0) window.__mazes.splice(idx, 1);
                // Spawn new maze; ALWAYS fullscreen for snake progression
                if (typeof spawnMaze === 'function') {
                    spawnMaze({ complexity: next, fullscreen: true });
                }
            } catch { }
            return 'goal';
        }
        // Sample a few points around center to detect wall stroke alpha
        const ctx = el.getContext('2d');
        const samples = [
            { x: lx, y: ly },
            { x: lx - Math.floor(SNAKE_SIZE / 2), y: ly },
            { x: lx + Math.floor(SNAKE_SIZE / 2), y: ly },
            { x: lx, y: ly - Math.floor(SNAKE_SIZE / 2) },
            { x: lx, y: ly + Math.floor(SNAKE_SIZE / 2) },
        ];
        for (const s of samples) {
            if (s.x < 0 || s.y < 0 || s.x >= el.width || s.y >= el.height) continue;
            const a = ctx.getImageData(s.x, s.y, 1, 1).data[3];
            if (a > 0) {
                // Hit a wall stroke (alpha present)
                return 'wall';
            }
        }
    }
    return null;
}

function moveSnakeTick() {
    if (!snakeActive || !snake.length) return;
    const head = snake[snake.length - 1];
    let nx = head.x;
    let ny = head.y;
    if (snakeDir === 'right') nx += SNAKE_SIZE;
    else if (snakeDir === 'left') nx -= SNAKE_SIZE;
    else if (snakeDir === 'up') ny -= SNAKE_SIZE;
    else if (snakeDir === 'down') ny += SNAKE_SIZE;

    // Movement within visible viewport (canvas coords)
    const vw = Math.floor(window.innerWidth / (window.zoomLevel || 1));
    const vh = Math.floor(window.innerHeight / (window.zoomLevel || 1));
    const maxX = vw - SNAKE_SIZE;
    const maxY = vh - SNAKE_SIZE;
    const minX = -panX;
    const minY = -panY;
    const isDefaultZoom = (window.zoomLevel || 1) === 1;
    if (isDefaultZoom) {
        // Wrap only at default dimensions
        if (nx > maxX) nx = minX;
        if (nx < minX) nx = maxX;
        if (ny > maxY) ny = minY;
        if (ny < minY) ny = maxY;
    } else {
        // When zoomed, clamp to visible viewport
        if (nx > maxX) nx = maxX;
        if (nx < minX) nx = minX;
        if (ny > maxY) ny = maxY;
        if (ny < minY) ny = minY;
    }

    // Move snake forward (push new head)
    snake.push({ x: nx, y: ny });

    // Collision check with canvas children (excluding snake layer itself)
    let ate = false;
    try { ate = handleSnakeCollision(nx, ny) === true; } catch { ate = false; }

    // If not eating, remove tail; if eating image, keep tail (grow by 1)
    if (!ate) {
        snake.shift();
    } else {
        // Grew -> add points and speed up
        snakeScore += 1;
        updateSnakeHud();
        if (snakeTimer) { clearInterval(snakeTimer); }
        snakeTimer = setInterval(moveSnakeTick, getSnakeSpeed());
    }
    renderSnake();
}

function handleSnakeCollision(x, y) {
    // First: check collision with any maze walls or goal
    try {
        const res = snakeMazeCheck(x, y);
        if (res === 'wall') {
            // Maze wall -> game over behavior, similar to hazard pixel
            try { exitMazeFocus(); } catch { }
            window.__snakeAwaitingReset = true;
            destroySnake();
            snakeActive = false;

            return false;
        } else if (res === 'goal') {
            // Goal reached -> spawn next maze already handled in check; continue game
            // Score: +1 per maze surpassed
            try { snakeScore += 1; updateSnakeHud(); } catch { }
            return false;
        }
    } catch { }

    // Canvas-space collision: compare snake head rect to element CSS positions (zoom/pan independent, works on mobile).
    const headR = x + SNAKE_SIZE, headB = y + SNAKE_SIZE;
    let target = null;
    if (canvas) {
        const children = canvas.children;
        for (let i = children.length - 1; i >= 0; i--) {
            const el = children[i];
            if (!el) continue;
            if (el.id === 'snake-layer'  || el.id === 'snake-hud' ||
                el.id === 'snake2-layer' || el.id === 'snake2-hud') continue;
            if (el.classList && (el.classList.contains('maze-resize-handle') || el.classList.contains('maze-move-handle'))) continue;
            const elL = parseFloat(el.style.left) || 0;
            const elT = parseFloat(el.style.top)  || 0;
            const elR = elL + (el.offsetWidth  || 0);
            const elB = elT + (el.offsetHeight || 0);
            if (headR > elL && x < elR && headB > elT && y < elB) { target = el; break; }
        }
    }
    // Fallback: PDF elements may be fixed/outside canvas — use elementsFromPoint only for them
    if (!target) {
        try {
            const c = canvas.getBoundingClientRect();
            const zl = window.zoomLevel || 1;
            const cx2 = c.left + (x + SNAKE_SIZE / 2) * zl;
            const cy2 = c.top  + (y + SNAKE_SIZE / 2) * zl;
            const els = document.elementsFromPoint(cx2, cy2) || [];
            for (const el of els) {
                if (el.closest && (el.closest('#pdf-modal') || el.closest('#pdf-container'))) {
                    target = el; break;
                }
            }
        } catch { }
    }
    if (!target) return;

    // If we hit a letter/span inside a word, promote target to its actionable ancestor
    if (target.closest) {
        const actionable = target.closest('#canvas a, #canvas > *');
        if (actionable && actionable !== canvas) target = actionable;
    }

    // Eat PDF viewer (modal or inline container)
    if (target.closest && (target.closest('#pdf-modal') || target.closest('#pdf-container'))) {
        try {
            const modal = document.getElementById('pdf-modal');
            if (modal && modal.classList && modal.classList.contains('show')) {
                // Use existing close helper if available
                if (typeof closePdfPreview === 'function') closePdfPreview();
                else modal.remove();
            }
            const container = document.getElementById('pdf-container');
            if (container && container.parentNode) container.remove();
        } catch { }
        return true;
    }

    if (target.tagName && target.tagName.toLowerCase() === 'img') {
        // Remove images on hit
        try { target.remove(); } catch { }
        return true; // ate image -> grow
    }

    // If snake hits the word "color": randomize app colors (only snake does this)
    if ((target.id && target.id === 'color-word') || (target.textContent && target.textContent.trim().toLowerCase() === 'color')) {
        try {
            const rnd = () => '#' + Math.floor(Math.random() * 16777215).toString(16).padStart(6, '0');
            const bg = rnd();
            const el = rnd();
            if (typeof applyColors === 'function') applyColors(bg, el);
            if (typeof saveColors === 'function') saveColors(bg, el);
        } catch { }
        return false;
    }

    // Trigger hazard spawn when hitting the word "pixel"
    if ((target.id && target.id === 'pixel-word') || (target.textContent && target.textContent.trim().toLowerCase() === 'pixel')) {
        // Start time counter on first collision with PIXEL word
        try {
            if (!snakeStartTime) {
                snakeStartTime = Date.now();
                if (snakeTimeTimer) { clearInterval(snakeTimeTimer); snakeTimeTimer = null; }
                snakeTimeTimer = setInterval(() => { try { updateSnakeHud(); } catch { } }, 1000);
                updateSnakeHud();
            }
        } catch { }
        try { spawnLoosePixels(28); } catch { }
        try { spawnPixelModeGoal(); } catch { }
        return false;
    }

    // Check collision with multicolor pixel goal
    if (target.classList && target.classList.contains('pixel-goal')) {
        // Score increase
        snakeScore++;
        updateSnakeHud();

        // Remove current goal and spawn new one
        try {
            if (pixelModeGoal && pixelModeGoal.parentNode) {
                pixelModeGoal.parentNode.removeChild(pixelModeGoal);
            }
            if (pixelGoalTimer) {
                clearInterval(pixelGoalTimer);
                pixelGoalTimer = null;
            }
        } catch { }

        // Spawn new goal after short delay
        setTimeout(() => {
            try { spawnPixelModeGoal(); } catch { }
        }, 500);

        return true; // Continue game
    }

    // If hitting a hazard pixel -> game over (snake disappears), clear pixels, freeze HUD until Enter reset
    if (target.classList && target.classList.contains('hazard-pixel')) {
        try {
            // Clear all hazard pixels and stop pattern timer
            canvas.querySelectorAll('.hazard-pixel').forEach(n => n.remove());
            if (hazardPatternTimer) { clearTimeout(hazardPatternTimer); hazardPatternTimer = null; }
        } catch { }
        // Flag awaiting reset
        window.__snakeAwaitingReset = true;
        destroySnake();
        snakeActive = false;

        return false;
    }

    // Dispatch a synthetic contextmenu at head position on the promoted target
    const evt = new MouseEvent('contextmenu', {
        bubbles: true,
        cancelable: true,
        clientX, clientY,
        view: window
    });
    // Mark that the spawn is originated by the snake so generators can randomize placement/size
    window.__spawnFromSnake = true;
    try { target.dispatchEvent(evt); } finally {
        setTimeout(() => { window.__spawnFromSnake = false; }, 0);
    }
    return false;
}

// Second snake implementation
let snake2Active = false;
let snake2 = [];
let snake2Dir = 'right';
let snake2Score = 0;
let snake2Timer = null;
let snake2Hud = document.getElementById('snake2-hud');

// Ensure second snake layer exists
function ensureSnake2Layer() {
    let layer = document.getElementById('snake2-layer');
    if (!layer) {
        layer = document.createElement('div');
        layer.id = 'snake2-layer';
        canvas.appendChild(layer);
    }
}

// Ensure second snake HUD exists (fixed on the right)
function ensureSnake2Hud() {
    if (!snake2Hud) {
        snake2Hud = document.createElement('div');
        snake2Hud.id = 'snake2-hud';
        snake2Hud.style.position = 'fixed';
        snake2Hud.style.top = '16px';
        snake2Hud.style.right = '16px';
        snake2Hud.style.fontSize = '16px';
        snake2Hud.style.letterSpacing = '2px';
        snake2Hud.style.userSelect = 'none';
        snake2Hud.style.pointerEvents = 'none';
        // match current element color
        if (window.__currentElColor) {
            try { snake2Hud.style.color = window.__currentElColor; } catch { }
        }
        snake2Hud.textContent = 'Snake 2 Score: 0';
        document.body.appendChild(snake2Hud);
    }
}

// Spawn second snake centered
function spawnSnake2() {
    ensureSnake2Layer();
    // Center of viewport -> canvas coords
    const viewportCenterX = Math.round(window.innerWidth / 2);
    const viewportCenterY = Math.round(window.innerHeight / 2);
    const canvasX = Math.round(viewportCenterX / zoomLevel) - panX;
    const canvasY = Math.round(viewportCenterY / zoomLevel) - panY;
    const gridAlignedX = Math.round(canvasX / SNAKE_SIZE) * SNAKE_SIZE;
    const gridAlignedY = Math.round(canvasY / SNAKE_SIZE) * SNAKE_SIZE;
    // Offset a bit vertically so both snakes don't overlap exactly
    const oy = gridAlignedY + 2 * SNAKE_SIZE;
    snake2 = [
        { x: gridAlignedX - 3 * SNAKE_SIZE, y: oy },
        { x: gridAlignedX - 2 * SNAKE_SIZE, y: oy },
        { x: gridAlignedX - 1 * SNAKE_SIZE, y: oy },
        { x: gridAlignedX, y: oy }
    ];
    snake2Dir = 'right';
    snake2Score = 0;
    updateSnake2Hud();
    renderSnake2();
}

// Toggle second snake with timer
function toggleSnake2() {
    if (window.__snakeAwaitingReset) {
        try { snake2Score = 0; } catch { }
        try { updateSnake2Hud(); } catch { }
        window.__snakeAwaitingReset = false;
    }

    snake2Active = !snake2Active;
    if (snake2Active) {
        spawnSnake2();
        if (snake2Timer) clearInterval(snake2Timer);
        snake2Timer = setInterval(moveSnake2Tick, getSnakeSpeed());
    } else {
        destroySnake2();
    }
}

function moveSnake2Tick() {
    if (!snake2Active || !snake2.length) return;
    const head = snake2[snake2.length - 1];
    let nx = head.x;
    let ny = head.y;
    if (snake2Dir === 'right') nx += SNAKE_SIZE;
    else if (snake2Dir === 'left') nx -= SNAKE_SIZE;
    else if (snake2Dir === 'up') ny -= SNAKE_SIZE;
    else if (snake2Dir === 'down') ny += SNAKE_SIZE;

    // Movement within visible viewport (canvas coords)
    const vw = Math.floor(window.innerWidth / (window.zoomLevel || 1));
    const vh = Math.floor(window.innerHeight / (window.zoomLevel || 1));
    const maxX = vw - SNAKE_SIZE;
    const maxY = vh - SNAKE_SIZE;
    const minX = -panX;
    const minY = -panY;
    const isDefaultZoom = (window.zoomLevel || 1) === 1;
    if (isDefaultZoom) {
        // Wrap only at default dimensions
        if (nx > maxX) nx = minX;
        if (nx < minX) nx = maxX;
        if (ny > maxY) ny = minY;
        if (ny < minY) ny = maxY;
    } else {
        // When zoomed, clamp to visible viewport
        if (nx > maxX) nx = maxX;
        if (nx < minX) nx = minX;
        if (ny > maxY) ny = maxY;
        if (ny < minY) ny = minY;
    }

    // Move snake forward (push new head)
    snake2.push({ x: nx, y: ny });

    // Collision check with canvas children (excluding snake layer itself)
    let ate = false;
    try { ate = handleSnake2Collision(nx, ny) === true; } catch { ate = false; }

    // If not eating, remove tail; if eating image, keep tail (grow by 1)
    if (!ate) {
        snake2.shift();
    } else {
        // Grew -> add points and speed up
        snake2Score += 1;
        updateSnake2Hud();
        if (snake2Timer) { clearInterval(snake2Timer); }
        snake2Timer = setInterval(moveSnake2Tick, getSnakeSpeed());
    }
    renderSnake2();
}

function handleSnake2Collision(x, y) {
    // First: check collision with any maze walls or goal
    try {
        const res = snakeMazeCheck(x, y);
        if (res === 'wall') {
            // Maze wall -> game over behavior, similar to hazard pixel
            try { exitMazeFocus(); } catch { }
            window.__snakeAwaitingReset = true;
            destroySnake2();
            snake2Active = false;

            return false;
        } else if (res === 'goal') {
            // Goal reached -> spawn next maze already handled in check; continue game
            // Score: +1 per maze surpassed
            try { snake2Score += 1; updateSnake2Hud(); } catch { }
            return false;
        }
    } catch { }

    // Canvas-space collision: compare snake head rect to element CSS positions (zoom/pan independent, works on mobile).
    const headR = x + SNAKE_SIZE, headB = y + SNAKE_SIZE;
    let target = null;
    if (canvas) {
        const children = canvas.children;
        for (let i = children.length - 1; i >= 0; i--) {
            const el = children[i];
            if (!el) continue;
            if (el.id === 'snake-layer'  || el.id === 'snake-hud' ||
                el.id === 'snake2-layer' || el.id === 'snake2-hud') continue;
            if (el.classList && (el.classList.contains('maze-resize-handle') || el.classList.contains('maze-move-handle'))) continue;
            const elL = parseFloat(el.style.left) || 0;
            const elT = parseFloat(el.style.top)  || 0;
            const elR = elL + (el.offsetWidth  || 0);
            const elB = elT + (el.offsetHeight || 0);
            if (headR > elL && x < elR && headB > elT && y < elB) { target = el; break; }
        }
    }
    // Fallback: PDF elements may be fixed/outside canvas — use elementsFromPoint only for them
    if (!target) {
        try {
            const c = canvas.getBoundingClientRect();
            const zl = window.zoomLevel || 1;
            const cx2 = c.left + (x + SNAKE_SIZE / 2) * zl;
            const cy2 = c.top  + (y + SNAKE_SIZE / 2) * zl;
            const els = document.elementsFromPoint(cx2, cy2) || [];
            for (const el of els) {
                if (el.closest && (el.closest('#pdf-modal') || el.closest('#pdf-container'))) {
                    target = el; break;
                }
            }
        } catch { }
    }
    if (!target) return;

    // If we hit a letter/span inside a word, promote target to its actionable ancestor
    if (target.closest) {
        const actionable = target.closest('#canvas a, #canvas > *');
        if (actionable && actionable !== canvas) target = actionable;
    }

    // Eat PDF viewer (modal or inline container)
    if (target.closest && (target.closest('#pdf-modal') || target.closest('#pdf-container'))) {
        try {
            const modal = document.getElementById('pdf-modal');
            if (modal && modal.classList && modal.classList.contains('show')) {
                // Use existing close helper if available
                if (typeof closePdfPreview === 'function') closePdfPreview();
                else modal.remove();
            }
            const container = document.getElementById('pdf-container');
            if (container && container.parentNode) container.remove();
        } catch { }
        return true;
    }

    if (target.tagName && target.tagName.toLowerCase() === 'img') {
        // Remove images on hit
        try { target.remove(); } catch { }
        return true; // ate image -> grow
    }

    // If snake hits the word "color": randomize app colors (only snake does this)
    if ((target.id && target.id === 'color-word') || (target.textContent && target.textContent.trim().toLowerCase() === 'color')) {
        try {
            const rnd = () => '#' + Math.floor(Math.random() * 16777215).toString(16).padStart(6, '0');
            const bg = rnd();
            const el = rnd();
            if (typeof applyColors === 'function') applyColors(bg, el);
            if (typeof saveColors === 'function') saveColors(bg, el);
        } catch { }
        return false;
    }

    // Trigger hazard spawn when hitting the word "pixel"
    if ((target.id && target.id === 'pixel-word') || (target.textContent && target.textContent.trim().toLowerCase() === 'pixel')) {
        // Start time counter on first collision with PIXEL word
        try {
            if (!snakeStartTime) {
                snakeStartTime = Date.now();
                if (snakeTimeTimer) { clearInterval(snakeTimeTimer); snakeTimeTimer = null; }
                snakeTimeTimer = setInterval(() => { try { updateSnakeHud(); } catch { } }, 1000);
                updateSnakeHud();
            }
        } catch { }
        try { spawnLoosePixels(28); } catch { }
        try { spawnPixelModeGoal(); } catch { }
        return false;
    }

    // Check collision with multicolor pixel goal
    if (target.classList && target.classList.contains('pixel-goal')) {
        // Score increase
        snake2Score++;
        updateSnake2Hud();

        // Remove current goal and spawn new one
        try {
            if (pixelModeGoal && pixelModeGoal.parentNode) {
                pixelModeGoal.parentNode.removeChild(pixelModeGoal);
            }
            if (pixelGoalTimer) {
                clearInterval(pixelGoalTimer);
                pixelGoalTimer = null;
            }
        } catch { }

        // Spawn new goal after short delay
        setTimeout(() => {
            try { spawnPixelModeGoal(); } catch { }
        }, 500);

        return true; // Continue game
    }

    // If hitting a hazard pixel -> game over (snake disappears), clear pixels, freeze HUD until Enter reset
    if (target.classList && target.classList.contains('hazard-pixel')) {
        try {
            // Clear all hazard pixels and stop pattern timer
            canvas.querySelectorAll('.hazard-pixel').forEach(n => n.remove());
            if (hazardPatternTimer) { clearTimeout(hazardPatternTimer); hazardPatternTimer = null; }
        } catch { }
        // Flag awaiting reset
        window.__snakeAwaitingReset = true;
        destroySnake2();
        snake2Active = false;

        return false;
    }

    // Dispatch a synthetic contextmenu at head position on the promoted target
    const evt = new MouseEvent('contextmenu', {
        bubbles: true,
        cancelable: true,
        clientX, clientY,
        view: window
    });
    // Mark that the spawn is originated by the snake so generators can randomize placement/size
    window.__spawnFromSnake = true;
    try { target.dispatchEvent(evt); } finally {
        setTimeout(() => { window.__spawnFromSnake = false; }, 0);
    }
    return false;
}

function updateSnake2Hud() {
    ensureSnakeHud();
    const punts2 = snakeHud.querySelector('#punts2-word');
    if (!punts2) return;
    try { createWordSlotMachine(punts2, String(snake2Score)); }
    catch { updateHudWord(punts2, String(snake2Score)); }
}

function renderSnake2() {
    const snake2Layer = document.getElementById('snake2-layer');
    if (!snake2Layer) return;
    snake2Layer.innerHTML = '';
    for (const part of snake2) {
        const div = document.createElement('div');
        div.style.position = 'absolute';
        div.style.width = SNAKE_SIZE + 'px';
        div.style.height = SNAKE_SIZE + 'px';
        div.style.left = part.x + 'px';
        div.style.top = part.y + 'px';
        div.style.background = 'blue';
        snake2Layer.appendChild(div);
    }
}

function destroySnake2() {
    snake2 = [];
    snake2Dir = 'right';
    snake2Score = 0;
    if (snake2Timer) { clearInterval(snake2Timer); }
    renderSnake2();
}

// Keyboard controls
document.addEventListener('keydown', (e) => {
    // Skip if user is typing in input fields
    if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) return;

    // Toggle with N key (N per "serp" en català)
    if (e.key === 'n' || e.key === 'N') {
        e.preventDefault();
        // Do not toggle during intro or if modals focus typing
        if (document.body.classList.contains('intro-active')) return;
        toggleSnake();
        return;
    }
    // Toggle second snake with M key
    if (e.key === 'm' || e.key === 'M') {
        e.preventDefault();
        if (document.body.classList.contains('intro-active')) return;
        toggleSnake2();
        return;
    }
    // ESC exits maze focus mode (fullscreen)
    if (e.key === 'Escape') {
        if (window.__mazeFocusActive) {
            e.preventDefault();
            try { exitMazeFocus(); } catch { }
        }
        return;
    }
    // Reset frozen score/time after hazard collision with Enter
    if (e.key === 'Enter') {
        if (window.__snakeAwaitingReset) {
            e.preventDefault();
            // Reset counters and HUD
            try { snakeScore = 0; } catch { }
            try { snakeStartTime = null; } catch { }
            try { updateSnakeHud(); } catch { }
            // Also reset snake2 HUD if present
            try { snake2Score = 0; } catch { }
            try { updateSnake2Hud(); } catch { }
            window.__snakeAwaitingReset = false;
        }
        return;
    }
    // If neither snake is active, ignore movement
    if (!snakeActive && !snake2Active) return;
    // Arrow keys control snake1
    if (e.key === 'ArrowUp') { e.preventDefault(); snakeDir = 'up'; }
    else if (e.key === 'ArrowDown') { e.preventDefault(); snakeDir = 'down'; }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); snakeDir = 'left'; }
    else if (e.key === 'ArrowRight') { e.preventDefault(); snakeDir = 'right'; }
    // WASD controls for snake2
    if (e.key === 'w' || e.key === 'W') { e.preventDefault(); snake2Dir = 'up'; }
    else if (e.key === 's' || e.key === 'S') { e.preventDefault(); snake2Dir = 'down'; }
    else if (e.key === 'a' || e.key === 'A') { e.preventDefault(); snake2Dir = 'left'; }
    else if (e.key === 'd' || e.key === 'D') { e.preventDefault(); snake2Dir = 'right'; }
});

// Spawn random hazard pixels around the canvas
let hazardPatternTimer = null;
let hazardPatternStartMs = null;
let pixelModeGoal = null;
let pixelGoalTimer = null;
function spawnLoosePixels(count = 20) {
    // Remove existing hazard pixels first to avoid overfill
    try {
        canvas.querySelectorAll('.hazard-pixel').forEach(n => n.remove());
    } catch { }
    const rect = canvas.getBoundingClientRect();

    // Dynamic count and size based on snake score (color pixel captures)
    const scoreMultiplier = Math.max(1, snakeScore / 3); // More pixels as score increases
    const dynamicCount = Math.floor(count + (scoreMultiplier * 5));

    for (let i = 0; i < dynamicCount; i++) {
        const px = document.createElement('div');
        px.className = 'hazard-pixel';

        // Variable sizes - more unpredictable with higher scores
        const minSize = Math.max(4, 8 - scoreMultiplier);
        const maxSize = Math.min(40, 20 + scoreMultiplier * 4);
        const size = Math.floor(minSize + Math.random() * (maxSize - minSize));
        px.style.width = size + 'px';
        px.style.height = size + 'px';

        // More spread out positions with higher scores
        const spreadFactor = 1 + (scoreMultiplier * 0.3);
        const cx = Math.floor((Math.random() * rect.width * spreadFactor) / zoomLevel) - panX;
        const cy = Math.floor((Math.random() * rect.height * spreadFactor) / zoomLevel) - panY;
        px.style.left = cx + 'px';
        px.style.top = cy + 'px';

        // Match element color
        const color = (window.__currentElColor || '#333');
        px.style.background = color;
        canvas.appendChild(px);
    }
    // Start/update pattern timer with score-based acceleration
    hazardPatternStartMs = Date.now();
    scheduleHazardRetheme();
}

function updateHazardPixelColors(color) {
    try {
        const nodes = canvas.querySelectorAll('.hazard-pixel');
        nodes.forEach(n => n.style.background = color);
    } catch { }
}

function rethemeHazardPixels() {
    const rect = canvas.getBoundingClientRect();
    const nodes = Array.from(canvas.querySelectorAll('.hazard-pixel'));
    if (!nodes.length) return;

    // Score-based chaos - more unpredictable changes with higher scores
    const scoreMultiplier = Math.max(1, snakeScore / 2);

    nodes.forEach((n, index) => {
        // Increasingly variable sizes
        const minSize = Math.max(3, 6 - scoreMultiplier);
        const maxSize = Math.min(50, 18 + scoreMultiplier * 6);
        const size = Math.floor(minSize + Math.random() * (maxSize - minSize));
        n.style.width = size + 'px';
        n.style.height = size + 'px';

        // More chaotic positioning with score progression
        const chaos = 1 + (scoreMultiplier * 0.4);
        const cx = Math.floor((Math.random() * rect.width * chaos) / zoomLevel) - panX;
        const cy = Math.floor((Math.random() * rect.height * chaos) / zoomLevel) - panY;
        n.style.left = cx + 'px';
        n.style.top = cy + 'px';

        // Some pixels become more aggressive (darker) with higher scores
        if (scoreMultiplier > 3 && Math.random() < 0.3) {
            const color = window.__currentElColor || '#333';
            n.style.background = color;
            n.style.opacity = '0.9';
        } else {
            n.style.opacity = '1';
        }
    });
}

function scheduleHazardRetheme() {
    try { if (hazardPatternTimer) { clearTimeout(hazardPatternTimer); } } catch { }

    // Score-based frequency acceleration - each color pixel capture makes changes faster
    const scoreMultiplier = Math.max(1, snakeScore);
    const baseInterval = 8000; // 8 seconds base
    const minInterval = 800;   // Fastest: 0.8 seconds

    // Exponential acceleration: faster with each score point
    const intervalMs = Math.max(minInterval, Math.round(baseInterval / (1 + scoreMultiplier * 0.7)));

    hazardPatternTimer = setTimeout(() => {
        rethemeHazardPixels();
        scheduleHazardRetheme();
    }, intervalMs);
}

// Spawn multicolor goal pixel for pixel mode
function spawnPixelModeGoal() {
    // Clean up existing goal
    try {
        if (pixelModeGoal && pixelModeGoal.parentNode) {
            pixelModeGoal.parentNode.removeChild(pixelModeGoal);
        }
        if (pixelGoalTimer) {
            clearInterval(pixelGoalTimer);
            pixelGoalTimer = null;
        }
    } catch { }

    // Create multicolor goal pixel
    const goalSize = SNAKE_SIZE;
    pixelModeGoal = document.createElement('div');
    pixelModeGoal.className = 'pixel-goal maze-el';
    pixelModeGoal.style.position = 'absolute';
    pixelModeGoal.style.width = goalSize + 'px';
    pixelModeGoal.style.height = goalSize + 'px';
    pixelModeGoal.style.borderRadius = '2px';
    pixelModeGoal.style.pointerEvents = 'auto';
    pixelModeGoal.style.transformOrigin = 'center';
    pixelModeGoal.style.userSelect = 'none';
    pixelModeGoal.style.boxShadow = '0 0 8px rgba(0,0,0,0.3)';
    pixelModeGoal.style.zIndex = '115';

    // Position randomly but avoid hazard pixels
    const rect = canvas.getBoundingClientRect();
    const margin = goalSize * 2;
    let gx, gy;
    let attempts = 0;

    do {
        gx = Math.floor(margin + Math.random() * (rect.width / zoomLevel - margin * 2)) - panX;
        gy = Math.floor(margin + Math.random() * (rect.height / zoomLevel - margin * 2)) - panY;
        attempts++;
    } while (attempts < 50); // Don't get stuck in infinite loop

    pixelModeGoal.style.left = gx + 'px';
    pixelModeGoal.style.top = gy + 'px';

    // Multicolor cycling animation
    const colors = [
        '#ff3b30', '#ff9500', '#ffcc00', '#34c759',
        '#5ac8fa', '#007aff', '#af52de', '#ff2d55'
    ];
    let colorIndex = Math.floor(Math.random() * colors.length);
    pixelModeGoal.style.background = colors[colorIndex];

    // Faster color cycling based on score for more urgency
    const cycleSpeed = Math.max(150, 300 - (snakeScore * 20));
    pixelGoalTimer = setInterval(() => {
        colorIndex = (colorIndex + 1) % colors.length;
        if (pixelModeGoal) {
            pixelModeGoal.style.background = colors[colorIndex];
        }
    }, cycleSpeed);

    canvas.appendChild(pixelModeGoal);
}

// Mobile D-pad
let dpadOverlay = null; // Left for compatibility but repurposed
let swipeTouchStartX = 0;
let swipeTouchStartY = 0;

function createDpadOverlay() {
    if (dpadOverlay) return;
    dpadOverlay = document.createElement('div');
    dpadOverlay.id = 'swipe-overlay';
    dpadOverlay.style.cssText = `
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        z-index: 9999;
    `;
    
    dpadOverlay.addEventListener('touchstart', (e) => {
        swipeTouchStartX = e.changedTouches[0].screenX;
        swipeTouchStartY = e.changedTouches[0].screenY;
    }, { passive: false });

    dpadOverlay.addEventListener('touchmove', (e) => {
        e.preventDefault(); // Prevent scrolling while playing
    }, { passive: false });

    dpadOverlay.addEventListener('touchend', (e) => {
        let touchEndX = e.changedTouches[0].screenX;
        let touchEndY = e.changedTouches[0].screenY;
        const diffX = touchEndX - swipeTouchStartX;
        const diffY = touchEndY - swipeTouchStartY;
        const threshold = 30; // Minimum swipe distance
        
        if (Math.abs(diffX) < threshold && Math.abs(diffY) < threshold) {
            // Treat as tap: temporarily disable overlay to click beneath
            dpadOverlay.style.pointerEvents = 'none';
            const elementUnderTap = document.elementFromPoint(e.changedTouches[0].clientX, e.changedTouches[0].clientY);
            if (elementUnderTap) {
                elementUnderTap.click();
            }
            dpadOverlay.style.pointerEvents = 'auto';
            return;
        }
        
        if (Math.abs(diffX) > Math.abs(diffY)) {
            // Horizontal swipe
            if (diffX > 0) {
                if (snakeActive && snakeDir !== 'left') snakeDir = 'right';
                if (typeof snake2Active !== 'undefined' && snake2Active && snake2Dir !== 'left') snake2Dir = 'right';
            } else {
                if (snakeActive && snakeDir !== 'right') snakeDir = 'left';
                if (typeof snake2Active !== 'undefined' && snake2Active && snake2Dir !== 'right') snake2Dir = 'left';
            }
        } else {
            // Vertical swipe
            if (diffY > 0) {
                if (snakeActive && snakeDir !== 'up') snakeDir = 'down';
                if (typeof snake2Active !== 'undefined' && snake2Active && snake2Dir !== 'up') snake2Dir = 'down';
            } else {
                if (snakeActive && snakeDir !== 'down') snakeDir = 'up';
                if (typeof snake2Active !== 'undefined' && snake2Active && snake2Dir !== 'down') snake2Dir = 'up';
            }
        }
    }, { passive: false });

    document.body.appendChild(dpadOverlay);
}

function removeDpadOverlay() {
    if (dpadOverlay) {
        dpadOverlay.remove();
        dpadOverlay = null;
    }
}
