;; BP_LovingCell_SC — optimizacion del TICK (2026-09-29, pedido de Narrativa por encargo de Beltran: "todas las
;; transiciones del recorrido a 72 fps"). Medido en la Quest: ReceiveTick 6-8 ms por cuadro (Simulate 4-5,5 +
;; PushAll 2,5-3,1). Meta: <= 2 ms, SIN cambiar el look aprobado (V4b).
;;
;; Que se hizo (todo en el BP; la matematica de GroupTarget / LifeApply / CalmStep / BridgeStep NO se toco):
;; 1. Solo se simulan los grupos que EXISTEN (N = GroupCount, antes siempre 10).
;; 2. Con los puentes apagados (bBridges false, el default) no corren ni la rampa de BridgeP ni BridgeStep: sus
;;    unicas salidas eran los arreglos Bridge*, que BridgeGate ponia en 0 igual. BridgeGate corre solo en Snap.
;; 3. Refresco escalonado del OBJETIVO de cada grupo (SimDivider R, default 3): el objetivo (GroupTarget + LifeApply,
;;    lo caro) se recalcula para cada grupo 1 de cada R cuadros, en turnos (grupo i cuando (i + SimFrame) % R == 0).
;;    El RESORTE (lo que mueve el grupo) sigue corriendo TODOS los cuadros contra el ultimo objetivo, y el arrastre
;;    rigido con el nucleo (CoreD x Kappa) tambien. El resorte (w ~1,1-1,4 rad/s) filtra la escalera: la diferencia
;;    es un retraso del objetivo de ~R/2 cuadros (~21 ms con R 3) sobre senales de 11-67 s de periodo.
;;    R = 1 reproduce EXACTO el comportamiento anterior (control A/B: set BP_LovingCell_SC_C SimDivider 1).
;;    CalmStep y el bucle de LifeStep se escalonan con el mismo turno (DoRef[i]); la fase del PLL (Psi) integra el
;;    tiempo REAL transcurrido desde el ultimo turno de ese grupo (GroupDT[i]).
;; 4. Empuje a los materiales: 328 SetColorParameterValueOnMaterials por cuadro -> ~86. Lo que no cambia en juego
;;    (LV2, LV3, LV5, BPr con puentes apagados, M6..M9 con N <= 6, DustK/DustCol, OuterK/OuterCol, visibilidades,
;;    grupos ocultos, puentes) se empuja solo cuando StaticDirty: en el Construction Script y en BeginPlay (Snap), y
;;    cuando cambian LV2 / LV3 / LV5 / N (deteccion en PushAll). 🔴 Si un director cambia EN JUEGO una perilla de
;;    look (DustOpacity, OuterOpacity, colores, OuterK...), tiene que poner StaticDirty = true.
;;
;; Grafos: NUEVOS GroupPrep, PushGroupLive · REESCRITOS (vaciados y escritos enteros) Simulate, StepGroup,
;; PushGlobals, PushAll, PushMore, PushOuter · CIRUGIA LifeStep (bucle 0..NLast + Branch DoRef[i]) y CalmStep
;; (2 bucles igual + el DT del PLL -> GroupDT[i]). PushGroup queda igual (es el camino "completo").
;; Variables nuevas: 9-Rendimiento SimDivider (int, 3, instance editable) · Z-Interno SimFrame NLast DoRef[] GroupDT[]
;; TgtA[] SprW2A[] SprDA[] StaticDirty (true) LV2P LV3P LV5P NP.

;; ===== GRAFO: GroupPrep
;; GroupPrep (Index): deja listos Tgt / SprW2 / SprD para el resorte del grupo Index.
;; Turno de refresco (DoRef[Index]): GroupTarget + LifeApply (como antes) y se guarda el resultado por grupo.
;; Fuera de turno: se reponen los valores guardados y se aplica el arrastre rigido que hacia LifeApply.
(fn GroupPrep (Index)
  (if (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetDoRef) Index)
    (CallFunction|GroupTarget :Index Index)
    (CallFunction|LifeApply :Index Index)
    (Utilities|Array|SetArrayElem (Variables|Z-Interno|GetTgtA) Index (Variables|Default|GetTgt))
    (Utilities|Array|SetArrayElem (Variables|Z-Interno|GetSprW2A) Index (Variables|Z-Interno|GetSprW2))
    (Utilities|Array|SetArrayElem (Variables|Z-Interno|GetSprDA) Index (Variables|Z-Interno|GetSprD))
    (Utilities|Array|SetArrayElem (Variables|Z-Interno|GetGroupDT) Index 0.0)
    (else
      (Variables|Default|SetTgt (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetTgtA) Index))
      (Variables|Z-Interno|SetSprW2 (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetSprW2A) Index))
      (Variables|Z-Interno|SetSprD (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetSprDA) Index))
      (Utilities|Array|SetArrayElem (Variables|Z-Interno|GetPos) Index (+ (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetPos) Index) (* (Variables|Z-Interno|GetCoreD) (Variables|Z-Interno|GetKappa)))))))

