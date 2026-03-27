
let pongActive = false;
let pongCursorPaddle = null;
let pongBall = null;
let pongVelocity = { x: 1.5, y: 1.5 };
let pongSpeed = 1.5;
let pongTouches = 0;
let pongAnimationFrame = null;
let pongMouseX = 0;
let pongMouseY = 0;
let pongHud = null;
let lastPongHudScore = 0;

// Debug/testing
let pongDebug = false;
let pongDebugNoAccel = true;
let pongDebugLayer = null;
let pongDebugMarkers = {};

function startPongGame(mouseX, mouseY) {
    if (pongActive) {
        stopPongGame();
        return;
    }

    pongActive = true;
    pongSpeed = 1.5;
    pongTouches = 0;
    pongMouseX = mouseX;
    pongMouseY = mouseY;

    // Create concave cursor paddle
    createCursorPaddle();

    // Create ball
    createPongBall();

    // Create and show HUD
    ensurePongHud();
    updatePongHud();

    // Add cursor tracking and reset controls
    addPongControls();

    // Start game loop
    pongGameLoop();
}

function createCursorPaddle() {
    pongCursorPaddle = document.createElement('div');
    pongCursorPaddle.className = 'pong-cursor-paddle';
    pongCursorPaddle.style.position = 'fixed';
    pongCursorPaddle.style.width = '50px';
    pongCursorPaddle.style.height = '50px';
    pongCursorPaddle.style.background = 'transparent'; // Hollow ring
    pongCursorPaddle.style.borderRadius = '50%';
    pongCursorPaddle.style.border = '2px solid #ff3b30'; // Start with first color
    pongCursorPaddle.style.zIndex = '9999';
    pongCursorPaddle.style.pointerEvents = 'none';
    pongCursorPaddle.style.transform = 'translateX(-50%) translateY(-50%)';

    // Position at initial mouse position
    pongCursorPaddle.style.left = pongMouseX + 'px';
    pongCursorPaddle.style.top = pongMouseY + 'px';

    // Multicolor cycling animation like the pixel
    const colors = ['#ff3b30', '#ff9500', '#ffcc00', '#34c759', '#5ac8fa', '#007aff', '#af52de', '#ff2d55'];
    let colorIndex = 0;

    setInterval(() => {
        if (pongCursorPaddle && pongActive) {
            colorIndex = (colorIndex + 1) % colors.length;
            pongCursorPaddle.style.borderColor = colors[colorIndex];
        }
    }, 200);

    document.body.appendChild(pongCursorPaddle);
}

function ensurePongHud() {
    if (!pongHud) {
        pongHud = document.createElement('div');
        pongHud.id = 'pong-hud';
        pongHud.style.position = 'fixed';
        pongHud.style.top = '20px';
        pongHud.style.right = '20px';
        pongHud.style.zIndex = '9998';
        pongHud.innerHTML = `
            <a id="pong-touches-word" href="#" style="display:block; font-size: 18px; letter-spacing: 2px; cursor: default; user-select: none;"></a>
        `;
        document.body.appendChild(pongHud);

        // Build slot machine effect for the HUD word
        const touches = pongHud.querySelector('#pong-touches-word');
        if (touches) {
            try { createWordSlotMachine(touches, '0'); } catch { touches.textContent = '0'; }
        }

        // Apply current color immediately
        if (window.__currentElColor) {
            try { touches.style.color = window.__currentElColor; } catch { }
        }
    }
}

function updatePongHud() {
    ensurePongHud();
    const touches = pongHud.querySelector('#pong-touches-word');
    if (pongTouches !== lastPongHudScore) {
        // On score change, rerun slot-machine effect for feedback
        try { createWordSlotMachine(touches, String(pongTouches)); }
        catch { updateHudWord(touches, String(pongTouches)); }
        lastPongHudScore = pongTouches;
    } else {
        updateHudWord(touches, String(pongTouches));
    }
    pongHud.classList.remove('hidden');
}

