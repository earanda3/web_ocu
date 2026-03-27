"""
Mode Neural - Simula el comportamiento de una red neuronal generando patrones emergentes
a partir de reglas simples de activación y propagación
"""
import time
import math
import random
from modes.base_mode import BaseMode

class ModeNeural(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Neural"
        self.neurons = []
        self.active_notes = {}
        self.last_update = time.monotonic()
        self.last_neuron_creation = 0
        self.note_scales = {
            "major": [0, 2, 4, 5, 7, 9, 11, 12],
            "minor": [0, 2, 3, 5, 7, 8, 10, 12],
            "pentatonic": [0, 3, 5, 7, 10, 12, 15, 17]
        }
        self.current_scale = "major"
        
    def setup(self):
        self.initialized = True
        self.active_notes = {}
        self.last_update = time.monotonic()
        self.last_neuron_creation = 0
        
        # Crear neuronas iniciales
        self.neurons = []
        
        # Distribución de notas base por registros
        base_notes = [36, 48, 60, 72]
        
        # Crear 10 neuronas iniciales
        for i in range(10):
            self.neurons.append({
                "id": i,
                "activation": 0.0,
                "threshold": random.uniform(0.5, 0.9),
                "decay_rate": random.uniform(0.2, 0.8),
                "base_note": random.choice(base_notes),
                "connections": [],
                "position": random.random(),
                "channel": i % 16,
                "last_fire": 0
            })
        
        # Crear conexiones iniciales
        for neuron in self.neurons:
            # Cada neurona se conecta a 1-3 otras neuronas aleatorias
            num_connections = random.randint(1, 3)
            potential_targets = [n for n in self.neurons if n["id"] != neuron["id"]]
            
            if potential_targets:
                # Seleccionar aleatoriamente hasta num_connections elementos
                targets = []
                available_targets = potential_targets.copy()
                
                for _ in range(min(num_connections, len(potential_targets))):
                    if not available_targets:
                        break
                        
                    # Seleccionar un índice aleatorio
                    idx = int(random.random() * len(available_targets))
                    # Añadir el elemento seleccionado a targets
                    targets.append(available_targets[idx])
                    # Eliminar el elemento seleccionado para evitar duplicados
                    available_targets.pop(idx)
                
                for target in targets:
                    neuron["connections"].append({
                        "target_id": target["id"],
                        "weight": random.uniform(0.3, 1.0),
                        "delay": random.uniform(0.1, 1.0)
                    })
        
        print(f"Red neuronal inicializada con {len(self.neurons)} neuronas")
    
    def _get_scale_note(self, base_note, step):
        """Obtener una nota de la escala actual"""
        # Asegurarse de que base_note y step sean enteros
        try:
            base_note = int(base_note)
            step = int(step)
            
            scale = self.note_scales.get(self.current_scale, self.note_scales["major"])
            octave = step // len(scale)
            index = step % len(scale)
            return base_note + scale[index] + (octave * 12)
        except Exception as e:
            print(f"Error en _get_scale_note: {e}, base_note={base_note}, step={step}")
            return base_note  # Devolver la nota base en caso de error
    
    def update(self, pot_values=None, button_states=None):
        """
        Actualiza el estado del modo basado en los valores de los potenciómetros y botones.
        
        Args:
            pot_values: Lista de valores de los potenciómetros [0-127]
            button_states: Lista de estados de los botones [True/False]
            
        Returns:
            dict: Diccionario con información del estado actual del modo
        """
        try:
            # Inicializar valores por defecto
            pot_values = pot_values if pot_values is not None else [64, 64, 64]
            button_states = button_states or []
            
            # Asegurarse de que pot_values tenga al menos 3 elementos
            while len(pot_values) < 3:
                pot_values.append(64)  # Valor por defecto 64 (centro)
                
            # Inicializar last_update si no existe
            if not hasattr(self, 'last_update'):
                self.last_update = time.monotonic()
                
            current_time = time.monotonic()
            dt = min(0.1, current_time - self.last_update)
            self.last_update = current_time
            
            # Parámetros controlados por potenciómetros
            excitability = 0.1 + (pot_values[0] / 127.0) * 0.9    # Excitabilidad de las neuronas (0.1 - 1.0)
            plasticity = (pot_values[1] / 127.0)                  # Plasticidad (adaptabilidad de las conexiones) (0.0 - 1.0)
            complexity = 0.1 + (pot_values[2] / 127.0) * 0.9      # Complejidad de la red (0.1 - 1.0)
            
            # Seleccionar escala basada en complejidad
            if complexity < 0.33:
                self.current_scale = "major"
            elif complexity < 0.66:
                self.current_scale = "minor"
            else:
                self.current_scale = "pentatonic"
            
            # Preparar el diccionario de estado que devolveremos al final
            status = {
                'mode': self.name,
                'excitability': f"{int(excitability * 100)}%",
                'plasticity': f"{int(plasticity * 100)}%",
                'complexity': f"{int(complexity * 100)}%",
                'neurons': len(self.neurons) if hasattr(self, 'neurons') else 0,
                'scale': self.current_scale,
                'active_notes': len(self.active_notes) if hasattr(self, 'active_notes') else 0
            }
            
            # Ocasionalmente añadir nuevas neuronas basado en la complejidad
            if current_time - self.last_neuron_creation > 5.0 and random.random() < complexity * 0.2:
                self.last_neuron_creation = current_time
                
                # Crear nueva neurona
                new_id = max([n["id"] for n in self.neurons]) + 1 if self.neurons else 0
                new_neuron = {
                    "id": new_id,
                    "activation": 0.0,
                    "threshold": random.uniform(0.5, 0.9),
                    "decay_rate": random.uniform(0.2, 0.8),
                    "base_note": random.choice([36, 48, 60, 72]),
                    "connections": [],
                    "position": random.random(),
                    "channel": new_id % 16,
                    "last_fire": 0
                }
                
                # Conectarla a algunas neuronas existentes
                num_connections = random.randint(1, 3)
                potential_targets = self.neurons.copy()
                
                if potential_targets:
                    # Seleccionar aleatoriamente hasta num_connections elementos
                    targets = []
                    available_targets = potential_targets.copy()
                    
                    # Seleccionar aleatoriamente hasta num_connections elementos
                    for _ in range(min(num_connections, len(potential_targets))):
                        if not available_targets:
                            break
                            
                        # Seleccionar un índice aleatorio
                        idx = int(random.random() * len(available_targets))
                        # Añadir el elemento seleccionado a targets
                        targets.append(available_targets[idx])
                        # Eliminar el elemento seleccionado para evitar duplicados
                        available_targets.pop(idx)
                    
                    for target in targets:
                        new_neuron["connections"].append({
                            "target_id": target["id"],
                            "weight": random.uniform(0.3, 1.0),
                            "delay": random.uniform(0.1, 1.0)
                        })
                        
                        # También crear algunas conexiones desde las neuronas existentes hacia la nueva
                        if random.random() < 0.5:
                            target["connections"].append({
                                "target_id": new_id,
                                "weight": random.uniform(0.3, 1.0),
                                "delay": random.uniform(0.1, 1.0)
                            })
                
                self.neurons.append(new_neuron)
            
            # Simular entrada externa a algunas neuronas (estímulo espontáneo)
            for neuron in self.neurons:
                # Estímulo aleatorio basado en excitabilidad
                if random.random() < excitability * 0.01:
                    neuron["activation"] += random.uniform(0.1, 0.5)
            
            # Procesar activaciones y generar notas
            fired_neurons = []
            
            for neuron in self.neurons:
                try:
                    # Decaimiento natural de la activación
                    neuron["activation"] *= (1.0 - neuron["decay_rate"] * dt)
                    
                    # Si la neurona supera su umbral, se activa
                    if neuron["activation"] > neuron["threshold"]:
                        fired_neurons.append(neuron)
                        neuron["last_fire"] = current_time
                        
                        # Resetear activación después de dispararse
                        neuron["activation"] = 0.0
                        
                        # Propagar señal a las neuronas conectadas (con retraso)
                        for connection in neuron["connections"]:
                            # Programar activación futura para las neuronas conectadas
                            target_id = connection["target_id"]
                            weight = connection["weight"]
                            
                            # Encontrar la neurona objetivo
                            target_neuron = next((n for n in self.neurons if n["id"] == target_id), None)
                            
                            if target_neuron:
                                # Incrementar activación de la neurona objetivo
                                target_neuron["activation"] += weight
                                
                                # Plasticidad: ajustar peso de la conexión
                                if random.random() < plasticity * 0.1:
                                    # Reforzar o debilitar conexión
                                    connection["weight"] += random.uniform(-0.1, 0.2)
                                    connection["weight"] = max(0.1, min(1.0, connection["weight"]))
                        
                        # Generar nota MIDI para esta neurona
                        neuron_id = f"neuron_{neuron['id']}"
                        
                        # Calcular nota basada en posición y escala
                        note_step = int(neuron["position"] * 8)  # 0-7 en la escala
                        note = self._get_scale_note(neuron["base_note"], note_step)
                        
                        # Velocidad basada en activación previa
                        velocity = int(max(40, min(127, neuron["threshold"] * 127)))
                        
                        # Detener la nota anterior si existe
                        if neuron_id in self.active_notes:
                            try:
                                old_note = self.active_notes[neuron_id]["note"]
                                channel = neuron["channel"]
                                note_off_msg = self.note_off(old_note, 0)
                                note_off_msg.channel = channel
                                self.midi_out.send(note_off_msg)
                            except Exception as e:
                                print(f"Error al detener nota: {e}")
                        
                        # Tocar la nueva nota
                        try:
                            note_on_msg = self.note_on(note, velocity)
                            note_on_msg.channel = neuron["channel"]
                            self.midi_out.send(note_on_msg)
                            self.active_notes[neuron_id] = {"note": note, "velocity": velocity}
                        except Exception as e:
                            print(f"Error al tocar nota: {e}")
                except Exception as e:
                    print(f"Error procesando neurona {neuron['id']}: {e}")
            
            # Detener notas de neuronas que no se han disparado recientemente
            neuron_ids_to_remove = []
            
            for neuron_id, note_data in self.active_notes.items():
                try:
                    real_id = int(neuron_id.split('_')[1])
                    neuron = next((n for n in self.neurons if n["id"] == real_id), None)
                    
                    if neuron and current_time - neuron["last_fire"] > 2.0:
                        note_off_msg = self.note_off(note_data["note"], 0)
                        note_off_msg.channel = neuron["channel"]
                        self.midi_out.send(note_off_msg)
                        neuron_ids_to_remove.append(neuron_id)
                except Exception as e:
                    print(f"Error al detener nota: {e}")
                    neuron_ids_to_remove.append(neuron_id)  # Añadir a la lista para eliminar en caso de error
            
            # Eliminar notas detenidas del diccionario
            for neuron_id in neuron_ids_to_remove:
                if neuron_id in self.active_notes:
                    del self.active_notes[neuron_id]
            
            # Actualizar el estado con información más reciente
            status['active_notes'] = len(self.active_notes)
            
            return status
            
        except Exception as e:
            print(f"Error general en update: {e}")
            return {
                'mode': self.name,
                'error': str(e)
            }
    
    def cleanup(self):
        """
        Limpia los recursos del modo y detiene todas las notas.
        Devuelve una lista de notas a detener en el formato [[note, velocity, channel], ...]
        """
        notes_to_stop = []
        
        # Detener todas las notas activas
        for neuron_id, note_data in self.active_notes.items():
            try:
                # Extraer el ID real de la neurona
                real_id = int(neuron_id.split('_')[1])
                
                # Encontrar el canal correspondiente
                channel = 0
                for neuron in self.neurons:
                    if neuron["id"] == real_id:
                        channel = neuron["channel"]
                        break
                
                notes_to_stop.append([note_data["note"], 0, channel])
                
                # Enviar mensaje MIDI para detener la nota
                note_off_msg = self.note_off(note_data["note"], 0)
                note_off_msg.channel = channel
                self.midi_out.send(note_off_msg)
            except Exception as e:
                print(f"Error al limpiar nota: {e}")
        
        self.active_notes = {}
        return notes_to_stop
