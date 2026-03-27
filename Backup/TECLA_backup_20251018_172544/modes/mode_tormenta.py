"""
Mode Tempesta - Combina sons de tempesta amb patrons melòdics
"""
import time
import math
import random
from modes.base_mode import BaseMode

class ModeTormenta(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Tempesta"
        
        # Estat de la tempesta
        self.background_intensity = 0.0   # Intensitat del fons de tempesta (Y)
        self.thunder_intensity = 0.0      # Intensitat dels trons (X)
        self.lightning_freq = 0.0         # Freqüència dels llamps (Z)
        
        # Sons de fons de tempesta (greus i vibrants)
        self.background_notes = {
            # Notes greus per simular la vibració de tempesta
            'deep_hum': {'note': 24, 'velocity': 0, 'active': False},   # Nota més greu
            'low_rumble': {'note': 28, 'velocity': 0, 'active': False}, # Tro de fons
            'mid_rumble': {'note': 32, 'velocity': 0, 'active': False}, # Tro mitjà
            'vibration': {'note': 36, 'velocity': 0, 'active': False}   # Vibració
        }
        
        # Estats i temps
        self.last_lightning = 0
        self.last_thunder = 0
        self.notes_playing = set()
        self.last_update = time.monotonic()
        
    def generate_storm_sounds(self, x, y, z):
        """
        Genera sons de tempesta amb fons atmosfèric greu i llamps clars
        """
        current_time = time.monotonic()
        dt = current_time - self.last_update
        
        # Actualitzar paràmetres principals des dels potenciòmetres
        self.thunder_intensity = x / 127.0      # Intensitat dels trons (X)
        self.lightning_intensity = y / 127.0     # Intensitat i freqüència dels llamps (Y)
        self.background_intensity = z / 127.0    # Intensitat del fons de trons (Z)
        
        # Llista de sons que es generaran en aquesta actualització
        storm_sounds = []
        
        # 1. Actualitzar el fons atmosfèric greu i vibrant
        self._update_background(current_time)
        
        # 2. Generar trons aleatoris (sons greus de fons)
        if (current_time - self.last_thunder) > (3.0 - (self.thunder_intensity * 2.5)) and \
           random.random() < (self.thunder_intensity * 0.7):
            self._add_thunder_sound(current_time, storm_sounds)
            self.last_thunder = current_time
        
        # 3. Generar llamps (notes agudes i distintives)
        # La intensitat dels llamps (Y) controla tant la freqüència com la intensitat
        lightning_wait_time = max(0.1, 2.0 - (self.lightning_intensity * 1.9))
        
        if (current_time - self.last_lightning) > lightning_wait_time:
            # Més intensitat = més llamps en cascada
            num_lightning = 1
            if self.lightning_intensity > 0.3:
                num_lightning += int(self.lightning_intensity * 5)
            
            # Generar llamps en cascada
            for i in range(num_lightning):
                self._add_lightning_sound(current_time + (i * 0.2), storm_sounds, i)
            
            self.last_lightning = current_time
        
        # Actualitzar l'últim temps d'actualització
        self.last_update = current_time
        
        return storm_sounds
        if self.rain_intensity > 0.3 and random.random() < 0.1:
            note = random.randint(25, 35)
            velocity = int(30 + self.rain_intensity * 40)
            storm_sounds.append({
                'type': 'thunder_rumble',
                'note': note,
                'velocity': velocity,
                'duration': 2.0 + random.random() * 3.0,
                'time': current_time
            })
        
        # Sons de vent atmosfèrics (més complexos)
        if self.wind_speed > 0.1:
            # Vent de fons (molt baix i constant)
            if random.random() < 0.2:
                note = random.choice([30, 31, 34, 35])
                velocity = int(20 + self.wind_speed * 30)
                storm_sounds.append({
                    'type': 'wind_atmos',
                    'note': note,
                    'velocity': velocity,
                    'duration': 1.0 + random.random() * 4.0,
                    'time': current_time
                })
            
            # Xiscles de vent (aguts)
            if random.random() < self.wind_speed * 0.3:
                note = random.randint(80, 90)
                velocity = int(30 + self.wind_speed * 40)
                storm_sounds.append({
                    'type': 'wind_howl',
                    'note': note,
                    'velocity': velocity,
                    'duration': 0.1 + random.random() * 0.5,
                    'time': current_time
                })
        
        # Sons de pluja (més subtils i orgànics)
        if self.rain_intensity > 0.1:
            # Gotes individuals
            if random.random() < self.rain_intensity * 0.3:
                note = random.randint(80, 100)
                velocity = int(20 + self.rain_intensity * 50)
                storm_sounds.append({
                    'type': 'rain_drop',
                    'note': note,
                    'velocity': velocity,
                    'duration': 0.05 + random.random() * 0.1,
                    'time': current_time
                })
            
            # Llençol de pluja
            if random.random() < self.rain_intensity * 0.1:
                for i in range(3):
                    note = random.randint(75, 95)
                    velocity = int(15 + self.rain_intensity * 30)
                    storm_sounds.append({
                        'type': 'rain_sheet',
                        'note': note,
                        'velocity': velocity,
                        'duration': 0.3 + random.random() * 0.5,
                        'time': current_time + (i * 0.05)
                    })
        
        # Llamps controlats pel potenciòmetre Z
        if (current_time - self.last_lightning) > (2.0 / (self.lightning_prob + 0.1)) and \
           random.random() < (self.lightning_prob * 0.2):
            self.last_lightning = current_time
            self.lightning_counter = 10
            
            # So de llamp (nota aguda i ràpida)
            note = random.randint(100, 110)
            velocity = random.randint(90, 110)
            storm_sounds.append({
                'type': 'lightning',
                'note': note,
                'velocity': velocity,
                'duration': 0.05 + random.random() * 0.1,
                'time': current_time
            })
            
            # Tro després del llamp (més fort amb més intensitat de pluja)
            delay = 0.1 + random.random() * 0.3
            note = random.randint(25, 35)
            velocity = int(80 + self.rain_intensity * 40)
            storm_sounds.append({
                'type': 'thunder',
                'note': note,
                'velocity': velocity,
                'duration': 1.0 + random.random() * 2.0,
                'time': current_time + delay
            })
            
            # Efecte de llum del llamp (nota molt aguda i ràpida)
            if random.random() < 0.7:  # 70% de probabilitat de llum addicional
                storm_sounds.append({
                    'type': 'lightning_flash',
                    'note': random.randint(110, 120),
                    'velocity': random.randint(60, 80),
                    'duration': 0.02 + random.random() * 0.05,
                    'time': current_time + (delay * 0.5)
                })
        
        # Melodia basada en la tempesta (afegint octaves)
        if random.random() < 0.3:  # Probabilitat de generar una nota melòdica
            # Escala menor harmònica per a un so més fosc/dramàtic
            scale = [0, 2, 3, 5, 7, 8, 11]  # Escala menor harmònica
            base_note = 48  # Do3
            octave_offset = random.randint(-1, 2)  # Variar l'octava
            note_idx = random.randint(0, len(scale)-1)
            
            # Afegir octaves superiors o inferiors basades en la intensitat
            octave_shift = 0
            if random.random() < self.rain_intensity * 0.7:  # Més probabilitat d'octaves altes amb molta pluja
                octave_shift = random.randint(1, 2)
            elif random.random() < 0.3:  # Ocasionals octaves baixes
                octave_shift = random.randint(-2, -1)
            
            note = base_note + (12 * (octave_offset + octave_shift)) + scale[note_idx]
            note = max(0, min(127, note))  # Assegurar que estigui en el rang MIDI
            
            velocity = 40 + int(60 * self.rain_intensity)
            duration = 0.2 + random.random() * (1.0 + self.wind_speed * 2.0)
            
            storm_sounds.append({
                'type': 'melody',
                'note': note,
                'velocity': velocity,
                'duration': duration,
                'time': current_time
            })
            
            # Afegir octava superior o inferior (50% de probabilitat)
            if random.random() < 0.5:
                octave_note = note + (12 if random.random() < 0.7 else -12)
                if 0 <= octave_note <= 127:  # Assegurar que estigui en el rang MIDI
                    storm_sounds.append({
                        'type': 'melody_octave',
                        'note': octave_note,
                        'velocity': max(20, velocity - 20),  # Una mica més suau
                        'duration': duration * 0.8,  # Una mica més curt
                        'time': current_time + random.random() * 0.1  # Petita variació temporal
                    })
        
        return storm_sounds
    
    def setup(self):
        self.initialized = True
        self.rain_intensity = 0.0
        self.wind_speed = 0.0
        self.lightning_counter = 0
        self.last_lightning = 0
        self.notes_playing = set()
        self.last_update = time.monotonic()
        
    def update(self, pot_values, button_states):
        current_time = time.monotonic()
        x, y, z = pot_values
        
        # Actualitzar paràmetres de la tempesta des dels potenciòmetres
        self.thunder_intensity = x / 127.0      # X: Intensitat dels trons
        self.lightning_intensity = y / 127.0    # Y: Intensitat dels llamps
        self.background_intensity = z / 127.0   # Z: Intensitat del fons
        
        # 1. Actualitzar sons de fons continus
        self._update_background(current_time)
        
        # Gestionar les notes de fons (activar/desactivar segons intensitat)
        for note_id, note_info in self.background_notes.items():
            if note_info['active']:
                # Aturar la nota si ja no s'ha de reproduir
                if note_info['velocity'] <= 10:  # Llindar mínim
                    self.midi_out.send(self.note_off(note_info['note'], 0))
                    note_info['active'] = False
                    if note_info['note'] in self.notes_playing:
                        self.notes_playing.remove(note_info['note'])
                # Actualitzar la velocitat si segueix activa
                elif note_info['note'] in self.notes_playing:
                    # Actualitzem velocitat sense aturar la nota
                    self.midi_out.send(self.note_on(note_info['note'], note_info['velocity']))
            else:
                # Iniciar la nota si s'ha de reproduir
                if note_info['velocity'] > 10:  # Llindar mínim
                    self.midi_out.send(self.note_on(note_info['note'], note_info['velocity']))
                    note_info['active'] = True
                    self.notes_playing.add(note_info['note'])
        
        # 2. Generar sons de tempesta (llamps i trons)
        storm_sounds = self.generate_storm_sounds(x, y, z)
        
        # 3. Processar sons generats
        notes_to_play = set(sound['note'] for sound in storm_sounds)
        
        # Iniciar noves notes
        for sound in storm_sounds:
            note = sound['note']
            if note not in self.notes_playing:
                velocity = sound.get('velocity', 80)
                self.midi_out.send(self.note_on(note, velocity))
                self.notes_playing.add(note)
        
        # Aturar notes que ja no es reprodueixen (excepte les de fons)
        background_notes = {info['note'] for info in self.background_notes.values()}
        notes_to_stop = [n for n in self.notes_playing 
                         if n not in notes_to_play and n not in background_notes]
        
        for note in notes_to_stop:
            self.midi_out.send(self.note_off(note, 30))  # Alliberament suau
            self.notes_playing.remove(note)
        
        # Actualitzar l'estat dels botons
        for i, pressed in enumerate(button_states):
            if pressed and hasattr(self, f'button_{i}_pressed'):
                getattr(self, f'button_{i}_pressed')()
        
        # Per compatibilitat amb codi antic
        self.rain_intensity = self.background_intensity
        self.wind_speed = self.thunder_intensity
        self.lightning_freq = self.lightning_intensity
        
        # Retornar informació de depuració
        return {
            'thunder': int(self.thunder_intensity * 100),
            'lightning': int(self.lightning_intensity * 100),
            'background': int(self.background_intensity * 100),
            'active_notes': len(self.notes_playing)
        }
    
    def _update_background(self, current_time):
        """Actualitza el fons greu i vibrant de la tempesta"""
        # Hum profund (sempre present, més intens amb més intensitat de fons)
        self.background_notes['deep_hum']['velocity'] = int(40 + self.background_intensity * 40)
        
        # Retruny baix (vibrant, més intens amb més intensitat de trons)
        low_rumble_vel = int(30 + self.thunder_intensity * 50)
        self.background_notes['low_rumble']['velocity'] = low_rumble_vel
        
        # Retruny mitjà (menys intens, però sempre present)
        mid_rumble_vel = int(20 + self.background_intensity * 40)
        self.background_notes['mid_rumble']['velocity'] = mid_rumble_vel
        
        # Vibració (efecte de tempesta que s'intensifica amb el fons)
        vibration_vel = int(15 + self.background_intensity * 35)
        self.background_notes['vibration']['velocity'] = vibration_vel
    
    def _add_thunder_sound(self, current_time, storm_sounds):
        """Afegeix sons de trons profunds i vibrants"""
        # Tipus de tro (basat en la intensitat del tro)
        if self.thunder_intensity > 0.7:
            # Tro profund i potent (tempesta força)
            base_note = random.randint(22, 30)
            velocity = random.randint(80, 100)  # Fort
            duration = 1.0 + random.random() * 2.0  # Llarg
        elif self.thunder_intensity > 0.3:
            # Tro mitjà (tempesta moderada)
            base_note = random.randint(28, 36)
            velocity = random.randint(60, 80)  # Moderat
            duration = 0.8 + random.random() * 1.5  # Moderadament llarg
        else:
            # Tro lleuger i distant (tempesta llunyana)
            base_note = random.randint(34, 40)
            velocity = random.randint(40, 60)  # Suau
            duration = 0.5 + random.random() * 1.0  # Curt
        
        # Afegir el tro principal
        storm_sounds.append({
            'type': 'thunder_main',
            'note': base_note,
            'velocity': velocity,
            'duration': duration,
            'time': current_time
        })
        
        # Afegir una segona capa de tro per a més profunditat (si el tro és intens)
        if self.thunder_intensity > 0.4 and random.random() < 0.7:
            storm_sounds.append({
                'type': 'thunder_layer',
                'note': base_note - 5,  # Una mica més greu
                'velocity': int(velocity * 0.7),  # Una mica més suau
                'duration': duration * 1.2,  # Una mica més llarg
                'time': current_time + random.random() * 0.2  # Lleuger retard
            })
    
    def _add_lightning_sound(self, current_time, storm_sounds, cascade_index=0):
        """Afegeix sons de llamps brillants i aguts amb efecte cascada"""
        # La intensitat del llamp depèn del potenciòmetre Y
        intensity_factor = self.lightning_intensity * 1.0
        
        # En cascada, fer que les notes variïn per crear un efecte de cascada descendent
        cascade_offset = cascade_index * 2  # Petita variació per a cada llamp en cascada
        
        # 1. El flaix del llamp (nota molt aguda i ràpida)
        # Més intens = més agut i fort
        flash_note = random.randint(96, 108) - cascade_offset  # Notes agudes amb variació
        flash_velocity = int(90 + (35 * intensity_factor))  # Velocitat basada en intensitat
        
        storm_sounds.append({
            'type': 'lightning_flash',
            'note': flash_note,
            'velocity': flash_velocity,
            'duration': 0.05 + random.random() * 0.1,  # Molt curt
            'time': current_time
        })
        
        # 2. Sons secundaris del llamp (efecte de cascada)
        # Per a cada llamp, afegir 1-3 notes secundàries que creen un efecte visual
        num_secondary = 1 + int(self.lightning_intensity * 3)
        for i in range(num_secondary):
            secondary_delay = 0.05 + (i * 0.03) + (random.random() * 0.02)
            secondary_note = flash_note - (3 * (i+1)) + random.randint(-2, 2)  # Descendint
            secondary_velocity = int(flash_velocity * (0.9 - (i * 0.1)))  # Decreixent
            
            storm_sounds.append({
                'type': 'lightning_cascade',
                'note': secondary_note,
                'velocity': secondary_velocity,
                'duration': 0.05 + random.random() * 0.1,
                'time': current_time + secondary_delay
            })
        
        # 3. El tro que segueix (basat en la intensitat dels trons)
        # Només afegir tro si no és un dels llamps secundaris en cascada
        if self.thunder_intensity > 0.2 and cascade_index == 0:  
            thunder_delay = 0.2 + random.random() * 0.3
            thunder_note = random.randint(30, 40)  # Nota greu
            thunder_velocity = int(70 + random.random() * 40 * self.thunder_intensity)
            
            storm_sounds.append({
                'type': 'lightning_thunder',
                'note': thunder_note,
                'velocity': thunder_velocity,
                'duration': 0.8 + random.random() * 1.5,
                'time': current_time + thunder_delay
            })
    
    def setup(self):
        """Inicialitza el mode Tempesta"""
        self.initialized = True
        self.background_intensity = 0.0
        self.thunder_intensity = 0.0
        self.lightning_intensity = 0.0
        
        # Per compatibilitat amb codi antic
        self.rain_intensity = 0.0
        self.wind_speed = 0.0
        self.lightning_freq = 0.0
        
        self.last_lightning = 0
        self.last_thunder = 0
        self.notes_playing = set()
        self.last_update = time.monotonic()
    
    def cleanup(self):
        """Netega totes les notes en sortir del mode"""
        # Aturar totes les notes de fons
        for note_info in self.background_notes.values():
            if note_info['active']:
                self.midi_out.send(self.note_off(note_info['note'], 0))
                note_info['active'] = False
        
        # Aturar la resta de notes
        notes_to_stop = list(self.notes_playing)
        for note in notes_to_stop:
            self.midi_out.send(self.note_off(note, 0))
        
        self.notes_playing.clear()
        return [(note, 0) for note in notes_to_stop]
