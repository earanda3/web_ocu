"""
Mode Riu - Simula el flux d'un riu amb patrons melòdics fluids i orgànics
"""
import time
import math
import random
from modes.base_mode import BaseMode

class ModeRio(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Riu"
        self.current_notes = []      # Notes actualment sonant
        self.water_level = 0.0       # Nivell d'aigua (0-1)
        self.flow_rate = 0.0         # Velocitat del flux (0-1)
        self.turbulence = 0.0        # Turbulència (0-1)
        self.last_update = time.monotonic()
        self.notes_playing = set()   # Notes actualment sonant
        
    def generate_water_sound(self, x, y, z):
        """
        Genera un so basat en el flux d'aigua amb acords melosos i fluïdos
        """
        current_time = time.monotonic()
        dt = current_time - self.last_update
        self.last_update = current_time
        
        # Actualitzar paràmetres del riu basats en els potenciòmetres
        target_water_level = y / 127.0  # Nivell d'aigua controlat per Y
        target_flow_rate = x / 127.0    # Velocitat del flux controlada per X
        target_turbulence = z / 127.0   # Turbulència controlada per Z
        
        # Suavitzar les transicions
        self.water_level = self.water_level * 0.95 + target_water_level * 0.05
        self.flow_rate = self.flow_rate * 0.95 + target_flow_rate * 0.05
        self.turbulence = self.turbulence * 0.95 + target_turbulence * 0.05
        
        # Escales i acords per a diferents estats del riu
        if self.flow_rate < 0.3:
            # Aigües tranquil·les - Escala pentatònica major amb extensions
            scale = [0, 2, 4, 7, 9]  # Do pentatònic major
            chords = [
                [0, 4, 7],      # Major
                [0, 4, 7, 11],  # Major 7
                [0, 4, 7, 10]   # 7a dominant
            ]
            base_octave = 4
            note_density = 0.1 + self.water_level * 0.2  # Menys densitat
        else:
            # Ràpids - Escala de blues per a més moviment
            scale = [0, 3, 5, 6, 7, 10]  # Blues scale
            chords = [
                [0, 3, 7],      # m
                [0, 3, 7, 10],  # m7
                [0, 5, 7, 10]   # m7 amb 5a al baix
            ]
            base_octave = 3
            note_density = 0.2 + self.flow_rate * 0.3  # Una mica més de densitat
        
        # Generar acords en lloc de notes individuals
        new_notes = []
        if random.random() < note_density * 0.5:  # Reduïm la densitat global
            # Seleccionar acord
            chord = random.choice(chords)
            velocity = int(50 + random.random() * 40 * self.water_level)
            
            # Tocar l'acord (màxim 3 notes a l'hora)
            # Seleccionar intervals aleatoris sense repetir (alternativa a random.sample)
            num_notes = min(3, len(chord))
            selected_indices = []
            
            while len(selected_indices) < num_notes:
                idx = random.randint(0, len(chord) - 1)
                if idx not in selected_indices:
                    selected_indices.append(idx)
            
            for idx in selected_indices:
                interval = chord[idx]
                octave_offset = random.randint(-1, 1)  # Petites variacions d'octava
                note = (base_octave + octave_offset) * 12 + interval
                note = max(0, min(127, note))  # Assegurar que estigui en el rang MIDI
                
                # Afegir a la llista de notes
                new_notes.append({
                    'note': note,
                    'velocity': max(30, velocity - random.randint(0, 20)),
                    'duration': 0.5 + random.random() * 2.0 * (2.0 - self.flow_rate),
                    'pitch_bend': int((random.random() * 2 - 1) * 300)  # Menys pitch bend
                })
        
        return new_notes
    
    def setup(self):
        self.initialized = True
        self.current_notes = []
        self.water_level = 0.5
        self.flow_rate = 0.5
        self.turbulence = 0.5
        self.last_update = time.monotonic()
        self.notes_playing = set()
        
    def update(self, pot_values, button_states):
        current_time = time.monotonic()
        dt = current_time - self.last_update
        x, y, z = pot_values
        
        # Limitar el nombre màxim de notes a 32 per evitar sobrecàrrega
        max_notes = 32
        
        # Generar nous sons d'aigua (menys freqüents)
        new_water_sounds = []
        if len(self.current_notes) < max_notes:  # Només generar noves notes si no hem arribat al límit
            # Reduir la probabilitat de generar noves notes
            if random.random() < 0.3:  # 30% de probabilitat en lloc de 100%
                new_water_sounds = self.generate_water_sound(x, y, z)
        
        # Actualitzar notes actuals
        updated_notes = []
        active_notes_count = 0
        
        # Processar notes existents (màxim 32 notes)
        for note_info in self.current_notes[-max_notes:]:  # Agafar com a màxim les últimes 32 notes
            note_info['age'] = note_info.get('age', 0) + dt
            
            # Si la nota ha acabat, aturar-la
            if note_info['age'] >= note_info['duration']:
                if note_info['note'] in self.notes_playing:
                    self.midi_out.send(self.note_off(note_info['note'], 0))
                    self.notes_playing.remove(note_info['note'])
            else:
                # Si encara està sonant, afegir a la llista actualitzada
                updated_notes.append(note_info)
                active_notes_count += 1
        
        # Afegir noves notes (fins a assolir el límit)
        for sound in new_water_sounds:
            if active_notes_count >= max_notes:
                break
                
            sound['age'] = 0
            updated_notes.append(sound)
            active_notes_count += 1
            
            # Reproduir la nova nota
            if sound['note'] not in self.notes_playing:
                self.midi_out.send(self.note_on(sound['note'], sound['velocity']))
                self.notes_playing.add(sound['note'])
        
        # Mantenir només les notes actives (sense duplicats)
        self.current_notes = updated_notes
        
        # Netejar notes que ja no sonen
        if len(self.notes_playing) > max_notes * 2:  # Si hi ha massa notes a notes_playing
            active_notes = {note['note'] for note in self.current_notes}
            for note in list(self.notes_playing):
                if note not in active_notes:
                    self.midi_out.send(self.note_off(note, 0))
                    self.notes_playing.remove(note)
        self.last_update = current_time
        
        return {
            'water_level': self.water_level,
            'flow_rate': self.flow_rate,
            'turbulence': self.turbulence,
            'active_notes': len(self.notes_playing),
            'total_notes': len(self.current_notes)
        }
    
    def cleanup(self):
        # Aturar totes les notes en sortir del mode
        notes_to_stop = list(self.notes_playing)
        self.notes_playing.clear()
        self.current_notes = []
        return [(note, 0) for note in notes_to_stop]
