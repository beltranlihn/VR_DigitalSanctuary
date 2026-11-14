;; pacer_pulse.dsl - BP_Pacer_SC.PacerPulseAudio(Dt) v2 (Beltran 2026-10-01: un pluck por segundo, distinto por fase:
;; 4 en la inhalacion, 3 en la retencion, 4 en la exhalacion, 3 en la retencion). Anclado al INICIO DE CADA FASE: el pluck k
;; de la fase f suena cuando floor((T - inicioFase) / PulseInterval) cambia (clave f*1000 + k + 1 guardada en PulseT, que
;; PacerPlay deja en 0 -> el primer pluck suena en T 0). Sonido por fase: SndPulseInhale / SndPulseHold (las dos retenciones) /
;; SndPulseExhale; si el de la fase esta vacio, SndPulse (el de antes). Solo PulseMode 0; el modo 1 queda como estaba (__MODO1__).
;; Variables en Default al escribir (las de categorias con espacio se mueven y se devuelven). Bools sin la b.
(fn PacerPulseAudio (Dt)
  (if (== (Variables|Default|GetPulseMode) 0)
      (bind _ph (Variables|Default|GetCurPhase))
      (bind _st (select (== _ph 0) 0.0 (select (== _ph 1) (Variables|Default|GetInhaleTime) (select (== _ph 2) (+ (Variables|Default|GetInhaleTime) (Variables|Default|GetHold1Time)) (+ (+ (Variables|Default|GetInhaleTime) (Variables|Default|GetHold1Time)) (Variables|Default|GetExhaleTime))))))
      (bind _k (Math|Float|Floor (/ (Math|Float|Max(Float) (- (Variables|Default|GetT) _st) 0.0) (Math|Float|Max(Float) (Variables|Default|GetPulseInterval) 0.05))))
      (bind _key (+ (+ (* 1000.0 _ph) (* 1.0 _k)) 1.0))
      (if (!= _key (Variables|Default|GetPulseT))
          (Variables|Default|SetPulseT _key)
          (bind _snd (select (== _ph 0) (Variables|Default|GetSndPulseInhale) (select (== _ph 2) (Variables|Default|GetSndPulseExhale) (Variables|Default|GetSndPulseHold))))
          (CallFunction|PacerPlaySnd :Snd (select (Utilities|IsValid _snd) _snd (Variables|Default|GetSndPulse)) :Vol (Variables|Default|GetSfxVolume)))))
