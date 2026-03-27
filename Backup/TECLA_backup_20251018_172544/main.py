# TECLA AMB MIDI

# =============================================================================
# IMPORTACIONES DE LIBRERÍAS
# =============================================================================
import time  # Para control de tiempo y delays
import random  # Para generación de números aleatorios
import math  # Para funciones matemáticas (seno, coseno, etc.)
import board  # Para acceso a pines de la Raspberry Pi Pico
import busio  # Para comunicación I2C
import digitalio  # Para control de pines digitales
import analogio  # Para lectura de pines analógicos
import pwmio  # Para generación de señales PWM
import usb_midi  # Para comunicación MIDI por USB
from adafruit_midi import MIDI  # Librería MIDI
from adafruit_midi.note_on import NoteOn  # Mensaje MIDI Note On
from adafruit_midi.note_off import NoteOff  # Mensaje MIDI Note Off
from adafruit_ssd1306 import SSD1306_I2C  # Controlador pantalla OLED

# =============================================================================
# CONFIGURACIÓN DE HARDWARE - ENTRADAS/SALIDAS
# =============================================================================

# Configuración MIDI - canal de salida 0
midi = MIDI(midi_out=usb_midi.ports[1], out_channel=0)

# Configuración de salidas PWM para generación de audio
pwm1 = pwmio.PWMOut(board.GP0, frequency=440, duty_cycle=80, variable_frequency=True)
pwm2 = pwmio.PWMOut(board.GP2, frequency=440, duty_cycle=80, variable_frequency=True)
pwm3 = pwmio.PWMOut(board.GP22, frequency=440, duty_cycle=80, variable_frequency=True)

# Salida jack - control de gate/trigger
out_jack = digitalio.DigitalInOut(board.GP1)
out_jack.direction = digitalio.Direction.OUTPUT
out_jack.value = False

# =============================================================================
# CONFIGURACIÓN DE BOTONES - ENTRADAS DIGITALES
# =============================================================================

# Botones de la cruceta (navegación principal)
boton_crueta_1 = digitalio.DigitalInOut(board.GP13)  # Subir octava
boton_crueta_1.direction = digitalio.Direction.INPUT
boton_crueta_1.pull = digitalio.Pull.DOWN

boton_crueta_2 = digitalio.DigitalInOut(board.GP14)  # Bajar octava
boton_crueta_2.direction = digitalio.Direction.INPUT
boton_crueta_2.pull = digitalio.Pull.DOWN

boton_crueta_3 = digitalio.DigitalInOut(board.GP15)  # Loop mode anterior
boton_crueta_3.direction = digitalio.Direction.INPUT
boton_crueta_3.pull = digitalio.Pull.DOWN

boton_crueta_4 = digitalio.DigitalInOut(board.GP3)   # Loop mode siguiente
boton_crueta_4.direction = digitalio.Direction.INPUT
boton_crueta_4.pull = digitalio.Pull.DOWN

# Botones extras (funciones especiales)
boton_extra_1 = digitalio.DigitalInOut(board.GP5)    # Cambiar configuración
boton_extra_1.direction = digitalio.Direction.INPUT
boton_extra_1.pull = digitalio.Pull.DOWN

boton_extra_2 = digitalio.DigitalInOut(board.GP4)    # Reset/parada total
boton_extra_2.direction = digitalio.Direction.INPUT
boton_extra_2.pull = digitalio.Pull.DOWN

# Lista de todos los botones para acceso fácil
buttons = [
    boton_crueta_1, boton_crueta_2, boton_crueta_3, 
    boton_crueta_4, boton_extra_1, boton_extra_2
]

# =============================================================================
# CONFIGURACIÓN DE POTENCIÓMETROS - ENTRADAS ANALÓGICAS
# =============================================================================

# Potenciómetros (slider, CV2/LDR, CV1/POTE)
pote_velocidad = analogio.AnalogIn(board.GP26)  # Slider - control principal de tempo
pote_analog_2 = analogio.AnalogIn(board.GP27)   # CV2/LDR - parámetros musicales
pote_analog_1 = analogio.AnalogIn(board.GP28)   # CV1/POTE - control de BPM (20-220)

potes = [pote_analog_1, pote_analog_2, pote_velocidad]  # Índices: 0, 1, 2

# =============================================================================
# CONFIGURACIÓN DE LEDs - SALIDAS VISUALES
# =============================================================================

led_1 = digitalio.DigitalInOut(board.GP10)  # Indicador freq1 activa (!= 0)
led_1.direction = digitalio.Direction.OUTPUT
led_1.value = False

led_2 = digitalio.DigitalInOut(board.GP6)  # LED que reproduce out_jack.value
led_2.direction = digitalio.Direction.OUTPUT
led_2.value = False

led_3 = digitalio.DigitalInOut(board.GP8)  # Indicador de modo activo / display config
led_3.direction = digitalio.Direction.OUTPUT
led_3.value = False

led_4 = digitalio.DigitalInOut(board.GP9)  # Indicador freq2 activa (!= 0)
led_4.direction = digitalio.Direction.OUTPUT
led_4.value = False

led_5 = digitalio.DigitalInOut(board.GP7) # Indicador duty activo (!= 0)
led_5.direction = digitalio.Direction.OUTPUT
led_5.value = False

led_6 = digitalio.DigitalInOut(board.GP11) # Indicador de modo activo / display config
led_6.direction = digitalio.Direction.OUTPUT
led_6.value = False

led_7 = digitalio.DigitalInOut(board.GP12) # Indicador de modo activo / display config
led_7.direction = digitalio.Direction.OUTPUT
led_7.value = False

