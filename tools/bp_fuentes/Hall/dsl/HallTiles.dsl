(fn HallTiles (Count V)
  (for _i (range Count)
    (Utilities|Array|SetArrayElem (Variables|Default|GetTileTgt) _i V :bSizeToFit true)))