# edit_apk_1020z.py - 2026-10-20 (noche), lo que vio Beltran en el APK Demo_BDW. Respaldos *_backup_1020z.py.
# 1) Click de audio al cambiar de nivel: antes de cada OpenLevel el volumen MAESTRO (submix MasterSubmixDefault, variable MasterMix)
#    baja a 0 con margen, y cada nivel lo devuelve a 1 al arrancar (la musica entra con su FadeIn de 3 s). Asi nada se corta sonando.
#    - Experiencia (EndTick, fase 18 = negro): rampa 1 -> 0 en 3 s y el menu se abre a los 4 s (antes 3 s, con la musica aun en cola).
#    - Menu (fase 10 = el velo se cierra al color de la experiencia, 6 s): la musica SIGUE sonando (ya no FadeAll al empezar el cierre:
#      eso dejaba ~7 s de silencio) y el maestro baja de 3,0 a 6,0 s; la experiencia se abre a los 6,5 s.
# 2) Menu -> experiencia mas corto (~50 s desde que se elige): la bienvenida a los VoDelay s (instancia 6 -> 3), VoGap 2,5 -> 1,2 s,
#    VO_D03 a los 2,5 s de instalado el HUD (antes 4), "You're ready" a los 3 s (antes 5), y el cierre arranca 0,6 s despues de que
#    termina la voz (antes VoGap).
import shutil


def edit(p, reps):
    shutil.copy(p, p.replace('.py', '_backup_1020z.py'))
    s = open(p, encoding='utf-8').read()
    for a, b in reps:
        assert s.count(a) == 1, (p, s.count(a), a[:140])
        s = s.replace(a, b)
    open(p, 'w', encoding='utf-8').write(s)
    print(p, 'ok')


MM = '(Variables|Default|GetMasterMix)'

edit('flow_dsl.py', [
    ("CODES['FBoot'] = '''(fn FBoot ()\n",
     "# 20-10 noche: FBoot devuelve el volumen maestro a 1 (el nivel anterior lo bajo a 0 antes del OpenLevel: sin click al cambiar de nivel)\n"
     "CODES['FBoot'] = '''(fn FBoot ()\n  (Audio|SetSubmixOutputVolume(lineargain) " + MM + " 1.0)\n"),
    ("""    (:3
      (if (>= _pt 3.0)
        %(g19)s""",
     """    (:3
      (Audio|SetSubmixOutputVolume(lineargain) %(mm)s (- 1.0 (Math|Float|MapRangeClamped _pt 0.0 3.0 0.0 1.0)))
      (if (>= _pt 4.0)
        %(g19)s"""),
    ("           amb=D('Amb'), menu=D('MenuLevel'), g16=GOPH(16),",
     "           amb=D('Amb'), mm=D('MasterMix'), menu=D('MenuLevel'), g16=GOPH(16),"),
])

edit('menu_dsl.py', [
    ("CODES['Boot'] = '''(fn Boot ()\n  (bind _veil %(veil)s)\n",
     "CODES['Boot'] = '''(fn Boot ()\n  (Audio|SetSubmixOutputVolume(lineargain) " + MM + " 1.0)\n  (bind _veil %(veil)s)\n"),
    ("""      (if (and (not %(said)s) (>= _pt 4.0))
        %(said1)s
        (Class|BPDemoVoiceSC|Say :self %(voice)s :Clip %(vom)s)
        (elif (and %(said)s (and (>= _pt 5.0) (>= %(qt)s %(gap)s)))""",
     """      (if (and (not %(said)s) (>= _pt 2.5))
        %(said1)s
        (Class|BPDemoVoiceSC|Say :self %(voice)s :Clip %(vom)s)
        (elif (and %(said)s (and (>= _pt 3.0) (>= %(qt)s %(gap)s)))"""),
    ("""    (:9
      (if (and (>= _pt 1.0) (>= %(qt)s %(gap)s))
        (Rendering|Material|SetColorParameterValueOnMaterials %(veil)s "CTop" %(ctopx)s)
        (Rendering|Material|SetColorParameterValueOnMaterials %(veil)s "CHor" %(chorx)s)
        (Class|BPDemoAmbSC|FadeAll %(amb)s)
        %(ph10)s""",
     """    (:9
      (if (and (>= _pt 1.0) (>= %(qt)s 0.6))
        (Rendering|Material|SetColorParameterValueOnMaterials %(veil)s "CTop" %(ctopx)s)
        (Rendering|Material|SetColorParameterValueOnMaterials %(veil)s "CHor" %(chorx)s)
        %(ph10)s"""),
    ("""    (:10
      (if (>= _pt 6.5)""",
     """    (:10
      (Audio|SetSubmixOutputVolume(lineargain) %(mm)s (- 1.0 (Math|Float|MapRangeClamped _pt 3.0 6.0 0.0 1.0)))
      (if (>= _pt 6.5)"""),
    ("''' % dict(ctopx='(select (== %s 1) %s (select (== %s 3) %s %s))' % (Z('Choice'), M('TopA'), Z('Choice'), D('TopC'), M('TopB')),",
     "''' % dict(mm=D('MasterMix'), ctopx='(select (== %s 1) %s (select (== %s 3) %s %s))' % (Z('Choice'), M('TopA'), Z('Choice'), D('TopC'), M('TopB')),"),
])
