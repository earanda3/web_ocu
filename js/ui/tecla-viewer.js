/* ================================================================
 * TECLA Viewer  –  js/ui/tecla-viewer.js
 * Floating MIDI simulator window for the ocu universe.
 * Theme adapts to site bg/el colors via window.teclaViewerApplyColors().
 * Exposes: openTeclaViewer(anchorEl?), closeTeclaViewer()
 * ================================================================ */

(function () {
    'use strict';

    // ── CSS (uses --tv-bg / --tv-el custom props, updated on color change) ───
    const CSS = `
#tecla-modal {
    position: absolute;
    z-index: 620;
    width: 680px;
    min-width: 380px;
    height: 560px;
    min-height: 360px;
    display: none;
    flex-direction: column;
    background: var(--tv-bg, #ffffff);
    color: var(--tv-el, #222222);
    border: 1px solid rgba(128,128,128,0.18);
    box-shadow: 0 12px 48px rgba(0,0,0,0.13), 0 2px 8px rgba(0,0,0,0.07);
    border-radius: 14px;
    overflow: hidden;
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    font-size: 12px;
    resize: both;
}
#tecla-modal.show { display: flex; }

.tv-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    border-bottom: 1px solid rgba(128,128,128,0.12);
    cursor: move;
    user-select: none;
    touch-action: none;
    flex-shrink: 0;
    background: rgba(128,128,128,0.04);
}
.tv-midi-label {
    font-size: 9px;
    letter-spacing: 2px;
    text-transform: uppercase;
    opacity: 0.35;
    margin-right: 2px;
}
.tv-midi-select {
    appearance: none;
    -webkit-appearance: none;
    border: 1px solid rgba(128,128,128,0.25);
    border-radius: 6px;
    padding: 3px 22px 3px 8px;
    font-size: 11px;
    background: var(--tv-bg, #fff) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='7' height='4'%3E%3Cpath d='M0 0l3.5 4L7 0z' fill='%23999'/%3E%3C/svg%3E") no-repeat right 7px center;
    color: var(--tv-el, #222);
    height: 26px;
    min-width: 130px;
    cursor: pointer;
    max-width: 180px;
}
.tv-midi-select:focus { outline: none; }
.tv-close {
    width: 22px; height: 22px;
    display: flex; align-items: center; justify-content: center;
    border-radius: 50%;
    border: none;
    background: rgba(128,128,128,0.1);
    color: var(--tv-el, #222);
    font-size: 15px;
    cursor: pointer;
    padding: 0; line-height: 1;
    transition: background 0.15s;
    flex-shrink: 0;
}
.tv-close:hover { background: rgba(128,128,128,0.2); }

/* ── Body ── */
.tv-body {
    display: flex;
    flex: 1;
    overflow: hidden;
    min-height: 0;
}

/* ── Modes panel ── */
.tv-modes {
    width: 170px;
    min-width: 120px;
    flex-shrink: 0;
    border-right: 1px solid rgba(128,128,128,0.12);
    display: flex;
    flex-direction: column;
    overflow: hidden;
}
.tv-modes-title {
    padding: 8px 12px 6px;
    font-size: 9px;
    letter-spacing: 3px;
    text-transform: uppercase;
    opacity: 0.4;
    flex-shrink: 0;
}
.tv-modes-list {
    flex: 1;
    overflow-y: auto;
    padding: 0 4px 8px;
    scrollbar-width: thin;
}
.tv-modes-list::-webkit-scrollbar { width: 4px; }
.tv-modes-list::-webkit-scrollbar-thumb { background: rgba(128,128,128,0.2); border-radius: 2px; }
.tv-mode-btn {
    display: block;
    width: 100%;
    text-align: left;
    padding: 5px 10px;
    border: none;
    background: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 12px;
    color: var(--tv-el, #222);
    opacity: 0.7;
    transition: opacity 0.1s, background 0.1s;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.tv-mode-btn:hover { opacity: 1; background: rgba(128,128,128,0.08); }
.tv-mode-btn.active { opacity: 1; font-weight: 600; background: rgba(128,128,128,0.12); }

/* ── Main area ── */
.tv-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 12px 14px 10px;
    overflow: hidden;
    gap: 10px;
    min-width: 0;
}

/* ── Status bar ── */
.tv-status {
    font-size: 11px;
    opacity: 0.55;
    min-height: 16px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* ── 4×4 grid ── */
.tv-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 5px;
    flex-shrink: 0;
    max-width: 300px;
}
.tv-btn {
    aspect-ratio: 1;
    border: 2px solid var(--tv-el, #222);
    border-radius: 8px;
    background: transparent;
    color: var(--tv-el, #222);
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0.65;
    transition: opacity 0.08s, background 0.08s, color 0.08s;
    user-select: none;
    touch-action: none;
    letter-spacing: 0;
}
.tv-btn:hover { opacity: 0.9; }
.tv-btn.pressed {
    background: var(--tv-el, #222);
    color: var(--tv-bg, #fff);
    opacity: 1;
}
.tv-btn.layer-key {
    border-style: dashed;
    opacity: 0.85;
}

/* ── Pots ── */
.tv-pots {
    display: flex;
    gap: 10px;
    align-items: center;
    flex-shrink: 0;
}
.tv-pot-wrap {
    display: flex;
    flex-direction: column;
    flex: 1;
    gap: 3px;
}
.tv-pot-label {
    display: flex;
    justify-content: space-between;
    font-size: 10px;
    opacity: 0.5;
}
.tv-pot-range {
    -webkit-appearance: none;
    width: 100%;
    height: 2px;
    background: rgba(128,128,128,0.2);
    border-radius: 2px;
    outline: none;
    cursor: pointer;
}
.tv-pot-range::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 13px; height: 13px;
    background: var(--tv-el, #222);
    border-radius: 50%;
    cursor: pointer;
}

/* ── Controls row ── */
.tv-controls {
    display: flex;
    gap: 7px;
    flex-shrink: 0;
    align-items: center;
}
.tv-ctrl-btn {
    padding: 5px 13px;
    border: 1.5px solid var(--tv-el, #222);
    border-radius: 7px;
    background: transparent;
    color: var(--tv-el, #222);
    font-size: 11px;
    cursor: pointer;
    opacity: 0.6;
    transition: opacity 0.12s, background 0.12s, color 0.12s;
    white-space: nowrap;
}
.tv-ctrl-btn:hover { opacity: 1; }
.tv-ctrl-btn.primary {
    background: var(--tv-el, #222);
    color: var(--tv-bg, #fff);
    opacity: 0.85;
}
.tv-ctrl-btn.primary:hover { opacity: 1; }
.tv-ctrl-btn:disabled { opacity: 0.2; cursor: default; }

/* ── Log ── */
.tv-log {
    flex: 1;
    overflow-y: auto;
    font-size: 10.5px;
    opacity: 0.5;
    line-height: 1.55;
    min-height: 40px;
    scrollbar-width: thin;
}
.tv-log::-webkit-scrollbar { width: 3px; }
.tv-log::-webkit-scrollbar-thumb { background: rgba(128,128,128,0.2); }
.tv-log-line { font-variant-numeric: tabular-nums; }
.tv-log-line.ok  { opacity: 0.8; }
.tv-log-line.warn { color: #b07700; opacity: 0.9; }
.tv-log-line.err { color: #b00000; opacity: 0.9; }

/* ── Footer ── */
.tv-footer {
    padding: 6px 14px 8px;
    border-top: 1px solid rgba(128,128,128,0.1);
    flex-shrink: 0;
    background: rgba(128,128,128,0.03);
    overflow: hidden;
    max-height: 80px;
    min-height: 32px;
}
`;

    if (!document.getElementById('tecla-viewer-style')) {
        const s = document.createElement('style');
        s.id = 'tecla-viewer-style';
        s.textContent = CSS;
        document.head.appendChild(s);
    }

    // ── Color sync ───────────────────────────────────────────────────────────
    function _applyColorsToModal(bg, el) {
        document.documentElement.style.setProperty('--tv-bg', bg || '#ffffff');
        document.documentElement.style.setProperty('--tv-el', el || '#222222');
    }

    // Read current site colors on open
    function _readSiteColors() {
        const bg = document.body.style.backgroundColor || '#ffffff';
        const elEl = document.querySelector('#canvas a');
        const el = elEl ? elEl.style.color : '#222222';
        return { bg: bg || '#ffffff', el: el || '#222222' };
    }

    // ── Inline WebMidiManager ─────────────────────────────────────────────────
    class WebMidiManager {
        constructor() {
            this.access = null;
            this.output = null;
            this.outputs = [];
            this.onLog = null;
            this.onUpdate = null;
        }
        async init() {
            if (!navigator.requestMIDIAccess)
                return { success: false, error: 'Web MIDI no disponible (cal Chrome/Edge)' };
            try {
                this.access = await navigator.requestMIDIAccess({ sysex: false });
                this._updateOutputs();
                this.access.onstatechange = () => {
                    this._updateOutputs();
                    if (this.onUpdate) this.onUpdate(this.outputs);
                };
                return { success: true, outputs: this.outputs };
            } catch (e) {
                return { success: false, error: `MIDI denegat: ${e.message}` };
            }
        }
        _updateOutputs() {
            this.outputs = [];
            if (!this.access) return;
            for (const [id, out] of this.access.outputs)
                this.outputs.push({ id, name: out.name, port: out });
        }
        selectOutput(id) {
            if (!id) { this.output = null; return true; }
            const found = this.outputs.find(o => o.id === id);
            if (found) { this.output = found.port; return true; }
            return false;
        }
        send(type, a, b, ch = 0) {
            const channel = Math.max(0, Math.min(15, ch | 0));
            let data;
            switch (type) {
                case 'note_on':       data = [0x90 | channel, a & 0x7F, b & 0x7F]; break;
                case 'note_off':      data = [0x80 | channel, a & 0x7F, b & 0x7F]; break;
                case 'control_change':data = [0xB0 | channel, a & 0x7F, b & 0x7F]; break;
                case 'pitchwheel': {
                    const p = Math.max(-8192, Math.min(8191, a | 0)) + 8192;
                    data = [0xE0 | channel, p & 0x7F, (p >> 7) & 0x7F]; break;
                }
                default: return;
            }
            if (this.output) try { this.output.send(data); } catch { }
            if (this.onLog) this.onLog(type, a, b, ch);
        }
        allNotesOff() {
            for (let ch = 0; ch < 16; ch++) {
                this.send('control_change', 120, 0, ch);
                this.send('control_change', 123, 0, ch);
            }
        }
        isAvailable() { return !!this.access; }
    }

    // ── Inline TECLASimulator ────────────────────────────────────────────────
    class TECLASimulator {
        constructor(webMidi, onLog) {
            this.webMidi = webMidi;
            this.onLog = onLog || (() => { });
            this.pyodide = null;
            this.state = null;
            this.isReady = false;
            this.isRunning = false;
            this._loopId = null;
            this.buttons = new Array(16).fill(false);
            this.pots = [0, 0, 0];
            this._modeName = null;
        }

        async initPyodide(onProgress) {
            if (this.isReady) return;
            onProgress?.('Carregant Pyodide…');

            // Lazy-load Pyodide CDN script if not yet present
            if (!window.loadPyodide) {
                await new Promise((res, rej) => {
                    const s = document.createElement('script');
                    s.src = 'https://cdn.jsdelivr.net/pyodide/v0.26.3/full/pyodide.js';
                    s.onload = res; s.onerror = rej;
                    document.head.appendChild(s);
                });
            }

            this.pyodide = await window.loadPyodide({
                indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.26.3/full/'
            });

            onProgress?.('Instal·lant mocks…');

            this.pyodide.globals.set('_js_midi_send', (type, a, b, ch) => {
                this.webMidi.send(type, a | 0, b | 0, ch | 0);
            });

            const mocksCode = await fetch('py/tecla_mocks.py').then(r => r.text());
            await this.pyodide.runPythonAsync(mocksCode);
            await this.pyodide.runPythonAsync('install_mocks()');

            this.pyodide.FS.mkdir('/tecla');
            this.pyodide.FS.mkdir('/tecla/modes');
            await this.pyodide.runPythonAsync("import sys; sys.path.insert(0, '/tecla')");

            const baseCode = await fetch('py/base_mode.py').then(r => r.text());
            this.pyodide.FS.writeFile('/tecla/modes/base_mode.py', baseCode);

            // Inline music_constants.py — no server fetch needed
            this.pyodide.FS.writeFile('/tecla/music_constants.py', `SCALES = (
    (0, 2, 4, 5, 7, 9, 11),
    (0, 2, 3, 5, 7, 9, 10),
    (0, 1, 3, 5, 7, 8, 10),
    (0, 2, 4, 6, 7, 9, 11),
    (0, 2, 4, 5, 7, 9, 10),
    (0, 2, 3, 5, 7, 8, 10),
    (0, 1, 3, 5, 6, 8, 10),
    (0, 2, 4, 7, 9),
    (0, 3, 5, 7, 10),
    (0, 1, 4, 6, 7),
    (0, 2, 5, 7, 9),
    (0, 1, 4, 5, 7, 8, 11),
    (0, 2, 3, 6, 7, 9, 10),
    (0, 2, 4, 6, 7, 9, 10),
    (0, 1, 3, 4, 6, 8, 10),
    (0, 2, 3, 5, 7, 9, 11),
    (0, 1, 4, 5, 7, 8, 11),
    (0, 1, 3, 6, 7, 8, 11),
    (0, 1, 4, 5, 7, 8, 10),
    (0, 1, 4, 5, 7, 9, 11),
    (0, 1, 3, 5, 7, 8, 10),
    (0, 1, 4, 5, 7, 8, 11),
    (0, 2, 4, 6, 8, 10),
    (0, 2, 4, 5, 7, 8, 11),
)
SCALE_NAMES = (
    'Jonic (Major)', 'Doric', 'Frigi', 'Lidi', 'Mixolidi',
    'Eolic (Minor)', 'Locri', 'Pentatonica Major', 'Pentatonica Menor',
    'Japonesa', 'Egipcia', 'Arabiga', 'Hongaresa Menor', 'Lidia Dominant',
    'Alterada', 'Menor Melodica', 'Raga Bhairav', 'Raga Todi', 'Flamenca',
    'Catalana', 'Frigia', 'Balcanica', 'Tons Sencers', 'Harmonica Major',
)
ARP_DIRS = (
    'up', 'down', 'pingpong', 'random', 'order',
    'alberti', 'alberti_alt', 'waltz', 'broken', 'tremolo',
    'zigzag', 'block', 'rolled', 'octaves', 'contrary', 'spread'
)
KEYS = (0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10, 5)
NOTES = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
CHORDS = {
    'Major': (0, 4, 7), 'm': (0, 3, 7), '7': (0, 4, 7, 10),
    'maj7': (0, 4, 7, 11), 'm7': (0, 3, 7, 10), 'dim': (0, 3, 6),
    'aug': (0, 4, 8), 'sus4': (0, 5, 7), 'sus2': (0, 2, 7),
}
def note_offset(note_name):
    try:
        return NOTES.index(note_name)
    except ValueError:
        return 0
`);

            this.state = this.pyodide.globals.get('_state');
            this.isReady = true;
            onProgress?.('Pyodide llest ✓');
            this._log('Motor Python inicialitzat', 'ok');
        }

        async loadMode(pyCode, fileName) {
            if (!this.isReady) throw new Error('Pyodide no inicialitzat');
            const wasRunning = this.isRunning;
            if (wasRunning) this.stopLoop();

            this.pyodide.FS.writeFile('/tecla/modes/mode_active.py', pyCode);

            await this.pyodide.runPythonAsync(`
import sys, importlib
if '_active_mode' in globals():
    try: _active_mode.cleanup()
    except: pass
    del _active_mode
for _k in list(sys.modules.keys()):
    if 'mode_active' in _k: del sys.modules[_k]
`);
            const result = await this.pyodide.runPythonAsync(`
import importlib
import modes.mode_active as _mode_mod
importlib.reload(_mode_mod)
from adafruit_midi import MIDI
import usb_midi
from modes.base_mode import BaseMode

# Primary: find BaseMode subclass
_mode_class = None
for _v in vars(_mode_mod).values():
    if isinstance(_v, type) and _v is not BaseMode and issubclass(_v, BaseMode):
        _mode_class = _v
        break

# Fallback: any class with setup() + update() (e.g. KeyboardMode)
if _mode_class is None:
    for _v in vars(_mode_mod).values():
        if (isinstance(_v, type)
                and callable(getattr(_v, 'setup', None))
                and callable(getattr(_v, 'update', None))
                and _v.__module__ == _mode_mod.__name__):
            _mode_class = _v
            break

if _mode_class is None:
    raise ValueError("Cap classe mode trobada")

_midi_inst = MIDI(midi_out=usb_midi.ports[1])

# Detect if constructor wants config_manager (e.g. KeyboardMode)
import inspect as _inspect
_params = list(_inspect.signature(_mode_class.__init__).parameters.keys())
if 'config_manager' in _params:
    class _MockCfgMgr:
        def get_keyboard_scales(self):
            try:
                import music_constants as _mc
                return list(range(len(_mc.SCALES)))
            except Exception:
                return list(range(24))
        def get_arpeggiator_modes(self):
            try:
                import music_constants as _mc
                return list(_mc.ARP_DIRS)
            except Exception:
                return ['up','down','pingpong','random']
        def get_potentiometer_functions(self):
            return {'pot_x':'Velocity/Arp Speed (dual)','pot_y':'Modulation (CC1)','pot_z':'Sustain (CC64)'}
        def get_arp_potentiometer_functions(self):
            return {'arp_pot_x':'Arp Speed (BPM)','arp_pot_y':'Arp Pattern Selector','arp_pot_z':'Gate Length'}
    _active_mode = _mode_class(_midi_inst, config_manager=_MockCfgMgr())
else:
    _active_mode = _mode_class(_midi_inst)

_active_mode.setup()
_active_mode.__class__.__name__
`);
            this._modeName = result;
            this._log(`Mode: ${this._modeName}`, 'ok');
            if (wasRunning) this.startLoop();
            return result;
        }

        startLoop() {
            if (this.isRunning || !this.isReady) return;
            if (!this.pyodide.globals.has('_active_mode')) {
                this._log('Cap mode carregat', 'warn'); return;
            }
            this.isRunning = true;
            this._loopId = setInterval(() => this._tick(), 50);
            this._log('Simulador iniciat ▶', 'ok');
        }

        stopLoop() {
            if (!this.isRunning) return;
            this.isRunning = false;
            if (this._loopId) { clearInterval(this._loopId); this._loopId = null; }
            try {
                this.pyodide.runPython(`
if '_active_mode' in globals() and hasattr(_active_mode, 'cleanup'):
    try: _active_mode.cleanup()
    except: pass
`);
            } catch { }
            this.webMidi.allNotesOff();
            this._log('Simulador aturat ■', 'info');
        }

        _tick() {
            try {
                for (let i = 0; i < 16; i++) this.state.set_button(i, this.buttons[i]);
                for (let i = 0; i < 3; i++)  this.state.set_pot(i, this.pots[i]);
                this.pyodide.runPython(`
_active_mode.update(
    [_state.pots[0], _state.pots[1], _state.pots[2]],
    list(_state.buttons)
)`);
            } catch (e) {
                console.warn('[TECLA tick]', e.message);
            }
        }

        pressButton(idx) {
            if (idx >= 0 && idx < 16) {
                this.buttons[idx] = true;
                if (this.isReady && this.isRunning) this._tick();
            }
        }
        releaseButton(idx) {
            if (idx >= 0 && idx < 16) {
                this.buttons[idx] = false;
                if (this.isReady && this.isRunning) this._tick();
            }
        }
        setPot(idx, v)    { if (idx >= 0 && idx < 3) this.pots[idx] = Math.max(0, Math.min(127, v | 0)); }

        _log(msg, type = 'info') { this.onLog(msg, type); }
    }

    // ── State ─────────────────────────────────────────────────────────────────
    let modal       = null;
    let sim         = null;
    let webMidi     = null;
    let modesIndex  = [];
    let logLines    = [];
    let activeModeBtn = null;
    let midiSelectEl  = null;
    let startBtn = null, stopBtn = null, initBtn = null;
    let statusEl = null, logEl = null;
    const MAX_LOG = 40;

    // ── Layer-switching state ──────────────────────────────────────────────────
    let _layer         = 0;                      // 0 = keyboard, 1 = button-mode
    let _btnModes      = new Array(12).fill(null); // {file, name} per slot
    let _assignPending = null;                    // mode awaiting slot assignment
    let _gridBtns      = [];                      // references to 16 grid buttons

    // ── Log helper ────────────────────────────────────────────────────────────
    function addLog(msg, type = 'info') {
        logLines.push({ msg, type });
        if (logLines.length > MAX_LOG) logLines.shift();
        if (logEl) {
            logEl.innerHTML = logLines.map(l =>
                `<div class="tv-log-line ${l.type}">${escHtml(l.msg)}</div>`
            ).join('');
            logEl.scrollTop = logEl.scrollHeight;
        }
    }

    function escHtml(s) {
        return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }

    function setStatus(msg) {
        if (statusEl) statusEl.textContent = msg;
    }

    // ── Build modal ────────────────────────────────────────────────────────────
    function buildModal() {
        if (document.getElementById('tecla-modal')) {
            modal = document.getElementById('tecla-modal');
            return;
        }

        modal = document.createElement('div');
        modal.id = 'tecla-modal';

        // ── Header ────────────────────────────────────────────────────────────
        const header = document.createElement('div');
        header.className = 'tv-header';

        const midiLbl = document.createElement('span');
        midiLbl.className = 'tv-midi-label';
        midiLbl.textContent = 'MIDI';

        midiSelectEl = document.createElement('select');
        midiSelectEl.className = 'tv-midi-select';
        midiSelectEl.style.flex = '1';
        _populateMidiSelect();
        midiSelectEl.onchange = () => {
            if (webMidi) webMidi.selectOutput(midiSelectEl.value);
        };
        midiSelectEl.addEventListener('mousedown', e => e.stopPropagation());

        const closeBtn = document.createElement('button');
        closeBtn.className = 'tv-close';
        closeBtn.innerHTML = '&times;';
        closeBtn.onclick = closeTeclaViewer;

        header.appendChild(midiLbl);
        header.appendChild(midiSelectEl);
        header.appendChild(closeBtn);

        // ── Body ─────────────────────────────────────────────────────────────
        const body = document.createElement('div');
        body.className = 'tv-body';

        // Left: modes
        const modesPanel = document.createElement('div');
        modesPanel.className = 'tv-modes';
        const modesTitle = document.createElement('div');
        modesTitle.className = 'tv-modes-title';
        modesTitle.textContent = 'Modes';
        const modesList = document.createElement('div');
        modesList.className = 'tv-modes-list';
        modesPanel.appendChild(modesTitle);
        modesPanel.appendChild(modesList);

        // Populate modes list (async)
        // Teclat (mode_keyboard) always first
        const teclatBtn = document.createElement('button');
        teclatBtn.className = 'tv-mode-btn';
        teclatBtn.textContent = '★ Teclat';
        teclatBtn.title = 'mode_keyboard.py';
        teclatBtn.style.fontWeight = '600';
        teclatBtn.onclick = () => {
            if (_layer === 1) {
                _assignPending = { file: 'mode_keyboard.py', name: 'Teclat' };
                _updateLayerUI();
            } else {
                loadModeByFile('mode_keyboard.py', teclatBtn);
            }
        };
        modesList.appendChild(teclatBtn);

        fetch('py/modes_index.json')
            .then(r => r.json())
            .then(data => {
                modesIndex = data.modes || [];
                modesIndex.forEach(m => {
                    const btn = document.createElement('button');
                    btn.className = 'tv-mode-btn';
                    btn.textContent = m.name;
                    btn.title = m.file;
                    btn.onclick = () => {
                        if (_layer === 1) {
                            _assignPending = { file: m.file, name: m.name };
                            _updateLayerUI();
                        } else {
                            loadModeByFile(m.file, btn);
                        }
                    };
                    modesList.appendChild(btn);
                });
            })
            .catch(() => addLog('modes_index.json no trobat', 'warn'));

        // Right: main
        const main = document.createElement('div');
        main.className = 'tv-main';

        // Status
        statusEl = document.createElement('div');
        statusEl.className = 'tv-status';
        statusEl.textContent = 'Selecciona un mode i prem Init';

        // 4×4 grid
        _gridBtns = [];
        const grid = document.createElement('div');
        grid.className = 'tv-grid';
        for (let i = 0; i < 16; i++) {
            const btn = document.createElement('div');
            btn.className = 'tv-btn';
            btn.dataset.idx = i;
            // Button 13 (index 12): layer toggle
            if (i === 12) {
                btn.textContent = '\u21C5';
                btn.title = 'Canviar capa';
                btn.classList.add('layer-key');
                btn.style.opacity = '0.85';
            } else {
                btn.textContent = i + 1;
            }
            _gridBtns.push(btn);

            const press = () => {
                if (!sim || !sim.isReady) return;

                // ── Button 13: toggle layer ──
                if (i === 12) {
                    _layer = 1 - _layer;
                    if (_layer === 0) _assignPending = null;
                    _updateLayerUI();
                    btn.classList.add('pressed');
                    setTimeout(() => btn.classList.remove('pressed'), 120);
                    return;
                }

                // ── Layer 1: mode assignment / activation ──
                if (_layer === 1 && i < 12) {
                    if (_assignPending) {
                        _btnModes[i] = { ..._assignPending };
                        _assignPending = null;
                        addLog(`"${_btnModes[i].name}" \u2192 tecla ${i + 1}`, 'ok');
                        _updateLayerUI();
                    } else if (_btnModes[i]) {
                        const m = _btnModes[i];
                        _layer = 0;
                        _assignPending = null;
                        _updateLayerUI();
                        loadModeByFile(m.file, activeModeBtn);
                    } else {
                        addLog(`Tecla ${i + 1}: sense mode assignat`, 'warn');
                    }
                    btn.classList.add('pressed');
                    setTimeout(() => btn.classList.remove('pressed'), 120);
                    return;
                }

                // ── Layer 0: normal keyboard ──
                sim.pressButton(i);
                btn.classList.add('pressed');
            };
            const release = () => {
                if (!sim || _layer === 1) return;
                sim.releaseButton(i);
                btn.classList.remove('pressed');
            };

            btn.addEventListener('mousedown',  press);
            btn.addEventListener('mouseup',    release);
            btn.addEventListener('mouseleave', release);
            btn.addEventListener('touchstart', e => { press(); e.preventDefault(); }, { passive: false });
            btn.addEventListener('touchend',   release);
            btn.addEventListener('touchcancel',release);
            grid.appendChild(btn);
        }

        // Pots X Y Z
        const potsRow = document.createElement('div');
        potsRow.className = 'tv-pots';
        ['X', 'Y', 'Z'].forEach((label, idx) => {
            const wrap = document.createElement('div');
            wrap.className = 'tv-pot-wrap';
            const lbl = document.createElement('div');
            lbl.className = 'tv-pot-label';
            const lspan = document.createElement('span');
            lspan.textContent = label;
            const vspan = document.createElement('span');
            vspan.textContent = '0';
            lbl.appendChild(lspan); lbl.appendChild(vspan);
            const range = document.createElement('input');
            range.type = 'range'; range.className = 'tv-pot-range';
            range.min = '0'; range.max = '127'; range.value = '0';
            range.addEventListener('mousedown', e => e.stopPropagation());
            range.oninput = () => {
                vspan.textContent = range.value;
                if (sim) sim.setPot(idx, +range.value);
            };
            wrap.appendChild(lbl); wrap.appendChild(range);
            potsRow.appendChild(wrap);
        });

        // Controls
        const controls = document.createElement('div');
        controls.className = 'tv-controls';

        initBtn = document.createElement('button');
        initBtn.className = 'tv-ctrl-btn primary';
        initBtn.textContent = '⚙ Init Python';
        initBtn.onclick = initSimulator;

        startBtn = document.createElement('button');
        startBtn.className = 'tv-ctrl-btn';
        startBtn.textContent = '▶ Start';
        startBtn.disabled = true;
        startBtn.onclick = () => { if (sim) sim.startLoop(); updateCtrlState(); };

        stopBtn = document.createElement('button');
        stopBtn.className = 'tv-ctrl-btn';
        stopBtn.textContent = '■ Stop';
        stopBtn.disabled = true;
        stopBtn.onclick = () => { if (sim) sim.stopLoop(); updateCtrlState(); };

        controls.appendChild(initBtn);
        controls.appendChild(startBtn);
        controls.appendChild(stopBtn);

        // Log
        logEl = document.createElement('div');
        logEl.className = 'tv-log';

        main.appendChild(statusEl);
        main.appendChild(grid);
        main.appendChild(potsRow);
        main.appendChild(controls);
        main.appendChild(logEl);

        body.appendChild(modesPanel);
        body.appendChild(main);

        // Footer (MIDI log strip)
        const footer = document.createElement('div');
        footer.className = 'tv-footer';
        footer.id = 'tecla-footer-log';

        modal.appendChild(header);
        modal.appendChild(body);
        modal.appendChild(footer);
        document.body.appendChild(modal);

        setupDrag(modal, header);
    }

    // ── Init simulator (Pyodide + WebMIDI) ────────────────────────────────────
    async function initSimulator() {
        initBtn.disabled = true;
        initBtn.textContent = '⚙ Inicialitzant…';

        // WebMIDI
        webMidi = new WebMidiManager();
        webMidi.onLog = (type, a, b, ch) => {
            const footer = document.getElementById('tecla-footer-log');
            if (footer) {
                const shortType = { note_on:'N+', note_off:'N-', control_change:'CC', pitchwheel:'PB' }[type] || type;
                footer.textContent = `${shortType} ${a} ${b > 0 ? '/ ' + b : ''} ch:${ch}`;
            }
        };
        webMidi.onUpdate = (outputs) => _populateMidiSelect(outputs);
        const midiRes = await webMidi.init();
        if (midiRes.success) {
            _populateMidiSelect(webMidi.outputs);
            if (webMidi.outputs.length > 0) webMidi.selectOutput(webMidi.outputs[0].id);
            addLog(`MIDI OK – ${webMidi.outputs.length} port(s)`, 'ok');
        } else {
            addLog(`MIDI: ${midiRes.error}`, 'warn');
        }

        // Pyodide
        sim = new TECLASimulator(webMidi, (msg, type) => {
            addLog(msg, type);
            setStatus(msg);
        });
        try {
            await sim.initPyodide((msg) => { setStatus(msg); addLog(msg); });
            initBtn.textContent = '✓ Python llest';
            startBtn.disabled = true; // need mode first
            setStatus('Selecciona un mode de la llista');
        } catch (e) {
            addLog('Error Pyodide: ' + e.message, 'err');
            setStatus('Error: ' + e.message);
            initBtn.disabled = false;
            initBtn.textContent = '⚙ Init Python';
        }
    }

    // ── Load mode by file ────────────────────────────────────────────────────
    async function loadModeByFile(file, btn) {
        if (!sim || !sim.isReady) {
            addLog('Inicialitza Python primer', 'warn');
            setStatus('Cal inicialitzar Python primer');
            return;
        }
        if (activeModeBtn) activeModeBtn.classList.remove('active');
        activeModeBtn = btn;
        btn.classList.add('active');

        setStatus(`Carregant ${file}…`);
        try {
            const code = await fetch(`py/modes/${file}`).then(r => r.text());
            await sim.loadMode(code, file);
            startBtn.disabled = false;
            stopBtn.disabled = false;
            if (!sim.isRunning) sim.startLoop();
            updateCtrlState();
            setStatus(`Mode actiu: ${sim._modeName}`);
        } catch (e) {
            addLog('Error mode: ' + e.message, 'err');
            setStatus('Error carregant mode');
            btn.classList.remove('active');
            activeModeBtn = null;
        }
    }

    // ── MIDI select population ───────────────────────────────────────────────
    function _populateMidiSelect(outputs) {
        if (!midiSelectEl) return;
        const list = outputs || (webMidi ? webMidi.outputs : []);
        const prev = midiSelectEl.value;
        midiSelectEl.innerHTML = '';
        const none = document.createElement('option');
        none.value = ''; none.textContent = list.length ? '— Port MIDI —' : '(sense ports)';
        midiSelectEl.appendChild(none);
        list.forEach(o => {
            const opt = document.createElement('option');
            opt.value = o.id; opt.textContent = o.name;
            midiSelectEl.appendChild(opt);
        });
        if (prev) midiSelectEl.value = prev;
    }

    // ── Update control button states ─────────────────────────────────────────
    function updateCtrlState() {
        if (!sim) return;
        startBtn.disabled = !sim.isReady || sim.isRunning || !sim._modeName;
        stopBtn.disabled  = !sim.isRunning;
    }

    // ── Layer UI update ───────────────────────────────────────────────────────
    function _updateLayerUI() {
        const isL1 = _layer === 1;
        _gridBtns.forEach((b, i) => {
            if (i === 12) {
                b.textContent = '\u21C5';
                b.title = isL1 ? 'Tornar a mode teclat' : 'Canviar a capa modes';
                b.classList.toggle('layer-key', true);
                b.style.background = isL1 ? 'var(--tv-el,#222)' : '';
                b.style.color      = isL1 ? 'var(--tv-bg,#fff)' : '';
                b.style.opacity    = '1';
                return;
            }
            if (i >= 13) return;
            if (isL1) {
                const m = _btnModes[i];
                const hasPending = !!_assignPending;
                b.style.fontWeight = m ? '700' : '';
                b.style.fontSize   = m ? '9px' : '';
                b.style.opacity    = m ? '0.95' : (hasPending ? '0.5' : '0.3');
                b.textContent      = m ? m.name.replace('mode_','').replace('.py','').substring(0,6) : (i + 1);
                b.title            = m ? m.name + '\nPrem per activar' : (hasPending ? 'Prem per assignar' : 'Sense mode');
            } else {
                b.style.background = '';
                b.style.color      = '';
                b.style.opacity    = '';
                b.style.fontWeight = '';
                b.style.fontSize   = '';
                b.textContent      = i + 1;
                b.title            = '';
            }
        });
        if (isL1) {
            setStatus(_assignPending
                ? `\u2192 Assigna "${_assignPending.name}" \u2014 prem una tecla (1-12)`
                : 'Capa modes \u21C5 \u2014 selecciona mode + prem tecla per assignar');
        } else {
            setStatus(sim?._modeName ? `Mode actiu: ${sim._modeName}` : 'Selecciona un mode');
        }
    }

    // ── Drag ─────────────────────────────────────────────────────────────────
    function setupDrag(el, handle) {
        let dragging = false, ox = 0, oy = 0;
        const start = (cx, cy) => {
            dragging = true;
            const r = el.getBoundingClientRect();
            ox = cx - r.left; oy = cy - r.top;
        };
        const move = (cx, cy) => {
            if (!dragging) return;
            el.style.left = Math.max(0, Math.min(cx - ox, window.innerWidth  - el.offsetWidth))  + 'px';
            el.style.top  = Math.max(0, Math.min(cy - oy, window.innerHeight - el.offsetHeight)) + 'px';
        };
        const end = () => { dragging = false; };

        handle.addEventListener('mousedown', e => {
            if (e.target.closest('.tv-close')) return;
            start(e.clientX, e.clientY); e.preventDefault();
        });
        document.addEventListener('mousemove', e => move(e.clientX, e.clientY));
        document.addEventListener('mouseup', end);
        handle.addEventListener('touchstart', e => {
            if (e.target.closest('.tv-close,.tv-midi-select')) return;
            start(e.touches[0].clientX, e.touches[0].clientY);
        }, { passive: true });
        document.addEventListener('touchmove', e => {
            if (!dragging) return;
            move(e.touches[0].clientX, e.touches[0].clientY); e.preventDefault();
        }, { passive: false });
        document.addEventListener('touchend', end);
    }

    // ── Public API ────────────────────────────────────────────────────────────
    function openTeclaViewer(anchorEl) {
        buildModal();
        modal = document.getElementById('tecla-modal');

        // Sync colors from site
        const { bg, el } = _readSiteColors();
        _applyColorsToModal(bg, el);

        if (anchorEl && anchorEl.getBoundingClientRect) {
            const r = anchorEl.getBoundingClientRect();
            modal.style.left = Math.max(0, Math.min(r.left + 40, window.innerWidth  - 700)) + 'px';
            modal.style.top  = Math.max(0, Math.min(r.top  + 20, window.innerHeight - 550)) + 'px';
        } else {
            modal.style.left = Math.max(0, Math.round((window.innerWidth  - 680) / 2)) + 'px';
            modal.style.top  = Math.max(0, Math.round((window.innerHeight - 530) / 4)) + 'px';
        }
        modal.classList.add('show');
    }

    function closeTeclaViewer() {
        if (!modal) return;
        modal.classList.remove('show');
        if (sim && sim.isRunning) sim.stopLoop();
    }

    // ── Color hook (called from applyColors in index.html) ───────────────────
    window.teclaViewerApplyColors = function (bg, el) {
        _applyColorsToModal(bg, el);
    };

    window.openTeclaViewer  = openTeclaViewer;
    window.closeTeclaViewer = closeTeclaViewer;

    // Keyboard close
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && modal && modal.classList.contains('show'))
            closeTeclaViewer();
    });

})();
