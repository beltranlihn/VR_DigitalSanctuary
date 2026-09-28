;; BP_LovingCell_SC — fase 3 (2026-09-28): hasta 10 grupos, sin puentes por defecto, perillas SizeVariation /
;; StrandCurl, nube de particulas. Funciones NUEVAS (grafos nuevos). Empalmes por cirugia: LifeStep(ForLoop.Completed)
;; -> LifeExtra · Simulate(BridgeStep.then) -> BridgeGate · PushAll(PushCentreFilm.then) -> PushMore ·
;; PushGlobals: + LV5.

;; LifeExtra (): al final de LifeStep. (1) LV5 = (SizeVariation, StrandCurl, WaterLight, WaterLightShell) para los
;;     materiales (.z .w = luz del agua, F5 2026-09-28: WaterLight 0 = apagada, SIEMPRE 0 en niveles sin fluido;
;;     WaterLightShell = la parte de esa luz que cae en la envoltura). En el grafo real: 2 getters conectados a los
;;     pines B y A del MakeColor (cirugia; el grafo NO se reescribe).
;; (2) RMin crece con el grupo MAS grande posible (GroupScale max = 1 + 0,8*SizeVariation) y RShift se recalcula
;;     con la MISMA formula de LifeStep (bind no es asignacion: el GetRMin de SetRShift lee el valor ya escrito).
(fn LifeExtra ()
  (bind _sv (Math|Float|Max(Float) (Variables|2-Forma|GetSizeVariation) 0.0))
  (Variables|Default|SetLV5 (Math|Color|MakeColor _sv (Variables|4-Vida|GetStrandCurl) (Variables|8-Agua|GetWaterLight) (Variables|8-Agua|GetWaterLightShell)))
  (Variables|Z-Interno|SetRMin (+ (Variables|Z-Interno|GetRMin) (* (* (* 7.2 (Math|Float|Max(Float) (Variables|2-Forma|GetGroupSize) 0.05)) 0.8) _sv)))
  (bind _t8 (Math|Float|Clamp(Float) (/ (Variables|Z-Interno|GetS) 0.8) 0.0 1.0))
  (bind _ca (Variables|2-Forma|GetCenterAttraction))
  (Variables|Z-Interno|SetRShift (Math|Float|Max(Float) 0.0 (- (+ (Variables|Z-Interno|GetRMin) 1.0) (* (* (Math|Float|Lerp (Variables|2-Forma|GetDistSeparated) (* (Variables|2-Forma|GetDistConnected) (- 1.15 (* 0.15 _ca))) (* (* _t8 _t8) (- 3.0 (* 2.0 _t8)))) (Variables|2-Forma|GetGroupSpread)) 0.82)))))

