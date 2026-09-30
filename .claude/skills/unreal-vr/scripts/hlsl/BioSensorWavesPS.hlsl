// BioSensorWavesPS v5 - M_BioSensorWaves_SC, PIXEL SHADER (unlit, ADITIVO, dos caras). Los AROS del sensor de
// respiracion/latido (blender-3d/assets/bio-sensor.md): anillos suaves que salen de la cinta de luz hacia la panza,
// SEGUIDOS, indicando hacia donde apuntar el sensor.
// La malla es un cilindro abierto: UV.y = 0 en el sensor, 1 al final.
// v2: u = v^Squeeze -> los aros FRENAN y se JUNTAN al alejarse; ancho compensado con du/dv (grosor parejo).
// v3 (Beltran, 2026-09-30: "no deben nacer como pulso; siempre constante: desde opacidad 0 hasta tomar el color y luego
// desvanecerse"): envolvente SUAVE en el recorrido -> cada aro nace invisible, sube a su color hasta FadeIn y se apaga
// desde FadeOut hasta el final (antes: nacia al maximo pegado a la cinta = destello).
// Entradas: UV (TexCoord 0), T (Time), Color, Intensity, Count (aros a lo largo), Speed (aros por segundo),
//           Width (ancho, fraccion de su periodo), Squeeze (2: frenan), FadeIn (0,35: hasta donde sube), FadeOut (0,45:
//           desde donde se apaga), Active (0..1: el BP lo baja cuando el sensor ya esta en la panza),
//           AppearGlow (v4: 0..1 de la aparicion 'luz primero', lo maneja BPC_AppearLuz_SC; aparte de Active).
// v5 (Beltran, 2026-09-30: "los anillos deben ir en la otra direccion, desde el sensor hacia afuera"): Unreal INVIERTE
// la V al importar el FBX (V=0 quedaba LEJOS del sensor) -> se da vuelta aca para que 0 sea el sensor otra vez.
float v = saturate(1.0 - UV.y);
float u = pow(v, Squeeze);
float ph = frac(u * Count - T * Speed);
float dudv = max(Squeeze * pow(max(v, 1.0e-3), Squeeze - 1.0), 0.1);
float d = (ph - 0.5) / max(Width * dudv, 1.0e-4);
float band = exp(-d * d);
float env = smoothstep(0.0, max(FadeIn, 1.0e-3), v) * (1.0 - smoothstep(min(FadeOut, 0.999), 1.0, v));
return Color * (band * env * Intensity * saturate(Active) * AppearGlow);
