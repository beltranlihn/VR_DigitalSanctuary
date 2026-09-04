# SM_PortalRoom — el interior del portal circular de luz

## Propósito
Interior tipo Turrell de la referencia de arte: sala abovedada de yeso suave, **nicho en arco** en el muro del fondo, y **portal circular** con anillo de luz cálida que conecta con una cámara posterior iluminada. Dos mallas:
- **`SM_PortalRoom_Shell`** — la cáscara completa (sala + nicho + túnel del portal + cámara posterior), normales hacia ADENTRO, origen en el centro del piso.
- **`SM_PortalRoom_Ring`** — el anillo emisor del portal (malla aparte, `M_Button_Glow` — la misma luz cálida del botón), truncado en el piso como la referencia.

## Estado
🟡 **Modelado, primera revisión de composición OK en viewport (2026-09-01).** Falta el veredicto de Beltrán, UVs, y export. `.blend` sin guardar.

## Parámetros (metros)
| Perilla | Valor |
|---|---|
| Sala | 8 × 10 × 4.2, bóveda por bevel 1.6 (cove piso-pared incluido) |
| Nicho | **arco real**: caja (5.0 × 1.8, hasta z=0.9) ∪ medio cilindro (r=2.5) + bevel suave 0.22 al rim; piso plano (truncado en z=0) |
| Muro del portal | y=5.9 → 6.3 (40 cm) |
| Portal | Ø2.6 (r=1.30), centro a z=1.05 → se hunde 25 cm bajo el piso pero **truncado en z=0** = umbral plano |
| Cámara posterior | 5.0 × 3.2 × 3.0, piso plano |
| Anillo | toro r mayor 1.30 × r menor 0.045 en el plano y=5.9, cortado bajo z=0.03 |

## Construcción
Volúmenes de AIRE (cajas con bevel + cilindros) unidos con **booleanos EXACT**, luego `flip_normals()` → cáscara interior. Los volúmenes que necesitan piso continuo se truncan en z=0 con un boolean (el bevel de una caja redondeada también curva la esquina del PISO y deja labio — trampa). ~2.8k tris la cáscara + 1.4k el anillo.

## Trampas que mordieron acá (ya en gotchas.md)
1. **`ob.parent = X` por Python NO compensa el transform del padre** — el anillo apareció 2.1 m arriba porque la cáscara tenía su origen en el centro del cubo original. Fix: `transform_apply(location)` del padre (origen al piso, correcto además para el export) ANTES de emparentar.
2. **Un volumen booleano que se pasa de largo se funde con el vecino**: el nicho v1 llegaba hasta y=6.69 (pasando el muro en 5.9-6.3) → nicho+cámara+portal quedaron fusionados y el portal no cortó ningún muro. Verificar los rangos y de cada void contra los planos de muro antes del union.

## Pendientes
- [ ] Veredicto de Beltrán sobre proporciones (arco, portal, alturas).
- [ ] Sombra facetada leve en el flanco derecho del arco (artefacto de shading del boolean) — si molesta con el material real: Weighted Normals o retopo local.
- [ ] UVs (canal 0 + **lightmap channel 1** — esta pieza es la que más luz horneada recibe).
- [ ] Export FBX (cáscara + anillo, dos Static Mesh) y materiales reales en Unreal (yeso + emisivo).

## Log
- **2026-09-01** — construido en 3 iteraciones: v1 (nicho fundido con la cámara, anillo flotando), v2 (muros correctos, anillo desplazado por el parenting), v3 (arco real caja∪cilindro, origen al piso, anillo en su lugar verificado por bbox).