;; ===== GRAFO: PushGroupLive
;; PushGroupLive (Index Cluster Arm Bridge): el empuje de un grupo en el Tick.
;; StaticDirty o puentes prendidos -> PushGroup completo (el de siempre). Si no: solo lo que se mueve, y nada si el
;; grupo esta oculto (su visibilidad ya la puso el ultimo empuje completo).
(fn PushGroupLive (Index Cluster Arm Bridge)
  (bind _n (Math|Integer|Clamp(Integer) (Variables|2-Forma|GetGroupCount) 1 10))
  (bind _pos (Variables|Z-Interno|GetPos))
  (bind _ip (Math|Integer|%(Integer) (+ (- Index 1) _n) _n))
  (bind _in (Math|Integer|%(Integer) (+ Index 1) _n))
  (bind _p (Utilities|Array|Get(acopy) _pos Index))
  (bind _pp (Utilities|Array|Get(acopy) _pos _ip))
  (bind _pn (Utilities|Array|Get(acopy) _pos _in))
  (bind _gi (Math|Color|MakeColor (.x _p) (.y _p) (.z _p) (Math|Conversions|ToFloat(Integer) Index)))
  (if (or (Variables|Z-Interno|GetStaticDirty) (Variables|2-Forma|GetBridges))
    (CallFunction|PushGroup :Index Index :Cluster Cluster :Arm Arm :Bridge Bridge)
    (else
      (if (< Index _n)
        (CallFunction|PushGlobals :Comp Cluster)
        (CallFunction|PushGlobals :Comp Arm)
        (Rendering|Material|SetColorParameterValueOnMaterials Cluster "GI" _gi)
        (Rendering|Material|SetColorParameterValueOnMaterials Arm "GI" _gi)
        (Rendering|Material|SetColorParameterValueOnMaterials Arm "GP" (Math|Color|MakeColor (.x _pp) (.y _pp) (.z _pp) (Math|Conversions|ToFloat(Integer) _ip)))
        (Rendering|Material|SetColorParameterValueOnMaterials Arm "GN" (Math|Color|MakeColor (.x _pn) (.y _pn) (.z _pn) (Math|Conversions|ToFloat(Integer) _in)))))))

;; ===== GRAFO: PushGlobals
;; PushGlobals (Comp): LV0 (nucleo), LV1 (estado/fase), LV4 (plano) cambian cada cuadro; LV2/LV3/LV5 solo con StaticDirty.
(fn PushGlobals (Comp)
  (Rendering|Material|SetColorParameterValueOnMaterials Comp "LV0" (Variables|Default|GetLV0))
  (Rendering|Material|SetColorParameterValueOnMaterials Comp "LV1" (Variables|Default|GetLV1))
  (Rendering|Material|SetColorParameterValueOnMaterials Comp "LV4" (Variables|Default|GetLV4))
  (if (Variables|Z-Interno|GetStaticDirty)
    (Rendering|Material|SetColorParameterValueOnMaterials Comp "LV2" (Variables|Default|GetLV2))
    (Rendering|Material|SetColorParameterValueOnMaterials Comp "LV3" (Variables|Default|GetLV3))
    (Rendering|Material|SetColorParameterValueOnMaterials Comp "LV5" (Variables|Default|GetLV5))))

;; ===== GRAFO: StepGroup
;; StepGroup (Index DT Snap): el resorte de siempre (Euler simplectico, mismas cuentas y mismo orden: la velocidad nueva
;; se calcula con la Pos ya arrastrada, como antes). GroupPrep reemplaza a GroupTarget + LifeApply.
(fn StepGroup (Index DT Snap)
  (bind _pos (Variables|Z-Interno|GetPos))
  (bind _output (Utilities|Array|Get(acopy) _pos Index))
  (bind _vel (Variables|Z-Interno|GetVel))
  (bind _output_1 (Utilities|Array|Get(acopy) _vel Index))
  (bind _tgt (Variables|Default|GetTgt))
  (bind _returnvalue_5 (+ _output_1 (* (- (* (- _tgt _output) (Variables|Z-Interno|GetSprW2)) (* _output_1 (Variables|Z-Interno|GetSprD))) DT)))
  (CallFunction|GroupPrep :Index Index)
  (Utilities|Array|SetArrayElem (Variables|Z-Interno|GetPos) Index (select Snap _tgt (+ _output (* _returnvalue_5 DT))))
  (Utilities|Array|SetArrayElem (Variables|Z-Interno|GetVel) Index (select Snap (Math|Vector|MakeVector 0.0 0.0 0.0) _returnvalue_5)))

