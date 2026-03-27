
window.__mazes = [];
window.__mazeFocusActive = false;
window.__mazeProgress = 1;

function spawnMaze(opts = {}) {
    const complexity = Math.max(1, Math.min(10, opts.complexity || 1));
    const fullscreen = !!(opts.fullscreen || window.__mazeFocusActive);
    let cellSize, rows, cols, w, h;
    const simpleMode = (complexity || 0) <= 2;

    // Determine size and cell size based on complexity and mode
    if (fullscreen) {
        // Fullscreen mode (snake progression)
        window.__mazeFocusActive = true;
        document.body.classList.add('maze-focus');
        cellSize = simpleMode ? 40 : (isMobile ? 25 : 30);
        w = window.innerWidth;
        h = window.innerHeight;
        // Ensure grid alignment
        cols = Math.floor(w / cellSize);
        rows = Math.floor(h / cellSize);
        // Adjust w/h to match exact grid
        w = cols * cellSize;
        h = rows * cellSize;
    } else {
        // Floating draggable maze
        cellSize = 20;
        const baseSize = 300 + (complexity * 20);
        w = baseSize;
        h = baseSize;
        cols = Math.floor(w / cellSize);
        rows = Math.floor(h / cellSize);
    }

    // Create canvas
    const mazeCanvas = document.createElement('canvas');
    mazeCanvas.width = w;
    mazeCanvas.height = h;
    mazeCanvas.className = 'maze-el';
    mazeCanvas.style.position = fullscreen ? 'fixed' : 'absolute';
    mazeCanvas.style.zIndex = fullscreen ? '100' : '105'; // Below snake (120) but above words
    mazeCanvas.style.background = 'rgba(255,255,255,0.9)';
    mazeCanvas.style.boxShadow = fullscreen ? 'none' : '0 4px 12px rgba(0,0,0,0.15)';

    // Position
    if (fullscreen) {
        mazeCanvas.style.left = '0';
        mazeCanvas.style.top = '0';
    } else {
        // Random position in safe area
        const vw = window.innerWidth / zoomLevel;
        const vh = window.innerHeight / zoomLevel;
        const left = Math.max(50, Math.random() * (vw - w - 50)) - panX;
        const top = Math.max(50, Math.random() * (vh - h - 50)) - panY;
        mazeCanvas.style.left = left + 'px';
        mazeCanvas.style.top = top + 'px';
    }

    document.getElementById('canvas').appendChild(mazeCanvas);

    // Maze generation (Recursive Backtracker)
    const grid = [];
    for (let r = 0; r < rows; r++) {
        const row = [];
        for (let c = 0; c < cols; c++) {
            row.push({ visited: false, walls: { top: true, right: true, bottom: true, left: true } });
        }
        grid.push(row);
    }

    const stack = [];
    const startR = Math.floor(Math.random() * rows);
    const startC = Math.floor(Math.random() * cols);
    let current = grid[startR][startC];
    current.visited = true;
    stack.push({ r: startR, c: startC });

    function getUnvisitedNeighbors(r, c) {
        const n = [];
        if (r > 0 && !grid[r - 1][c].visited) n.push({ r: r - 1, c: c, dir: 'top' });
        if (r < rows - 1 && !grid[r + 1][c].visited) n.push({ r: r + 1, c: c, dir: 'bottom' });
        if (c > 0 && !grid[r][c - 1].visited) n.push({ r: r, c: c - 1, dir: 'left' });
        if (c < cols - 1 && !grid[r][c + 1].visited) n.push({ r: r, c: c + 1, dir: 'right' });
        return n;
    }

    // Generate
    while (stack.length > 0) {
        const currPos = stack[stack.length - 1];
        const neighbors = getUnvisitedNeighbors(currPos.r, currPos.c);
        if (neighbors.length > 0) {
            const next = neighbors[Math.floor(Math.random() * neighbors.length)];
            // Remove walls
            if (next.dir === 'top') {
                grid[currPos.r][currPos.c].walls.top = false;
                grid[next.r][next.c].walls.bottom = false;
            } else if (next.dir === 'bottom') {
                grid[currPos.r][currPos.c].walls.bottom = false;
                grid[next.r][next.c].walls.top = false;
            } else if (next.dir === 'left') {
                grid[currPos.r][currPos.c].walls.left = false;
                grid[next.r][next.c].walls.right = false;
            } else if (next.dir === 'right') {
                grid[currPos.r][currPos.c].walls.right = false;
                grid[next.r][next.c].walls.left = false;
            }
            grid[next.r][next.c].visited = true;
            stack.push({ r: next.r, c: next.c });
        } else {
            stack.pop();
        }
    }

    // Draw
    const ctx = mazeCanvas.getContext('2d');
    ctx.clearRect(0, 0, w, h);
    ctx.strokeStyle = window.__currentElColor || '#333';
    ctx.lineWidth = 2;
    ctx.lineCap = 'square';

    ctx.beginPath();
    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
            const x = c * cellSize;
            const y = r * cellSize;
            const cell = grid[r][c];
            if (cell.walls.top) { ctx.moveTo(x, y); ctx.lineTo(x + cellSize, y); }
            if (cell.walls.right) { ctx.moveTo(x + cellSize, y); ctx.lineTo(x + cellSize, y + cellSize); }
            if (cell.walls.bottom) { ctx.moveTo(x, y + cellSize); ctx.lineTo(x + cellSize, y + cellSize); }
            if (cell.walls.left) { ctx.moveTo(x, y); ctx.lineTo(x, y + cellSize); }
        }
    }
    ctx.stroke();

    // Add portal/goal
    // Goal is furthest point or random far point
    const goalR = Math.floor(Math.random() * rows);
    const goalC = Math.floor(Math.random() * cols);
    const goalX = goalC * cellSize + cellSize / 2;
    const goalY = goalR * cellSize + cellSize / 2;
    const goalRadius = Math.max(2, cellSize / 3);

    // Draw portal on canvas
    function drawPortal(color) {
        ctx.save();
        ctx.beginPath();
        ctx.arc(goalX, goalY, goalRadius, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.restore();
    }
    drawPortal('#007aff');

    // Animate portal
    let portalHue = 0;
    const portalTimer = setInterval(() => {
        portalHue = (portalHue + 5) % 360;
        drawPortal(`hsl(${portalHue}, 70%, 50%)`);
    }, 50);

    // Store metadata
    const mazeData = {
        el: mazeCanvas,
        grid: grid,
        cellSize: cellSize,
        rows: rows,
        cols: cols,
        goalX: goalC, // grid coords
        goalY: goalR,
        goalR: goalRadius, // pixel radius
        complexity: complexity,
        portalTimer: portalTimer,
        scale: 1
    };
    window.__mazes.push(mazeData);

    // Interactions for non-fullscreen mazes
    if (!fullscreen) {
        // Drag
        let isDragging = false;
        let startX, startY, initialLeft, initialTop;

        mazeCanvas.addEventListener('mousedown', (e) => {
            if (e.target !== mazeCanvas) return;
            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;
            initialLeft = parseFloat(mazeCanvas.style.left);
            initialTop = parseFloat(mazeCanvas.style.top);
            mazeCanvas.style.cursor = 'grabbing';
        });

        window.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            const dx = (e.clientX - startX) / zoomLevel;
            const dy = (e.clientY - startY) / zoomLevel;
            mazeCanvas.style.left = (initialLeft + dx) + 'px';
            mazeCanvas.style.top = (initialTop + dy) + 'px';
        });

        window.addEventListener('mouseup', () => {
            isDragging = false;
            mazeCanvas.style.cursor = 'grab';
        });
        mazeCanvas.style.cursor = 'grab';

        // Add resize handle
        const resizeHandle = document.createElement('div');
        resizeHandle.className = 'maze-resize-handle';
        resizeHandle.style.cssText = `
            position: absolute;
            width: 20px;
            height: 20px;
            background: rgba(0,0,0,0.1);
            bottom: 0;
            right: 0;
            cursor: se-resize;
            z-index: 106;
        `;
        // We need a wrapper to hold canvas + handle if we want the handle to move with it easily,
        // OR we just append handle to body and sync pos. 
        // Simpler: append handle to body and update its pos in a loop or mutation observer.
        // Actually, let's just make the canvas resizable via standard interaction if possible.
        // For now, keep it simple: non-fullscreen mazes are static size generated.
    } else {
        // Fullscreen: add close hint
        const hint = document.createElement('div');
        hint.className = 'maze-hint';
        hint.textContent = 'ESC per sortir';
        hint.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(255,255,255,0.8);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            pointer-events: none;
            z-index: 1000;
            opacity: 0;
            transition: opacity 0.5s;
        `;
        document.body.appendChild(hint);
        setTimeout(() => hint.style.opacity = '1', 1000);
        setTimeout(() => hint.style.opacity = '0', 4000);
        setTimeout(() => hint.remove(), 5000);
    }
}

function exitMazeFocus() {
    window.__mazeFocusActive = false;
    document.body.classList.remove('maze-focus');
    // Remove all fullscreen mazes
    clearAllMazes();
}

function clearAllMazes() {
    window.__mazes.forEach(m => {
        if (m.portalTimer) clearInterval(m.portalTimer);
        if (m.el && m.el.parentNode) m.el.parentNode.removeChild(m.el);
    });
    window.__mazes = [];
}
