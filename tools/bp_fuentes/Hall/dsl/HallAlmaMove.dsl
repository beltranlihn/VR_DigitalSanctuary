(fn HallAlmaMove (Tag)
  (Utilities|IsValid (Variables|Default|GetAlma)
    (:"Is Valid" (Class|BPAlmaSC|MoveTo (Variables|Default|GetAlma) :PointTag Tag))
    (:"Is Not Valid")))