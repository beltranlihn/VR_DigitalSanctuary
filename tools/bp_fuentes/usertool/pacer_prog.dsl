;; pacer_prog.dsl - BP_Pacer_SC: el PROGRESO de la etapa en el anillo mas chico (pedido de Beltran 2026-09-30:
;; "puntitos alrededor que marcan la cantidad de ciclos... y un radial slider suavecito que avance en sentido del reloj").
;; El material dibuja (entrada Prog del Custom = ProgCount, ProgValue, ProgRadius, ProgAmt); el BP solo empuja 4 escalares.
;;   ProgCount = Cycles (0 = infinito o bShowProgress false -> no dibuja nada)
;;   ProgValue = clamp((CycleIndex + T/Total) / Cycles): 0 en la pausa de entrada, sube continuo, 1 al terminar
;; Variables en Default al escribir (las de categoria con espacios se pasan a Default y se devuelven despues).

;; ===== GRAFO: PacerPushProg
(fn PacerPushProg ()
  (bind _panel (Variables|Default|GetPanel))
  (bind _cyc (Variables|Default|GetCycles))
  (Rendering|Material|SetScalarParameterValueonMaterials _panel "ProgCount" (select (Variables|Default|GetShowProgress) (__I2F__ _cyc) 0.0))
  (Rendering|Material|SetScalarParameterValueonMaterials _panel "ProgValue" (Math|Float|Clamp(Float) (/ (+ (__I2F__ (Variables|Default|GetCycleIndex)) (/ (Variables|Default|GetT) (Math|Float|Max(Float) (Variables|Default|GetTotal) 0.01))) (Math|Float|Max(Float) (__I2F__ _cyc) 1.0))))
  (Rendering|Material|SetScalarParameterValueonMaterials _panel "ProgRadius" (Variables|Default|GetProgRadius))
  (Rendering|Material|SetScalarParameterValueonMaterials _panel "ProgAmt" (Variables|Default|GetProgAmt)))
