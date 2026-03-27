"""
Mode ToDrone - Drone constant amb control de brillantor, gate i octava
Inspirat en mode PedalJazz però simplificat per només drone
Funcions potenciòmetres basades en mode teclat
"""
import time
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

class ModeToDrone(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "ToDrone"
        self.last_update = time.monotonic()
        self.active_drone_notes = []
        
        # Tonalitat (índex al cercle de quintes)
        self.key_circle = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
        self.key_offsets = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
        self.key_index = 0  # C per defecte
        
        # Doble click per canviar tonalitat (detectat en RELEASE, no en press)
        self.last_button_release_time = [0] * 16
        self.last_button_state = [False] * 16
        self.double_click_threshold = 0.4
        
        # Octava (variable per potenciòmetre Z)
        self.base_octave = 3  # Octava base per al drone
        
        # Paràmetres controlables per potenciòmetres
        self.velocity = 80  # Brillantor/intensitat (0-127) - Pot Y
        
        # Gate: efecte temporal amb CC11 (Expression) - Pot X
        self.gate_enabled = False
        self.gate_period = 0.2  # període total del cicle (segons)
        self.gate_min_expr = 0  # valor mínim d'expressió (0-127)
        self.gate_duty = 0.5  # duty cycle (proporció en high)
        self.gate_last_toggle = 0
        self.gate_high = True  # estat actual: high (127) o low (min_expr)
        
        # Tracking de CC MIDI
        self.cc_values = {
            11: 127,  # Expression (màxim per defecte)
            1: 0      # Modulació (CC1)
        }
        
    def setup(self):
        self.initialized = True
        self.last_update = time.monotonic()
        # Resetar temps de doble click per evitar que el click d'activació compti
        self.last_button_release_time = [0] * 16
        self.last_button_state = [False] * 16
        self._start_drone()
        
    def _start_drone(self):
        """Inicia el drone constant"""
        self._stop_drone()
        
        key_offset = self.key_offsets[self.key_index]
        base_note = self.base_octave * 12 + key_offset
        
        # Drone amb tònica + quinta (sostre harmònic simple i constant)
        # Notes: tònica (I), quinta (V)
        drone_intervals = [0, 7]  # Quinta perfecta
        
        self.active_drone_notes = []
        for interval in drone_intervals:
            note = max(24, min(96, base_note + interval))
            self.active_drone_notes.append(note)
            self.midi_out.send(self.note_on(note, self.velocity))
        
        print(f"🎵 ToDrone: {self.key_circle[self.key_index]} (oct {self.base_octave})")
    
    def _stop_drone(self):
        """Para el drone actual"""
        for note in self.active_drone_notes:
            self.midi_out.send(self.note_off(note, 0))
        self.active_drone_notes = []
    
    def update(self, pot_values, button_states):
        current_time = time.monotonic()
        dt = current_time - self.last_update
        self.last_update = current_time
        x, y, z = pot_values
        
        # POT X: Gate (efecte temporal amb CC11 Expression)
        if x < 10:
            # Pot a 0: gate OFF
            if self.gate_enabled:
                self.gate_enabled = False
                # Restaurar expressió a màxim quan es desactiva
                self._send_cc(11, 127)
        else:
            # Pot > 0: gate actiu
            self.gate_enabled = True
            # Velocitat: 0.5s (lent) a 0.05s (ràpid)
            self.gate_period = 0.5 - (x / 127.0) * 0.45
            # Profunditat fixa: silenci total en fase baixa
            self.gate_min_expr = 0
            # Duty cycle fix: 50% high, 50% low
            self.gate_duty = 0.5
        
        # POT Y: Modulació (CC1) - igual que al mode teclat
        self._send_cc(1, y)
        
        # POT Z: Octava (rang greu a agut)
        # Mapejar potenciòmetre a rang d'octaves: 2-6
        new_octave = 2 + int((z / 127.0) * 4.99)  # 2, 3, 4, 5, 6
        if new_octave != self.base_octave:
            self.base_octave = new_octave
            # CRÍTIC: Reiniciar drone només quan canvia octava
            # Això és acceptable perquè és un canvi intencionat gros
            self._start_drone()
        
        # Processar Gate: modulació temporal de CC11 (Expression)
        if self.gate_enabled:
            time_since_toggle = current_time - self.gate_last_toggle
            if self.gate_high:
                # Fase alta: esperar gate_period * gate_duty
                if time_since_toggle >= self.gate_period * self.gate_duty:
                    # Canviar a fase baixa
                    self.gate_high = False
                    self.gate_last_toggle = current_time
                    self._send_cc(11, self.gate_min_expr)
            else:
                # Fase baixa: esperar gate_period * (1 - gate_duty)
                if time_since_toggle >= self.gate_period * (1 - self.gate_duty):
                    # Canviar a fase alta
                    self.gate_high = True
                    self.gate_last_toggle = current_time
                    self._send_cc(11, 127)
        
        # Doble click en qualsevol botó: canviar tonalitat cromàtica
        # Detectat en RELEASE per evitar canvis accidentals en activar el mode
        for btn_idx in range(min(len(button_states), 16)):
            current_state = bool(button_states[btn_idx])
            prev_state = self.last_button_state[btn_idx]
            
            # Detectar flanc de baixada (release)
            if prev_state and not current_state:
                time_since_last_release = current_time - self.last_button_release_time[btn_idx]
                if 0.05 < time_since_last_release < self.double_click_threshold:
                    # Doble click detectat (dos releases ràpids)
                    self.last_button_release_time[btn_idx] = 0
                    self.key_index = (self.key_index + 1) % 12
                    self._start_drone()
                else:
                    # Primer release
                    self.last_button_release_time[btn_idx] = current_time
            
            self.last_button_state[btn_idx] = current_state
        
        # Retornar info per visualització
        return {
            'key': self.key_circle[self.key_index],
            'octave': self.base_octave,
            'velocity': self.velocity,
            'gate': 'ON' if self.gate_enabled else 'OFF'
        }
    
    def _send_cc(self, cc_num, value):
        """Envia un CC MIDI a tots els canals"""
        self.cc_values[cc_num] = value
        try:
            for ch in range(16):
                self.midi_out.send(ControlChange(cc_num, value, channel=ch))
        except Exception:
            pass
    
    def cleanup(self):
        """Aturar drone quan es canvia de mode o es prem stop"""
        self._stop_drone()
        # Desactivar CC al sortir
        self._send_cc(11, 127)  # Expression al màxim
        self._send_cc(74, 64)   # Brightness neutral
        return [(note, 0) for note in self.active_drone_notes]
