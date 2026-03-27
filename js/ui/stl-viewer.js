
let stlViewers = [];

function initStlViewer() {
    // No modal initialization needed - viewers are created on demand
}

function openStlViewer(filePath) {
    console.log('openStlViewer called with:', filePath);
    const canvas = window.canvas || document.getElementById('canvas');
    if (!canvas) {
        console.error('Canvas not found');
        return;
    }

    const viewerContainer = document.createElement('div');
    viewerContainer.className = 'stl-viewer-container';
    viewerContainer.style.position = 'absolute';
    
    // Random size between 200px and 600px
    const randomSize = Math.floor(200 + Math.random() * 400);
    viewerContainer.style.width = randomSize + 'px';
    viewerContainer.style.height = randomSize + 'px';
    
    viewerContainer.style.cursor = 'move';
    viewerContainer.style.userSelect = 'none';
    viewerContainer.style.zIndex = '100';
    viewerContainer.style.pointerEvents = 'auto';
    viewerContainer.style.overflow = 'visible';

    const canvasRect = canvas.getBoundingClientRect();
    const zoomLevel = window.zoomLevel || 1;
    const panX = window.panX || 0;
    const panY = window.panY || 0;
    
    // Random position within canvas safe area
    const margin = 100;
    const logicalW = canvasRect.width / zoomLevel;
    const logicalH = canvasRect.height / zoomLevel;
    const maxX = Math.max(100, logicalW - randomSize - margin);
    const maxY = Math.max(100, logicalH - randomSize - margin);
    const randomX = Math.max(0, margin + Math.random() * (maxX - margin)) - panX;
    const randomY = Math.max(0, margin + Math.random() * (maxY - margin)) - panY;
    
    viewerContainer.style.left = randomX + 'px';
    viewerContainer.style.top = randomY + 'px';
    
    // Store random values for the viewer
    const randomRotationX = Math.random() * Math.PI * 2;
    const randomRotationY = Math.random() * Math.PI * 2;
    const randomRotationZ = Math.random() * Math.PI * 2;
    const randomOpacity = 0.4 + Math.random() * 0.6; // Between 0.4 and 1.0
    
    viewerContainer.dataset.rotationX = randomRotationX;
    viewerContainer.dataset.rotationY = randomRotationY;
    viewerContainer.dataset.rotationZ = randomRotationZ;
    viewerContainer.dataset.opacity = randomOpacity;
    
    console.log('Container created with size:', randomSize, 'position:', randomX, randomY);

    const renderContainer = document.createElement('div');
    renderContainer.style.width = '100%';
    renderContainer.style.height = '100%';
    renderContainer.style.position = 'relative';
    renderContainer.style.overflow = 'visible';
    viewerContainer.appendChild(renderContainer);

    canvas.appendChild(viewerContainer);

    const viewer = initThreeJS(renderContainer, filePath, {
        rotationX: parseFloat(viewerContainer.dataset.rotationX),
        rotationY: parseFloat(viewerContainer.dataset.rotationY),
        rotationZ: parseFloat(viewerContainer.dataset.rotationZ),
        opacity: parseFloat(viewerContainer.dataset.opacity)
    });
    viewer.container = viewerContainer;
    stlViewers.push(viewer);

    if (typeof addWordDragEvents === 'function') {
        addWordDragEvents(viewerContainer);
    }

    enableStlResize(viewerContainer, viewer);
}

