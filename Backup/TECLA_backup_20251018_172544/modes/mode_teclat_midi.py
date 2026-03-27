"""
Mode Teclat MIDI - Converteix els 16 botons en un teclat MIDI amb diverses escales musicals
"""
import time
import random
from modes.base_mode import BaseMode

class ModeTeclatMIDI(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Teclat MIDI"
        self.active_notes = {}  # Diccionari per guardar notes actives
        self.last_update = time.monotonic()
        
        # Definir les escales musicals disponibles
        self.scales = {
            "major": [0, 2, 4, 5, 7, 9, 11],  # Escala major (Do, Re, Mi, Fa, Sol, La, Si)
            "minor": [0, 2, 3, 5, 7, 8, 10],  # Escala menor natural
            "pentatonic": [0, 2, 4, 7, 9],    # Escala pentatònica major
            "blues": [0, 3, 5, 6, 7, 10],     # Escala de blues
            "chromatic": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],  # Escala cromàtica
            "dorian": [0, 2, 3, 5, 7, 9, 10], # Mode dòric
            "phrygian": [0, 1, 3, 5, 7, 8, 10], # Mode frigi
            "lydian": [0, 2, 4, 6, 7, 9, 11], # Mode lidi
            "mixolydian": [0, 2, 4, 5, 7, 9, 10], # Mode mixolidi
        }
        
        # Disposicions de teclat (per als 16 botons)
        self.keyboard_layouts = {
            "scale_4x4": self._generate_scale_4x4,     # 4 files de 4 notes en escala
            "scale_2x8": self._generate_scale_2x8,     # 2 files de 8 notes
            "chromatic": self._generate_chromatic,     # Notes cromàtiques consecutives
            "chord_pads": self._generate_chord_pads,   # Acords en lloc de notes individuals
            "bass_melody": self._generate_bass_melody  # Baixos i melodia
        }
        
        # Valors per defecte
        self.current_scale = "major"
        self.current_layout = "scale_4x4"
        self.root_note = 60  # Do central (C4)
        self.velocity = 80
        self.octave_offset = 0
        self.key_notes = {}  # Mapeig de cada botó a una nota MIDI
    
    def setup(self):
        """Inicialitza l'estat del mode."""
        self.initialized = True
        self.active_notes = {}
        self._update_key_mapping()
        print(f"Mode Teclat MIDI iniciat. Escala: {self.current_scale}, Disposició: {self.current_layout}")
    
    def _get_scale_note(self, scale_name, root, step):
        """Obté una nota de l'escala a partir de la nota base i el pas."""
        if scale_name not in self.scales:
            scale_name = "major"
            
        scale = self.scales[scale_name]
        octave = step // len(scale)
        scale_step = step % len(scale)
        
        return root + scale[scale_step] + (octave * 12)
    
    def _generate_scale_4x4(self):
        """Genera un mapeig de 4x4 amb notes de l'escala seleccionada."""
        mapping = {}
        for i in range(16):
            row = i // 4  # Fila (0-3)
            col = i % 4   # Columna (0-3)
            
            # Calcular el pas dins l'escala (les files superiors tenen notes més altes)
            step = col + (3 - row) * 4  # Files invertides (la més baixa té les notes més altes)
            
            # Obtenir la nota MIDI segons l'escala actual
            mapping[i] = self._get_scale_note(self.current_scale, self.root_note + self.octave_offset * 12, step)
        
        return mapping
    
    def _generate_scale_2x8(self):
        """Genera un mapeig de 2x8 amb notes de l'escala seleccionada."""
        mapping = {}
        for i in range(16):
            row = i // 8  # Fila (0-1)
            col = i % 8   # Columna (0-7)
            
            # Les files de dalt tenen notes més agudes
            step = col + (1 - row) * 8  # La fila 0 (superior) té les notes més altes
            
            # Obtenir la nota MIDI segons l'escala actual
            mapping[i] = self._get_scale_note(self.current_scale, self.root_note + self.octave_offset * 12, step)
        
        return mapping
    
    def _generate_chromatic(self):
        """Genera un mapeig cromàtic (notes consecutives)."""
        mapping = {}
        for i in range(16):
            # Simplement notes consecutives
            mapping[i] = self.root_note + self.octave_offset * 12 + i
        
        return mapping
    
    def _generate_chord_pads(self):
        """Genera un mapeig d'acords en lloc de notes individuals."""
        mapping = {}
        scale = self.scales[self.current_scale]
        root = self.root_note + self.octave_offset * 12
        
        # Definir tipus d'acords (tríades i quatríades)
        chord_types = [
            [0, 2, 4],      # Major (1, 3, 5)
            [0, 2, 4, 6],   # Major 7 (1, 3, 5, 7)
            [0, 2, 4, 7],   # Major 9 (1, 3, 5, 9)
            [0, 3, 7],      # Menor (1, b3, 5)
            [0, 3, 7, 10],  # Menor 7 (1, b3, 5, b7)
            [0, 3, 7, 11],  # Menor major 7 (1, b3, 5, 7)
            [0, 4, 7],      # Suspès 4 (1, 4, 5)
            [0, 2, 7],      # Suspès 2 (1, 2, 5)
            [0, 3, 6],      # Disminuït (1, b3, b5)
            [0, 3, 6, 9],   # Disminuït 7 (1, b3, b5, bb7)
            [0, 4, 8],      # Augmentat (1, 3, #5)
            [0, 4, 8, 10],  # Augmentat 7 (1, 3, #5, b7)
            [0, 2, 6],      # Quarta suspesa (1, 3, #5, b7)
            [0, 5, 7],      # Quarta (1, 4, 5)
            [0, 4, 7, 10],  # Dominant 7 (1, 3, 5, b7)
            [0, 4, 7, 10, 14]  # Dominant 9 (1, 3, 5, b7, 9)
        ]
        
        # Assignar acords als botons
        for i in range(16):
            # Usar diferents notes fonamentals de l'escala
            degree = i % len(scale)
            chord_root = root + scale[degree]
            
            # Seleccionar un tipus d'acord apropiat per al grau de l'escala
            chord_idx = i % len(chord_types)
            
            # Guardar la informació de l'acord
            mapping[i] = {
                "root": chord_root,
                "intervals": chord_types[chord_idx]
            }
        
        return mapping
    
    def _generate_bass_melody(self):
        """Genera un mapeig amb baixos a l'esquerra i notes melòdiques a la dreta."""
        mapping = {}
        scale = self.scales[self.current_scale]
        root = self.root_note + self.octave_offset * 12
        
        # Primers 8 botons: baixos (una octava més baixa)
        for i in range(8):
            step = i % len(scale)
            mapping[i] = root - 12 + scale[step]
        
        # Següents 8 botons: notes melòdiques
        for i in range(8, 16):
            step = (i - 8) % len(scale)
            mapping[i] = root + scale[step]
        
        return mapping
    
    def _update_key_mapping(self):
        """Actualitza el mapeig de botons segons la disposició i escala actual."""
        if self.current_layout not in self.keyboard_layouts:
            self.current_layout = "scale_4x4"
            
        # Generar el mapeig amb la funció corresponent a la disposició actual
        self.key_notes = self.keyboard_layouts[self.current_layout]()
    
    def update(self, pot_values, button_states):
        """
        Actualitza l'estat del teclat MIDI basant-se en les entrades dels potenciòmetres i botons.
        
        Args:
            pot_values: Valors dels potenciòmetres [0-127]
            button_states: Estat dels botons [True/False] x 16
        """
        current_time = time.monotonic()
        dt = current_time - self.last_update
        self.last_update = current_time
        
        # Actualitzar paràmetres basats en els potenciòmetres
        if len(pot_values) >= 3:
            # Potenciòmetre 1: Selecció d'escala
            scale_idx = int(pot_values[0] / 128 * len(self.scales))
            scale_idx = min(scale_idx, len(self.scales) - 1)
            new_scale = list(self.scales.keys())[scale_idx]
            
            # Potenciòmetre 2: Selecció de disposició de teclat
            layout_idx = int(pot_values[1] / 128 * len(self.keyboard_layouts))
            layout_idx = min(layout_idx, len(self.keyboard_layouts) - 1)
            new_layout = list(self.keyboard_layouts.keys())[layout_idx]
            
            # Potenciòmetre 3: Velocitat de les notes
            self.velocity = int(pot_values[2] / 128 * 127) + 1  # 1-127
            
            # Actualitzar el mapeig si ha canviat l'escala o la disposició
            if new_scale != self.current_scale or new_layout != self.current_layout:
                self.current_scale = new_scale
                self.current_layout = new_layout
                self._update_key_mapping()
        
        # Processar l'estat dels botons
        for i, is_pressed in enumerate(button_states):
            if i < len(button_states):  # Assegurar-se que el botó existeix
                button_id = f"button_{i}"
                
                if is_pressed:
                    # Botó premut
                    if button_id not in self.active_notes:
                        # Nova nota
                        if self.current_layout == "chord_pads":
                            # En mode acords, tocar múltiples notes
                            chord_info = self.key_notes.get(i)
                            if chord_info:
                                chord_notes = []
                                for interval in chord_info["intervals"]:
                                    note = chord_info["root"] + interval
                                    if 0 <= note <= 127:  # Assegurar-se que la nota està dins del rang MIDI
                                        self.midi_out.send(self.note_on(note, self.velocity))
                                        chord_notes.append(note)
                                
                                self.active_notes[button_id] = {
                                    "type": "chord",
                                    "notes": chord_notes
                                }
                        else:
                            # Mode normal, tocar una sola nota
                            note = self.key_notes.get(i, 60)  # Nota per defecte: C4 (60)
                            if 0 <= note <= 127:  # Assegurar-se que la nota està dins del rang MIDI
                                self.midi_out.send(self.note_on(note, self.velocity))
                                self.active_notes[button_id] = {
                                    "type": "note",
                                    "note": note
                                }
                
                elif button_id in self.active_notes:
                    # Botó deixat anar, aturar notes
                    note_info = self.active_notes[button_id]
                    
                    if note_info["type"] == "chord":
                        # Aturar totes les notes de l'acord
                        for note in note_info["notes"]:
                            self.midi_out.send(self.note_off(note, 0))
                    else:
                        # Aturar nota individual
                        self.midi_out.send(self.note_off(note_info["note"], 0))
                    
                    # Eliminar la nota del diccionari d'actives
                    del self.active_notes[button_id]
        
        # Retornar informació d'estat
        return {
            "mode": "Teclat MIDI",
            "escala": self.current_scale,
            "disposició": self.current_layout,
            "velocitat": self.velocity,
            "notes_actives": len(self.active_notes)
        }
    
    def cleanup(self):
        """Atura totes les notes actives en sortir del mode."""
        notes_to_stop = []
        
        # Recórrer totes les notes actives i aturar-les
        for button_id, note_info in self.active_notes.items():
            if note_info["type"] == "chord":
                # Aturar totes les notes de l'acord
                for note in note_info["notes"]:
                    notes_to_stop.append([note, 0, 0])  # [note, velocity, channel]
                    self.midi_out.send(self.note_off(note, 0))
            else:
                # Aturar nota individual
                note = note_info["note"]
                notes_to_stop.append([note, 0, 0])
                self.midi_out.send(self.note_off(note, 0))
        
        self.active_notes = {}
        return notes_to_stop
