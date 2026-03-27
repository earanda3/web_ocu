"""
Mode Acords Aleatoris - Genera progressions d'acords aleatòries.
"""
import time
import random
from adafruit_midi.note_off import NoteOff
from adafruit_midi.note_on import NoteOn
from adafruit_midi.control_change import ControlChange

class ModeAcordsAleatoris:
    """Mode que genera acords aleatoris amb diferents progressions."""
    
    # Definim els tipus d'acords
    CHORDS = {
        'major': [0, 4, 7],
        'minor': [0, 3, 7],
        '7th': [0, 4, 7, 10],
        'm7': [0, 3, 7, 10],
        'maj7': [0, 4, 7, 11],
        'sus2': [0, 2, 7],
        'sus4': [0, 5, 7],
        'dim': [0, 3, 6]
    }
    
    # Notes de l'escala (Do Major per defecte)
    SCALE = [0, 2, 4, 5, 7, 9, 11]  # C, D, E, F, G, A, B
    
    def __init__(self, midi_out, config=None):
        """Inicialitza el mode d'acords aleatoris."""
        self.midi_out = midi_out
        self.config = config or {}
        self.initialized = False
        self.iteration = 0
        self.active_notes = []
        self.current_chord = []
        self.next_chord_time = 0
        self.chord_duration = 2.0
        self.current_chord_type = 'major'
        self.chord_types = list(self.CHORDS.keys())
        
    def _get_random_chord(self, base_note=None):
        """Retorna un acord aleatori."""
        if base_note is None:
            # Utilitzem random.randint en lloc de random.choice per compatibilitat
            base_note = 48 + self.SCALE[random.randint(0, len(self.SCALE)-1)]  # Do3 a Si3
            
        # Utilitzem random.randint en lloc de random.choice per compatibilitat
        chord_type = self.chord_types[random.randint(0, len(self.chord_types)-1)]
        chord_intervals = self.CHORDS[chord_type]
        
        # Afegir octava superior per fer l'acord més ric
        chord_notes = chord_intervals + [i+12 for i in chord_intervals]
        
        # Triar entre 3 i 5 notes de l'acord
        num_notes = random.randint(3, 5)
        # En lloc de random.sample, que pot no estar disponible, barregem i agafem els primers n
        shuffled_notes = list(chord_notes)
        for i in range(len(shuffled_notes) - 1, 0, -1):
            j = random.randint(0, i)
            shuffled_notes[i], shuffled_notes[j] = shuffled_notes[j], shuffled_notes[i]
        selected_notes = shuffled_notes[:min(num_notes, len(shuffled_notes))]
        
        return [base_note + note for note in selected_notes]
    
    def _play_chord(self, notes, velocity=80, channel=0):
        """Reprodueix un acord de notes."""
        for note in notes:
            self.midi_out.send(self.note_on(note, velocity, channel))
            
        # Guardar les notes actives per poder-les aturar després
        current_time = time.monotonic()
        self.active_notes.extend([
            {'note': note, 'end_time': current_time + self.chord_duration, 'channel': channel}
            for note in notes
        ])
    
    def setup(self):
        """Inicialitza el mode."""
        self.initialized = True
        self.iteration = 0
        self.midi_out.send(self.control_change(91, 64))  # Reverb
        self.next_chord_time = time.monotonic()
    
    def cleanup(self):
        """Netega el mode."""
        for note_info in self.active_notes:
            self.midi_out.send(self.note_off(
                note_info['note'], 
                0,
                note_info['channel']
            ))
        self.active_notes = []
        return []
    
    def update(self, pot_values, button_states):
        """Actualitza l'estat del mode."""
        current_time = time.monotonic()
        x, y, z = pot_values
        
        # Control de tipus d'acord amb el potenciòmetre X
        chord_type_idx = int((x / 127.0) * (len(self.chord_types) - 1))
        self.current_chord_type = self.chord_types[chord_type_idx]
        
        # Control de velocitat amb el potenciòmetre Y (0.5s a 4s)
        min_duration = 0.5
        max_duration = 4.0
        self.chord_duration = min_duration + (y / 127.0) * (max_duration - min_duration)
        
        # Control de reverberació amb el potenciòmetre Z
        reverb = int(30 + (z / 127.0) * 90)
        self.midi_out.send(self.control_change(91, reverb))
        
        # Reproduir nou acord si ha passat el temps
        if current_time >= self.next_chord_time:
            # Aturar notes actuals
            for note_info in self.active_notes:
                self.midi_out.send(self.note_off(
                    note_info['note'],
                    0,
                    note_info['channel']
                ))
            self.active_notes = []
            
            # Generar i reproduir nou acord
            self.current_chord = self._get_random_chord()
            self._play_chord(self.current_chord, velocity=80, channel=0)
            self.next_chord_time = current_time + self.chord_duration
        
        # Aturar notes que hagin acabat
        notes_to_remove = []
        for i, note_info in enumerate(self.active_notes):
            if current_time >= note_info['end_time']:
                self.midi_out.send(self.note_off(
                    note_info['note'], 
                    0,
                    note_info['channel']
                ))
                notes_to_remove.append(i)
        
        for i in sorted(notes_to_remove, reverse=True):
            if i < len(self.active_notes):
                self.active_notes.pop(i)
        
        return {
            'mode': 'Acords',
            'tipus': self.current_chord_type,
            'temps': f"{self.chord_duration:.1f}s"
        }
    
    def note_on(self, note, velocity=127, channel=0):
        """Retorna un missatge de nota ON."""
        return NoteOn(
            min(max(0, note), 127), 
            min(max(0, velocity), 127), 
            channel=min(max(0, channel), 15)
        )
    
    def note_off(self, note, velocity=0, channel=0):
        """Retorna un missatge de nota OFF."""
        return NoteOff(
            min(max(0, note), 127), 
            min(max(0, velocity), 127), 
            channel=min(max(0, channel), 15)
        )
    
    def control_change(self, control, value, channel=0):
        """Retorna un missatge de control canvi."""
        return ControlChange(
            min(max(0, control), 127),
            min(max(0, value), 127),
            channel=min(max(0, channel), 15)
        )
    
    def get_mode_info(self):
        """Retorna informació sobre el mode."""
        return {
            'name': 'Acords Aleatoris',
            'description': 'Genera progressions d\'acords aleatòries.',
            'version': '1.0',
            'controls': {
                'X': 'Tipus d\'acord',
                'Y': 'Velocitat',
                'Z': 'Reverb'
            }
        }