leds = [led_1, led_2, led_3, led_4, led_5, led_6, led_7]

# =============================================================================
# VARIABLES GLOBALES DEL SISTEMA
# =============================================================================

# Control de octava y modos especiales
octava = 0        # Rango: -1 a 8
octava_new = 0    # Octava temporal para modo caos
kidmos = 0        # Contador para modos especiales
caos = 0          # Modo caótico (0=normal, 1=caótico)
caos_note = 0     # Nota aleatoria para modo caos
rio_base = 64     # Base para algoritmo Río

# Estados del sistema
loop_mode = 0     # Modo de operación actual (0-8)
configout = 0     # Configuración de salida (0=loop, 1=duty, 2=freq1, 3=freq2)
last_interaction_time = time.monotonic()  # Tiempo de última interacción

# Control de armonías y duty cycles
dutyharm = 0      # Tipo de duty cycle para armónicos (0-7)
freqharm1 = 0     # Primer intervalo armónico (0-8)  
freqharm2 = 0     # Segundo intervalo armónico (0-8)

# Variables de tiempo y secuencia
iteration = 0     # Contador general de iteraciones
position = 0      # Posición en secuencias rítmicas
playing_notes = set()  # Conjunto de notas activas
nota_actual = 0   # Nota MIDI actualmente sonando

# Control de visualización
show_config_mode = False  # Modo de visualización de configuración
config_display_timer = 0  # Temporizador para modo visualización

# Estados para algoritmos específicos
state_harmony = {
    'previous_note': 60,
    'last_profile': 0,
    'last_tension': 0,
    'initialized': False
}

# =============================================================================
# CONFIGURACIÓN DE LA PANTALLA OLED
# =============================================================================

i2c = busio.I2C(scl=board.GP21, sda=board.GP20)  # Configuración I2C
display = SSD1306_I2C(128, 64, i2c, addr=0x3C)   # Inicialización pantalla OLED
display.fill(0)  # Limpiar pantalla
display.show()   # Actualizar pantalla

# =============================================================================
# FUNCIONES DE VISUALIZACIÓN - PANTALLA OLED
# =============================================================================

def draw_cfg_icon(x=110, y=0):
    """Icono pequeño indicando qué se está configurando (configout)"""
    display.fill_rect(x-2, y, 18, 8, 0)  # Limpiar área
    display.rect(x-2, y, 18, 8, 1)       # Dibujar marco
    # Iconos según configout
    if configout == 0:  # Loop
        display.text("L", x, y, 1)
        display.hline(x+8, y+6, 6, 1)
    elif configout == 1:  # Duty
        display.text("D", x, y, 1)
        display.vline(x+9, y+1, 6, 1)
    elif configout == 2:  # H1
        display.text("H1", x, y, 1)
    elif configout == 3:  # H2
        display.text("H2", x, y, 1)

def draw_mod_icon(x=110, y=10):
    """Símbolo del modo activo en 16x12 aprox"""
    display.fill_rect(x-2, y, 18, 12, 0)  # Limpiar área
    display.rect(x-2, y, 18, 12, 1)       # Dibujar marco
    
    # Símbolos según loop_mode
    if loop_mode == 1:  # Fractal
        for i in range(6):
            display.hline(x-1+i*3, y+2+(i%2), 2, 1)
    elif loop_mode == 2:  # Río
        for i in range(0, 16, 3):
            display.hline(x-2+i, y+3+int(2*math.sin(i)), 3, 1)
    elif loop_mode == 3:  # Tormenta
        display.vline(x+6, y+1, 8, 1)
        display.hline(x+2, y+5, 10, 1)
        display.text("*", x+11, y+2, 1)
    elif loop_mode == 4:  # Armonía
        display.text("♪", x+3, y+2, 1)
    elif loop_mode == 5:  # Bosque
        display.vline(x+4, y+2, 8, 1)
        display.hline(x+2, y+6, 5, 1)
        display.text(".", x+10, y+3, 1)
    elif loop_mode == 6:  # Escala CV
        display.hline(x, y+4, 14, 1)
        display.vline(x+4, y+2, 6, 1)
        display.vline(x+9, y+2, 6, 1)
    elif loop_mode == 7:  # Euclidiano
        for i in range(5):
            display.fill_rect(x+2+i*3, y+8-(i%2)*4, 2, 3, 1)
    elif loop_mode == 8:  # Cosmos
        display.circle(x+8, y+6, 4, 1)
        display.text(".", x+2, y+3, 1)
        display.text(".", x+13, y+9, 1)

def draw_duty_meter(x=110, y=20):
    """Barra mini que refleja dutyharm (0–7)"""
    display.fill_rect(x-2, y, 18, 8, 0)  # Limpiar área
    display.rect(x-2, y, 18, 8, 1)       # Dibujar marco
    length = int((dutyharm / 7) * 14)     # Calcular longitud
    display.fill_rect(x, y+2, max(1, length), 4, 1)  # Dibujar barra