;; BridgeGate (): al final de Simulate. Con bBridges apagado (default, pedido de Beltran 2026-09-28: "no hagamos
;; esa union") los puentes quedan en 0 y su estado se limpia: prenderlos despues arranca desde cero.
(fn BridgeGate ()
  (if (not (Variables|2-Forma|GetBridges))
    (Utilities|Array|Resize (Variables|Z-Interno|GetBridgeQ) 10)
    (Utilities|Array|Resize (Variables|Z-Interno|GetBridgeV) 10)
    (Utilities|Array|Resize (Variables|Z-Interno|GetBridgeL) 10)
    (Utilities|Array|Resize (Variables|Z-Interno|GetBridgeTm) 10)
    (for _b (range 10)
      (Utilities|Array|SetArrayElem (Variables|Z-Interno|GetBridgeP) _b 0.0)
      (Utilities|Array|SetArrayElem (Variables|Z-Interno|GetBridgeQ) _b 0.0)
      (Utilities|Array|SetArrayElem (Variables|Z-Interno|GetBridgeV) _b 0.0)
      (Utilities|Array|SetArrayElem (Variables|Z-Interno|GetBridgeL) _b 0.0)
      (Utilities|Array|SetArrayElem (Variables|Z-Interno|GetBridgeTm) _b 0.0))))

;; PushMore (): al final de PushAll. Grupos 6-9, M6..M9 del nucleo y su membrana, y la nube de particulas.
(fn PushMore ()
  (bind _n (Math|Integer|Clamp(Integer) (Variables|2-Forma|GetGroupCount) 1 10))
  (CallFunction|PushGroup :Index 6 :Cluster (Variables|Default|GetCluster6) :Arm (Variables|Default|GetArm6) :Bridge (Variables|Default|GetBridge6))
  (CallFunction|PushGroup :Index 7 :Cluster (Variables|Default|GetCluster7) :Arm (Variables|Default|GetArm7) :Bridge (Variables|Default|GetBridge7))
  (CallFunction|PushGroup :Index 8 :Cluster (Variables|Default|GetCluster8) :Arm (Variables|Default|GetArm8) :Bridge (Variables|Default|GetBridge8))
  (CallFunction|PushGroup :Index 9 :Cluster (Variables|Default|GetCluster9) :Arm (Variables|Default|GetArm9) :Bridge (Variables|Default|GetBridge9))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentre) "M6" (Math|Color|MakeColor (.x (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 6)) (.y (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 6)) (.z (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 6)) (select (> _n 6) 1.0 0.0)))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentre) "M7" (Math|Color|MakeColor (.x (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 7)) (.y (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 7)) (.z (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 7)) (select (> _n 7) 1.0 0.0)))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentre) "M8" (Math|Color|MakeColor (.x (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 8)) (.y (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 8)) (.z (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 8)) (select (> _n 8) 1.0 0.0)))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentre) "M9" (Math|Color|MakeColor (.x (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 9)) (.y (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 9)) (.z (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 9)) (select (> _n 9) 1.0 0.0)))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentreFilm) "M6" (Math|Color|MakeColor (.x (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 6)) (.y (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 6)) (.z (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 6)) (select (> _n 6) 1.0 0.0)))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentreFilm) "M7" (Math|Color|MakeColor (.x (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 7)) (.y (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 7)) (.z (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 7)) (select (> _n 7) 1.0 0.0)))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentreFilm) "M8" (Math|Color|MakeColor (.x (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 8)) (.y (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 8)) (.z (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 8)) (select (> _n 8) 1.0 0.0)))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentreFilm) "M9" (Math|Color|MakeColor (.x (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 9)) (.y (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 9)) (.z (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 9)) (select (> _n 9) 1.0 0.0)))
  (CallFunction|PushGlobals :Comp (Variables|Default|GetDust))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetDust) "M0" (Math|Color|MakeColor (.x (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 0)) (.y (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 0)) (.z (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 0)) (select (> _n 0) 1.0 0.0)))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetDust) "M1" (Math|Color|MakeColor (.x (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 1)) (.y (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 1)) (.z (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 1)) (select (> _n 1) 1.0 0.0)))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetDust) "M2" (Math|Color|MakeColor (.x (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 2)) (.y (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 2)) (.z (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 2)) (select (> _n 2) 1.0 0.0)))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetDust) "M3" (Math|Color|MakeColor (.x (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 3)) (.y (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 3)) (.z (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 3)) (select (> _n 3) 1.0 0.0)))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetDust) "M4" (Math|Color|MakeColor (.x (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 4)) (.y (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 4)) (.z (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 4)) (select (> _n 4) 1.0 0.0)))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetDust) "M5" (Math|Color|MakeColor (.x (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 5)) (.y (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 5)) (.z (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 5)) (select (> _n 5) 1.0 0.0)))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetDust) "M6" (Math|Color|MakeColor (.x (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 6)) (.y (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 6)) (.z (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 6)) (select (> _n 6) 1.0 0.0)))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetDust) "M7" (Math|Color|MakeColor (.x (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 7)) (.y (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 7)) (.z (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 7)) (select (> _n 7) 1.0 0.0)))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetDust) "M8" (Math|Color|MakeColor (.x (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 8)) (.y (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 8)) (.z (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 8)) (select (> _n 8) 1.0 0.0)))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetDust) "M9" (Math|Color|MakeColor (.x (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 9)) (.y (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 9)) (.z (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) 9)) (select (> _n 9) 1.0 0.0)))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetDust) "DustK" (Math|Color|MakeColor (Variables|5-Particulas|GetDustSize) (Variables|5-Particulas|GetDustOpacity) (Variables|5-Particulas|GetDustDrift) (Variables|5-Particulas|GetDustOffset)))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetDust) "DustCol" (Variables|5-Particulas|GetDustColor))
  (Rendering|SetVisibility (Variables|Default|GetDust) (> (Variables|5-Particulas|GetDustOpacity) 0.001)))
