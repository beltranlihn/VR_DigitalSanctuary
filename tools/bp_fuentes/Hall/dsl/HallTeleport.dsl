(fn HallTeleport (To)
  (Transformation|SetActorLocationAndRotation :self (Variables|Default|GetPawn) :NewLocation (Transformation|GetWorldLocation :self To) :NewRotation (Math|Rotator|MakeRotator :Yaw (.yaw (Transformation|GetWorldRotation :self To))) :bSweep false :bTeleport true)
  (Variables|Default|SetWalkDur 0.0)
  (Variables|Default|SetWalkT 0.0))