def animacion_inicio_espectacular():
    """Animación de inicio coordinada entre LEDs y pantalla"""
    display.fill(0)
    display.show()

    # Fase 1: Encendido en espiral
    orden_leds = [led_3, led_6, led_4, led_5, led_1, led_7]
    for led in orden_leds:
        led.value = True
        display.fill(0)
        display.text("CHIPTUNE", 25, 25, 1)
        display.show()
        time.sleep(0.2)
        led.value = False
        led_2.value = True
        led.value = True
        display.fill(0)
        display.text("CHIPTUNE", 25, 25, 1)
        display.show()
        time.sleep(0.2)
        led_2.value = True
        led.value = False

    # Fase 2: Onda radial desde el centro
    for i in range(3):
        display.fill(0)
        display.circle(64, 32, 5 + i*5, 1)  # Círculo que crece
        display.show()
        time.sleep(0.2)
        # Periféricos ON en eco
        for led in [led_3, led_6, led_4, led_5, led_1, led_7]:
            led.value = True
            time.sleep(0.05)
            led.value = False

    # Fase 3: Final coordinado
    for i in range(6):
        estado = (i % 2 == 0)
        for led in [led_1, led_3, led_4, led_5, led_6, led_7, led_2]:
            led.value = estado
        display.fill(0)
        display.text("READY", 40, 25, 1)
        if estado:
            display.text("CHIPTUNE ACTIVE", 10, 45, 1)
        display.show()
        time.sleep(0.3)

    # Apagar todo
    for led in [led_1, led_3, led_4, led_5, led_6, led_7, led_2]:
        led.value = False
    display.fill(0)
    display.show()

def mostrar_info_loop_mode():
    """Muestra en pantalla OLED: config actual, nombres de parámetros, nota y octava"""
    
    # Si el modo caos está activo, mostrar rayo y salir
    if caos == 1:
        dibujar_rayo()
        return
    
    # Si estamos en modo parado (loop_mode = 0), mostrar animación de ojo
    if loop_mode == 0:
        animacion_ojo()
        return

    # Diccionario de nombres
    loop_names = {
        1: "Fractal", 2: "Rio", 3: "Tormenta", 4: "Armonia",
        5: "Bosque", 6: "Escala CV", 7: "Euclidiano", 8: "Cosmos"
    }
    
    duty_names = {
        0: "Normal", 1: "75/50/30", 2: "90/50/25", 3: "100/75/50",
        4: "40/30/20", 5: "150/100/25", 6: "75/50/40", 7: "200/25/10"
    }
    
    harmonic_names = {
        0: "Unisono", 1: "Octava", 2: "Quinta", 3: "Cuarta",
        4: "Tercera M", 5: "Tercera m", 6: "Sexta M", 7: "Septima", 8: "Tritono"
    }

    # Limpiar pantalla
    display.fill(0)

    # Línea 1: Configuración actual
    config_names = ["Loop", "Duty", "H1", "H2"]
    config_text = f"Cfg: {config_names[configout]}"
    display.text(config_text, 0, 0, 1)

    # Línea 2: Loop actual por nombre
    loop_text = f"Mod: {loop_names.get(loop_mode, 'Desconocido')}"
    display.text(loop_text, 0, 10, 1)

    # Línea 3: Duty por nombre
    duty_text = f"Dty: {duty_names.get(dutyharm, 'Desconocido')}"
    display.text(duty_text, 0, 20, 1)

    # Obtener valores analógicos en voltios
    cv1_val = get_voltage(pote_velocidad)  # CV1 en voltios
    cv2_val = get_voltage(pote_analog_2)   # CV2 en voltios

    # Línea 4: H1 + CV1
    harm1_text = f"H1: {harmonic_names.get(freqharm1, '---')}"
    cv1_text   = f"CV1:{cv1_val:0.2f}V"
    display.text(harm1_text, 0, 30, 1)
    display.text(cv1_text,   70, 30, 1)

    # Línea 5: H2 + CV2
    harm2_text = f"H2: {harmonic_names.get(freqharm2, '---')}"
    cv2_text   = f"CV2:{cv2_val:0.2f}V"
    display.text(harm2_text, 0, 40, 1)
    display.text(cv2_text,   70, 40, 1)
    
    # Línea 6: Nota actual y octava
    note_name = midi_to_note_name(nota_actual)
    display.text(f"Nota: {note_name}", 0, 50, 1)
    oct_text = f"Oct: {octava}"
    display.text(oct_text, 70, 50, 1)

    # Dibujar iconos
    draw_cfg_icon(100, 0)
    draw_mod_icon(100, 10)
    draw_duty_meter(100, 20)
    display.show()

def animacion_ojo():
    """Animación de ojo con expresividad según duty, H1 y H2"""
    display.fill(0)
    tiempo_actual = time.monotonic()
    fase = int((tiempo_actual % 4.0) * 2)  # 8 fases de 0.5s

    centro_x, centro_y = 64, 32
    radio_ojo = 15

    # Dibujar contorno del ojo
    display.circle(centro_x, centro_y, radio_ojo, 1)

    # Determinar posición de la pupila según fase
    if fase == 0 or fase == 7:  # Mirando al frente
        pupila_x, pupila_y = centro_x, centro_y
    elif fase == 1 or fase == 4:  # Parpadeo
        display.hline(centro_x - radio_ojo, centro_y, radio_ojo * 2, 1)
        pupila_x, pupila_y = centro_x, centro_y
    elif fase == 2 or fase == 3:  # Mirando a la izquierda
        pupila_x, pupila_y = centro_x - 8, centro_y
    elif fase == 5 or fase == 6:  # Mirando a la derecha
        pupila_x, pupila_y = centro_x + 8, centro_y

    # Dibujar pupila (si no está parpadeando)
    if fase not in [1, 4]:
        display.circle(pupila_x, pupila_y, 5, 1)

    # Símbolos complementarios según configuraciones activas
    if dutyharm != 0:
        display.text("db", centro_x - 5, centro_y + 20, 1)   # vibración arriba
    if freqharm1 != 0:
        display.text("o", centro_x - 23, centro_y, 1)       # chispa izquierda
    if freqharm2 != 0:
        display.text("o", centro_x + 18, centro_y, 1)       # chispa derecha
    if (dutyharm != 0) + (freqharm1 != 0) + (freqharm2 != 0) > 2:
        display.text("www", centro_x - 9, centro_y -20, 1)   # emoción extra
    if (dutyharm != 0) + (freqharm1 != 0) + (freqharm2 != 0) > 1:
        display.text("o", centro_x +23, centro_y +1, 1)   # emoción extra
        display.text("o", centro_x -28, centro_y +1, 1)   # emoción extra

    display.show()

