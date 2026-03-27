/**
 * TECLASimulator — Motor del simulador web amb Pyodide
 *
 * Executa els fitxers .py dels modes TECLA al navegador via WebAssembly Python (Pyodide).
 * El pont Python→JS intercepta les crides MIDI i les redirigeix a WebMidiManager.
 *
 * Ús:
 *   const sim = new TECLASimulator(webMidi, onLog);
 *   await sim.initPyodide();
 *   await sim.loadMode(pyCode, 'mode_todrone.py');
 *   sim.startLoop();
 */
import { WebMidiManager } from './tecla-webmidi.js';

export class TECLASimulator {
    constructor(webMidi, onLog) {
        this.webMidi = webMidi;          // WebMidiManager instance
        this.onLog = onLog || (() => { }); // callback(msg, type)
        this.pyodide = null;
        this.state = null;             // proxy de l'objecte _state Python
        this.isReady = false;
        this.isRunning = false;
        this._loopId = null;
        this.buttons = new Array(16).fill(false);
        this.pots = [0, 0, 0];        // 0-127
        this._modeName = null;
    }

    // ── Inicialitzar Pyodide ─────────────────────────────────────────────────

    async initPyodide(onProgress) {
        if (this.isReady) return;
        onProgress?.('Carregant Pyodide (Python al navegador)…');

        // loadPyodide és global, injectat per l'script CDN de Pyodide
        this.pyodide = await window.loadPyodide({
            indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.26.3/full/'
        });

        onProgress?.('Instal·lant mocks de CircuitPython…');

        // Exposa la funció MIDI bridge a Python
        this.pyodide.globals.set('_js_midi_send', (type, a, b, ch) => {
            this.webMidi.send(type, a | 0, b | 0, ch | 0);
        });

        // Carrega i executa els mocks
        const mocksRes = await fetch('/py/tecla_mocks.py');
        const mocksCode = await mocksRes.text();
        await this.pyodide.runPythonAsync(mocksCode);
        await this.pyodide.runPythonAsync('install_mocks()');

        // Configura el sistema de fitxers virtual per als imports Python
        this.pyodide.FS.mkdir('/tecla');
        this.pyodide.FS.mkdir('/tecla/modes');
        await this.pyodide.runPythonAsync("import sys; sys.path.insert(0, '/tecla')");

        // Carrega base_mode.py al VFS
        const baseRes = await fetch('/py/base_mode.py');
        const baseCode = await baseRes.text();
        this.pyodide.FS.writeFile('/tecla/modes/base_mode.py', baseCode);

        // Guarda la referència a l'estat compartit
        this.state = this.pyodide.globals.get('_state');

        this.isReady = true;
        onProgress?.('Pyodide llest ✓');
        this._log('Motor Python inicialitzat correctament', 'ok');
    }

    // ── Carregar mode ────────────────────────────────────────────────────────

    async loadMode(pyCode, fileName) {
        if (!this.isReady) throw new Error('Pyodide no inicialitzat');

        const wasRunning = this.isRunning;
        if (wasRunning) this.stopLoop();

        // Escriu el codi del mode al VFS
        this.pyodide.FS.writeFile('/tecla/modes/mode_active.py', pyCode);

        // Cleanup del mode anterior i purga de mòduls
        await this.pyodide.runPythonAsync(`
import sys, importlib

# Neteja el mode anterior
if '_active_mode' in globals():
    try: _active_mode.cleanup()
    except: pass
    del _active_mode

# Purga tots els mòduls del mode actiu
for _k in list(sys.modules.keys()):
    if 'mode_active' in _k:
        del sys.modules[_k]
`);

        // Importa el mòdul directament (no import *) i cerca la classe dins __dict__
        const result = await this.pyodide.runPythonAsync(`
import importlib
import modes.mode_active as _mode_mod
importlib.reload(_mode_mod)

from adafruit_midi import MIDI
import usb_midi
from modes.base_mode import BaseMode

_mode_class = None
for _v in vars(_mode_mod).values():
    if isinstance(_v, type) and _v is not BaseMode and issubclass(_v, BaseMode):
        _mode_class = _v
        break

if _mode_class is None:
    raise ValueError("No s'ha trobat cap classe que hereti de BaseMode a mode_active")

_midi_inst = MIDI(midi_out=usb_midi.ports[1])
_active_mode = _mode_class(_midi_inst)
_active_mode.setup()
_active_mode.__class__.__name__
`);

        this._modeName = result;
        this._log(`Mode carregat: ${this._modeName}`, 'ok');

        if (wasRunning) this.startLoop();
        return result;
    }

    // ── Bucle d'actualització (20 Hz) ────────────────────────────────────────

    startLoop() {
        if (this.isRunning || !this.isReady) return;
        if (!this.pyodide.globals.has('_active_mode')) {
            this._log('Cap mode carregat. Carrega un mode .py primer.', 'warn');
            return;
        }
        this.isRunning = true;
        this._loopId = setInterval(() => this._tick(), 50);
        this._log('Simulador iniciat', 'ok');
    }

    stopLoop() {
        if (!this.isRunning) return;
        this.isRunning = false;
        if (this._loopId) { clearInterval(this._loopId); this._loopId = null; }

        // Crida cleanup + All Notes Off
        try {
            this.pyodide.runPython(`
if '_active_mode' in globals() and hasattr(_active_mode, 'cleanup'):
    try: _active_mode.cleanup()
    except: pass
`);
        } catch { }
        this.webMidi.allNotesOff();
        this._log('Simulador aturat', 'info');
    }

    _tick() {
        try {
            // Sincronitza estat JS → Python
            for (let i = 0; i < 16; i++) this.state.set_button(i, this.buttons[i]);
            for (let i = 0; i < 3; i++)  this.state.set_pot(i, this.pots[i]);

            // Crida update del mode
            this.pyodide.runPython(`
_active_mode.update(
    [_state.pots[0], _state.pots[1], _state.pots[2]],
    list(_state.buttons)
)
`);
        } catch (e) {
            // Errors de mode (ex: codi invàlid) — no atura el simulador
            console.warn('[Simulator tick]', e.message);
        }
    }

    // ── Controls ─────────────────────────────────────────────────────────────

    pressButton(idx) { if (idx >= 0 && idx < 16) this.buttons[idx] = true; }
    releaseButton(idx) { if (idx >= 0 && idx < 16) this.buttons[idx] = false; }
    setPot(idx, value) { if (idx >= 0 && idx < 3) this.pots[idx] = Math.max(0, Math.min(127, value | 0)); }

    // ── Log helper ───────────────────────────────────────────────────────────

    _log(msg, type = 'info') { this.onLog(msg, type); }
}
