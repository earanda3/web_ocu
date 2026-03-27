"""
Mode Sinusoidal - Genera ones sinusoidals modulables amb efectes de rizado
"""
import time
import math
import random
from modes.base_mode import BaseMode

class ModeOnaSinusoidal(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Sinusoidal"
        self.phase = 0.0
        self.last_update = time.monotonic()
        self.notes_playing = set()
        self.base_frequency = 220.0  # Hz (A3)
        self.current_note = None
        
    def setup(self):
        self.initialized = True
        self.phase = 0.0
        self.last_update = time.monotonic()
        self.notes_playing = set()
        self.current_note = None
        
    def update(self, pot_values, button_states):
        current_time = time.monotonic()
        dt = current_time - self.last_update
        self.last_update = current_time
        
        x, y, z = pot_values
        
        # Control de freqüència bàsica (X)
        self.base_frequency = 55.0 + (x / 127.0) * 880.0  # Aprox. A1 a A6
        
        # Control d'amplitud de modulació (Y)
        mod_amount = y / 127.0
        
        # Control de freqüència de modulació (Z)
        mod_freq = 0.5 + (z / 127.0) * 10.0  # De 0.5Hz a 10.5Hz
        
        # Calcular la fase actual amb modulació
        mod = math.sin(self.phase * mod_freq * 2 * math.pi) * mod_amount
        current_freq = self.base_frequency * (1.0 + mod)
        
        # Actualitzar fase
        self.phase += dt
        if self.phase >= 1.0:
            self.phase -= 1.0
        
        # Convertir freqüència a nota MIDI (12 semitons per octava, 69 = A4 = 440Hz)
        # Utilitzem logaritme natural i canvi de base per compatibilitat amb MicroPython
        note_num = 12 * (math.log(current_freq / 440.0) / math.log(2)) + 69
        note_num = max(0, min(127, int(round(note_num))))
        
        # Si la nota ha canviat, actualitzar
        if self.current_note != note_num:
            # Aturar nota anterior
            if self.current_note is not None:
                self.midi_out.send(self.note_off(self.current_note, 0))
                self.notes_playing.discard(self.current_note)
            
            # Reproduir nova nota
            velocity = 80  # Velocitat fixa, podria ser controlada per un altre potenciòmetre
            self.midi_out.send(self.note_on(note_num, velocity))
            self.notes_playing.add(note_num)
            self.current_note = note_num
        
        return {
            'freq': current_freq,
            'note': note_num,
            'mod_amount': mod_amount,
            'mod_freq': mod_freq
        }
    
    def cleanup(self):
        notes_to_stop = list(self.notes_playing)
        self.notes_playing.clear()
        if self.current_note is not None:
            self.midi_out.send(self.note_off(self.current_note, 0))
            self.current_note = None
        return [(note, 0) for note in notes_to_stop]
