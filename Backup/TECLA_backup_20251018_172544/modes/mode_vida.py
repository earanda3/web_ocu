"""
Mode Vida - Acords suaus i melosos que es desenvolupen orgànicament
"""
import time
import random
from modes.base_mode import BaseMode

class ModeVida(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Vida"
        self.chords = []
        self.current_chord = []
        self.last_chord_change = 0
        self.chord_duration = 8.0  # segons
        self.last_note_time = 0
        self.note_interval = 0.5  # segons entre notes
        self.arp_direction = 1  # 1 per amunt, -1 per avall
        self.arp_position = 0
        self.velocity = 70
        
        # Definir progressions d'acords harmoniosos
        self.chord_progressions = [
            # Progressió I-V-vi-IV (C-G-Am-F)
            [
                [48, 52, 55],  # Do major
                [47, 50, 55],  # Sol major 2a inversió
                [45, 48, 52],  # La menor
                [45, 53, 57]   # Fa major 2a inversió
            ],
            # Progressió vi-IV-I-V (Am-F-C-G)
            [
                [45, 48, 52],  # La menor
                [45, 53, 57],  # Fa major 2a inversió
                [48, 52, 55],  # Do major
                [47, 50, 55]   # Sol major 2a inversió
            ],
            # Progressió I-vi-ii-V (C-Am-Dm-G)
            [
                [48, 52, 55],  # Do major
                [45, 48, 52],  # La menor
                [50, 53, 57],  # Re menor
                [47, 50, 55]   # Sol major 2a inversió
            ]
        ]
        
    def setup(self):
        self.initialized = True
        self.last_chord_change = time.monotonic()
        self.last_note_time = 0
        self.arp_position = 0
        self.current_chord = []
        self._select_new_chord_progression()
        
    def _select_new_chord_progression(self):
        """Selecciona una nova progressió d'acords aleatòria"""
        progression = random.choice(self.chord_progressions)
        self.chords = [chord[:] for chord in progression]  # Fer còpia
        self.chord_index = 0
        self.current_chord = self.chords[0]
        
    def _next_chord(self):
        """Passa al següent acord de la progressió"""
        self.chord_index = (self.chord_index + 1) % len(self.chords)
        
        # De tant en tant, canviar de progressió
        if self.chord_index == 0 and random.random() < 0.3:
            self._select_new_chord_progression()
        else:
            self.current_chord = self.chords[self.chord_index]
            
        # Canviar ocasionalment la direcció de l'arpegi
        if random.random() < 0.3:
            self.arp_direction *= -1
            
    def _play_note(self, note, velocity):
        """Reprodueix una nota amb un to suau"""
        # Afegir una mica d'aleatorietat a la velocitat per un so més orgànic
        vel = max(40, min(100, velocity + random.randint(-10, 10)))
        self.midi_out.send(self.note_on(note, vel))
        
    def update(self, pot_values, button_states):
        current_time = time.monotonic()
        x, y, z = pot_values
        
        # Actualitzar paràmetres basats en els potenciòmetres
        self.chord_duration = 4.0 + (x / 127.0) * 12.0  # 4-16 segons
        self.note_interval = 0.2 + (y / 127.0) * 0.8  # 0.2-1.0 segons
        self.velocity = 60 + int((z / 127.0) * 40)  # 60-100 de velocitat
        
        # Canviar d'acord si ha passat el temps
        if current_time - self.last_chord_change > self.chord_duration:
            self.last_chord_change = current_time
            self._next_chord()
            
        # Tocar notes de l'arpegi
        if current_time - self.last_note_time > self.note_interval and self.current_chord:
            self.last_note_time = current_time
            
            # Aturar nota anterior si n'hi ha
            if hasattr(self, 'last_note'):
                self.midi_out.send(self.note_off(self.last_note, 0))
            
            # Seleccionar la següent nota de l'acord
            note = self.current_chord[self.arp_position]
            self._play_note(note, self.velocity)
            self.last_note = note
            
            # Actualitzar posició de l'arpegi
            self.arp_position += self.arp_direction
            if self.arp_position >= len(self.current_chord) or self.arp_position < 0:
                self.arp_position = len(self.current_chord) - 1 if self.arp_direction < 0 else 0
                # Canviar ocasionalment la direcció en arribar al final
                if random.random() < 0.3:
                    self.arp_direction *= -1
        
        return {
            'mode': 'Vida',
            'acord': f"{self._chord_name(self.current_chord)}",
            'tempo': f"{60.0/self.note_interval:.1f} BPM",
            'intensitat': f"{int((self.velocity-60)/40*100)}%"
        }
    
    def _chord_name(self, notes):
        """Retorna el nom de l'acord actual (simplificat)"""
        if not notes:
            return "-"
        note_names = ['Do', 'Do#', 'Re', 'Re#', 'Mi', 'Fa', 
                     'Fa#', 'Sol', 'Sol#', 'La', 'Sib', 'Si']
        root = note_names[notes[0] % 12]
        
        # Detecció molt simple del tipus d'acord
        intervals = sorted([n - notes[0] for n in notes])
        if intervals == [0, 4, 7]:
            return f"{root} Maj"
        elif intervals == [0, 3, 7]:
            return f"{root} m"
        return f"{root} acord"
    
    def cleanup(self):
        # Aturar totes les notes
        if hasattr(self, 'last_note'):
            self.midi_out.send(self.note_off(self.last_note, 0))
        return []
