"""
Mode Jazz - Per a músics de jazz que volen improvisar
Doble click per canviar tonalitat
Pots: Octava, Progressió, Swing
"""
import random
import time
from modes.base_mode import BaseMode

class ModeJazzChords(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Jazz"
        self.current_chord = []
        self.last_chord_time = 0
        self.chord_duration = 2.0  # segons
        self.key = 0  # Tonalitat (0-11, C a B)
        self.octave = 4  # Octava base
        self.progression_type = 0  # 0 = single chord, 1-4 = progressions
        self.swing_amount = 0.5  # 0-1, quantitat de swing
        
        # Detecció de doble click
        self.last_button_press = {}
        self.double_click_threshold = 0.3  # segons
        
        # Progressions de jazz disponibles
        self.progressions = [
            # 0: Un sol acord (per defecte)
            [[0, 4, 7, 11]],  # Maj7
            
            # 1: II-V-I major
            [
                [2, 5, 9, 12],    # Dm7
                [7, 11, 14, 17],  # G7
                [0, 4, 7, 11],    # CMaj7
            ],
            
            # 2: II-V-I menor
            [
                [2, 5, 8, 12],    # Dm7b5
                [7, 10, 14, 17],  # G7alt
                [0, 3, 7, 10],    # Cm7
            ],
            
            # 3: Blues (I-IV-V)
            [
                [0, 4, 7, 10],    # C7
                [5, 9, 12, 15],   # F7
                [7, 11, 14, 17],  # G7
            ],
            
            # 4: Coltrane changes
            [
                [0, 4, 7, 11],    # CMaj7
                [8, 12, 15, 19],  # AbMaj7
                [4, 8, 11, 15],   # EMaj7
            ],
        ]
        
        self.chord_index = 0
        self.last_prog_type = 0
        
    def setup(self):
        self.initialized = True
        self.current_chord = []
        self.last_chord_time = 0
        self.chord_index = 0
        
    def _detect_double_click(self, button_index):
        """Detecta doble click en un botó"""
        current_time = time.monotonic()
        
        if button_index in self.last_button_press:
            time_diff = current_time - self.last_button_press[button_index]
            if time_diff < self.double_click_threshold:
                # Doble click detectat!
                self.last_button_press[button_index] = 0  # Reset
                return True
        
        self.last_button_press[button_index] = current_time
        return False
        
    def update(self, pot_values, button_states):
        current_time = time.monotonic()
        x, y, z = pot_values
        
        # Detectar doble click per canviar tonalitat
        for i, pressed in enumerate(button_states):
            if pressed and self._detect_double_click(i):
                # Canviar tonalitat (C, C#, D, D#, etc.)
                self.key = (self.key + 1) % 12
                print(f"Nova tonalitat: {['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'][self.key]}")
        
        # POT X: Octava (3-6)
        new_octave = 3 + int((x / 127.0) * 3)  # 3, 4, 5 o 6
        if new_octave != self.octave:
            self.octave = new_octave
            # Forçar actualització d'acord
            self.last_chord_time = 0
        
        # POT Y: Tipus de progressió (0-4)
        self.progression_type = int((y / 127.0) * (len(self.progressions) - 0.01))
        
        # Si canvia tipus de progressió, reiniciar
        if self.progression_type != self.last_prog_type:
            self.chord_index = 0
            self.last_chord_time = 0
            self.last_prog_type = self.progression_type
        
        # POT Z: Swing (0.0 = straight, 1.0 = molt swing)
        self.swing_amount = z / 127.0
        
        # Ajustar duració segons swing
        base_duration = 2.0
        if self.progression_type == 0:
            # Single chord: duració més llarga
            self.chord_duration = base_duration * 2
        else:
            # Progressió: variar amb swing
            self.chord_duration = base_duration * (0.5 + self.swing_amount)
        
        # Actualitzar acord
        if current_time - self.last_chord_time > self.chord_duration:
            # Aturar notes actuals
            for note in self.current_chord:
                self.midi_out.send(self.note_off(note, 0))
            
            # Generar nou acord
            progression = self.progressions[self.progression_type]
            chord_intervals = progression[self.chord_index]
            
            # Aplicar tonalitat i octava
            self.current_chord = []
            for interval in chord_intervals:
                note = (self.octave * 12) + self.key + interval
                note = max(0, min(127, note))
                self.current_chord.append(note)
            
            # Reproduir acord amb variació de velocitat per swing
            for i, note in enumerate(self.current_chord):
                # Notes amb swing tenen velocitats variades
                vel_variation = int(self.swing_amount * 20 * (1 if i % 2 == 0 else -1))
                velocity = max(60, min(110, 90 + vel_variation))
                self.midi_out.send(self.note_on(note, velocity))
            
            # Avançar a següent acord de la progressió
            self.chord_index = (self.chord_index + 1) % len(progression)
            self.last_chord_time = current_time
        
        key_names = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
        prog_names = ['Acord', 'II-V-I Maj', 'II-V-I m', 'Blues', 'Coltrane']
        
        return {
            'mode': 'Jazz',
            'key': key_names[self.key],
            'oct': f'Oct{self.octave}',
            'prog': prog_names[self.progression_type],
            'swing': f'{int(self.swing_amount*100)}%'
        }
    
    def cleanup(self):
        # Aturar totes les notes
        notes_to_stop = list(self.current_chord)
        self.current_chord = []
        return [(note, 0) for note in notes_to_stop]
