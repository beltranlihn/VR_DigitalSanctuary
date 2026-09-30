// AppearTracePS v1 - M_AppearTrace_SC (unlit, ADITIVO, dos caras): el TRAZO de luz de la aparicion 'luz primero'
// (blender-3d/assets/aparicion-luz.md). La malla es una cinta plana a lo largo del contorno de la ranura del objeto
// (SM_<X>_Trace_SC): UV.x = fraccion del contorno desde arriba, antihorario visto desde la cara; UV.y = 0..1 a lo ancho.
// Una semilla de luz (Head) nace arriba y DIBUJA el contorno (Sweep 0 -> 1), destella y se apaga (Glow -> 0).
// Entradas: UV (TexCoord 0), Sweep, Soft (0,05), Head, Glow, Halo (0,3), Color.
float dv = UV.y - 0.5;
float qc = dv / 0.09;
float qh = dv / 0.28;
float prof = exp(-qc * qc) + Halo * exp(-qh * qh);
float front = Sweep * (1.0 + Soft);
float lit = saturate((front - UV.x) / max(Soft, 1.0e-4));
float hc = front - 0.5 * Soft;
float dd = frac(UV.x - hc + 0.5) - 0.5;
float qd = dd / 0.028;
float k = lit * Glow + exp(-qd * qd) * Head;
return Color * (k * prof);
