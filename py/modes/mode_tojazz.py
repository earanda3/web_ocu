"""
Mode ToJazz - Pedal jazz amb extensions i tensions
Graus: I (tònica), III (terça major), V (quinta), VII (setena major), IX (novena)
Sonoritat jazz moderna, ideal per improvisació jazzística
"""
import time
import math
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange
from adafruit_midi.pitch_bend import PitchBend

class ModeToJazz(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "ToJazz"
        self.last_update = time.monotonic()
        self.active_drones = []
        self.key_circle = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
        self.key_offsets = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
        self.key_index = 0
        self.last_button_press_time = [0] * 16
        self.double_click_threshold = 0.3
        self.base_octave = 3
        self.breath_phase = 0.0
        
        # Tipus d'acords jazz disponibles
        self.chord_types = {
            'maj9': [0, 4, 7, 11, 14],      # I, III, V, VII, IX - Suau i obert
            'm7': [0, 3, 7, 10, 14],        # I, IIIb, V, VIIb, IX - Melancòlic
            '7': [0, 4, 7, 10, 14],         # I, III, V, VIIb, IX - Dominant bluesero
            'dim7': [0, 3, 6, 9, 12],       # I, IIIb, Vb, VIb, I - Tensió
            'sus4': [0, 5, 7, 10, 14],      # I, IV, V, VIIb, IX - Suspensió
        }
        self.chord_type_names = ['maj9', 'm7', '7', 'dim7', 'sus4']
        self.current_chord_type = 0  # Índex del tipus d'acord actual
        
    def setup(self):
        self.initialized = True
        self.last_update = time.monotonic()
        self.breath_phase = 0.0
        # Resetar temps de doble click per evitar que el click d'activació compti
        self.last_button_press_time = [0] * 16
        self._start_pedal()
        
    def _start_pedal(self):
        self._stop_pedal()
        key_offset = self.key_offsets[self.key_index]
        base_note = self.base_octave * 12 + key_offset
        self.active_drones = []
        
        # Usar el tipus d'acord actual
        chord_type = self.chord_type_names[self.current_chord_type]
        degrees = self.chord_types[chord_type]
        
        velocities = [80, 65, 75, 60, 55]
        for i, degree in enumerate(degrees):
            note = max(24, min(96, base_note + degree))
            self.active_drones.append((note, velocities[i]))
            self.midi_out.send(self.note_on(note, velocities[i]))
        print(f"🎷 ToJazz: {self.key_circle[self.key_index]}{chord_type}")
    
    def _stop_pedal(self):
        for note, _ in self.active_drones:
            self.midi_out.send(self.note_off(note, 0))
        self.active_drones = []
    
    def update(self, pot_values, button_states):
        current_time = time.monotonic()
        dt = current_time - self.last_update
        self.last_update = current_time
        x, y, z = pot_values
        
        # X: Nombre de capes (1-5)
        num_layers = 1 + int((x / 127.0) * 4)
        if num_layers != len(self.active_drones):
            self._stop_pedal()
            key_offset = self.key_offsets[self.key_index]
            base_note = self.base_octave * 12 + key_offset
            self.active_drones = []
            
            # Usar el tipus d'acord actual
            chord_type = self.chord_type_names[self.current_chord_type]
            degrees = self.chord_types[chord_type]
            
            velocities = [80, 65, 75, 60, 55]
            for i in range(num_layers):
                if i < len(degrees):
                    note = max(24, min(96, base_note + degrees[i]))
                    self.active_drones.append((note, velocities[i]))
                    self.midi_out.send(self.note_on(note, velocities[i]))
        
        # Y: Reverb (CC91) per profunditat jazz
        self._send_cc(91, y)
        
        # Z: Tipus d'acord (maj9, m7, 7, dim7, sus4)
        new_chord_type = int((z / 127.0) * (len(self.chord_type_names) - 0.01))
        if new_chord_type != self.current_chord_type:
            self.current_chord_type = new_chord_type
            self._start_pedal()  # Reiniciar pedal amb nou tipus d'acord
        
        # Doble click: canviar tonalitat cromàtica
        for btn_idx in range(len(button_states)):
            if btn_idx < len(button_states) and button_states[btn_idx]:
                time_since = current_time - self.last_button_press_time[btn_idx]
                if time_since < self.double_click_threshold:
                    self.last_button_press_time[btn_idx] = 0
                    self.key_index = (self.key_index + 1) % 12
                    self._start_pedal()
                else:
                    self.last_button_press_time[btn_idx] = current_time
        
        layer_names = ['I', 'I-III', 'I-III-V', 'I-III-V-VII', 'Full']
        chord_type = self.chord_type_names[self.current_chord_type]
        return {
            'key': self.key_circle[self.key_index],
            'chord': chord_type,
            'layers': layer_names[num_layers - 1] if num_layers <= 5 else 'Full'
        }
    
    def _send_cc(self, cc_num, value):
        try:
            for ch in range(16):
                self.midi_out.send(ControlChange(cc_num, value, channel=ch))
        except Exception:
            pass
    
    def cleanup(self):
        """Aturar pedal quan es canvia de mode o es prem stop"""
        self._stop_pedal()
        self._send_cc(91, 0)
        self._send_cc(1, 0)
        return [(note, 0) for note, _ in self.active_drones]
