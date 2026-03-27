"""
Mode Cascada - Simula el so sorollós i potent d'una cascada amb múltiples capes de soroll
"""
import time
import math
import random
from modes.base_mode import BaseMode

class ModeCascada(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Cascada Sorollosa"
        self.notes_playing = set()
        self.last_update = time.monotonic()
        
        # Paràmetres de la cascada
        self.noise_bands = []  # Bandes de soroll a diferents freqüències
        self.last_noise_update = 0
        self.noise_update_interval = 0.1  # Actualitzar el soroll cada 100ms
        
        # Capes de soroll (cada una amb la seva pròpia freqüència i amplitud)
        self.layers = [
            # Banda baixa (soroll de baixa freqüència per al rugit)
            {'note': 36, 'vel': 0, 'type': 'low_noise', 'active': False, 'last_vel': 0},
            # Banda mitjana (soroll de mitja freqüència pel cos principal)
            {'note': 60, 'vel': 0, 'type': 'mid_noise', 'active': False, 'last_vel': 0},
            # Banda alta (soroll d'alta freqüència per l'aigua que cau)
            {'note': 84, 'vel': 0, 'type': 'high_noise', 'active': False, 'last_vel': 0},
            # Impactes aleatoris (simulen roques i turbulències)
            {'note': 0, 'vel': 0, 'type': 'impact', 'next_impact': 0, 'active': False}
        ]
        
        # Paràmetres de control
        self.intensity = 0.5
        self.brightness = 0.5
        self.roughness = 0.5
        self.last_impact_time = 0
        
    def setup(self):
        self.initialized = True
        self.last_update = time.monotonic()
        self.notes_playing = set()
        self.last_noise_update = 0
        
        # Iniciar les capes de soroll amb valors per defecte
        self._update_layers(96, 64, 96)  # Valors inicials alts per a un so més ric
        
    def _update_layers(self, intensity, roughness, brightness):
        """Actualitza les capes de soroll basades en els paràmetres"""
        current_time = time.monotonic()
        
        # Actualitzar paràmetres de control (0.0 a 1.0)
        self.intensity = intensity / 127.0
        self.roughness = roughness / 127.0
        self.brightness = brightness / 127.0
        
        # Banda baixa (36-48) - Rugit profund de la cascada
        self.layers[0]['note'] = 36 + int(self.roughness * 12)  # Més rugositat = més agut
        self.layers[0]['vel'] = int(80 + (self.intensity * 40))  # Més intensitat = més volum
        
        # Banda mitjana (60-72) - Cos principal del soroll
        mid_note = 60 + int((1.0 - self.roughness) * 12)
        self.layers[1]['note'] = mid_note
        self.layers[1]['vel'] = int(60 + (self.intensity * 50))
        
        # Banda alta (84-96) - Aigua que cau i xoca
        high_note = 84 + int(self.roughness * 12)
        self.layers[2]['note'] = high_note
        self.layers[2]['vel'] = int(40 + (self.brightness * 60))
        
        # Configura impactes aleatoris
        self.layers[3]['vel'] = int(90 * self.intensity)
        # Temps fins al proper impacte (entre 0.5 i 3 segons, més ràpid amb més rugositat)
        if current_time > self.last_impact_time + 0.5:
            self.layers[3]['next_impact'] = current_time + (0.5 + random.random() * (3.0 - (self.roughness * 2.5)))
    
    def _generate_impact(self, current_time):
        """Genera un impacte de soroll aleatori"""
        if current_time > self.last_impact_time + 0.2:  # Evitar saturació
            # Nota aleatòria dins d'un rang que soni a impacte d'aigua
            impact_note = 45 + int(random.random() * 30)
            velocity = int(70 + (random.random() * 40 * self.intensity))
            
            # Enviar nota MIDI
            self.midi_out.send(self.note_on(impact_note, velocity))
            self.notes_playing.add(impact_note)
            
            # Programar apagat de la nota després d'un temps aleatori
            off_time = 0.05 + (random.random() * 0.2)
            def schedule_note_off():
                time.sleep(off_time)
                self.midi_out.send(self.note_off(impact_note, 0))
                if impact_note in self.notes_playing:
                    self.notes_playing.remove(impact_note)
            
            # Iniciar un fil per a l'apagat (simplificat per a CircuitPython)
            try:
                import _thread
                _thread.start_new_thread(schedule_note_off, ())
            except Exception:
                # Si no hi ha suport de fils, fer-ho de manera síncrona
                time.sleep(off_time)
                self.midi_out.send(self.note_off(impact_note, 0))
                if impact_note in self.notes_playing:
                    self.notes_playing.remove(impact_note)
            
            self.last_impact_time = current_time
    
    def update(self, pot_values, button_states):
        current_time = time.monotonic()
        
        # Llegir potenciòmetres i actualitzar capes
        self._update_layers(*pot_values)
        
        # Actualitzar soroll de fons (bandes de soroll)
        if current_time - self.last_noise_update >= self.noise_update_interval:
            self.last_noise_update = current_time
            
            # Actualitzar cada capa de soroll
            for layer in self.layers[:3]:  # Les tres primeres són bandes de soroll
                if layer['active']:
                    # Aturar la nota anterior
                    self.midi_out.send(self.note_off(layer['note'], 0))
                    if layer['note'] in self.notes_playing:
                        self.notes_playing.remove(layer['note'])
                
                # Actualitzar nota amb petita variació per a un efecte més orgànic
                variation = random.randint(-1, 1)
                layer['note'] = max(0, min(127, layer['note'] + variation))
                
                # Aplicar variació de velocitat per a un efecte més dinàmic
                vel_variation = random.randint(-5, 5)
                current_vel = max(10, min(127, layer['vel'] + vel_variation))
                
                # Enviar nova nota
                self.midi_out.send(self.note_on(layer['note'], current_vel))
                self.notes_playing.add(layer['note'])
                layer['active'] = True
            
            # Gestionar impactes aleatoris
            if current_time > self.layers[3]['next_impact']:
                self._generate_impact(current_time)
        
        # Actualitzar l'últim temps d'actualització
        self.last_update = current_time
        
        return {
            'intensity': int(self.intensity * 127),
            'roughness': int(self.roughness * 127),
            'brightness': int(self.brightness * 127),
            'active_notes': len(self.notes_playing),
            'low_note': self.layers[0]['note'],
            'mid_note': self.layers[1]['note'],
            'high_note': self.layers[2]['note']
        }
    
    def cleanup(self):
        notes_to_stop = list(self.notes_playing)
        self.notes_playing.clear()
        
        # Desactivar totes les capes
        for layer in self.layers:
            if 'active' in layer:
                layer['active'] = False
        
        return [(note, 0) for note in notes_to_stop]