;; ===== GRAFO: Simulate
(fn Simulate (DT Snap)
  (bind _dt (Math|Float|Min(Float) DT 0.05))
  (bind _n (Math|Integer|Clamp(Integer) (Variables|2-Forma|GetGroupCount) 1 10))
  (bind _r (select (< (Variables|9-Rendimiento|GetSimDivider) 1) 1 (Variables|9-Rendimiento|GetSimDivider)))
  (bind _fake (select (Variables|1-Estado|GetFakeSignal) (- 0.5 (* 0.5 (Math|Trig|Cos(Radians) (/ (* 6.2831853 (Variables|Z-Interno|GetClock)) (Math|Float|Max(Float) (Variables|1-Estado|GetFakePeriod) 1.0))))) (Variables|1-Estado|GetGlobalState)))
  (Utilities|Array|Resize (Variables|Z-Interno|GetPos) 10)
  (Utilities|Array|Resize (Variables|Z-Interno|GetVel) 10)
  (Utilities|Array|Resize (Variables|Z-Interno|GetBridgeP) 10)
  (Utilities|Array|Resize (Variables|Z-Interno|GetTgtA) 10)
  (Utilities|Array|Resize (Variables|Z-Interno|GetSprW2A) 10)
  (Utilities|Array|Resize (Variables|Z-Interno|GetSprDA) 10)
  (Utilities|Array|Resize (Variables|Z-Interno|GetGroupDT) 10)
  (Utilities|Array|Resize (Variables|Z-Interno|GetDoRef) 10)
  (Variables|Z-Interno|SetClock (+ (Variables|Z-Interno|GetClock) _dt))
  (Variables|Z-Interno|SetS (select Snap _fake (Math|Interpolation|FInterpTo (Variables|Z-Interno|GetS) _fake _dt (Variables|1-Estado|GetStateSmoothing))))
  (Variables|Z-Interno|SetPhase (Math|Float|%(Float) (+ (Variables|Z-Interno|GetPhase) (/ (* 6.2831853 _dt) (/ 7.0 (* (Math|Float|Max(Float) (Variables|4-Vida|GetPulseSpeed) 0.05) (+ 1.0 (* 0.4 (Variables|1-Estado|GetAgitation))))))) 6.2831853))
  (Variables|Z-Interno|SetStaticDirty (or (Variables|Z-Interno|GetStaticDirty) Snap))
  (Variables|Z-Interno|SetSimFrame (select Snap 0 (+ (Variables|Z-Interno|GetSimFrame) 1)))
  (Variables|Z-Interno|SetNLast (- _n 1))
  (for _i (range _n)
    (Utilities|Array|SetArrayElem (Variables|Z-Interno|GetDoRef) _i (or Snap (== (Math|Integer|%(Integer) (+ _i (Variables|Z-Interno|GetSimFrame)) _r) 0)))
    (Utilities|Array|SetArrayElem (Variables|Z-Interno|GetGroupDT) _i (+ (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetGroupDT) _i) _dt)))
  (CallFunction|LifeStep :DT _dt :Snap Snap)
  (CallFunction|CalmStep :DT _dt :Snap Snap)
  (for _index (range _n)
    (CallFunction|StepGroup :Index _index :DT _dt :Snap Snap))
  (if (Variables|2-Forma|GetBridges)
    (for _index_1 (range 10)
      (Utilities|Array|SetArrayElem (Variables|Z-Interno|GetBridgeP) _index_1 (Math|Float|MapRangeClamped (Variables|Z-Interno|GetS) (+ 0.54 (* 0.04 (Math|Conversions|ToFloat(Integer) _index_1))) (+ 0.74 (* 0.04 (Math|Conversions|ToFloat(Integer) _index_1))) 0.0 1.0)))
    (CallFunction|BridgeStep :DT _dt :Snap Snap)
    (CallFunction|BridgeGate)
    (else
      (if Snap
        (CallFunction|BridgeGate)))))

