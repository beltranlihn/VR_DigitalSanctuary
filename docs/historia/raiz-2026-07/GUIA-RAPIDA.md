# Guía rápida — trabajar con Claude en Soul Charger

Prácticas del lado del usuario para que Claude trabaje mejor y gaste menos tokens.

## Las 4 que más ayudan
1. **Abre Unreal ANTES de abrir Claude, y déjalo abierto toda la sesión.**
   El MCP se conecta al arrancar Claude; si Unreal no está corriendo, Claude no tiene las herramientas (hay que reiniciar Claude). Si el editor se cierra a mitad de sesión, se pierde el MCP y se rompe el cache.
2. **`/clear` al cambiar de tema** (otro Blueprint, otro subsistema).
   No arrastrar una sesión eterna: el contexto viejo se paga en cada mensaje.
3. **Elige modelo / effort / fast al INICIO de la sesión y no los cambies a mitad.**
   Cada cambio reprocesa todo el contexto a precio completo. Si necesitas cambiarlos, hazlo junto con un `/clear` (ahí el cache se reconstruye de todos modos, así que el cambio sale gratis).
4. **Save All en Unreal antes de pedir `/commit`.**
   Git ve el `.uasset` en disco, no lo que esté sin guardar en el editor.

## Para menos idas y vueltas (menos tokens)
5. **Prompts específicos.** "Agrega un branch en la función X del BP Y" rinde mucho más que "mejora esto" (que obliga a escanear todo).
6. **Da el error textual, un screenshot, o qué esperabas.** Cuando Claude puede verificar contra algo concreto, no gasta vueltas adivinando.
7. **Lo que Claude no puede crear** (structs, enums, plugins, project settings) **pídelo por lote**, con nombres y campos definidos, para hacerlo de una sola vez.

## Comandos útiles
- **`/usage`** y **`/context`** → ver el consumo y cuándo conviene `/clear`.
- **`/clear`** (tarea nueva) · **`/compact`** (corte dentro de la misma tarea) · **`/rewind`** (abandonar un camino; más barato que `/compact`).
- **`/commit`** → respaldo a GitHub (Soul Charger).
- **Plan mode (Shift+Tab)** antes de una tarea grande: Claude propone el enfoque y tú lo apruebas, evitando retrabajo caro. **Escape** para frenar si va por mal camino.

## No hace falta repetir
El target Quest 3, el flujo del proyecto y las preferencias (incluido el idioma) ya están en la memoria y la skill; se cargan solos.
