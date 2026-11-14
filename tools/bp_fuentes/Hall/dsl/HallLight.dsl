(fn HallLight (Lit)
  (Utilities|IsValid (Variables|Default|GetLights)
    (:"Is Valid"
      (if Lit
        (Class|BPHallLightsSC|LightsOn (Variables|Default|GetLights))
        (else (Class|BPHallLightsSC|LightsOff (Variables|Default|GetLights)))))
    (:"Is Not Valid")))