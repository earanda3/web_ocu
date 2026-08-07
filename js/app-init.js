// ocu app init tail — extracted from the second inline <script> in index.html.
// Runs AFTER stl-viewer/info-viewer/tecla-viewer, exactly as before.
        // Initialize STL viewer on page load
        if (typeof initStlViewer === 'function') {
            initStlViewer();
        }

        // Track which canvas word was clicked/right-clicked so STL spawns near it
        document.addEventListener('click', (e) => {
            const a = e.target.closest && e.target.closest('#canvas a');
            if (a) window.__stlSpawnOriginEl = a;
        }, true);
        document.addEventListener('contextmenu', (e) => {
            const a = e.target.closest && e.target.closest('#canvas a');
            if (a) window.__stlSpawnOriginEl = a;
        }, true);

        // Mobile: rearrange initial inline words into a vertical column
        if (window.isMobile) {
            requestAnimationFrame(() => {
                const colX = 40;
                let y = 120;
                const rowH = 55;
                [
                    'tao', 'color-word', 'newtro-word',
                    'cw-ocu', 'cw-ocu3d', 'cw-zines',
                    'serp-word', 'soroboru-word', 'afegir-word',
                    'arxius-word', 'tecla-link-word', 'ordre-word'
                ].forEach(id => {
                    const el = document.getElementById(id);
                    if (!el) return;
                    el.style.position = 'absolute';
                    el.style.left = colX + 'px';
                    el.style.top = y + 'px';
                    el.style.transform = '';
                    y += rowH;
                });
                const aboutBtn = document.getElementById('about-btn');
                if (aboutBtn) { aboutBtn.style.left = '20px'; aboutBtn.style.top = '20px'; }
            });
        }
