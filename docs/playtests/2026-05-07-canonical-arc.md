# Canonical A → B1 → C1 playthrough — 2026-05-07

**Run by:** `node scripts/dump-canonical-arc-transcript.mjs`. Drives
the verbatim command list from `tests/e2e/canonical-arc.spec.ts` against
the current build, and captures `#story-output` at the end. No bucket
overrides — morale is whatever the playthrough naturally produces, so
the m5 perception variants land at the bucket the player would actually
hit at the cupola viewport.

**Final state:** O2 58%, morale 53%, room `Command Module`, inventory: multimeter, dosimeter, Yevgenia's flight notebook, flashlight b1=4 b2=2 act2=engineer

**Verifies:**

- All assertions from `tests/e2e/canonical-arc.spec.ts` (Zhuchok, Main
  Corridor, Life Support, World War III, isolated power bus, four-digit
  safe code, armament bay, Commander Diane Chen, Begin preparations)
- The `cupola-nadir-war` perception variant fires at whatever morale
  bucket the player actually lands in by the time they examine the
  viewport. The other four variant sites (`cupola-nadir-revisit`,
  `examine-yevgenia`, `examine-petrov`, `reactor-radiation-tick`)
  are not on the canonical path; their bucket-forced dump lives in
  `2026-05-07-m5-perception.md`.
- No `[PERCEIVE …]` or `[MIRSEND …]` markers leak to the visible panel

---

## Full transcript

