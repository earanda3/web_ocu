/**
 * WebMidiManager — Capa Web MIDI API per al simulador TECLA
 * Gestiona l'accés als ports MIDI del sistema i l'enviament de missatges
 */
export class WebMidiManager {
    constructor() {
        this.access = null;
        this.output = null;
        this.outputs = [];
        this.onLog = null;   // callback(type, a, b, ch)
        this.onUpdate = null;   // callback() quan canvien els ports
    }

    async init() {
        if (!navigator.requestMIDIAccess) {
            return { success: false, error: 'Web MIDI API no disponible (cal Chrome/Edge)' };
        }
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
        for (const [id, out] of this.access.outputs) {
            this.outputs.push({ id, name: out.name, port: out });
        }
    }

    selectOutput(id) {
        if (!id) { this.output = null; return true; }
        const found = this.outputs.find(o => o.id === id);
        if (found) { this.output = found.port; return true; }
        return false;
    }

    /**
     * Envia un missatge MIDI al port seleccionat.
     * @param {string} type  'note_on' | 'note_off' | 'control_change' | 'pitchwheel'
     * @param {number} a     nota / control / pitch_bend_value
     * @param {number} b     velocitat / valor
     * @param {number} ch    canal (0-15)
     */
    send(type, a, b, ch = 0) {
        const channel = Math.max(0, Math.min(15, ch | 0));
        let data;
        switch (type) {
            case 'note_on':
                data = [0x90 | channel, a & 0x7F, b & 0x7F];
                break;
            case 'note_off':
                data = [0x80 | channel, a & 0x7F, b & 0x7F];
                break;
            case 'control_change':
                data = [0xB0 | channel, a & 0x7F, b & 0x7F];
                break;
            case 'pitchwheel': {
                const p = Math.max(-8192, Math.min(8191, a | 0)) + 8192;
                data = [0xE0 | channel, p & 0x7F, (p >> 7) & 0x7F];
                break;
            }
            default: return;
        }

        if (this.output) {
            try { this.output.send(data); } catch (e) { /* port tancat */ }
        }
        if (this.onLog) this.onLog(type, a, b, ch);
    }

    allNotesOff() {
        for (let ch = 0; ch < 16; ch++) {
            this.send('control_change', 120, 0, ch);  // All Sound Off
            this.send('control_change', 123, 0, ch);  // All Notes Off
        }
    }

    isAvailable() { return !!this.access; }
}
