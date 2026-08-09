// Screenshot feature — a discreet camera button that captures the VISIBLE window
// and lets you download it as PNG or JPG. html2canvas is loaded lazily on first use
// so it never weighs on the initial page load. Loaded as a classic script.
(function () {
    'use strict';

    var H2C_SRC = 'vendor/html2canvas.min.js';
    var _h2cPromise = null;

    // Load html2canvas once, on demand.
    function loadHtml2Canvas() {
        if (window.html2canvas) return Promise.resolve(window.html2canvas);
        if (_h2cPromise) return _h2cPromise;
        _h2cPromise = new Promise(function (resolve, reject) {
            var s = document.createElement('script');
            s.src = H2C_SRC;
            s.async = true;
            s.onload = function () { resolve(window.html2canvas); };
            s.onerror = function () { reject(new Error('no s\'ha pogut carregar html2canvas')); };
            document.head.appendChild(s);
        });
        return _h2cPromise;
    }

    function timestamp() {
        var d = new Date();
        var p = function (n) { return String(n).padStart(2, '0'); };
        return d.getFullYear() + p(d.getMonth() + 1) + p(d.getDate()) + '-' +
            p(d.getHours()) + p(d.getMinutes()) + p(d.getSeconds());
    }

    function downloadBlob(blob, filename) {
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        setTimeout(function () {
            try { document.body.removeChild(a); } catch (e) { }
            URL.revokeObjectURL(url);
        }, 1000);
    }

    // Capture the currently visible viewport into a <canvas>.
    function captureViewport() {
        // Force every open 3D viewer to render its current frame right now, so its
        // WebGL buffer is up to date and gets captured (needs preserveDrawingBuffer).
        try {
            (window.stlViewers || []).forEach(function (v) {
                if (v && v.renderer && v.scene && v.camera) v.renderer.render(v.scene, v.camera);
            });
        } catch (e) { }

        return loadHtml2Canvas().then(function (html2canvas) {
            var bg = getComputedStyle(document.body).backgroundColor || '#ffffff';
            var vw = window.innerWidth || document.documentElement.clientWidth || 1280;
            var vh = window.innerHeight || document.documentElement.clientHeight || 800;
            return html2canvas(document.body, {
                x: window.scrollX,
                y: window.scrollY,
                width: vw,
                height: vh,
                windowWidth: vw,
                windowHeight: vh,
                scale: Math.min(window.devicePixelRatio || 1, 2),
                backgroundColor: bg,
                useCORS: true,
                logging: false
            });
        });
    }

    function exportCanvas(canvas, fmt) {
        var isJpg = (fmt === 'jpg');
        var type = isJpg ? 'image/jpeg' : 'image/png';
        var name = 'ocu-' + timestamp() + '.' + (isJpg ? 'jpg' : 'png');
        canvas.toBlob(function (blob) {
            if (blob) downloadBlob(blob, name);
        }, type, isJpg ? 0.92 : undefined);
    }

    // ---- UI ---------------------------------------------------------------

    function buildUI() {
        var btn = document.createElement('button');
        btn.id = 'screenshot-btn';
        btn.type = 'button';
        btn.title = 'Fer una captura';
        btn.setAttribute('aria-label', 'Fer una captura de pantalla');
        btn.setAttribute('data-html2canvas-ignore', 'true');
        // Camera glyph (inline SVG so it recolours cleanly and needs no asset).
        btn.innerHTML =
            '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" ' +
            'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' +
            '<path d="M4 8h3l1.5-2h7L17 8h3a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z"/>' +
            '<circle cx="12" cy="13" r="3.2"/></svg>';

        // Small format chooser popup.
        var menu = document.createElement('div');
        menu.id = 'screenshot-menu';
        menu.setAttribute('data-html2canvas-ignore', 'true');
        menu.innerHTML =
            '<span class="ss-label">Desa com a</span>' +
            '<button type="button" data-fmt="png">PNG</button>' +
            '<button type="button" data-fmt="jpg">JPG</button>';

        document.body.appendChild(menu);
        document.body.appendChild(btn);

        function closeMenu() { menu.classList.remove('open'); }
        function openMenu() { menu.classList.add('open'); }

        btn.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            if (menu.classList.contains('open')) { closeMenu(); return; }
            openMenu();
        });

        // Pick a format → capture the viewport, then download in that format.
        menu.addEventListener('click', function (e) {
            var target = e.target.closest('button[data-fmt]');
            if (!target) return;
            e.preventDefault();
            var fmt = target.getAttribute('data-fmt');
            closeMenu();
            btn.classList.add('busy');
            btn.disabled = true;
            captureViewport().then(function (canvas) {
                exportCanvas(canvas, fmt);
            }).catch(function (err) {
                console.error('[screenshot]', err);
                alert('No s\'ha pogut fer la captura: ' + (err && err.message ? err.message : err));
            }).then(function () {
                btn.classList.remove('busy');
                btn.disabled = false;
            });
        });

        // Close the menu when clicking elsewhere.
        document.addEventListener('click', function (e) {
            if (!menu.classList.contains('open')) return;
            if (e.target === btn || btn.contains(e.target) || menu.contains(e.target)) return;
            closeMenu();
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', buildUI);
    } else {
        buildUI();
    }
})();