def animacion_gameboy():
    """Animación de consola Game Boy con movimiento oscilante"""
    display.fill(0)
    t = time.monotonic()
    # Oscilación horizontal suave
    offset_x = int(math.sin(t * 0.8) * 20)  # se mueve entre -20 y +20 px
    base_x = 40 + offset_x  # posición base horizontal
    base_y = 10             # posición vertical fija

    # Marco de la consola
    display.rect(base_x, base_y, 48, 64-10, 1)  # cuerpo rectangular

    # Pantalla
    display.rect(base_x+6, base_y+4, 36, 24, 1)

    # Cruceta (D-pad)
    cx, cy = base_x+12, base_y+36
    display.vline(cx, cy-3, 7, 1)
    display.hline(cx-3, cy, 7, 1)

    # Botones A y B
    display.circle(base_x+32, base_y+36, 2, 1)  # botón A
    display.circle(base_x+38, base_y+30, 2, 1)  # botón B

    # Start y Select (dos rayitas)
    display.hline(base_x+18, base_y+46, 6, 1)
    display.hline(base_x+28, base_y+46, 6, 1)

    display.show()

def dibujar_rayo():
    """Dibuja una animación de rayo para el modo caos"""
    display.fill(0)
    
    # Coordenadas base para el rayo
    x_center = 64
    y_start = 0
    y_end = 64
    
    # Añadir ramificaciones del rayo
    for branch in range(6):
        branch_x = x_center + random.randint(-60, 60)
        for i in range(0, 60, 2):
            offset = int(4 * math.sin(iteration * 0.3 + i * 0.2))
            display.vline(branch_x + offset, 10 + i, 15, 1)
    
    # Mostrar la nota actual en el centro, más grande
    note_text = midi_to_note_name(nota_actual)
    
    # Calcular posición para centrar el texto
    text_width = len(note_text) * 6  # Cada carácter tiene 6 píxeles de ancho
    text_x = (128 - text_width) // 2
    text_y = 20  # Posición vertical
    
    # Dibujar fondo para mejor legibilidad
    display.fill_rect(text_x - 2, text_y - 2, text_width + 4, 10, 0)
    
    # Dibujar la nota más grande (dibujando dos veces con desplazamiento)
    display.text(note_text, text_x, text_y, 1)
    display.text(note_text, text_x + 1, text_y, 1)
    display.text(note_text, text_x, text_y + 1, 1)
    
    # Texto "CAOS" debajo
    caos_text = "uWu"
    caos_width = len(caos_text) * 6
    caos_x = (128 - caos_width) // 2
    display.text(caos_text, caos_x, 40, 1)
    
    display.show()

# =============================================================================
# FUNCIONES DE PROCESAMIENTO DE SEÑALES ANALÓGICAS
# =============================================================================

def get_voltage(pin):
    """Convierte valor ADC a voltaje (0-3.3V)"""
    return (pin.value * 3.3) / 65536

# Rangos y escalas para conversión
pot_min, pot_max = 0.0, 3.3
step = (pot_max - pot_min) / 127.0        # Escala completa MIDI (0-127)
step_melo = (pot_max - pot_min) / 10.0    # Escala melódica
step_escala = (pot_max - pot_min) / 6.0   # Escala melódica
step_control = (pot_max - pot_min) / 50.0 # Control general
step_nota = (pot_max - pot_min) / 23.0    # Notas musicales
step_ritme = (pot_max - pot_min) / 36.0   # Ritmos y patrones

def steps(voltage):
    """Escala voltaje a rango MIDI 0-127"""
    return round((voltage - pot_min) / step)

def steps_melo(voltage):
    """Escala voltaje para parámetros melódicos"""
    return round((voltage - pot_min) / step_melo)

def steps_escala(voltage):
    """Escala voltaje para parámetros escala"""
    return round((voltage - pot_min) / step_escala)

def steps_control(voltage):
    """Escala voltaje para control general"""
    return round((voltage - pot_min) / step_control)

def steps_nota(voltage):
    """Escala voltaje para selección de notas"""
    return round((voltage - pot_min) / step_nota)

def steps_ritme(voltage):
    """Escala voltaje para parámetros rítmicos"""
    return round((voltage - pot_min) / step_ritme)

def map_value(value, in_min, in_max, out_min, out_max):
    """Mapea un valor de un rango a otro"""
    return out_min + (float(value - in_min) * (out_max - out_min) / (in_max - in_min))

def voltage_to_bpm(voltage):
    """Convierte voltaje a BPM (20-220 BPM)"""
    return map_value(voltage, pot_min, pot_max, 20, 220)

def bpm_to_sleep_time(bpm):
    """Convierte BPM a tiempo de sleep en segundos"""
    return 30.0 / bpm

def get_bpm_from_pot():
    """Obtiene el BPM actual del potenciómetro GP28"""
    voltage = get_voltage(pote_analog_1)
    bpm = voltage_to_bpm(voltage)
    return bpm

def get_sleep_time_from_bpm():
    """Obtiene el tiempo de sleep basado en el BPM actual"""
    bpm = get_bpm_from_pot()
    sleep_time = bpm_to_sleep_time(bpm)
    return sleep_time