;; ===== GRAFO: PushOuter
(fn PushOuter ()
  (bind _n (Math|Integer|Clamp(Integer) (Variables|2-Forma|GetGroupCount) 1 10))
  (bind _on (> (Variables|6-Envoltura|GetOuterOpacity) 0.001))
  (bind _pos (Variables|Z-Interno|GetPos))
  (bind _p0 (Utilities|Array|Get(acopy) _pos 0))
  (bind _p1 (Utilities|Array|Get(acopy) _pos 1))
  (bind _p2 (Utilities|Array|Get(acopy) _pos 2))
  (bind _p3 (Utilities|Array|Get(acopy) _pos 3))
  (bind _p4 (Utilities|Array|Get(acopy) _pos 4))
  (bind _p5 (Utilities|Array|Get(acopy) _pos 5))
  (bind _p6 (Utilities|Array|Get(acopy) _pos 6))
  (bind _p7 (Utilities|Array|Get(acopy) _pos 7))
  (bind _p8 (Utilities|Array|Get(acopy) _pos 8))
  (bind _p9 (Utilities|Array|Get(acopy) _pos 9))
  (if (not _on)
    (Rendering|SetVisibility (Variables|Default|GetOuterShell) false)
    (else
      (CallFunction|PushGlobals :Comp (Variables|Default|GetOuterShell))
      (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetOuterShell) "M0" (Math|Color|MakeColor (.x _p0) (.y _p0) (.z _p0) (select (> _n 0) 1.0 0.0)))
      (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetOuterShell) "M1" (Math|Color|MakeColor (.x _p1) (.y _p1) (.z _p1) (select (> _n 1) 1.0 0.0)))
      (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetOuterShell) "M2" (Math|Color|MakeColor (.x _p2) (.y _p2) (.z _p2) (select (> _n 2) 1.0 0.0)))
      (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetOuterShell) "M3" (Math|Color|MakeColor (.x _p3) (.y _p3) (.z _p3) (select (> _n 3) 1.0 0.0)))
      (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetOuterShell) "M4" (Math|Color|MakeColor (.x _p4) (.y _p4) (.z _p4) (select (> _n 4) 1.0 0.0)))
      (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetOuterShell) "M5" (Math|Color|MakeColor (.x _p5) (.y _p5) (.z _p5) (select (> _n 5) 1.0 0.0)))
      (if (or (Variables|Z-Interno|GetStaticDirty) (> _n 6))
        (Rendering|SetVisibility (Variables|Default|GetOuterShell) true)
        (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetOuterShell) "M6" (Math|Color|MakeColor (.x _p6) (.y _p6) (.z _p6) (select (> _n 6) 1.0 0.0)))
        (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetOuterShell) "M7" (Math|Color|MakeColor (.x _p7) (.y _p7) (.z _p7) (select (> _n 7) 1.0 0.0)))
        (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetOuterShell) "M8" (Math|Color|MakeColor (.x _p8) (.y _p8) (.z _p8) (select (> _n 8) 1.0 0.0)))
        (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetOuterShell) "M9" (Math|Color|MakeColor (.x _p9) (.y _p9) (.z _p9) (select (> _n 9) 1.0 0.0)))
        (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetOuterShell) "OuterK" (Math|Color|MakeColor (+ (Math|Float|Max(Float) (Variables|6-Envoltura|GetOuterMargin) 0.0) (+ (Math|Float|Max(Float) (Variables|5-Particulas|GetDustOffset) 0.0) (+ (* 1.8 (Math|Float|Max(Float) (Variables|5-Particulas|GetDustDrift) 0.0)) (* 2.0 (Math|Float|Max(Float) (Variables|5-Particulas|GetDustSize) 0.0))))) (Variables|6-Envoltura|GetOuterBody) (Variables|6-Envoltura|GetOuterSoftness) (Variables|6-Envoltura|GetOuterWobble)))
        (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetOuterShell) "OuterCol" (Math|Color|NewOpacity(LinearColor) (Variables|6-Envoltura|GetOuterColor) (Variables|6-Envoltura|GetOuterOpacity)))))))

