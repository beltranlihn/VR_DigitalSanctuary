// ChargeHaloTintPS v1 - M_ChargeHaloTint_SC (2026-10-01, Mesh 3D). El HALO de la carga en ALPHA BLEND, no aditivo.
// Pedido de Beltrán (vía Narrativa): "el halo de color de la carga casi no se notaba; que se note sin ensuciar".
// Causa: M_ChargeHalo_SC es aditivo y casi todas las cargas pasan sobre fondos claros (Hall, Uyuni, Entering):
// sumar luz a algo casi blanco no cambia nada. Acá el halo TIÑE el fondo con su color (saturado) y sobre oscuro
// sigue leyéndose como luz.
// Entrada C = la salida del Custom original de M_ChargeHalo_SC (anillo gaussiano + relleno + temblor, ya × Amount y × Color).
// Parámetros: Sat (HaloSat 1,6: satura los StageColor pastel), OpGain (HaloOpGain 2: cuánto alfa da la intensidad),
//             MaxOp (HaloMaxOpacity 0,6: tope, nunca tapa del todo), Glow (HaloGlow 1,1).
// Salidas: return = Emissive (RGB) · Alpha = Opacity (salida adicional CMOT_Float1).
// Sin borde duro: el alfa sale de la MISMA forma gaussiana, con smoothstep.
float m = max(max(C.r, C.g), C.b);
float3 hue = C / max(m, 1.0e-4);
float l = dot(hue, float3(0.3, 0.59, 0.11));
hue = saturate(lerp(float3(l, l, l), hue, Sat));
float a = saturate(m * OpGain);
a = a * a * (3.0 - 2.0 * a);
Alpha = a * MaxOp;
return hue * Glow;