function enableStlResize(container, viewer) {
    const EDGE = 10;
    
    // Wheel controls (use capture to prevent conflicts)
    container.addEventListener('wheel', (e) => {
        if (e.ctrlKey || e.metaKey) {
            // Ctrl/Cmd+Wheel: OPACITY (HIGHEST PRIORITY - ALWAYS WORKS)
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            if (viewer.mesh && viewer.mesh.material) {
                const currentOpacity = viewer.mesh.material.opacity;
                const delta = -Math.sign(e.deltaY) * 0.05;
                const newOpacity = Math.min(1, Math.max(0.1, currentOpacity + delta));
                viewer.mesh.material.opacity = newOpacity;
            }
            return false;
        } else if (e.altKey) {
            // Alt+Wheel: resize container
            e.preventDefault();
            e.stopPropagation();
            const currentWidth = parseFloat(container.style.width) || container.offsetWidth;
            const currentHeight = parseFloat(container.style.height) || container.offsetHeight;
            const factor = 1 + (-Math.sign(e.deltaY)) * 0.03;
            const newWidth = Math.min(8000, Math.max(100, currentWidth * factor));
            const newHeight = Math.min(8000, Math.max(100, currentHeight * factor));
            container.style.width = newWidth + 'px';
            container.style.height = newHeight + 'px';
            if (viewer.renderer) {
                viewer.renderer.setSize(newWidth, newHeight);
                viewer.camera.aspect = newWidth / newHeight;
                viewer.camera.updateProjectionMatrix();
            }
            return false;
        } else if (e.shiftKey) {
            // Shift+Wheel: scale object (change mesh scale)
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            if (viewer.mesh) {
                const currentScale = viewer.mesh.scale.x;
                const delta = -Math.sign(e.deltaY) * 0.05;
                const newScale = Math.min(3, Math.max(0.3, currentScale + delta));
                viewer.mesh.scale.set(newScale, newScale, newScale);
            }
            return false;
        } else {
            // No modifier: rotation (trackpad two-finger or mouse wheel)
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            if (viewer.mesh) {
                const deltaX = e.deltaX || 0;
                const deltaY = e.deltaY || 0;
                viewer.mesh.rotation.y += deltaX * 0.005;
                viewer.mesh.rotation.x += deltaY * 0.005;
            }
            return false;
        }
    }, { passive: false, capture: true });
    
    // Shift+drag rotation system
    let rotating = false;
    let rotateStart = { x: 0, y: 0 };
    
    // Edge/corner drag resize
    let resizing = false;
    let dir = { left: false, right: false, top: false, bottom: false };
    let start = { x: 0, y: 0, left: 0, top: 0, width: 0, height: 0 };

    function getDir(e) {
        const r = container.getBoundingClientRect();
        const onLeft = (e.clientX - r.left) <= EDGE;
        const onRight = (r.right - e.clientX) <= EDGE;
        const onTop = (e.clientY - r.top) <= EDGE;
        const onBottom = (r.bottom - e.clientY) <= EDGE;
        return { left: onLeft, right: onRight, top: onTop, bottom: onBottom };
    }

    function updateCursor(e) {
        if (resizing || rotating) return;
        if (e.shiftKey) {
            container.style.cursor = 'grab';
            return;
        }
        const d = getDir(e);
        let cursor = '';
        if ((d.right && d.bottom) || (d.left && d.top)) cursor = 'nwse-resize';
        else if ((d.right && d.top) || (d.left && d.bottom)) cursor = 'nesw-resize';
        else if (d.left || d.right) cursor = 'ew-resize';
        else if (d.top || d.bottom) cursor = 'ns-resize';
        else cursor = 'move';
        container.style.cursor = cursor;
    }

    container.addEventListener('mousemove', updateCursor);

    // Double-click to change color with color wheel
    container.addEventListener('dblclick', (e) => {
        e.preventDefault();
        e.stopPropagation();
        
        if (!viewer.mesh || !viewer.mesh.material) return;
        
        // Remove any existing color wheels
        const existing = document.querySelector('.color-wheel-wrapper');
        if (existing) existing.remove();
        
        // Get canvas reference
        const canvas = window.canvas || document.getElementById('canvas');
        const canvasRect = canvas.getBoundingClientRect();
        const zoomLevel = window.zoomLevel || 1;
        const panX = window.panX || 0;
        const panY = window.panY || 0;
        
        // Color wheel dimensions
        const wheelSize = 180;
        
        // Position in canvas coordinates (near object)
        const rect = container.getBoundingClientRect();
        let posX = ((rect.right - canvasRect.left) / zoomLevel) + 20 - panX;
        let posY = ((rect.top + rect.height / 2 - canvasRect.top) / zoomLevel) - (wheelSize / 2) - panY
;
        
        // Create color wheel wrapper (draggable)
        const wrapper = document.createElement('div');
        wrapper.className = 'color-wheel-wrapper';
        wrapper.style.cssText = `
            position: absolute;
            left: ${posX}px;
            top: ${posY}px;
            width: ${wheelSize}px;
            height: ${wheelSize}px;
            z-index: 10000;
            cursor: move;
            user-select: none;
            animation: fadeIn 0.2s ease;
        `;
        
        // Create color picker with CSS gradients
        const colorPicker = document.createElement('div');
        colorPicker.style.cssText = `
            width: 100%;
            height: 100%;
            border-radius: 50%;
            position: relative;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            cursor: crosshair;
            background: 
                conic-gradient(
                    red 0deg,
                    yellow 60deg,
                    lime 120deg,
                    cyan 180deg,
                    blue 240deg,
                    magenta 300deg,
                    red 360deg
                );
        `;
        
        // Overlay: white center (llums) to black edge (foscos)
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 50%;
            background: radial-gradient(circle, 
                white 0%, 
                transparent 50%, 
                black 100%
            );
            pointer-events: none;
        `;
        
        colorPicker.appendChild(overlay);
        wrapper.appendChild(colorPicker);
        canvas.appendChild(wrapper);
        
        // Add animation style if not exists
        if (!document.querySelector('#color-wheel-style')) {
            const style = document.createElement('style');
            style.id = 'color-wheel-style';
            style.textContent = `
                @keyframes fadeIn {
                    from { opacity: 0; transform: scale(0.8); }
                    to { opacity: 1; transform: scale(1); }
                }
            `;
            document.head.appendChild(style);
        }
        
        // Make color wheel draggable
        if (typeof addWordDragEvents === 'function') {
            addWordDragEvents(wrapper);
        }
        
        // Add resize with pinch/scroll
        wrapper.addEventListener('wheel', (evt) => {
            evt.preventDefault();
            evt.stopPropagation();
            const currentSize = parseFloat(wrapper.style.width);
            const factor = 1 + (-Math.sign(evt.deltaY)) * 0.05;
            const newSize = Math.min(400, Math.max(100, currentSize * factor));
            wrapper.style.width = newSize + 'px';
            wrapper.style.height = newSize + 'px';
        }, { passive: false });
        
        // Mobile pinch resize
        let pinchDist = 0;
        let pinchSize = 0;
        wrapper.addEventListener('touchstart', (evt) => {
            if (evt.touches.length === 2) {
                evt.preventDefault();
                const dx = evt.touches[0].clientX - evt.touches[1].clientX;
                const dy = evt.touches[0].clientY - evt.touches[1].clientY;
                pinchDist = Math.sqrt(dx * dx + dy * dy);
                pinchSize = parseFloat(wrapper.style.width);
            }
        });
        wrapper.addEventListener('touchmove', (evt) => {
            if (evt.touches.length === 2) {
                evt.preventDefault();
                const dx = evt.touches[0].clientX - evt.touches[1].clientX;
                const dy = evt.touches[0].clientY - evt.touches[1].clientY;
                const dist = Math.sqrt(dx * dx + dy * dy);
                const scale = dist / pinchDist;
                const newSize = Math.min(400, Math.max(100, pinchSize * scale));
                wrapper.style.width = newSize + 'px';
                wrapper.style.height = newSize + 'px';
            }
        });
        
        // Store viewer reference for color selection
        wrapper.viewerRef = viewer;
        
        // Handle color selection
        const selectColor = (evt) => {
            evt.preventDefault();
            evt.stopPropagation();
            
            console.log('selectColor called');
            console.log('viewer:', wrapper.viewerRef);
            console.log('mesh:', wrapper.viewerRef ? wrapper.viewerRef.mesh : 'no viewer');
            
            const rect = wrapper.getBoundingClientRect();
            const x = evt.clientX - rect.left;
            const y = evt.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const dx = x - centerX;
            const dy = y - centerY;
            const distance = Math.sqrt(dx * dx + dy * dy);
            const radius = rect.width / 2;
            
            // Only select if within circle
            if (distance > radius) {
                console.log('Click outside circle');
                return;
            }
            
            // Calculate angle for hue (0-360)
            // atan2: -180 to 180, 0° = right (3 o'clock)
            // We want: 0° = top (12 o'clock) = red
            let angle = Math.atan2(dx, -dy) * (180 / Math.PI);
            if (angle < 0) angle += 360;
            
            // Calculate distance ratio (0-1)
            const distanceRatio = Math.min(1, distance / radius);
            
            // HSL calculation
            const hue = Math.round(angle);
            const saturation = Math.round(distanceRatio * 100);
            // Center = white (100%), middle = pure color (50%), edge = black (0%)
            let lightness;
            if (distanceRatio < 0.5) {
                // Center to middle: white to pure color
                lightness = 100 - (distanceRatio * 100);
            } else {
                // Middle to edge: pure color to black
                lightness = 50 - ((distanceRatio - 0.5) * 100);
            }
            lightness = Math.round(Math.max(0, lightness));
            
            const color = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
            console.log('Calculated color:', color);
            
            // Apply to mesh
            if (wrapper.viewerRef && wrapper.viewerRef.mesh && wrapper.viewerRef.mesh.material) {
                wrapper.viewerRef.mesh.material.color.setStyle(color);
                console.log('✓ Color applied to mesh');
            } else {
                console.error('✗ Cannot apply color - mesh not found');
            }
        };
        
        wrapper.addEventListener('click', selectColor);
        wrapper.addEventListener('mousedown', (evt) => {
            if (evt.target === wrapper || evt.target === colorPicker || evt.target.parentNode === colorPicker) {
                selectColor(evt);
            }
        });
        wrapper.addEventListener('mousemove', (evt) => {
            if (evt.buttons === 1 && (evt.target === wrapper || evt.target === colorPicker || evt.target.parentNode === colorPicker)) {
                selectColor(evt);
            }
        });
        
        // Close on Escape key
        const keyHandler = (evt) => {
            if (evt.key === 'Escape') {
                wrapper.remove();
                document.removeEventListener('keydown', keyHandler);
            }
        };
        document.addEventListener('keydown', keyHandler);
    });

    container.addEventListener('mousedown', (e) => {
        // Shift+click for rotation (object stays in place)
        if (e.shiftKey && viewer.mesh) {
            e.preventDefault();
            e.stopPropagation();
            rotating = true;
            rotateStart.x = e.clientX;
            rotateStart.y = e.clientY;
            container.style.cursor = 'grabbing';
            document.body.style.cursor = 'grabbing';
            return;
        }
        
        const d = getDir(e);
        if (!(d.left || d.right || d.top || d.bottom)) return;
        e.preventDefault();
        e.stopPropagation();
        dir = d;
        resizing = true;
        
        const zoomLevel = window.zoomLevel || 1;
        const panX = window.panX || 0;
        const panY = window.panY || 0;
        const canvas = window.canvas || document.getElementById('canvas');
        const canvasRect = canvas.getBoundingClientRect();
        
        start.x = (e.clientX - canvasRect.left) / zoomLevel - panX;
        start.y = (e.clientY - canvasRect.top) / zoomLevel - panY;
        
        const rect = container.getBoundingClientRect();
        start.left = parseFloat(container.style.left) || ((rect.left - canvasRect.left) / zoomLevel - panX);
        start.top = parseFloat(container.style.top) || ((rect.top - canvasRect.top) / zoomLevel - panY);
        start.width = parseFloat(container.style.width) || (rect.width / zoomLevel);
        start.height = parseFloat(container.style.height) || (rect.height / zoomLevel);
        
        document.body.style.cursor = container.style.cursor || 'nwse-resize';
    });

    document.addEventListener('mousemove', (e) => {
        // Handle Shift+drag rotation (object stays in place)
        if (rotating && viewer.mesh) {
            e.preventDefault();
            e.stopPropagation();
            const deltaX = e.clientX - rotateStart.x;
            const deltaY = e.clientY - rotateStart.y;
            
            // Rotate based on mouse movement
            // Horizontal movement rotates around Y axis
            // Vertical movement rotates around X axis
            viewer.mesh.rotation.y += deltaX * 0.01;
            viewer.mesh.rotation.x += deltaY * 0.01;
            
            rotateStart.x = e.clientX;
            rotateStart.y = e.clientY;
            return;
        }
        
        if (!resizing) return;
        e.preventDefault();
        
        const zoomLevel = window.zoomLevel || 1;
        const panX = window.panX || 0;
        const panY = window.panY || 0;
        const canvas = window.canvas || document.getElementById('canvas');
        const canvasRect = canvas.getBoundingClientRect();
        
        const px = (e.clientX - canvasRect.left) / zoomLevel - panX;
        const py = (e.clientY - canvasRect.top) / zoomLevel - panY;
        const dx = px - start.x;
        const dy = py - start.y;

        let newWidth = start.width;
        let newHeight = start.height;
        let newLeft = start.left;
        let newTop = start.top;

        if (dir.right) newWidth = Math.max(100, start.width + dx);
        if (dir.bottom) newHeight = Math.max(100, start.height + dy);
        if (dir.left) {
            newWidth = Math.max(100, start.width - dx);
            newLeft = start.left + (start.width - newWidth);
        }
        if (dir.top) {
            newHeight = Math.max(100, start.height - dy);
            newTop = start.top + (start.height - newHeight);
        }

        // Maintain aspect ratio for corners
        if ((dir.left || dir.right) && (dir.top || dir.bottom)) {
            const avgDim = (newWidth + newHeight) / 2;
            newWidth = avgDim;
            newHeight = avgDim;
            if (dir.left) newLeft = start.left + (start.width - newWidth);
            if (dir.top) newTop = start.top + (start.height - newHeight);
        }

        container.style.width = newWidth + 'px';
        container.style.height = newHeight + 'px';
        container.style.left = newLeft + 'px';
        container.style.top = newTop + 'px';
        
        if (viewer.renderer) {
            viewer.renderer.setSize(newWidth, newHeight);
            viewer.camera.aspect = newWidth / newHeight;
            viewer.camera.updateProjectionMatrix();
        }
    });

    document.addEventListener('mouseup', () => {
        if (rotating) {
            rotating = false;
            container.style.cursor = 'move';
            document.body.style.cursor = 'auto';
        }
        if (resizing) {
            resizing = false;
            document.body.style.cursor = 'auto';
        }
    });

    // Pinch resize for mobile
    let pinch = { active: false, dist: 0, width: 0, height: 0 };
    container.style.touchAction = 'none';
    
    container.addEventListener('touchstart', (e) => {
        if (e.touches.length === 2) {
            e.preventDefault();
            pinch.active = true;
            const dx = e.touches[0].clientX - e.touches[1].clientX;
            const dy = e.touches[0].clientY - e.touches[1].clientY;
            pinch.dist = Math.sqrt(dx * dx + dy * dy);
            pinch.width = parseFloat(container.style.width) || container.offsetWidth;
            pinch.height = parseFloat(container.style.height) || container.offsetHeight;
        }
    });

    container.addEventListener('touchmove', (e) => {
        if (pinch.active && e.touches.length === 2) {
            e.preventDefault();
            const dx = e.touches[0].clientX - e.touches[1].clientX;
            const dy = e.touches[0].clientY - e.touches[1].clientY;
            const dist = Math.sqrt(dx * dx + dy * dy);
            const scale = dist / pinch.dist;
            const newWidth = Math.max(100, Math.min(8000, pinch.width * scale));
            const newHeight = Math.max(100, Math.min(8000, pinch.height * scale));
            container.style.width = newWidth + 'px';
            container.style.height = newHeight + 'px';
            if (viewer.renderer) {
                viewer.renderer.setSize(newWidth, newHeight);
                viewer.camera.aspect = newWidth / newHeight;
                viewer.camera.updateProjectionMatrix();
            }
        }
    });

    container.addEventListener('touchend', () => {
        pinch.active = false;
    });
}

function initThreeJS(container, filePath, options = {}) {
    console.log('initThreeJS called with options:', options);
    
    if (typeof THREE === 'undefined') {
        console.error('THREE.js not loaded!');
        return null;
    }
    
    const rect = container.getBoundingClientRect();
    console.log('Container rect:', rect);
    
    const scene = new THREE.Scene();
    scene.background = null;

    const camera = new THREE.PerspectiveCamera(35, rect.width / rect.height, 1, 50000);
    camera.position.set(0, 0, 200);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(rect.width, rect.height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);
    container.appendChild(renderer.domElement);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const keyLight = new THREE.DirectionalLight(0xffffff, 0.8);
    keyLight.position.set(5, 10, 7);
    scene.add(keyLight);

    const fillLight = new THREE.DirectionalLight(0xffffff, 0.3);
    fillLight.position.set(-5, 0, -5);
    scene.add(fillLight);

    const viewer = {
        scene,
        camera,
        renderer,
        mesh: null,
        animationId: null,
        controls: null,
        options: options
    };

    viewer.controls = createOrbitControls(camera, renderer.domElement);
    loadSTLFile(viewer, filePath);
    animateStl(viewer);
    
    return viewer;
}

function createOrbitControls(camera, domElement) {
    const controls = {
        enabled: true,
        rotateSpeed: 1.0,
        zoomSpeed: 1.2,
        minDistance: 1,
        maxDistance: 500,
        autoRotate: false,
        target: new THREE.Vector3(0, 0, 0)
    };

    let isRotating = false;
    let isPanning = false;
    let startX = 0, startY = 0;
    let lastX = 0, lastY = 0;
    const spherical = { theta: 0, phi: Math.PI / 2, radius: 100 };

    domElement.addEventListener('mousedown', (e) => {
        if (e.button === 0) {
            isRotating = true;
            startX = lastX = e.clientX;
            startY = lastY = e.clientY;
            e.preventDefault();
        } else if (e.button === 2) {
            isPanning = true;
            startX = lastX = e.clientX;
            startY = lastY = e.clientY;
            e.preventDefault();
        }
    });

    domElement.addEventListener('contextmenu', (e) => e.preventDefault());

    document.addEventListener('mousemove', (e) => {
        if (isRotating) {
            const deltaX = e.clientX - lastX;
            const deltaY = e.clientY - lastY;
            spherical.theta -= deltaX * 0.01 * controls.rotateSpeed;
            spherical.phi -= deltaY * 0.01 * controls.rotateSpeed;
            spherical.phi = Math.max(0.01, Math.min(Math.PI - 0.01, spherical.phi));
            updateCameraPosition();
            lastX = e.clientX;
            lastY = e.clientY;
        } else if (isPanning) {
            const deltaX = e.clientX - lastX;
            const deltaY = e.clientY - lastY;
            const distance = camera.position.distanceTo(controls.target);
            const factor = distance * 0.001;
            const right = new THREE.Vector3();
            const up = new THREE.Vector3();
            camera.getWorldDirection(right);
            right.cross(camera.up).normalize();
            up.copy(camera.up);
            controls.target.addScaledVector(right, -deltaX * factor);
            controls.target.addScaledVector(up, deltaY * factor);
            updateCameraPosition();
            lastX = e.clientX;
            lastY = e.clientY;
        }
    });

    document.addEventListener('mouseup', () => {
        isRotating = false;
        isPanning = false;
    });

    domElement.addEventListener('wheel', (e) => {
        e.preventDefault();
        const delta = e.deltaY > 0 ? 1.1 : 0.9;
        spherical.radius *= delta;
        spherical.radius = Math.max(controls.minDistance, Math.min(controls.maxDistance, spherical.radius));
        updateCameraPosition();
    });

    function updateCameraPosition() {
        const x = spherical.radius * Math.sin(spherical.phi) * Math.sin(spherical.theta);
        const y = spherical.radius * Math.cos(spherical.phi);
        const z = spherical.radius * Math.sin(spherical.phi) * Math.cos(spherical.theta);
        camera.position.set(x, y, z).add(controls.target);
        camera.lookAt(controls.target);
    }

    updateCameraPosition();
    return controls;
}

function loadSTLFile(viewer, filePath) {

    fetch(filePath)
        .then(response => {
            if (!response.ok) throw new Error('STL file not found');
            return response.arrayBuffer();
        })
        .then(arrayBuffer => {
            const geometry = parseSTL(arrayBuffer);
            geometry.computeVertexNormals();
            geometry.center();

            const box = new THREE.Box3().setFromObject(new THREE.Mesh(geometry));
            const size = box.getSize(new THREE.Vector3());
            const maxDim = Math.max(size.x, size.y, size.z);
            const scale = 50 / maxDim;
            geometry.scale(scale, scale, scale);

            const opts = viewer.options || {};
            
            // Generate random color (HSL for better results)
            const randomHue = Math.floor(Math.random() * 360);
            const randomSaturation = 70 + Math.floor(Math.random() * 30); // 70-100%
            const randomLightness = 40 + Math.floor(Math.random() * 30); // 40-70%
            const randomColor = `hsl(${randomHue}, ${randomSaturation}%, ${randomLightness}%)`;
            
            const material = new THREE.MeshPhongMaterial({
                color: randomColor,
                shininess: 30,
                specular: 0x222222,
                side: THREE.DoubleSide,
                flatShading: false,
                transparent: true,
                opacity: opts.opacity || 1.0
            });

            viewer.mesh = new THREE.Mesh(geometry, material);
            
            // Apply random rotation
            if (opts.rotationX !== undefined) viewer.mesh.rotation.x = opts.rotationX;
            if (opts.rotationY !== undefined) viewer.mesh.rotation.y = opts.rotationY;
            if (opts.rotationZ !== undefined) viewer.mesh.rotation.z = opts.rotationZ;
            
            viewer.scene.add(viewer.mesh);

            if (viewer.controls) {
                viewer.controls.target.set(0, 0, 0);
            }
        })
        .catch(error => {
            console.error('Error loading STL:', error);
        });
}

function parseSTL(arrayBuffer) {
    const view = new DataView(arrayBuffer);
    const isBinary = view.byteLength > 84;
    
    if (isBinary) {
        const numTriangles = view.getUint32(80, true);
        const vertices = [];
        
        for (let i = 0; i < numTriangles; i++) {
            const offset = 84 + i * 50;
            
            for (let j = 0; j < 3; j++) {
                const vertexOffset = offset + 12 + j * 12;
                vertices.push(
                    view.getFloat32(vertexOffset, true),
                    view.getFloat32(vertexOffset + 4, true),
                    view.getFloat32(vertexOffset + 8, true)
                );
            }
        }
        
        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
        return geometry;
    }
    
    const decoder = new TextDecoder('utf-8');
    const text = decoder.decode(arrayBuffer);
    const vertices = [];
    const normalPattern = /facet\s+normal\s+([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)\s+([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)\s+([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)/g;
    const vertexPattern = /vertex\s+([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)\s+([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)\s+([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)/g;
    
    let match;
    while ((match = vertexPattern.exec(text)) !== null) {
        vertices.push(parseFloat(match[1]), parseFloat(match[3]), parseFloat(match[5]));
    }
    
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    return geometry;
}

function animateStl(viewer) {
    viewer.animationId = requestAnimationFrame(() => animateStl(viewer));
    if (viewer.renderer && viewer.scene && viewer.camera) {
        viewer.renderer.render(viewer.scene, viewer.camera);
    }
}

function closeStlViewer(container) {
    const index = stlViewers.findIndex(v => v.container === container);
    if (index !== -1) {
        const viewer = stlViewers[index];
        cleanupThreeJS(viewer);
        stlViewers.splice(index, 1);
    }
    if (container && container.parentNode) {
        container.remove();
    }
}

function cleanupThreeJS(viewer) {
    if (viewer.animationId) {
        cancelAnimationFrame(viewer.animationId);
        viewer.animationId = null;
    }

    if (viewer.mesh) {
        if (viewer.mesh.geometry) viewer.mesh.geometry.dispose();
        if (viewer.mesh.material) viewer.mesh.material.dispose();
        viewer.mesh = null;
    }

    if (viewer.scene) {
        viewer.scene.clear();
        viewer.scene = null;
    }

    if (viewer.renderer) {
        if (viewer.renderer.domElement && viewer.renderer.domElement.parentNode) {
            viewer.renderer.domElement.parentNode.removeChild(viewer.renderer.domElement);
        }
        viewer.renderer.dispose();
        viewer.renderer = null;
    }

    viewer.camera = null;
    viewer.controls = null
}

window.openStlViewer = openStlViewer;
window.closeStlViewer = closeStlViewer;
window.initStlViewer = initStlViewer;
