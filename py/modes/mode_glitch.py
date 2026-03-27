"""
Mode Glitch - Stutter rítmic, l'error com a estètica
X: Velocitat del stutter (lent/rapid)
Y: Patró (Regular, Triplet, Accelerando, Caos, Binary)
Z: Pitch drift (0=afinat, 127=pitch bend caotic)
"""
import time, random, math
from modes.base_mode import BaseMode
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange
from adafruit_midi.pitch_bend import PitchBend

_KEYS=('C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B')
_OFF=(0,1,2,3,4,5,6,7,8,9,10,11)
_PATTERNS=(
    ((0.5,0.5),(0.5,0.5),(0.5,0.5),(0.5,0.5)),
    ((0.33,0.67),(0.33,0.67),(0.67,0.33),(0.33,0.67)),
    ((0.8,0.2),(0.6,0.4),(0.4,0.6),(0.2,0.8)),
    ((0.7,0.3),(0.1,0.9),(0.5,0.5),(0.9,0.1)),
    ((0.75,0.25),(0.25,0.75),(0.75,0.25),(0.5,0.5)),
)
_PNAMES=('Regular','Triplet','Accel','Caos','Binary')


def _non(m,n,v):
    try: msg=NoteOn(n&0x7F,max(1,min(127,v)));msg.channel=0;m.send(msg)
    except Exception: pass
def _noff(m,n):
    try: msg=NoteOff(n&0x7F,0);msg.channel=0;m.send(msg)
    except Exception: pass
def _pb(m,v):
    try: msg=PitchBend(max(-8192,min(8191,v)));msg.channel=0;m.send(msg)
    except Exception: pass


class ModeGlitch(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name="Glitch"
        self.key_idx=0;self.octave=4;self.pat_idx=0
        self.base_note=0;self.note_on=False
        self.step_dur=0.1;self.sub_step=0;self.phase='on';self.phase_end_t=0.0
        self.drift_phase=0.0;self.last_pb=0;self.pb_time=0.0
        self.active_notes=[]

    def setup(self):
        self.initialized=True;self.sub_step=0;self.phase='on';self.drift_phase=0.0
        try:
            self.midi_out.send(ControlChange(91,0))
            self.midi_out.send(ControlChange(64,0))
        except Exception: pass
        self._set_note();self.phase_end_t=time.monotonic()
        print(f"Glitch: {_PNAMES[self.pat_idx]} {_KEYS[self.key_idx]}")

    def _set_note(self):
        self.base_note=max(24,min(96,self.octave*12+_OFF[self.key_idx]))

    def _on(self,vel=90):
        if not self.note_on: _non(self.midi_out,self.base_note,vel);self.note_on=True;self.active_notes=[self.base_note]
    def _off(self):
        if self.note_on: _noff(self.midi_out,self.base_note);self.note_on=False;self.active_notes=[]

    def update(self, pot_values, button_states):
        x,y,z=pot_values;now=time.monotonic()
        self.step_dur=max(0.03,0.5-(x/127.0)*0.47)
        np=min(4,int((y/127.0)*5))
        if np!=self.pat_idx:
            self.pat_idx=np;self.sub_step=0;self.phase='on';self._off()
            print(f"Glitch: {_PNAMES[self.pat_idx]}")
        dd=z/127.0
        if dd>0.05:
            dt=now-self.pb_time;self.pb_time=now;self.drift_phase+=dt*(0.3+dd*2.0)
            pb=int(math.sin(self.drift_phase)*dd*4000+random.uniform(-dd*1500,dd*1500))
            pb=max(-8191,min(8191,pb))
            if abs(pb-self.last_pb)>100: _pb(self.midi_out,pb);self.last_pb=pb
        elif self.last_pb!=0: _pb(self.midi_out,0);self.last_pb=0
        if now>=self.phase_end_t:
            pat=_PATTERNS[self.pat_idx]
            if self.pat_idx==3: fo=random.uniform(0.05,0.95);ff=1.0-fo
            else: fo,ff=pat[self.sub_step%len(pat)]
            if self.phase=='on':
                self._on(random.randint(75,110));self.phase_end_t=now+self.step_dur*fo;self.phase='off'
            else:
                self._off();self.phase_end_t=now+self.step_dur*ff;self.phase='on'
                self.sub_step=(self.sub_step+1)%len(pat)
        return {'key':_KEYS[self.key_idx],'pat':_PNAMES[self.pat_idx]}

    def stop(self): self.cleanup()

    def cleanup(self):
        self._off()
        try:
            _pb(self.midi_out,0)
            self.midi_out.send(ControlChange(123,0))
            self.midi_out.send(ControlChange(120,0))
        except Exception: pass
