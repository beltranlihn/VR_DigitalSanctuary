# BP_OSCReceiver — progress tracker

- **refPath**: `/Game/OSC/BP_OSCReceiver.BP_OSCReceiver` (class `BP_OSCReceiver_C`; in node ids it's `BPOSCReceiver`)
- **parent**: Actor · **in level**: yes (user placed it)
- **Purpose**: Runs an OSC server that receives float messages over the LAN and exposes them as variables for other BPs to read.
- **Status**: 🟢 done (scale path working)

## Variables
- `OSCServer` : OSCServer ref — holds the running server (prevents GC). public.
- `scale` : float — latest value from OSC address `/muse`. public (read by Ball).

## Graphs
- **EventBeginPlay**: `CreateOSCServer("0.0.0.0", 8000, multicast=false, listen=true, "VR_OSCServer")` → `SetOSCServer` → `AssignOnOscMessageReceived(server, OnOscMessageReceived_Event)`.
- **OnOscMessageReceived_Event (Message, IPAddress, Port)** (Assign-generated, correctly typed): `GetOSCMessageAddress` → `ConvertOSCAddressToString` → `SwitchOnString` → case **`/muse`** → `GetOSCMessageFloatAtIndex(Message, 0)` → `Set scale`.

## Done ✅
- OSC server on 0.0.0.0:8000, listening.
- `/muse` float → `scale` variable.

## TODO / next
- Add more address cases (each → its own variable) as needed. Remember: SwitchOnString case strings are set in the editor Details panel, NOT via API — don't rewrite the switch by DSL (it duplicates & loses `/muse`).
- Optional: remap/clamp incoming float before storing.

## Open questions / risks
- OSC listens on UDP 8000; the MCP server uses TCP 8000 (no conflict, distinct protocols).

## Session log
- 2026-07-15: created; OSC server + delegate (via Assign node) + `/muse`→scale. Untangled duplicate events from an earlier DSL-rewrite mistake; now clean.
