"""partitura_def.py - la lista de perillas de tiempo de la Obra (DA_Partitura_Obra).

Cada entrada: (nombre, tipo, valor inicial, categoria, que hace).
  tipo 'f' = segundos (float) · 'a5' = 5 valores, uno por etapa (Entering, Recognizing, Loving, Attracting, Surrounding)
Los valores iniciales son los EFECTIVOS de la Obra el 2026-10-02 (antes estaban escritos como literales en los
grafos de BP_Obra_SC o en sus variables). Se cambian en el editor abriendo DA_Partitura_Obra, NO aca: este
archivo es la definicion (nombres, categorias, documentacion) y el valor con el que se creo el asset.
Todos los tiempos son segundos del reloj del director (PT = tiempo dentro de la fase; T = tiempo de la etapa).
"""
P = [
 # 1 Inicio y Hall
 ("Aviso_Dur", "f", 19.0, "1 Inicio y Hall", "Duracion del aviso de prototipo (fase 16), si bDisclaimer."),
 ("Titulo_Aparece", "f", 2.5, "1 Inicio y Hall", "Cuando se coloca el titulo SOUL CHARGER en el Hall (PT de la fase 9)."),
 ("Titulo_RevelaIni", "f", 3.0, "1 Inicio y Hall", "El titulo empieza a revelarse."),
 ("Titulo_RevelaFin", "f", 6.5, "1 Inicio y Hall", "El titulo termina de revelarse."),
 ("Bajada_RevelaIni", "f", 5.0, "1 Inicio y Hall", "La bajada (subtitulo) empieza a revelarse."),
 ("Bajada_RevelaFin", "f", 7.5, "1 Inicio y Hall", "La bajada termina de revelarse."),
 ("Logos_RevelaIni", "f", 6.0, "1 Inicio y Hall", "Los logos empiezan a revelarse (JHU +0,3 s, IDEAS +0,6 s)."),
 ("Logos_RevelaFin", "f", 8.0, "1 Inicio y Hall", "Los logos terminan de revelarse."),
 ("Titulo_SaleIni", "f", 17.0, "1 Inicio y Hall", "Titulo, bajada y logos empiezan a irse."),
 ("Titulo_SaleFin", "f", 19.5, "1 Inicio y Hall", "Titulo, bajada y logos terminan de irse."),
 ("Titulo_Fin", "f", 20.0, "1 Inicio y Hall", "Se oculta el actor del titulo."),
 ("Hall_VeloAbreIni", "f", 3.5, "1 Inicio y Hall", "El velo negro empieza a abrir a la niebla del Hall."),
 ("Hall_VeloAbreFin", "f", 5.5, "1 Inicio y Hall", "El velo termina de abrir en el Hall."),
 ("Hall_IntroA", "f", 3.0, "1 Inicio y Hall", "Cuando la Obra le dice al Hall que arranque (HallIntro)."),
 ("HUD_EEGRetardo", "f", 1.0, "1 Inicio y Hall", "Cuanto despues de nacer el HUD nace la linea del EEG."),
 # 2 Cada etapa
 ("Etapa_VeloAbreIni", "f", 1.0, "2 Cada etapa", "El velo de color empieza a abrir la etapa (T)."),
 ("Etapa_VeloAbreFin", "f", 4.0, "2 Cada etapa", "El velo termina de abrir la etapa."),
 ("Etapa_TituloRevelaIni", "f", 0.5, "2 Cada etapa", "El titulo de la etapa empieza a revelarse."),
 ("Etapa_TituloRevelaFin", "f", 1.8, "2 Cada etapa", "El titulo de la etapa termina de revelarse."),
 ("Etapa_TituloSaleIni", "f", 4.6, "2 Cada etapa", "El titulo de la etapa empieza a irse."),
 ("Etapa_TituloSaleFin", "f", 5.6, "2 Cada etapa", "El titulo de la etapa termina de irse."),
 ("Etapa_TituloOculto", "f", 5.7, "2 Cada etapa", "Desde aca el titulo de la etapa queda oculto."),
 ("Alma_Entra", "f", 5.5, "2 Cada etapa", "Cuando entra Alma (fin de la fase 0; el reloj de la etapa salta a 9 en ese momento)."),
 ("Alma_VozRetardo", "f", 1.5, "2 Cada etapa", "Cuanto espera Alma para empezar a hablar al llegar."),
 ("Alma_TrasVoz", "f", 3.0, "2 Cada etapa", "Cuanto queda Alma despues de su voz antes de las instrucciones."),
 ("Instr_Dur", "a5", [8.5, 6.0, 6.0, 6.0, 0.6], "2 Cada etapa", "Tiempo de instrucciones antes de StageBegin, por etapa."),
 ("Instr_EsperaMax", "f", 20.0, "2 Cada etapa", "Attracting: tope de espera a las voces de la consigna antes de empezar."),
 ("Etapa_Tope", "a5", [240.0, 180.0, 120.0, 240.0, 240.0], "2 Cada etapa", "Cortafuegos: si la etapa no termina sola, se cierra a los N s de mecanica."),
 ("Salida_Dur", "a5", [2.5, 2.5, 2.5, 2.5, 2.5], "2 Cada etapa", "Salida de la etapa (StageOutro) antes de la carga; nunca menos que la voz + Salida_TrasVoz."),
 ("Salida_TrasVoz", "f", 0.6, "2 Cada etapa", "Margen despues de la voz de felicitacion antes de la carga."),
 ("Carga_Dur", "a5", [4.0, 4.0, 4.0, 4.0, 6.0], "2 Cada etapa", "Duracion de la carga del anillo por etapa (la ultima es la carga final)."),
 ("Carga_Minima", "f", 1.0, "2 Cada etapa", "Minimo de la fase de carga antes de poder cerrarla."),
 ("Despedida_Retardo", "f", 0.9, "2 Cada etapa", "Cuanto espera Alma para invitar a la siguiente etapa."),
 ("Despedida_TrasVoz", "f", 1.3, "2 Cada etapa", "Cuanto queda Alma despues de la invitacion antes de irse."),
 ("Velo_CierreDur", "f", 2.5, "2 Cada etapa", "Cuanto tarda el velo en cerrar la etapa antes de pasar a la siguiente."),
 # 3 Modo simulado y cortes
 ("Sim_EtapaMax", "f", 90.0, "3 Simulado y cortes", "Con bSimulated: Attracting y Surrounding cierran a los N s si nadie juega."),
 ("Dibujo_Corte", "f", 205.0, "3 Simulado y cortes", "Surrounding: a los N s se acaba el tiempo, se guarda y presenta el dibujo."),
 ("Dibujo_TopeTrasCorte", "f", 30.0, "3 Simulado y cortes", "Tope de seguridad despues del corte del dibujo."),
 # 4 Final
 ("Final_NegroRampa", "f", 2.0, "4 Final", "En la carga final, cuanto dura la rampa a negro (termina con la carga)."),
 ("Regreso_HallA", "f", 0.3, "4 Final", "Cuando, ya en negro, se salta al Hall para el regreso."),
 ("Regreso_VeloIni", "f", 0.2, "4 Final", "Regreso: el velo empieza a abrir."),
 ("Regreso_VeloFin", "f", 1.4, "4 Final", "Regreso: el velo termina de abrir."),
 ("Regreso_PezA", "f", 1.6, "4 Final", "Regreso: cuando el alma sale como pez y el Hall la sigue."),
 ("Res_AlmaA", "f", 0.5, "4 Final", "Resultados: cuando llega Alma y empieza su lectura (VO_34b)."),
 ("Res_PezMin", "f", 1.8, "4 Final", "Resultados: minimo antes de que el alma se asiente en su anillo."),
 ("Res_PezMax", "f", 3.4, "4 Final", "Resultados: el alma se asienta a mas tardar a los N s."),
 ("Res_GusanoA", "f", 2.0, "4 Final", "Resultados: cuando suena la melodia (gusano)."),
 ("Res_Explorar", "f", 25.0, "4 Final", "Resultados: tiempo para explorar despues de la lectura de Alma."),
 ("Res_InvitaRecorte", "f", 1.2, "4 Final", "Los botones aparecen N s antes de que termine la invitacion a compartir."),
 ("Res_BotonesVoz", "f", 1.8, "4 Final", "Cuanto despues de aparecer los botones habla Alma (VO_36p)."),
 ("Res_SalidaRetardo", "f", 0.5, "4 Final", "Cuanto despues de elegir se va el cuadro."),
 ("Res_Cortafuegos", "f", 30.0, "4 Final", "Si nadie elige SHARE/DON'T SHARE en N s, se elige solo."),
 ("Res_Tope", "f", 150.0, "4 Final", "Cortafuegos de toda la fase de resultados."),
 ("Comp_Nado", "f", 4.0, "4 Final", "SHARE: cuanto nada el alma hasta la puerta."),
 ("Comp_Lejos", "f", 3.0, "4 Final", "SHARE: cuanto tarda el alma en irse por la puerta."),
 ("Salida_HallA", "f", 0.5, "4 Final", "Cuando arranca la salida del Hall hacia la constelacion."),
 ("Const_AlmaLlega", "f", 5.0, "4 Final", "Constelacion: cuando aparece tu alma (si compartiste)."),
 ("Const_Voz35", "f", 8.0, "4 Final", "Constelacion: cuando suena VO_35b."),
 ("Const_Voz37TrasVoz", "f", 0.6, "4 Final", "Constelacion: margen entre VO_35b y VO_37."),
 ("Creditos_Dur", "f", 60.0, "4 Final", "Duracion de la constelacion con creditos."),
 ("Fundido_Dur", "f", 3.5, "4 Final", "Fundido final antes de reiniciar la obra."),
]
NAMES = [p[0] for p in P]
