"""
Mode Jazz - Genera progressions d'acords de jazz basades en els valors dels potenciòmetres
"""
import random
from modes.base_mode import BaseMode

class ModeJazzChords(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Jazz"
        self.current_chord = []
        self.last_chord_time = 0
        self.chord_duration = 1.0  # segons
        
    def jazz_chord_progression(self, x, y, z, octave):
        """
        Genera una progressió d'acords de jazz basada en els valors dels potenciòmetres
        
        Paràmetres:
        - x: Controla la complexitat de l'acord (0-127)
        - y: Controla el tipus de progressió (0-127)
        - z: Controla la variació harmònica (0-127)
        - octave: Octava base
        
        Retorna:
        - Llista de notes que formen l'acord
        """
        # Escales de jazz comunes
        scales = {
            'major': [0, 2, 4, 5, 7, 9, 11],
            'dorian': [0, 2, 3, 5, 7, 9, 10],
            'mixolydian': [0, 2, 4, 5, 7, 9, 10],
            'minor': [0, 2, 3, 5, 7, 8, 10],
            'diminished': [0, 2, 3, 5, 6, 8, 9, 11],
            'whole_tone': [0, 2, 4, 6, 8, 10],
            'chromatic': list(range(12))
        }
        
        # Progressions d'acords de jazz comuns
        progressions = [
            # II-V-I en major
            [
                [0, 4, 7, 11],    # Maj7
                [2, 5, 9, 0],     # m7
                [7, 11, 14, 17]   # 7
            ],
            # II-V-I en menor
            [
                [0, 3, 7, 10],    # m7
                [5, 8, 11, 14],   # m7b5
                [7, 10, 14, 17]   # 7alt
            ],
            # Blues
            [
                [0, 4, 7, 10],    # 7
                [5, 8, 10, 13],   # 7
                [7, 10, 14, 17]   # 7
            ],
            # Coltrane changes
            [
                [0, 4, 7, 11],    # Maj7
                [6, 10, 13, 17],  # 7
                [2, 6, 9, 13],    # 7
                [8, 12, 15, 19]   # 7
            ]
        ]
        
        # Seleccionar escala basada en el potenciòmetre Y
        scale_idx = int((y / 127.0) * (len(scales) - 1))
        scale_name = list(scales.keys())[scale_idx]
        scale = scales[scale_name]
        
        # Seleccionar progressió basada en el potenciòmetre X
        prog_idx = int((x / 127.0) * (len(progressions) - 1))
        progression = progressions[prog_idx]
        
        # Seleccionar acord dins de la progressió basat en el potenciòmetre Z
        chord_idx = int((z / 127.0) * (len(progression) - 1))
        chord_intervals = progression[chord_idx]
        
        # Aplicar variacions a l'acord basades en els potenciòmetres
        chord = []
        for interval in chord_intervals:
            # Afegir variació basada en el potenciòmetre Z
            variation = int((z / 127.0) * 3) - 1  # -1, 0, o 1
            note = (octave * 12) + scale[interval % len(scale)] + (variation * 12)
            
            # Assegurar-se que la nota estigui en el rang MIDI (0-127)
            note = max(0, min(127, note))
            chord.append(note)
        
        return chord
    
    def setup(self):
        self.initialized = True
        self.current_chord = []
        self.last_chord_time = 0
        
    def update(self, pot_values, button_states):
        import time
        
        current_time = time.monotonic()
        x, y, z = pot_values
        
        # Actualitzar acord cada cert temps o quan canviïn els potenciòmetres significativament
        if (current_time - self.last_chord_time > self.chord_duration or 
            not hasattr(self, 'last_pot_values') or 
            any(abs(a-b) > 5 for a, b in zip([x,y,z], self.last_pot_values))):
            
            # Aturar notes actuals
            for note in self.current_chord:
                self.midi_out.send(self.note_off(note, 0))
            
            # Generar nou acord
            octave = 4  # Octava base
            self.current_chord = self.jazz_chord_progression(x, y, z, octave)
            
            # Reproduir nou acord
            for note in self.current_chord:
                velocity = 100  # Velocitat fixa, es pot fer variable
                self.midi_out.send(self.note_on(note, velocity))
            
            self.last_chord_time = current_time
            self.last_pot_values = (x, y, z)
        
        return {
            'chord': self.current_chord,
            'x': x,
            'y': y,
            'z': z
        }
    
    def cleanup(self):
        # Aturar totes les notes en sortir del mode
        notes_to_stop = list(self.current_chord)
        self.current_chord = []
        return [(note, 0) for note in notes_to_stop]