def boton_presionado(boton, tiempo_espera=0.05, tiempo_post_accion=0.15):
    """Verifica si un botón fue presionado con debounce y pausa adicional"""
    if boton.value:
        time.sleep(tiempo_espera)
        if boton.value:
            time.sleep(tiempo_post_accion)
            return True
    return False

def midi_to_note_name(midi_note):
    """Convierte nota MIDI a nombre de nota (ej: 60 -> C4)"""
    if midi_note == 0:
        return "---"
    
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = (midi_note // 12) - 1
    note_index = midi_note % 12
    return f"{note_names[note_index]}{octave}"

# =============================================================================
# FUNCIONES DE GENERACIÓN MUSICAL
# =============================================================================

def generar_ritmo_euclideo(pulsos, pasos):
    """Genera patrón rítmico euclidiano"""
    if pasos <= 0:
        return [0]
    if pulsos > pasos:
        pulsos = pasos
    grupos = [[1] for _ in range(pulsos)] + [[0] for _ in range(pasos - pulsos)]
    while len(grupos) > 1:
        nuevos_grupos = []
        for i in range(0, len(grupos) // 2):
            nuevos_grupos.append(grupos[i] + grupos[-(i + 1)])
        if len(grupos) % 2 == 1:
            nuevos_grupos.append(grupos[len(grupos) // 2])
        grupos = nuevos_grupos
    return [item for sublist in grupos for item in sublist]

def mandelbrot_to_midi(cx, cy, max_iter=200):
    """Convierte coordenadas Mandelbrot a nota MIDI"""
    x, y = 0.0, 0.0
    iteration = 0
    while x*x + y*y <= 4 and iteration < max_iter:
        x_new = x*x - y*y + cx
        y = 2*x*y + cy
        x = x_new
        iteration += 1
    return iteration % 60 + 32

def sinusoidal_value_2(iteration, ampli, base_frequency):
    """Genera valor sinusoidal para modulación"""
    min_value, max_value = 0, 127
    amplitude = ampli / 2
    offset = (max_value + min_value) / 2
    modulated_frequency = base_frequency * (1 + 63/255)
    phase = iteration * modulated_frequency
    value = amplitude * math.sin(phase) + offset
    return max(min(round(value), max_value), min_value)

def harmonic_next_note(x, y, previous_note=0):
    """Genera siguiente nota basada en armonía"""
    intervals = {
        0: [3, 4, 7, 12],
        1: [2, 5, 9, 16],
        2: [1, 6, 11, 19],
        3: [8, 14, 17, 23],
        4: [10, 15, 20, 24],
        5: [13, 18, 21, 22]
    }
    
    harmonic_profile = min(x // 21, 5)
    tension = min(y // 32, 3)
    selected_interval = intervals[harmonic_profile][tension]
    direction = 1 if (x ^ y) % 2 else -1
    base_note = previous_note + (direction * selected_interval)
    harmonic_variation = int((x % 16) - (y % 16))
    final_note = (base_note + harmonic_variation) % 128
    return max(0, min(final_note, 127))

# =============================================================================
# FUNCIONES DE GESTIÓN DE NOTAS MIDI
# =============================================================================

def midi_to_frequency(midi_note):
    """Convierte nota MIDI a frecuencia en Hz"""
    return round(440 * (2 ** ((midi_note - 69) / 12)))

def apply_harmonic_interval(note, harmonic_type):
    """Aplica intervalo armónico a nota MIDI"""
    if harmonic_type == 0:
        harmonic = 0
    elif harmonic_type == 1:
        harmonic = 12
    elif harmonic_type == 2:
        harmonic = 7
    elif harmonic_type == 3:
        harmonic = 5
    elif harmonic_type == 4:
        harmonic = 4
    elif harmonic_type == 5:
        harmonic = 3
    elif harmonic_type == 6:
        harmonic = 9
    elif harmonic_type == 7:
        harmonic = 10
    elif harmonic_type == 8:
        harmonic = 6  # tritono
    else:
        harmonic = 0
        
    nota_modificada = note + harmonic
    if nota_modificada >= 127:
        nota_modificada = note
    return nota_modificada

def play_note_full(note, play, octava, periode, duty=dutyharm, freq1=freqharm1, freq2=freqharm2):
    """Reproduce una nota completa con MIDI, PWM y control visual"""
    global nota_actual
    nota_actual = note

    # Silencio: no gate, no LED2
    if play == 0 or note == 0:
        out_jack.value = False
        led_2.value = False
        return

    # --- Pulso visual breve al inicio ---
    out_jack.value = False
    led_2.value = False
    time.sleep(0.02)  # pulso fijo de 20ms, no depende de la nota
    out_jack.value = True
    led_2.value = True

    # --- Nota MIDI ---
    midi.send(NoteOn(note, 100))
    playing_notes.add(note)
    time.sleep(periode / 200)  # duración real de la nota
    midi.send(NoteOff(note, 100))

    # --- Armónicos y PWM ---
    note1 = note
    note2 = apply_harmonic_interval(note, freq1)
    note3 = apply_harmonic_interval(note, freq2)

    base_freq = midi_to_frequency(note1)
    freq2_val = midi_to_frequency(note2)
    freq3_val = midi_to_frequency(note3)

    # Duty cycles predefinidos
    duty_cycles = {
        0: (32768, 32768, 32768),
        1: (32768, 26214, 19661),
        2: (45875, 32768, 16384),
        3: (52428, 39321, 26214),
        4: (26214, 19661, 13107),
        5: (49152, 32768, 8192),
        6: (39321, 32768, 26214),
        7: (65000, 16384, 4096)
    }
    duty_cycle1, duty_cycle2, duty_cycle3 = duty_cycles.get(duty, (32768, 32768, 32768))

    # Aplicar frecuencias y duty cycles a los PWM
    pwm1.frequency = base_freq
    pwm2.frequency = freq2_val
    pwm3.frequency = freq3_val
    pwm1.duty_cycle = duty_cycle1
    pwm2.duty_cycle = duty_cycle2
    pwm3.duty_cycle = duty_cycle3

def stop_all_notes():
    """Detiene todas las notas activas"""
    for note in playing_notes:
        midi.send(NoteOff(note, 0))
    playing_notes.clear()

# =============================================================================
# FUNCIONES DE VISUALIZACIÓN CON LEDs
# =============================================================================

def update_config_indicators():
    """Actualiza LEDs que indican configuraciones no por defecto"""
    led_5.value = (dutyharm != 0)  # Duty cycle activo
    led_1.value = (freqharm1 != 0) # Frecuencia armónica 1 activa
    led_4.value = (freqharm2 != 0) # Frecuencia armónica 2 activa

def display_configuration_mode():
    """Muestra la configuración actual en los LEDs 6, 3, 7"""
    led_6.value = False
    led_3.value = False  
    led_7.value = False
    
    if configout == 0:
        display_value(loop_mode, 8)  # Mostrar loop mode
    elif configout == 1:
        display_value(dutyharm, 7)   # Mostrar duty cycle
    elif configout == 2:
        display_value(freqharm1, 8)  # Mostrar armónico 1
    elif configout == 3:
        display_value(freqharm2, 8)  # Mostrar armónico 2

def display_value(value, max_value):
    """Muestra un valor en los LEDs 6, 3, 7 usando codificación binaria"""
    normalized_value = int((value / max_value) * 7)
    led_6.value = (normalized_value & 4) != 0  # Bit 2
    led_3.value = (normalized_value & 2) != 0  # Bit 1  
    led_7.value = (normalized_value & 1) != 0  # Bit 0

def update_loop_mode_indicators():
    """Actualiza LEDs indicadores del loop_mode actual"""
    if loop_mode == 1:
        led_6.value, led_7.value, led_3.value = False, False, False
    elif loop_mode == 2:
        led_6.value, led_7.value, led_3.value = False, False, True
    elif loop_mode == 3:
        led_6.value, led_7.value, led_3.value = False, True, False
    elif loop_mode == 4:
        led_6.value, led_7.value, led_3.value = False, True, True
    elif loop_mode == 5:
        led_6.value, led_7.value, led_3.value = True, False, False
    elif loop_mode == 6:
        led_6.value, led_7.value, led_3.value = True, False, True
    elif loop_mode == 7:
        led_6.value, led_7.value, led_3.value = True, True, False
    elif loop_mode == 8:
        led_6.value, led_7.value, led_3.value = True, True, True
    else:
        led_6.value, led_7.value, led_3.value = False, False, False

# =============================================================================
# LOOP PRINCIPAL
# =============================================================================

animacion_inicio_espectacular()  # Ejecutar animación de inicio

while True:
    # Mostrar información o animación según estado
    if time.monotonic() - last_interaction_time > 60:  # 60 segundos sin tocar nada
        animacion_gameboy()
    else:
        mostrar_info_loop_mode()

    # Leer valores de potenciómetros
    pot_values = [get_voltage(pote) for pote in potes]
    x, y, z = pot_values
    
    # Calcular BPM y tiempo de sleep
    current_bpm = get_bpm_from_pot()
    sleep_time = get_sleep_time_from_bpm()
    
    # Generar ritmo euclidiano
    ritmo = generar_ritmo_euclideo(steps_ritme(y), steps_ritme(z)+1)
    to = random.randint(0, 1)
    caos_note = random.randint(0, 1)
    
    # Mapear valores para Mandelbrot
    cx = map_value(potes[1].value, 0, 65535, -1.5, 1.5)
    cy = map_value(potes[2].value, 0, 65535, -1.5, 1.5)
    
    # Control de modo de visualización de configuración
    if show_config_mode:
        config_display_timer += 1
        if config_display_timer > 50:
            show_config_mode = False
            config_display_timer = 0

    # Modo parada (loop_mode = 0)
    if loop_mode == 0:
        duty_cycle = 0
        out_jack.value = False
        led_2.value = False
        pwm1.duty_cycle = duty_cycle
        pwm2.duty_cycle = duty_cycle
        pwm3.duty_cycle = duty_cycle
        time.sleep(sleep_time / 5)

    # --- DETECCIÓN DE BOTONES ---
    
    # Botón extra 1: Cambiar configuración
    if boton_presionado(boton_extra_1):
        last_interaction_time = time.monotonic()
        configout = (configout + 1) % 4
        show_config_mode = True
        config_display_timer = 0

    # Botón extra 2: Reset/parada total
    if boton_presionado(boton_extra_2):
        last_interaction_time = time.monotonic()
        loop_mode = 0
        stop_all_notes()
        iteration = 0
        caos = 0
        configout = 0
        for led in leds:
            led.value = False

    # Botón cruceta 1: Subir octava o activar modo especial
    if boton_presionado(boton_crueta_1):
        last_interaction_time = time.monotonic()
        if octava < 8:
            octava += 1
            kidmos = caos = 0
        else:
            kidmos += 1
            if kidmos >= 5: kidmos = caos = 0
            elif kidmos >= 3: caos = 1

    # Botón cruceta 2: Bajar octava o activar modo especial  
    if boton_presionado(boton_crueta_2):
        last_interaction_time = time.monotonic()
        if octava > 0:
            octava -= 1
            kidmos = caos = 0
        else:
            kidmos += 1
            if kidmos >= 5: kidmos = caos = 0
            elif kidmos >= 3: caos = 1

    # Botón cruceta 3: Decrementar valor actual
    if boton_presionado(boton_crueta_3):
        last_interaction_time = time.monotonic()
        if configout == 0:
            loop_mode = (loop_mode - 1)
            if loop_mode < 1:
                loop_mode = 8
        elif configout == 1:
            dutyharm = (dutyharm - 1) % 8
        elif configout == 2:
            freqharm1 = (freqharm1 - 1) % 9
        elif configout == 3:
            freqharm2 = (freqharm2 - 1) % 9

        show_config_mode = True
        config_display_timer = 0
        stop_all_notes()

    # Botón cruceta 4: Incrementar valor actual
    if boton_presionado(boton_crueta_4):
        last_interaction_time = time.monotonic()
        if configout == 0:
            loop_mode = (loop_mode + 1)
            if loop_mode > 8:
                loop_mode = 1
        elif configout == 1:
            dutyharm = (dutyharm + 1) % 8
        elif configout == 2:
            freqharm1 = (freqharm1 + 1) % 9
        elif configout == 3:
            freqharm2 = (freqharm2 + 1) % 9

        show_config_mode = True
        config_display_timer = 0
        stop_all_notes()
    
    # Actualizar indicadores LED
    if show_config_mode:
        display_configuration_mode()
    else:
        update_loop_mode_indicators()
    
    update_config_indicators()

    # --- EJECUCIÓN DE MODOS DE LOOP ---
    
    # LOOP 1: MANDELBROT
    if loop_mode == 1:
        note = mandelbrot_to_midi(cx, cy)
        if caos == 1:
            octava_new = random.randint(0,8)
            play_note_full(note, 1, octava_new, sleep_time * 20, dutyharm, freqharm1, freqharm2)
            if caos_note == 0:
                note = 0
            else:
                play_note_full(note, 1, octava_new, sleep_time * 20, dutyharm, freqharm1, freqharm2)
        
        play_note_full(note, 1, octava, sleep_time * 20, dutyharm, freqharm1, freqharm2)

    # LOOP 2: RÍO
    elif loop_mode == 2:
        corriente = steps_control(y) / 25
        turbulencia = steps(z)
        rio_time = time.time()

        # Rango de la octava actual
        nota_min = 12 * octava
        nota_max = nota_min + 11

        # Base del río: avanza dentro de la octava
        rio_base = (rio_base + corriente) % 12
        nota_base = nota_min + rio_base

        # Ondas y turbulencias
        wave = math.sin(rio_time * 0.8) * (corriente * 0.5)
        ripple = math.cos(rio_time * 2.2) * (turbulencia * 0.3)
        random_offset = random.uniform(-corriente * 0.2, turbulencia * 0.2)

        # Nota final dentro de la octava
        nota_rio = int(
            max(nota_min,
                min(nota_max, nota_base + wave + ripple + random_offset))
        )

        # Patrón de gate irregular (oleaje)
        patron_gate = [1, 1, 1, 0, 0, 1, 1, 1, 1, 0]  # 10 pasos
        gate_on = patron_gate[iteration % len(patron_gate)]

        if caos == 1:
            octava_new = random.randint(0, 8)
            if caos_note == 0:
                nota_rio = 0
            else:
                if gate_on:
                    play_note_full(nota_rio, 1, octava_new,
                                   sleep_time * 20, dutyharm, freqharm1, freqharm2)

        if gate_on:
            play_note_full(nota_rio, 1, octava, sleep_time * 20, dutyharm, freqharm1, freqharm2)
        else:
            play_note_full(nota_rio, 0, octava, sleep_time * 20, dutyharm, freqharm1, freqharm2)

    # LOOP 3: TORMENTA
    elif loop_mode == 3:
        escala_tormenta = [0, 3, 5, 7, 10]
        fuerza_viento = steps(x)
        intensidad_lluvia = steps_control(y)
        frecuencia_rayos = steps_melo(z)
        
        efecto_viento = max(0, min(63, int(fuerza_viento * 0.5)))
        nota_base = 12 * min(octava, 10) + int(intensidad_lluvia * 0.48)
        nota_base = max(0, min(127, nota_base))
        
        if random.randint(0, 1000) < (frecuencia_rayos * 100):
            direccion = 1 if random.random() > 0.3 else -1
            for i, intervalo in enumerate(escala_tormenta[::direccion]):
                multiplicador = max(1, min(3, (i+1)))
                nota_relampago = nota_base + (intervalo * direccion * multiplicador)
                nota_relampago = max(0, min(127, nota_relampago))
                if caos == 1:
                    octava_new = random.randint(0,8)
                    if caos_note == 0:
                        nota_relampago = 0
                    else:
                        play_note_full(nota_relampago, 1, octava_new, sleep_time * 20, dutyharm, freqharm1, freqharm2)
                play_note_full(nota_relampago, 1, octava, sleep_time * 20, dutyharm, freqharm1, freqharm2)
        else:
            variacion_lluvia = random.randint(-2 + frecuencia_rayos, 2 + frecuencia_rayos)
            nota_lluvia = max(0, min(127, nota_base + variacion_lluvia))
            if caos == 1:
                octava_new = random.randint(0,8)
                if caos_note == 0:
                    nota_lluvia = 0
                else: 
                    play_note_full(nota_lluvia, 1, octava_new, sleep_time * 20, dutyharm, freqharm1, freqharm2)
            else:
                play_note_full(nota_lluvia, 1, octava, sleep_time * 20, dutyharm, freqharm1, freqharm2)
            time.sleep(sleep_time * 0.5)

    # LOOP 4: ARMONÍA
    elif loop_mode == 4:
        if not state_harmony['initialized']:
            state_harmony.update({
                'previous_note': 60,
                'last_profile': 0,
                'last_tension': 0,
                'initialized': True
            })

        x_param = steps_melo(y) % 128
        y_param = steps_melo(z) % 128
        new_note = harmonic_next_note(x_param, y_param, state_harmony['previous_note'])

        # Limitar a la octava actual
        nota_min = 12 * octava
        nota_max = nota_min + 11
        new_note = max(nota_min, min(nota_max, new_note))

        if caos == 1:
            octava_new = random.randint(0, 8)
            if caos_note == 0:
                new_note = 0
            else:
                play_note_full(
                    new_note, 1, octava_new,
                    sleep_time * 20, dutyharm, freqharm1, freqharm2
                )

        state_harmony.update({
            'previous_note': new_note,
            'last_profile': min(x_param // 21, 5),
            'last_tension': min(y_param // 32, 3)
        })

        play = 1 if iteration % 2 == 0 else 0
        play_note_full(
            new_note, play, octava,
            sleep_time * 20, dutyharm, freqharm1, freqharm2
        )

        if any(btn.value for btn in buttons):
            state_harmony.update({
                'previous_note': 60,
                'last_profile': 0,
                'last_tension': 0
            })
            stop_all_notes()
            
    # LOOP 5: BOSQUE
    elif loop_mode == 5:
        densidad = int((y / 65535) * 5) + 1   # cuántas "sorpresas" por ciclo
        profundidad = int((z / 65535) * 3)    # desplaza la octava hacia abajo

        nota_min = 12 * (octava + profundidad)
        nota_max = nota_min + 11

        # Cada paso puede ser un "descubrimiento"
        if iteration % densidad == 0:
            salto = random.choice([-2, -1, 0, 1, 2, 4, 7])  # pasos pequeños o quintas
            nota_bosque = random.randint(nota_min, nota_max) + salto
        else:
            nota_bosque = random.randint(nota_min, nota_max)

        nota_bosque = max(nota_min, min(nota_max, nota_bosque))

        # Gate irregular como luciérnagas
        gate_on = random.choice([0, 1, 1])  # más probabilidad de sonar que de callar

        if caos == 1:
            octava_new = random.randint(0, 8)
            if caos_note == 0:
                nota_bosque = 0
            else:
                if gate_on:
                    play_note_full(nota_bosque, 1, octava_new,
                                   sleep_time * 20, dutyharm, freqharm1, freqharm2)
        else:
            if gate_on:
                play_note_full(nota_bosque, 1, octava,
                               sleep_time * 20, dutyharm, freqharm1, freqharm2)

    # LOOP 6: ESCALA CV
    elif loop_mode == 6:
        # Escalas mayores básicas
        escalas = {
            0: [0, 2, 4, 5, 7, 9, 11],   # C mayor
            1: [2, 4, 6, 7, 9, 11, 1],   # D mayor
            2: [4, 6, 8, 9, 11, 1, 3],   # E mayor
            3: [5, 7, 9, 10, 0, 2, 4],   # F mayor
            4: [7, 9, 11, 0, 2, 4, 6],   # G mayor
            5: [9, 11, 1, 2, 4, 6, 8],   # A mayor
            6: [11, 1, 3, 4, 6, 8, 10],  # B mayor
        }

        # CV1 selecciona tonalidad (0–6)
        tonalidad = steps_escala(z)
        escala = escalas[tonalidad]

        # CV2 controla salto de rango (1–4 pasos por ejemplo)
        salto = steps_escala(y)

        # Nota base en la octava actual
        nota_base = 12 * octava

        # Índice de la escala según la iteración
        indice = (iteration * salto) % len(escala)

        # Nota final cuantizada
        nota = nota_base + escala[indice]

        # Tocar nota
        play_note_full(nota, 1, octava, sleep_time * 10, dutyharm, freqharm1, freqharm2)

    # LOOP 7: EUCLIDIANO
    elif loop_mode == 7:
        if position >= steps_ritme(z):
            position = 0

        ritmo = generar_ritmo_euclideo(steps_ritme(y), steps_ritme(z) + 1)
        to_play = ritmo[position]
        nota_base = max(0, (octava * 12) + random.randint(-3, 3) if position > 0 else 0)
        
        if caos == 1:
            octava_new = random.randint(0,8)
            if caos_note == 0:
                nota_base = 0
            else:
                play_note_full(nota_base, to_play, octava_new, sleep_time * 20, dutyharm, freqharm1, freqharm2)
        play_note_full(nota_base, to_play, octava, sleep_time * 20, dutyharm, freqharm1, freqharm2)
        position += 1

    # LOOP 8: COSMOS
    elif loop_mode == 8:
        fractal_note = mandelbrot_to_midi(cx, cy)
        sinusoidal_note = int(sinusoidal_value_2(iteration, steps(z), steps(y) * 2 / 100))
        armonica = harmonic_next_note(steps_melo(y), steps_melo(z), fractal_note)

        base_note = (fractal_note + sinusoidal_note + armonica) // 3
        base_note = max(0, min(127, base_note))
        
        if caos == 1:
            octava = random.randint(0,8)
            if caos_note == 0:
                base_note = 0

        ritmo = generar_ritmo_euclideo(steps_ritme(y), steps_ritme(z) + 1)
        to_play = ritmo[iteration % len(ritmo)]
        play = 1 if iteration % 2 == 0 else 0
        final_play = play * to_play

        play_note_full(base_note, final_play, octava, sleep_time * 20, dutyharm, freqharm1, freqharm2)
        iteration = (iteration + 1) % 60000