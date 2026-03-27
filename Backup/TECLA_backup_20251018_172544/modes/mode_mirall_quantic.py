"""
Mode Mirall Quàntic - Emula comportamientos de la física cuántica como superposición,
entrelazamiento e incertidumbre de Heisenberg
"""
import time
import math
import random
from modes.base_mode import BaseMode

class ModeMirallQuantic(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Mirall Quàntic"
        self.particles = []
        self.entangled_pairs = []
        self.active_notes = {}
        self.last_update = time.monotonic()
        self.current_observation = 0
        
    def setup(self):
        self.initialized = True
        self.active_notes = {}
        self.last_update = time.monotonic()
        
        # Crear partículas cuánticas
        base_notes = [36, 48, 60, 72]
        self.particles = []
        
        for i in range(8):
            self.particles.append({
                "id": i,
                "state": random.random(),
                "spin": random.choice([-1, 1]),
                "position": random.random(),
                "momentum": random.random() * 2 - 1,
                "base_note": random.choice(base_notes),
                "channel": i % 4,
                "last_collapse": 0,
                "superposition": True
            })
        
        # Crear pares entrelazados manualmente sin usar random.shuffle
        self.entangled_pairs = []
        
        # Crear una lista de IDs de partículas y mezclarla manualmente
        particle_ids = [p["id"] for p in self.particles]
        
        # Mezclar la lista manualmente (algoritmo Fisher-Yates simplificado)
        for i in range(len(particle_ids) - 1, 0, -1):
            # Generar un índice aleatorio entre 0 e i
            j = int(random.random() * (i + 1))
            # Intercambiar elementos
            particle_ids[i], particle_ids[j] = particle_ids[j], particle_ids[i]
            
        # Crear pares entrelazados
        for i in range(0, len(particle_ids), 2):
            if i + 1 < len(particle_ids):
                self.entangled_pairs.append((particle_ids[i], particle_ids[i+1]))
    
    def _get_entangled_particle(self, particle_id):
        """Encuentra la partícula entrelazada con la dada"""
        for pair in self.entangled_pairs:
            if pair[0] == particle_id:
                return pair[1]
            elif pair[1] == particle_id:
                return pair[0]
        return None
    
    def update(self, pot_values, button_states):
        current_time = time.monotonic()
        dt = min(0.1, current_time - self.last_update)
        self.last_update = current_time
        
        # Parámetros controlados por potenciómetros
        uncertainty = 0.1 + (pot_values[0] / 127.0) * 0.9    # Principio de incertidumbre (0.1 - 1.0)
        entanglement = (pot_values[1] / 127.0)               # Fuerza de entrelazamiento (0.0 - 1.0)
        observation_rate = 0.1 + (pot_values[2] / 127.0)     # Frecuencia de "observación" (colapso de función de onda) (0.1 - 1.1)
        
        # Incrementar contador de observación
        self.current_observation += dt * observation_rate
        observation_event = self.current_observation >= 1.0
        
        if observation_event:
            self.current_observation = 0
        
        # Actualizar cada partícula cuántica
        for particle in self.particles:
            # El principio de incertidumbre: no podemos conocer posición y momento con precisión
            # Cuanto más precisa la posición, más incierto el momento y viceversa
            if particle["superposition"]:
                # En superposición, la posición y el momento evolucionan según una función de onda
                particle["position"] += particle["momentum"] * dt * (1.0 - uncertainty)
                particle["momentum"] += (random.random() * 2 - 1) * dt * uncertainty
                
                # Mantener valores en rango
                particle["position"] %= 1.0
                particle["momentum"] = max(-1.0, min(1.0, particle["momentum"]))
            
            # Evento de observación (colapso de la función de onda)
            if observation_event and random.random() < observation_rate:
                particle["superposition"] = False
                particle["last_collapse"] = current_time
                
                # Al observar, la partícula colapsa a un estado definido
                particle["state"] = random.random()
                
                # Si está entrelazada, la partícula gemela también colapsa
                entangled_id = self._get_entangled_particle(particle["id"])
                if entangled_id is not None and random.random() < entanglement:
                    for p in self.particles:
                        if p["id"] == entangled_id:
                            p["superposition"] = False
                            p["last_collapse"] = current_time
                            # Estado opuesto debido al entrelazamiento
                            p["state"] = 1.0 - particle["state"]
                            p["spin"] = -particle["spin"]
            
            # Volver a superposición después de un tiempo
            if not particle["superposition"] and current_time - particle["last_collapse"] > 2.0:
                particle["superposition"] = True
            
            # Generar notas basadas en el estado de la partícula
            particle_id = f"particle_{particle['id']}"
            
            # Calcular nota basada en el estado y la posición
            scale = [0, 2, 3, 5, 7, 8, 10, 12]  # Escala dórica
            note_idx = int(particle["state"] * len(scale))
            position_octave = int(particle["position"] * 3) - 1  # -1, 0, o 1 octava
            
            note = particle["base_note"] + scale[note_idx] + (position_octave * 12)
            note = max(0, min(127, note))  # Mantener en rango MIDI
            
            # Calcular velocidad basada en el momento
            velocity = int(abs(particle["momentum"]) * 64 + 63)  # 63-127
            
            # Decidir si tocar la nota
            should_play = False
            
            if not particle["superposition"]:
                # Partículas colapsadas siempre generan notas
                should_play = True
            elif random.random() < 0.05:
                # Partículas en superposición ocasionalmente generan notas
                should_play = True
            
            if should_play:
                # Detener la nota anterior si existe
                if particle_id in self.active_notes:
                    try:
                        old_note = self.active_notes[particle_id]["note"]
                        channel = particle["channel"]
                        note_off_msg = self.note_off(old_note, 0)
                        note_off_msg.channel = channel
                        self.midi_out.send(note_off_msg)
                    except Exception as e:
                        print(f"Error al detener nota: {e}")
                
                # Tocar la nueva nota
                try:
                    note_on_msg = self.note_on(note, velocity)
                    note_on_msg.channel = particle["channel"]
                    self.midi_out.send(note_on_msg)
                    self.active_notes[particle_id] = {"note": note, "velocity": velocity}
                except Exception as e:
                    print(f"Error al tocar nota: {e}")
        
        return {
            "mode": "Mirall Quàntic",
            "incertesa": f"{int(uncertainty * 100)}%",
            "entrellaçament": f"{int(entanglement * 100)}%",
            "observació": f"{int(observation_rate * 100)}%"
        }
    
    def cleanup(self):
        notes_to_stop = []
        
        # Detener todas las notas activas
        for particle_id, note_data in self.active_notes.items():
            # Extraer el ID real de la partícula
            real_id = int(particle_id.split('_')[1])
            
            # Encontrar el canal correspondiente
            channel = 0
            for particle in self.particles:
                if particle["id"] == real_id:
                    channel = particle["channel"]
                    break
            
            notes_to_stop.append([note_data["note"], 0, channel])
            
            # Enviar mensaje MIDI para detener la nota
            try:
                note_off_msg = self.note_off(note_data["note"], 0)
                note_off_msg.channel = channel
                self.midi_out.send(note_off_msg)
            except Exception as e:
                print(f"Error al limpiar nota: {e}")
        
        self.active_notes = {}
        return notes_to_stop
