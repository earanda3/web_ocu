"""
Mode Dinamo - Genera un drone ambient modular amb múltiples harmònics
"""
import time
import math
import random
from modes.base_mode import BaseMode

class ModeDinamo(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Dinamo"
        self.notes_playing = set()
        self.harmonics = [
            {'note': 0, 'vel': 0, 'phase': 0.0, 'freq_mult': 1.0},
            {'note': 0, 'vel': 0, 'phase': 0.0, 'freq_mult': 2.0},
            {'note': 0, 'vel': 0, 'phase': 0.0, 'freq_mult': 3.0},
        ]
        self.base_note = 48  # C3
        self.last_update = time.monotonic()
        
    def setup(self):
        self.initialized = True
        self.last_update = time.monotonic()
        self.notes_playing = set()
        # Inicialitzar harmònics
        self._update_harmonics(self.base_note)
        
    def _update_harmonics(self, base_note):
        """Actualitza les notes dels harmònics basant-se en la nota base"""
        for i, h in enumerate(self.harmonics):
            # Calcula la nota de l'harmònic (afegint intervals justos per a millor harmonia)
            # Utilitzem logaritme natural i canvi de base per compatibilitat amb MicroPython
            note_offset = int(12 * (math.log(h['freq_mult']) / math.log(2)))
            h['note'] = base_note + note_offset
            h['vel'] = int(80 / (i + 1))  # Els harmònics superiors sonen més suaus
            h['phase'] = random.random()  # Fase aleatòria per a un so més orgànic
    
    def update(self, pot_values, button_states):
        current_time = time.monotonic()
        dt = current_time - self.last_update
        self.last_update = current_time
        
        x, y, z = pot_values
        
        # Control de la nota base (X)
        new_base_note = 36 + int((x / 127.0) * 24)  # 24 semitons (2 octaves)
        if new_base_note != self.base_note:
            self.base_note = new_base_note
            self._update_harmonics(self.base_note)
        
        # Control de la intensitat (Y) - afecta el volum dels harmònics
        intensity = y / 127.0
        
        # Control de la modulació (Z) - afecta la velocitat de la modulació
        mod_speed = 0.1 + (z / 127.0) * 2.0  # Velocitat de modulació
        
        # Actualitzar fases i modulació
        for h in self.harmonics:
            # Modulació de volum basada en el temps i la fase
            mod = (math.sin(current_time * mod_speed + h['phase'] * 2 * math.pi) + 1) * 0.5
            vel = int(h['vel'] * intensity * (0.5 + 0.5 * mod))  # Modula entre 50% i 100% de la velocitat
            
            # Si la velocitat és massa baixa, aturem la nota
            if vel < 10:
                if h['note'] in self.notes_playing:
                    self.midi_out.send(self.note_off(h['note'], 0))
                    self.notes_playing.discard(h['note'])
            else:
                # Actualitzar la nota si no està sonant o si la velocitat ha canviat significativament
                if h['note'] not in self.notes_playing or abs(vel - h.get('last_vel', 0)) > 5:
                    if h['note'] in self.notes_playing:
                        self.midi_out.send(self.note_off(h['note'], 0))
                    self.midi_out.send(self.note_on(h['note'], vel))
                    self.notes_playing.add(h['note'])
                    h['last_vel'] = vel
        
        return {
            'base_note': self.base_note,
            'intensity': intensity,
            'mod_speed': mod_speed,
            'active_notes': len(self.notes_playing)
        }
    
    def cleanup(self):
        notes_to_stop = list(self.notes_playing)
        self.notes_playing.clear()
        return [(note, 0) for note in notes_to_stop]
