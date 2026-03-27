
# Fitxer per reiniciar el dispositiu CIRCUITPY
import supervisor
import time

print("Reiniciant TECLA...")
time.sleep(0.5)
supervisor.reload()