;; ===== GRAFO: PushMore
(fn PushMore ()
  (bind _n (Math|Integer|Clamp(Integer) (Variables|2-Forma|GetGroupCount) 1 10))
  (bind _pos (Variables|Z-Interno|GetPos))
  (bind _p0 (Utilities|Array|Get(acopy) _pos 0))
  (bind _p1 (Utilities|Array|Get(acopy) _pos 1))
  (bind _p2 (Utilities|Array|Get(acopy) _pos 2))
  (bind _p3 (Utilities|Array|Get(acopy) _pos 3))
  (bind _p4 (Utilities|Array|Get(acopy) _pos 4))
  (bind _p5 (Utilities|Array|Get(acopy) _pos 5))
  (bind _p6 (Utilities|Array|Get(acopy) _pos 6))
  (bind _p7 (Utilities|Array|Get(acopy) _pos 7))
  (bind _p8 (Utilities|Array|Get(acopy) _pos 8))
  (bind _p9 (Utilities|Array|Get(acopy) _pos 9))
  (bind _m6 (Math|Color|MakeColor (.x _p6) (.y _p6) (.z _p6) (select (> _n 6) 1.0 0.0)))
  (bind _m7 (Math|Color|MakeColor (.x _p7) (.y _p7) (.z _p7) (select (> _n 7) 1.0 0.0)))
  (bind _m8 (Math|Color|MakeColor (.x _p8) (.y _p8) (.z _p8) (select (> _n 8) 1.0 0.0)))
  (bind _m9 (Math|Color|MakeColor (.x _p9) (.y _p9) (.z _p9) (select (> _n 9) 1.0 0.0)))
  (CallFunction|PushGroupLive :Index 6 :Cluster (Variables|Default|GetCluster6) :Arm (Variables|Default|GetArm6) :Bridge (Variables|Default|GetBridge6))
  (CallFunction|PushGroupLive :Index 7 :Cluster (Variables|Default|GetCluster7) :Arm (Variables|Default|GetArm7) :Bridge (Variables|Default|GetBridge7))
  (CallFunction|PushGroupLive :Index 8 :Cluster (Variables|Default|GetCluster8) :Arm (Variables|Default|GetArm8) :Bridge (Variables|Default|GetBridge8))
  (CallFunction|PushGroupLive :Index 9 :Cluster (Variables|Default|GetCluster9) :Arm (Variables|Default|GetArm9) :Bridge (Variables|Default|GetBridge9))
  (CallFunction|PushGlobals :Comp (Variables|Default|GetDust))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetDust) "M0" (Math|Color|MakeColor (.x _p0) (.y _p0) (.z _p0) (select (> _n 0) 1.0 0.0)))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetDust) "M1" (Math|Color|MakeColor (.x _p1) (.y _p1) (.z _p1) (select (> _n 1) 1.0 0.0)))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetDust) "M2" (Math|Color|MakeColor (.x _p2) (.y _p2) (.z _p2) (select (> _n 2) 1.0 0.0)))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetDust) "M3" (Math|Color|MakeColor (.x _p3) (.y _p3) (.z _p3) (select (> _n 3) 1.0 0.0)))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetDust) "M4" (Math|Color|MakeColor (.x _p4) (.y _p4) (.z _p4) (select (> _n 4) 1.0 0.0)))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetDust) "M5" (Math|Color|MakeColor (.x _p5) (.y _p5) (.z _p5) (select (> _n 5) 1.0 0.0)))
  (CallFunction|PushOuter)
  (if (or (Variables|Z-Interno|GetStaticDirty) (> _n 6))
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentre) "M6" _m6)
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentre) "M7" _m7)
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentre) "M8" _m8)
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentre) "M9" _m9)
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentreFilm) "M6" _m6)
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentreFilm) "M7" _m7)
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentreFilm) "M8" _m8)
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentreFilm) "M9" _m9)
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetDust) "M6" _m6)
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetDust) "M7" _m7)
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetDust) "M8" _m8)
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetDust) "M9" _m9)
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetDust) "DustK" (Math|Color|MakeColor (Variables|5-Particulas|GetDustSize) (Variables|5-Particulas|GetDustOpacity) (Variables|5-Particulas|GetDustDrift) (Variables|5-Particulas|GetDustOffset)))
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetDust) "DustCol" (Variables|5-Particulas|GetDustColor))
    (Rendering|SetVisibility (Variables|Default|GetDust) (> (Variables|5-Particulas|GetDustOpacity) 0.001))))