```
[Interpreter connected.]
You were sleeping. The bunk warm. The harness loose against you. The station thrumming the way it always does. Three small comforts you were not aware of having.

Then the crash. Not a sound. A weight. The whole station shoved sideways like a bottle off a shelf. A light went off behind your eyes. Not a flash. A whole room of sun. Inside your skull. For one impossible second.

Then nothing.

Now. You are floating. Your face is wet. You touch your forehead and your hand comes back warm and dark. You bang the back of your head on the bulkhead trying to right yourself and that is what brings you all the way back into the room.

The room is black. The kind of black that does not have lights coming back on in it. You can hear your own breath. You can hear the long whistle of air leaving somewhere it shouldn't. Slowing. Stopping. Then nothing. The absolute nothing of a station that is not running.

You are bleeding. You do not know how badly. You float in your sleeping harness. Second bunk from forward. Port wall. Crew Quarters. Whatever happened was not small.

[New here? Type HELP for a list of commands. STATUS shows your vitals. LOOK describes the room. EXAMINE [thing] inspects an object.]

MIR'S END

An Interactive Survival Story by Seith Miller

Release 1 / Serial number 260506 / Inform 7 v10.1.2 / D

Crew Quarters

[Auto-saved]
You float in the sleeping bay of Mir-3. Four bunks in slots along the port wall. Yours is the second from forward.

The darkness is absolute. You can barely see your hand.

A sealed hatch forward to the main corridor. A second hatch aft, trefoil-marked, to the Reactor Module.

You can see an emergency locker (closed), a photograph, a pen and a chocolate bar here.

>‍

You open the emergency locker, revealing a flashlight.

[Your score has just gone up by one point.]

>‍

Taken.

>‍

You squeeze the lever. Quick rhythm. The dynamo whirs up with that familiar beetle-drone. The little lamp throws a warm yellow beam across the bay. Cables. Straps. The edges of your bunk. Shadows resolve into real objects again.

[Your score has just gone up by one point.]

>‍

You pull the lever.

A long wet hiss. Air rushes past you. The stale warm of your module bleeding through the valve into the cold beyond. Your ears pop. Objects not tethered down drift toward the hatch. The photograph. The pen. A drop of condensation. Pulled by the last of the pressure differential.

The hiss fades. The needle on the gauge swings up from zero and stops somewhere low. Sufficient. Your eardrums settle. The hatch releases with a soft mechanical clunk.

You have just shared half your air with a vacuum. It had to be done.

[Your score has just gone up by one point.]

>‍

Main Corridor

[Auto-saved]
The main corridor of Mir-3 is the central node. Six ports meeting at a single volume. It is wrong in every way you can parse. Cold. Low-pressure. Silent in a way that is not the silence of a machine at rest but the silence of a place something has happened to.

Frost glazes the inner hull where the breach vented. Loose objects drift in a slow parade. A mug. A clipboard. A flight manual open to a page no one will finish reading.

Yevgenia Kozlova floats near the maintenance panel. You look at her once. Then you look away.

Hatches lead in every direction. Fore (north) to the Command Module. Aft (south) to the Crew Quarters. Starboard (east) to the Armament Bay, its hatch marked КАТАЛОГ ВМФ-07 and dogged shut. Port (west) to the Hydroponics Lab. Zenith (up) to Life Support. Nadir (down) to the Observation Cupola.

>‍

You unclip the notebook from the front of her suit. You try not to disturb her more than you have to.

>‍

You turn to the last full page.

EMP confirmed. Not solar. Not ours. Military grade. Every bus fried simultaneously.

Reactor tripped clean. Isolated bus in the command module SHOULD still be intact. Capacitors look OK on external inspection. Requires multimeter and manual hard-reset sequence. See margin notes.

Life support: twelve to eighteen hours on passive LiOH. After that, CO₂ wins.

Selengrad burn: combined delta-v from Mir-3 and one American station. 1,247 m/s if we shed non-essential mass. Window opens in 9h. One station alone cannot make it. The Moon is a delta-v problem.

КАТАЛОГ ВМФ-07. Code is 1524. I am the only one on the station who knows it now.

ARGON-87 still online. Backup telemetry AI on the isolated bus. Ask him about transmit if comms are restored. He may have heard something we cannot.

Need Petrov to authorize the approach to the Americans. He will hate it. He will agree. He knows we have no other option.

There is nothing else in the notebook. The margin math confirms the Selengrad trajectory. Fuel. Time. The burn window. If Mir-3 combines reserves with Freedom Station.

>‍

Life Support Module

A cylindrical compartment. Institutional green of Soviet spaceflight. Every inner surface is equipment.

Forward, the O₂ generator stands silent. Beneath it, a stack of lithium-hydroxide canisters tick passively. The only thing keeping you alive. Aft, a water recycler drips condensate into a catch-tray. On the port wall, CO₂ scrubbers hang dark. Their fans stopped by the EMP. On the starboard wall, a dosimeter panel glows faintly. It has its own power cell. Nothing else in here does. Overhead, an emergency EVA airlock is dogged shut.

The hatch to the central node is below you (nadir).

You can see a dosimeter here.

>‍

Taken.

>‍

Main Corridor

The main corridor of Mir-3 is the central node. Six ports meeting at a single volume. It is wrong in every way you can parse. Cold. Low-pressure. Silent in a way that is not the silence of a machine at rest but the silence of a place something has happened to.

Frost glazes the inner hull where the breach vented. Loose objects drift in a slow parade. A mug. A clipboard. A flight manual open to a page no one will finish reading.

Yevgenia Kozlova floats near the maintenance panel. You look at her once. Then you look away.

Hatches lead in every direction. Fore (north) to the Command Module. Aft (south) to the Crew Quarters. Starboard (east) to the Armament Bay, its hatch marked КАТАЛОГ ВМФ-07 and dogged shut. Port (west) to the Hydroponics Lab. Zenith (up) to Life Support. Nadir (down) to the Observation Cupola.

>‍

Observation Cupola

[Auto-saved]
The observation cupola is a blister of reinforced glass on the station's nadir side. Commander Petrov is here. He did not make it inside.

Through the viewport, the Earth below. Something is wrong with the nightside.

The hatch back to the central node is above you (zenith).

>‍



You press your face to the glass. You look down. The Earth is below you, the way it always is.

The nightside should be a field of glittering city lights.

Instead, the Earth is on fire. Not continent-wide fire. Point fire. Hundreds of points. Blooms of orange and white. Some already fading. Some still expanding in slow-motion circles. Fresh ones joining them every few seconds.

You try to count the new flashes. Seven. Nine. Fourteen. The number keeps climbing.

This is not the aftermath of something. This is happening now. Thermonuclear weapons, in the hundreds, detonating beneath you in real time.

World War III. From three hundred kilometres up you have the clearest view of it ever captured by human eyes.

The silence that follows is heavier than vacuum.

>‍

Main Corridor

[Auto-saved]
The main corridor of Mir-3 is the central node. Six ports meeting at a single volume. It is wrong in every way you can parse. Cold. Low-pressure. Silent in a way that is not the silence of a machine at rest but the silence of a place something has happened to.

Frost glazes the inner hull where the breach vented. Loose objects drift in a slow parade. A mug. A clipboard. A flight manual open to a page no one will finish reading.

Yevgenia Kozlova floats near the maintenance panel. You look at her once. Then you look away.

Hatches lead in every direction. Fore (north) to the Command Module. Aft (south) to the Crew Quarters. Starboard (east) to the Armament Bay, its hatch marked КАТАЛОГ ВМФ-07 and dogged shut. Port (west) to the Hydroponics Lab. Zenith (up) to Life Support. Nadir (down) to the Observation Cupola.

>‍

Command Module

[Auto-saved]
The command module. Cramped. Packed with control panels. Every panel is dead. On the zenith wall, a small armored safe. КАТАЛОГ ВМФ-07. On the nadir wall, the emergency toolkit. Forward, external observation ports and dead navigational radar displays. The main corridor is aft (south). The Soyuz ferry is docked to starboard (east).

You can see an emergency toolkit (closed), a status console and a communications array here.

>‍

You open the emergency toolkit, revealing a multimeter.

>‍

Taken.

>‍

You work alone. Yevgenia's notebook wedged open beside the console with a bent clip.

Her handwriting walks you through it. Test the capacitor bank first. Green. Short the reset pin to ground for three seconds. You count under your breath. Reseat the isolation relay. You are not an engineer. You follow the instructions of a dead woman as carefully as anyone has ever followed anything.

With a sharp crack and a brief flash, the status console flickers to life.

Her notes have a short margin comment at this point. if it sparks here, you did it right. You let yourself breathe.

The screen is dim. Half the pixels are dead. But it works. Status readouts begin scrolling. Most of them bad.

[Your score has just gone up by three points.]

>‍

You pull up Petrov's last log entry. He dictated it to the console. Timestamped minutes after the EMP. Minutes before the impact.

Commander Vasili Petrov, Mir-3. Time is 03:52 Moscow. Status: EMP event confirmed at 03:47. All systems offline. Kozlova believes the isolated bus in this module is recoverable. We are assembling tools.

Sensor scrape suggests a second object inbound. I do not know what it is. I do not recognize the profile. If this station survives the next hour, whoever is listening will need to know. The armament bay on this module is intact. Kozlova has the access code. Use it if you have to. The weapon is aboard for a reason. We may not have been told all of them.

If you are reading this and I am not still talking. Do what you can. Make it worth something.

The log ends. The console shows the timestamp of its last write. 03:53. One minute before the impact.

[Your score has just gone up by one point.]

>‍

You enter 1-5-2-4. A single green light acknowledges. Somewhere behind the wall a heavy magnetic bolt withdraws with a dull metallic tock. Then a second, further away. The hatch to the armament bay has dogged itself open.

You have just armed yourself in space. Whatever that means now.

[Your score has just gone up by two points.]

>‍

You tune the communications array carefully through the static.

Through the noise, a voice. Faint. Broken. Unmistakably human. Unmistakably English.

...this is Freedom Station, transmitting on emergency frequency... if anyone... we have sustained critical damage from the electromagnetic pulse... life support failing... request assistance from any station, any vessel... five crew, two injured... oxygen reserves critical...

The transmission loops. An automated distress call.

Freedom Station. The American orbital platform. Your mirror image. The Americans are dying.

Below you, the nations that built both your stations are still destroying each other.

>‍

You key the microphone yourself. There is no one else to key it for you.

Freedom Station, this is Mir-3. We read your distress call. Say your status. Over.

The loop cuts. A pause. Long enough that you think the signal is gone. Then a new voice. Live. Shaking with relief and surprise.

Mir-3... oh my God. This is Commander Diane Chen, Freedom Station. We... we did not expect anyone to answer.

You trade damage reports with a stranger. Five crew on her side. Two injured. One on yours. No injured. You skip over the word alive. She skips over it too.

You open Yevgenia's notebook. You tell Chen about Selengrad.

A pause. Then her voice again. Quieter. You are proposing we fly to the Moon.

I am proposing we try. It is that or a slow death in orbit.

Five American survivors. You. One lunar base in caretaker mode. One plan scribbled in a dead engineer's handwriting.

Begin preparations, Chen says, after a long silence. We have work to do.

[Your score has just gone up by five points.]

>‍


```
