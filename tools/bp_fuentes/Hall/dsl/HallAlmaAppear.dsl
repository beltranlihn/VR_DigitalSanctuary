(fn HallAlmaAppear (Tag)
  (Utilities|IsValid (Variables|Default|GetAlma)
    (:"Is Valid" (Class|BPAlmaSC|AppearAt (Variables|Default|GetAlma) :PointTag Tag))
    (:"Is Not Valid")))