// Debug overlay and tests
function ensurePongDebugLayer() {
    if (pongDebugLayer) return;
    pongDebugLayer = document.createElement('div');
    pongDebugLayer.id = 'pong-debug-layer';
    pongDebugLayer.style.position = 'absolute';
    pongDebugLayer.style.left = '0';
    pongDebugLayer.style.top = '0';
    pongDebugLayer.style.zIndex = '116';
    pongDebugLayer.style.pointerEvents = 'none';
    canvas.appendChild(pongDebugLayer);
}
function placeDebugDot(id, cx, cy, color) {
    if (!pongDebug) return;
    ensurePongDebugLayer();
    let dot = pongDebugMarkers[id];
    if (!dot) {
        dot = document.createElement('div');
        dot.className = 'pong-debug-dot';
        dot.style.position = 'absolute';
        dot.style.width = '4px';
        dot.style.height = '4px';
        dot.style.borderRadius = '50%';
        dot.style.background = color || '#007aff';
        dot.style.boxShadow = '0 0 0 1px rgba(0,0,0,0.2)';
        pongDebugLayer.appendChild(dot);
        pongDebugMarkers[id] = dot;
    }
    dot.style.background = color || dot.style.background || '#007aff';
    dot.style.left = (cx - 2) + 'px';
    dot.style.top = (cy - 2) + 'px';
}
function clearPongDebug() {
    if (pongDebugLayer) {
        try { pongDebugLayer.remove(); } catch { }
        pongDebugLayer = null;
    }
    pongDebugMarkers = {};
}
function togglePongDebug() {
    pongDebug = !pongDebug;
    if (!pongDebug) clearPongDebug();
}
function runBounceTest(kind) {
    if (!pongActive || !pongBall || !pongCursorPaddle) return;
    const canvasRect = canvas.getBoundingClientRect();
    const paddleRect = pongCursorPaddle.getBoundingClientRect();
    const paddleCenterX = ((paddleRect.left + paddleRect.width / 2) - canvasRect.left) / zoomLevel - panX;
    const paddleCenterY = ((paddleRect.top + paddleRect.height / 2) - canvasRect.top) / zoomLevel - panY;
    const ballRadius = 4;
    const discRadius = 25;
    const minSeparation = discRadius + ballRadius;
    const offset = minSeparation + 2; // start just outside so next step collides
    const testSpeed = 2.2; // stable test speed
    let cx = paddleCenterX;
    let cy = paddleCenterY;
    let vx = 0, vy = 0;
    switch (kind) {
        case 'vertical-top':
            cx = paddleCenterX; cy = paddleCenterY - offset; vx = 0; vy = +testSpeed; break;
        case 'vertical-bottom':
            cx = paddleCenterX; cy = paddleCenterY + offset; vx = 0; vy = -testSpeed; break;
        case 'lateral-left':
            cx = paddleCenterX - offset; cy = paddleCenterY; vx = +testSpeed; vy = 0; break;
        case 'lateral-right':
            cx = paddleCenterX + offset; cy = paddleCenterY; vx = -testSpeed; vy = 0; break;
        default:
            return;
    }
    pongBall.style.left = (cx - ballRadius) + 'px';
    pongBall.style.top = (cy - ballRadius) + 'px';
    pongVelocity.x = vx;
    pongVelocity.y = vy;
    if (pongDebug) {
        placeDebugDot('paddle', paddleCenterX, paddleCenterY, '#ff9500');
    }
}

function createPongBall() {
    pongBall = document.createElement('div');
    pongBall.className = 'pong-ball';
    pongBall.style.position = 'absolute';
    pongBall.style.width = '8px';
    pongBall.style.height = '8px';
    pongBall.style.borderRadius = '0'; // Square pixel
    pongBall.style.zIndex = '115';
    pongBall.style.background = window.__currentElColor || '#333';

    // Spawn at random position away from edges
    const margin = 100;
    const vw = Math.floor(window.innerWidth / zoomLevel);
    const vh = Math.floor(window.innerHeight / zoomLevel);
    const startX = Math.floor(margin + Math.random() * (vw - margin * 2)) - panX;
    const startY = Math.floor(margin + Math.random() * (vh - margin * 2)) - panY;

    pongBall.style.left = startX + 'px';
    pongBall.style.top = startY + 'px';

    // Random initial velocity
    const angle = Math.random() * Math.PI * 2;
    pongVelocity.x = Math.cos(angle) * pongSpeed;
    pongVelocity.y = Math.sin(angle) * pongSpeed;

    canvas.appendChild(pongBall);
}

function stopPongGame() {
    pongActive = false;
    if (pongAnimationFrame) {
        cancelAnimationFrame(pongAnimationFrame);
        pongAnimationFrame = null;
    }
    if (pongCursorPaddle) {
        pongCursorPaddle.remove();
        pongCursorPaddle = null;
    }
    if (pongBall) {
        pongBall.remove();
        pongBall = null;
    }
    if (pongHud) {
        pongHud.classList.add('hidden');
    }
    clearPongDebug();
    document.removeEventListener('mousemove', pongMouseMoveHandler);
    document.removeEventListener('touchmove', pongTouchMoveHandler);
}