;; ===== GRAFO: PushAll
;; LV0/LV1/LV4 los escribe LifeLV (el SetLV0/LV1/LV4 que habia aca antes quedaba pisado: se quito).
(fn PushAll ()
  (bind _n (Math|Integer|Clamp(Integer) (Variables|2-Forma|GetGroupCount) 1 10))
  (bind _pos (Variables|Z-Interno|GetPos))
  (bind _p0 (Utilities|Array|Get(acopy) _pos 0))
  (bind _p1 (Utilities|Array|Get(acopy) _pos 1))
  (bind _p2 (Utilities|Array|Get(acopy) _pos 2))
  (bind _p3 (Utilities|Array|Get(acopy) _pos 3))
  (bind _p4 (Utilities|Array|Get(acopy) _pos 4))
  (bind _p5 (Utilities|Array|Get(acopy) _pos 5))
  (bind _lv2 (Math|Color|MakeColor (Variables|2-Forma|GetGroupSize) (Variables|2-Forma|GetGroupSpread) (Variables|2-Forma|GetCenterAttraction) (Variables|2-Forma|GetConnectionStrength)))
  (bind _lv3 (Math|Color|MakeColor (Variables|3-Membrana|GetMembraneThickness) (Variables|3-Membrana|GetMembraneOpacity) (Variables|4-Vida|GetNoiseAmount) (Variables|4-Vida|GetOrganicMotion)))
  (Variables|Z-Interno|SetStaticDirty (or (Variables|Z-Interno|GetStaticDirty) (or (not (Math|Color|NearEqual(LinearColor) _lv2 (Variables|Z-Interno|GetLV2P) 0.0)) (or (not (Math|Color|NearEqual(LinearColor) _lv3 (Variables|Z-Interno|GetLV3P) 0.0)) (or (not (Math|Color|NearEqual(LinearColor) (Variables|Default|GetLV5) (Variables|Z-Interno|GetLV5P) 0.0)) (!= _n (Variables|Z-Interno|GetNP)))))))
  (Variables|Default|SetLV2 _lv2)
  (Variables|Default|SetLV3 _lv3)
  (CallFunction|LifeLV)
  (CallFunction|PushGlobals :Comp (Variables|Default|GetCentre))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentre) "M0" (Math|Color|MakeColor (.x _p0) (.y _p0) (.z _p0) (select (> _n 0) 1.0 0.0)))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentre) "M1" (Math|Color|MakeColor (.x _p1) (.y _p1) (.z _p1) (select (> _n 1) 1.0 0.0)))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentre) "M2" (Math|Color|MakeColor (.x _p2) (.y _p2) (.z _p2) (select (> _n 2) 1.0 0.0)))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentre) "M3" (Math|Color|MakeColor (.x _p3) (.y _p3) (.z _p3) (select (> _n 3) 1.0 0.0)))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentre) "M4" (Math|Color|MakeColor (.x _p4) (.y _p4) (.z _p4) (select (> _n 4) 1.0 0.0)))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentre) "M5" (Math|Color|MakeColor (.x _p5) (.y _p5) (.z _p5) (select (> _n 5) 1.0 0.0)))
  (CallFunction|PushGroupLive :Index 0 :Cluster (Variables|Default|GetCluster0) :Arm (Variables|Default|GetArm0) :Bridge (Variables|Default|GetBridge0))
  (CallFunction|PushGroupLive :Index 1 :Cluster (Variables|Default|GetCluster1) :Arm (Variables|Default|GetArm1) :Bridge (Variables|Default|GetBridge1))
  (CallFunction|PushGroupLive :Index 2 :Cluster (Variables|Default|GetCluster2) :Arm (Variables|Default|GetArm2) :Bridge (Variables|Default|GetBridge2))
  (CallFunction|PushGroupLive :Index 3 :Cluster (Variables|Default|GetCluster3) :Arm (Variables|Default|GetArm3) :Bridge (Variables|Default|GetBridge3))
  (CallFunction|PushGroupLive :Index 4 :Cluster (Variables|Default|GetCluster4) :Arm (Variables|Default|GetArm4) :Bridge (Variables|Default|GetBridge4))
  (CallFunction|PushGroupLive :Index 5 :Cluster (Variables|Default|GetCluster5) :Arm (Variables|Default|GetArm5) :Bridge (Variables|Default|GetBridge5))
  (CallFunction|PushCentreFilm)
  (CallFunction|PushMore)
  (Variables|Z-Interno|SetLV2P (Variables|Default|GetLV2))
  (Variables|Z-Interno|SetLV3P (Variables|Default|GetLV3))
  (Variables|Z-Interno|SetLV5P (Variables|Default|GetLV5))
  (Variables|Z-Interno|SetNP _n)
  (Variables|Z-Interno|SetStaticDirty false))
