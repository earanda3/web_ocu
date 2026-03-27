"""
Mode Matemàtic - Genera melodies complexes basades en patrons matemàtics
"""
import time
import math
import random
from modes.base_mode import BaseMode

class ModeMatematicArmonic(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Matemàtic"
        self.iteration = 0
        self.notes_playing = set()
        self.last_note_time = 0
        self.note_duration = 0.3
        self.current_scale = []
        self.current_pattern = []
        self.pattern_position = 0
        self.sequence_length = 8
        
    def generate_scale(self, root_note, scale_type='major'):
        """
        Genera una escala musical a partir d'una nota arrel i un tipus d'escala
        """
        # Intervals per a diferents escales (en semitons respecte a l'arrel)
        scales = {
            'major': [0, 2, 4, 5, 7, 9, 11],
            'minor': [0, 2, 3, 5, 7, 8, 10],
            'dorian': [0, 2, 3, 5, 7, 9, 10],
            'mixolydian': [0, 2, 4, 5, 7, 9, 10],
            'lydian': [0, 2, 4, 6, 7, 9, 11],
            'phrygian': [0, 1, 3, 5, 7, 8, 10],
            'locrian': [0, 1, 3, 5, 6, 8, 10],
            'harmonic_minor': [0, 2, 3, 5, 7, 8, 11],
            'melodic_minor': [0, 2, 3, 5, 7, 9, 11],
            'whole_tone': [0, 2, 4, 6, 8, 10],
            'diminished': [0, 2, 3, 5, 6, 8, 9, 11],
            'pentatonic': [0, 2, 4, 7, 9],
            'blues': [0, 3, 5, 6, 7, 10],
            'chromatic': list(range(12))
        }
        
        # Obtenir els intervals de l'escala seleccionada
        intervals = scales.get(scale_type.lower(), scales['major'])
        
        # Generar l'escala en dues octaves
        scale = []
        for octave in range(2):  # Dues octaves per a més rang
            for interval in intervals:
                note = root_note + (octave * 12) + interval
                if note <= 127:  # Assegurar que estigui en el rang MIDI
                    scale.append(note)
        
        return scale
    
    def generate_pattern(self, scale, complexity, x, y, z):
        """
        Genera un patró melòdic basat en l'escala i la complexitat
        """
        pattern = []
        length = 4 + int(complexity * 4)  # De 4 a 8 notes
        
        # Generar el patró basat en funcions matemàtiques
        for i in range(length):
            # Utilitzar funcions trigonomètriques per a crear patrons interessants
            t = i / max(1, length-1)  # Normalitzar a [0,1]
            
            # Combinar múltiples ones amb diferents freqüències i fases
            wave = (
                0.5 * math.sin(t * 2 * math.pi * 1.0) +  # Onda fonamental
                0.3 * math.sin(t * 2 * math.pi * 2.3 + 1.0) +  # Segon harmònic
                0.2 * math.sin(t * 2 * math.pi * 3.1 + 2.0)    # Tercer harmònic
            )
            
            # Ajustar l'amplitud i el desplaçament basats en els potenciòmetres
            wave = wave * (y / 64.0)  # Amplitud controlada per Y
            wave = wave + (z / 64.0 - 1.0)  # Desplaçament controlat per Z
            
            # Escalar al rang de l'escala
            note_idx = int((wave + 1.0) * 0.5 * (len(scale) - 1))
            note_idx = max(0, min(len(scale)-1, note_idx))  # Assegurar dins dels límits
            
            pattern.append(scale[note_idx])
        
        return pattern
    
    def setup(self):
        self.initialized = True
        self.iteration = 0
        self.notes_playing = set()
        self.last_note_time = 0
        self.current_scale = self.generate_scale(48, 'major')
        self.current_pattern = self.generate_pattern(self.current_scale, 0.5, 64, 64, 64)
        self.pattern_position = 0
        
    def update(self, pot_values, button_states):
        current_time = time.monotonic()
        x, y, z = pot_values
        
        # Actualitzar paràmetres basats en els potenciòmetres
        root_note = 36 + int((x / 127.0) * 36)  # De C2 a C5
        scale_type_idx = int((y / 127.0) * 10) % 5  # 5 tipus d'escala principals
        scale_types = ['major', 'minor', 'dorian', 'mixolydian', 'pentatonic']
        scale_type = scale_types[scale_type_idx]
        
        # Generar nova escala si ha canviat el tipus o l'arrel
        if (not hasattr(self, 'current_scale_type') or 
            self.current_scale_type != scale_type or 
            self.current_root_note != root_note):
            self.current_scale = self.generate_scale(root_note, scale_type)
            self.current_scale_type = scale_type
            self.current_root_note = root_note
        
        # Actualitzar complexitat basada en el potenciòmetre Z
        complexity = z / 127.0
        
        # Generar nou patró si la complexitat ha canviat significativament
        if (not hasattr(self, 'current_complexity') or 
            abs(self.current_complexity - complexity) > 0.1):
            self.current_pattern = self.generate_pattern(
                self.current_scale, complexity, x, y, z)
            self.current_complexity = complexity
            self.pattern_position = 0
        
        # Reproduir la següent nota del patró
        if current_time - self.last_note_time > self.note_duration:
            # Aturar notes anteriors
            for note in self.notes_playing:
                self.midi_out.send(self.note_off(note, 0))
            self.notes_playing.clear()
            
            # Reproduir la següent nota del patró
            if self.current_pattern:
                note = self.current_pattern[self.pattern_position]
                velocity = 80 + int(40 * (z / 127.0))  # Velocitat basada en Z
                
                self.midi_out.send(self.note_on(note, velocity))
                self.notes_playing.add(note)
                
                # Avançar a la següent posició del patró
                self.pattern_position = (self.pattern_position + 1) % len(self.current_pattern)
                self.last_note_time = current_time
        
        # Actualitzar iteració per a canvis progressius
        self.iteration += 1
        
        return {
            'root_note': root_note,
            'scale_type': scale_type,
            'complexity': complexity,
            'pattern_position': self.pattern_position,
            'pattern_length': len(self.current_pattern) if self.current_pattern else 0,
            'current_note': self.current_pattern[self.pattern_position-1] if self.current_pattern else None
        }
    
    def cleanup(self):
        # Aturar totes les notes en sortir del mode
        notes_to_stop = list(self.notes_playing)
        self.notes_playing.clear()
        return [(note, 0) for note in notes_to_stop]