function pongMouseMoveHandler(e) {
    pongMouseX = e.clientX;
    pongMouseY = e.clientY;
    if (pongCursorPaddle) {
        pongCursorPaddle.style.left = pongMouseX + 'px';
        pongCursorPaddle.style.top = pongMouseY + 'px';
    }
}

function pongTouchMoveHandler(e) {
    if (e.touches.length > 0) {
        pongMouseX = e.touches[0].clientX;
        pongMouseY = e.touches[0].clientY;
        if (pongCursorPaddle) {
            pongCursorPaddle.style.left = pongMouseX + 'px';
            pongCursorPaddle.style.top = pongMouseY + 'px';
        }
    }
}

function addPongControls() {
    document.addEventListener('mousemove', pongMouseMoveHandler);
    document.addEventListener('touchmove', pongTouchMoveHandler, { passive: true });

    // Reset game on click/tap
    const resetHandler = () => {
        if (pongActive) {
            stopPongGame();
            startPongGame(pongMouseX, pongMouseY);
        }
    };
    // Only bind if not already bound (simple check)
    // Actually, stopPongGame removes them, so we are good.
}

function pongGameLoop() {
    if (!pongActive || !pongBall) return;

    // Move ball
    const currentLeft = parseFloat(pongBall.style.left);
    const currentTop = parseFloat(pongBall.style.top);

    let nextLeft = currentLeft + pongVelocity.x;
    let nextTop = currentTop + pongVelocity.y;

    // Canvas boundaries (accounting for zoom/pan)
    const vw = Math.floor(window.innerWidth / zoomLevel);
    const vh = Math.floor(window.innerHeight / zoomLevel);
    const minX = -panX;
    const maxX = minX + vw - 8; // 8 is ball size
    const minY = -panY;
    const maxY = minY + vh - 8;

    // Wall collisions
    if (nextLeft <= minX || nextLeft >= maxX) {
        pongVelocity.x *= -1;
        nextLeft = Math.max(minX, Math.min(nextLeft, maxX));
    }
    if (nextTop <= minY || nextTop >= maxY) {
        pongVelocity.y *= -1;
        nextTop = Math.max(minY, Math.min(nextTop, maxY));
    }

    // Paddle collision
    // Convert paddle client coords to canvas coords
    const canvasRect = canvas.getBoundingClientRect();
    const paddleCanvasX = (pongMouseX - canvasRect.left) / zoomLevel - panX;
    const paddleCanvasY = (pongMouseY - canvasRect.top) / zoomLevel - panY;

    // Simple circle collision
    const ballCenterX = nextLeft + 4;
    const ballCenterY = nextTop + 4;
    const paddleRadius = 25; // 50px / 2
    const ballRadius = 4;

    const dx = ballCenterX - paddleCanvasX;
    const dy = ballCenterY - paddleCanvasY;
    const distance = Math.sqrt(dx * dx + dy * dy);

    if (distance < (paddleRadius + ballRadius)) {
        // Hit!
        // Calculate normal
        const nx = dx / distance;
        const ny = dy / distance;

        // Reflect velocity
        const dot = pongVelocity.x * nx + pongVelocity.y * ny;
        pongVelocity.x = pongVelocity.x - 2 * dot * nx;
        pongVelocity.y = pongVelocity.y - 2 * dot * ny;

        // Push out to avoid sticking
        const overlap = (paddleRadius + ballRadius) - distance;
        nextLeft += nx * overlap;
        nextTop += ny * overlap;

        // Increase speed slightly
        pongSpeed = Math.min(15, pongSpeed * 1.05);
        const speed = Math.sqrt(pongVelocity.x * pongVelocity.x + pongVelocity.y * pongVelocity.y);
        pongVelocity.x = (pongVelocity.x / speed) * pongSpeed;
        pongVelocity.y = (pongVelocity.y / speed) * pongSpeed;

        pongTouches++;
        updatePongHud();
    }

    // Update position
    pongBall.style.left = nextLeft + 'px';
    pongBall.style.top = nextTop + 'px';

    pongAnimationFrame = requestAnimationFrame(pongGameLoop);
}
