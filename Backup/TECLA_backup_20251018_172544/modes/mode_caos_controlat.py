"""
Mode Caos - Genera patrons melòdics caòtics però musicals
"""
import time
import random
import math
from modes.base_mode import BaseMode

class ModeCaosControlat(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Caos"
        self.notes_playing = set()
        self.last_note_time = 0
        self.notes_history = []
        self.scale = [0, 2, 4, 5, 7, 9, 11]  # Escala major
        self.base_octave = 4
        self.chaos = 0.5
        self.range_notes = 24
        self.tempo = 120
        
    def setup(self):
        self.initialized = True
        self.notes_playing.clear()
        self.notes_history = []
        self.last_note_time = time.monotonic()
        
    def _get_next_note(self, chaos):
        """Genera la següent nota basada en el nivell de caos"""
        if not self.notes_history or random.random() < chaos * 0.5:
            # Nota completament nova
            note = random.choice(self.scale) + (self.base_octave + random.randint(0, 2)) * 12
        else:
            # Basada en l'historial amb variacions
            last_note = self.notes_history[-1]
            step = random.choice([-2, -1, 1, 2])
            note = last_note + step * (1 + int(random.random() * chaos * 3))
        
        # Mantenir la nota dins del rang
        min_note = self.base_octave * 12
        max_note = min_note + self.range_notes
        return max(min_note, min(max_note, note))
    
    def update(self, pot_values, button_states):
        current_time = time.monotonic()
        x, y, z = pot_values
        
        # Actualitzar paràmetres
        self.chaos = x / 127.0
        self.range_notes = 12 + int((y / 127.0) * 36)  # 1 a 4 octaves
        self.tempo = 30 + int((z / 127.0) * 210)  # 30 a 240 BPM
        
        # Calcular quan toca la següent nota
        note_interval = 60.0 / (self.tempo / 4.0)  # 1/4 de nota
        
        if current_time - self.last_note_time >= note_interval:
            self.last_note_time = current_time
            
            # Aturar notes anteriors
            for note in list(self.notes_playing):
                self.midi_out.send(self.note_off(note, 0))
                self.notes_playing.remove(note)
            
            # Generar nova nota
            note = self._get_next_note(self.chaos)
            velocity = 40 + int(random.random() * 60)  # Velocitat aleatòria
            
            # Afegir a l'historial (màxim 10 notes)
            self.notes_history.append(note)
            if len(self.notes_history) > 10:
                self.notes_history.pop(0)
            
            # Reproduir la nota
            self.midi_out.send(self.note_on(note, velocity))
            self.notes_playing.add(note)
        
        return {
            'mode': 'Caos',
            'chaos': f"{int(self.chaos*100)}%",
            'range': f"{self.range_notes//12} octaves",
            'tempo': f"{self.tempo} BPM",
            'note': self.notes_history[-1] if self.notes_history else '--'
        }
    
    def cleanup(self):
        notes_to_stop = list(self.notes_playing)
        self.notes_playing.clear()
        
        # Aturar totes les notes
        for note in notes_to_stop:
            self.midi_out.send(self.note_off(note, 0))
            
        return [(note, 0) for note in notes_to_stop]
