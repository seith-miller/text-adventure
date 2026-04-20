"MIR'S END" by "Seith Miller"

The story headline is "An Interactive Survival Story".
The story genre is "Science Fiction".
The story description is "You awaken aboard the Soviet space station Mir-3 after a catastrophic impact. The rest of the crew is dead. The world below is ending. Now you must survive."
The release number is 1.

Use scoring.

Part 1 - Resources and Status

Chapter 1 - Resource Variables

Oxygen-level is a number that varies. Oxygen-level is 100.
Morale-level is a number that varies. Morale-level is 50.

Chapter 2 - Status Bar

[In-story status bar intentionally omitted. The Web UI renders
 O2 / Morale / Inventory from window.MirsEnd.setState, driven by
 the MIRSEND status line emitted below. The Inform 7 v10.1.2
 compiler we use doesn't recognize "fill status bar with ...", and
 we don't need an in-game bar since the Web UI covers it.]

Chapter 3 - Oxygen Timer

Every turn:
	decrease oxygen-level by 1;
	if oxygen-level <= 0:
		say "The air has grown impossibly thin. Your vision tunnels. You fought as long as you could, but without oxygen, the darkness wins.";
		end the story saying "You have suffocated".

Chapter 4 - UI Status Bridge

[Emit a machine-readable status line every turn so the Web UI can mirror
 oxygen-level / morale-level / inventory into window.MirsEnd.setState.
 ui.js detects the [MIRSEND ...] prefix, parses it, and suppresses it
 from the visible story panel.]

To say mirsend-inventory-list:
	let counter be 0;
	repeat with item running through things carried by the player:
		if counter > 0:
			say ",";
		say "[printed name of item]";
		increment counter.

Every turn:
	say "[line break][bracket]MIRSEND o2=[oxygen-level] morale=[morale-level] inv=[mirsend-inventory-list][close bracket][line break]".

Part 2 - The Station

Chapter 1 - Crew Quarters

The Crew Quarters is a room. "You float in the cramped sleeping bay of Mir-3.[if the chemical flashlight is lit] The warm yellow beam from the Zhuchok reveals chaos — personal effects drift in zero-g: a photograph, a pen, a sachet of reconstituted borscht. The status panel above your bunk is dead black.[otherwise] The darkness is absolute. You can barely see your hand in front of your face.[end if] A sealed hatch leads north to the main corridor."

The player is in the Crew Quarters.

The sleeping harness is scenery in the Crew Quarters. The description of the sleeping harness is "A standard-issue cosmonaut sleeping harness, bolted to the bulkhead. Half the straps are torn — you tore them yourself in the first confused seconds after the shock that woke you."

The emergency locker is a closed openable container in the Crew Quarters. The emergency locker is fixed in place. The description of the emergency locker is "A sturdy metal locker magnetically latched to the wall, marked with a red cross.[if the emergency locker is open and the chemical flashlight is in the emergency locker] Inside you can see a Zhuchok — the hand-dynamo flashlight every cosmonaut grew up with.[end if]"

Instead of taking the emergency locker:
	say "The locker is bolted to the bulkhead. It's not going anywhere."

[The Inform name "chemical flashlight" is kept for schema stability with
 save files and tests; the player sees "Zhuchok" via the printed name
 and Understand synonyms below.]
The chemical flashlight is a thing in the emergency locker. The printed name of the chemical flashlight is "flashlight". Understand "zhuchok" or "zhuk" or "torch" or "dynamo" or "lamp" as the chemical flashlight. The description of the chemical flashlight is "A Zhuchok — Bakelite body, a small folding squeeze-lever, made in Krasnodar sometime in the last thirty years. No batteries; the lever spins a tiny generator against a rotor and the whole thing whirs like its namesake beetle when you pump it.[if lit] It is throwing a warm, unsteady yellow beam right now.[otherwise] Give it a few squeezes and the lamp will glow for as long as you keep pumping.[end if]".

The chemical flashlight can be lit or unlit. The chemical flashlight is unlit.

The chemical flashlight is a device.

Instead of switching on the chemical flashlight:
	if the chemical flashlight is not carried by the player:
		try silently taking the chemical flashlight;
	if the chemical flashlight is lit:
		say "The Zhuchok is already glowing.";
	otherwise:
		now the chemical flashlight is lit;
		increase morale-level by 5;
		say "You squeeze the lever in a quick rhythm. The dynamo whirs up with that familiar beetle-drone and the little lamp throws a warm yellow beam across the bay. Shadows — cables, straps, the edges of your bunk — resolve into real objects again."

The photograph is a thing in the Crew Quarters. The description of the photograph is "A small photograph of a family standing before a dacha in winter. The faces smile from another lifetime."

The pen is a thing in the Crew Quarters. The description of the pen is "A standard-issue ballpoint pen, drifting lazily in zero gravity."

The bunk status panel is scenery in the Crew Quarters. The description of the bunk status panel is "The status panel above your bunk is dead black. Not even the emergency indicators are lit."

Chapter 2 - The Sealed Hatch

[The hatch north is held shut by a pressure differential: the corridor
 depressurized when the station was struck. The pressure-equalization
 valve bleeds your module's atmosphere into the corridor until
 pressures roughly match. Mechanical; works with no power.]

Corridor-pressurized is a truth state that varies. Corridor-pressurized is false.

The sealed hatch is scenery in the Crew Quarters. Understand "hatch" or "door" or "bulkhead" or "seal" as the sealed hatch. The description of the sealed hatch is "A heavy steel hatch, emergency-sealed. Its small porthole is fogged with frost from the other side. You can feel the cold of vacuum coming through the metal. Beside the hatch is a red-painted emergency pressure-equalization valve with a three-language warning placard."

The pressure valve is scenery in the Crew Quarters. Understand "valve" or "lever" or "equalizer" or "equaliser" or "placard" or "emergency valve" as the pressure valve. The description of the pressure valve is "[if corridor-pressurized is true]The valve is in its open position. A faint whisper still moves through it as the air in the Crew Quarters continues to equalize with the corridor beyond. Pressure is stable — low, but breathable.[otherwise]A red-painted lever, set into the bulkhead next to the sealed hatch. The placard reads, in Russian, English, and German: EMERGENCY EQUALIZATION. OPERATE ONLY IF CORRIDOR VENTED. IRREVERSIBLE. The needle beside it reads zero on the corridor side.[end if]"

Opening the pressure valve is an action applying to nothing.
Understand "turn valve" or "pull valve" or "pull lever" or "turn lever" or "open valve" or "use valve" or "equalize" or "equalise" or "equalize pressure" or "pressurize corridor" or "pressurise corridor" as opening the pressure valve.

Check opening the pressure valve:
	if the player is not in the Crew Quarters:
		say "You aren't at the valve." instead;
	if corridor-pressurized is true:
		say "The valve is already open. Pressure equalized some time ago." instead.

Carry out opening the pressure valve:
	now corridor-pressurized is true.

Report opening the pressure valve:
	say "You pull the lever.[paragraph break]A long, wet hiss. Air rushes past you — the stale warm of your module bleeding through the valve into the cold beyond. Your ears pop. Objects not tethered down — the photograph, the pen, a drop of condensation — drift toward the hatch, pulled by the last of the pressure differential.[paragraph break]The hiss fades. The needle on the gauge swings up from zero and stops somewhere low, but sufficient. Your eardrums settle. The hatch releases with a soft mechanical clunk.[paragraph break]You have just shared half your air with a vacuum. It had to be done."

Chapter 3 - Main Corridor

The Main Corridor is north of the Crew Quarters. "The main corridor of Mir-3 stretches in both directions, a tunnel of drifting debris and dead screens. It is wrong in every way you can parse — cold, low-pressure, and silent in a way that is not the silence of a machine at rest but the silence of a place something has happened to.[paragraph break]Frost glazes the inner hull where the breach vented. Loose objects float in a slow-motion parade: a mug, a clipboard, a flight manual open to a page no one will finish reading.[paragraph break]Yevgenia Kozlova floats near the maintenance panel. You look at her once, and then you look away.[paragraph break]The crew quarters lie to the south, the command module is to the north, and the observation cupola is to the east."

The drifting debris is scenery in the Main Corridor. The description of the drifting debris is "Cables hang loose from open maintenance panels. Frost layers the inner hull where insulation has lost power. The air is thin and cold; each breath stings the back of your throat."

The frost is scenery in the Main Corridor. The description of the frost is "Thick frost on the inner plates. The breach must have been fast — fast enough that the moisture in the corridor's atmosphere flashed to ice on its way out."

The maintenance panel is scenery in the Main Corridor. The description of the maintenance panel is "An open maintenance panel reveals a tangle of loose cables and blown circuit breakers. Whatever hit the station punched through every system at once."

[Yevgenia's body — was an NPC, now scenery. Keep the Inform object
 name for save-state compatibility.]
Yevgenia is scenery in the Main Corridor. The printed name of Yevgenia is "Yevgenia's body". Understand "yevgenia" or "kozlova" or "engineer" or "body" or "woman" or "her" as Yevgenia. The description of Yevgenia is "Yevgenia Kozlova, the station's engineer, suspended in the middle of the corridor by zero-g. Her face is calm — she probably never registered what happened. A thin film of frost on her eyelashes. She still has her flight notebook clipped to the chest of her suit. The hand nearest the maintenance panel holds a screwdriver she will never put down."

Instead of taking Yevgenia:
	say "You can't bring yourself to move her. Not yet."

Instead of attacking Yevgenia:
	say "She is beyond anything you could do."

Yevgenia's notebook is a thing. Understand "notebook" or "book" or "journal" or "notes" or "her notebook" as Yevgenia's notebook. The printed name of Yevgenia's notebook is "Yevgenia's flight notebook". The description of Yevgenia's notebook is "A water-stained field notebook, half in Cyrillic shorthand, half in numbers. Yevgenia's handwriting. The last entries fill most of a page and are dated tonight. You could read it."

Instead of taking Yevgenia's notebook when Yevgenia's notebook is part of Yevgenia:
	now Yevgenia's notebook is in the Main Corridor;
	now the player carries Yevgenia's notebook;
	say "You unclip the notebook from the front of her suit. You try not to disturb her more than you have to."

Yevgenia's notebook is part of Yevgenia.

Reading is an action applying to one thing.
Understand "read [something]" as reading.

Instead of reading Yevgenia's notebook:
	say "You turn to the last full page.[paragraph break][italic type]EMP confirmed — not solar, not ours. Military grade. Every bus fried simultaneously.[line break]Reactor tripped clean. Isolated bus in the command module SHOULD still be intact — capacitors look OK on external inspection. Requires multimeter + manual hard-reset sequence. See margin notes.[line break]Life support: twelve to eighteen hours on passive LiOH. After that, CO₂ wins.[line break]Selengrad — yes. Caretaker for two years but closed-loop atmosphere and hydroponics should still be functional. Combined fuel reserves from Mir-3 + one American could reach it. One station alone cannot — the Moon is a delta-v problem.[line break]Need Petrov to authorize the approach to the Americans. He will hate it. He will agree. He knows we have no other option.[roman type][paragraph break]There is nothing else in the notebook. The margin math confirms the Selengrad trajectory — fuel, time, the burn window — if Mir-3 combines reserves with Freedom Station."

Chapter 4 - Observation Cupola

The Observation Cupola is east of the Main Corridor. "The observation cupola is a blister of reinforced glass on the station's nadir side. Commander Petrov is here. He did not make it inside.[paragraph break][if war-is-discovered is true]Through the viewport you can see the Earth below. Fresh nuclear flashes keep blooming across the nightside — new ones every few seconds, a constellation of deaths.[otherwise]Through the viewport you can see the Earth below. Something seems wrong with the nightside.[end if][paragraph break]The corridor lies to the west."

The viewport is scenery in the Observation Cupola.

War-is-discovered is a truth state that varies. War-is-discovered is false.

Instead of examining the viewport:
	if war-is-discovered is false:
		now war-is-discovered is true;
		decrease morale-level by 15;
		say "You press your face to the reinforced glass and look down at the Earth.[paragraph break]The nightside should be a field of glittering city lights.[paragraph break]Instead, the Earth is on fire. Not continent-wide fire — point fire. Hundreds of points. Blooms of orange and white: some already fading, some still expanding in slow-motion circles, fresh ones joining them every few seconds.[paragraph break]You try to count the new flashes. Seven. Nine. Fourteen. The number keeps climbing.[paragraph break]This is not the aftermath of something. This is happening now. Thermonuclear weapons, in the hundreds, detonating beneath you in real time.[paragraph break]World War III. And from three hundred kilometres up you have the clearest view of it ever captured by human eyes.[paragraph break]The silence that follows is heavier than vacuum.";
	otherwise:
		say "You look down. The flashes are still coming. Fewer now, perhaps, or perhaps only harder to pick out from the smoke. You force yourself to look away."

Understand "look through [something]" as examining.

The reinforced glass is scenery in the Observation Cupola. The description of the reinforced glass is "Thick reinforced glass designed to withstand micrometeorite impacts. Right now it frames the worst view in human history."

[Petrov's body — was an NPC, now scenery.]
Petrov is scenery in the Observation Cupola. The printed name of Petrov is "Commander Petrov's body". Understand "petrov" or "commander" or "body" or "man" or "him" as Petrov. The description of Petrov is "Commander Petrov, thirty years' service, one hand still on the hatch wheel. He was trying to get inside the cupola — trying to see for himself what was happening to the country that built him. The hatch was sealed by the breach before he could. His eyes are open. His face is the face of a man who worked it out in the last two seconds he had."

Instead of taking Petrov:
	say "You can't."

Instead of attacking Petrov:
	say "He is beyond anything you could do."

The mechanical watch is a thing that is part of Petrov. The description of the mechanical watch is "Petrov's mechanical watch — no electronics, unaffected by the EMP. It still ticks. It reads just past 03:47 Moscow time. The impact was not long ago."

Instead of taking the mechanical watch:
	say "You consider taking the watch. You decide against it. Let him keep the time."

Chapter 5 - Command Module

The Command Module is north of the Main Corridor. "The command module is a cramped space packed with control panels.[if power-is-restored is true] A single console flickers with dim, partial life — the isolated power bus has been restored. The main corridor is to the south.[otherwise] Every panel is dead. The main corridor is to the south.[end if]"

Power-is-restored is a truth state that varies. Power-is-restored is false.

The control panels are scenery in the Command Module. The description of the control panels is "[if power-is-restored is true]Most panels remain dead, but the working console on the main bus flickers with partial life.[otherwise]Row upon row of switches, dials, and screens — all dark. The electromagnetic pulse killed every system simultaneously.[end if]"

The emergency toolkit is a closed openable container in the Command Module. The emergency toolkit is fixed in place. The description of the emergency toolkit is "A toolkit magnetically latched to the wall, containing essential repair instruments."

The multimeter is a thing in the emergency toolkit. The description of the multimeter is "A sturdy analogue multimeter — one of the few instruments unaffected by the EMP. Essential for diagnosing electrical faults."

The manual pressure gauges are scenery in the Command Module. The description of the manual pressure gauges is "Analogue pressure gauges — the only instruments still functioning. They show hull pressure is low but stable, CO₂ levels are slowly rising, and there is a clear indication of a hull breach along the central service node. Whatever hit the station hit it there."

The status console is a device in the Command Module. The status console is fixed in place. The status console is switched off. The description of the status console is "[if power-is-restored is true]The screen is dim and half the pixels are dead, but it works. Status readouts scroll across it — most of them bad. Hull integrity compromised at the service node. Life support offline. Communications array available. Oxygen reserves: critical. The console also holds Commander Petrov's last log entry, flagged for review.[otherwise]The main status console is completely dead. No power reaches it.[end if]"

To say comms-status-powered:
	if distress-call-heard is false:
		say "The communications array is patched into the restored power bus. You could try to use it to listen for signals.";
	otherwise if responded-to-americans is true:
		say "The radio crackles with the open channel to Freedom Station.";
	otherwise:
		say "Through the static, you can hear the faint American distress call repeating on the emergency frequency."

The communications array is a thing in the Command Module. The communications array is fixed in place. The description of the communications array is "[if power-is-restored is true][comms-status-powered][otherwise]The communications array is dead without power.[end if]"

Understand "radio" as the communications array.

Reading Petrov's log is an action applying to nothing.
Understand "read log" or "read petrov's log" or "read commander's log" or "read console log" or "review log" as reading Petrov's log.

Petrov-log-read is a truth state that varies. Petrov-log-read is false.

Check reading Petrov's log:
	if the player is not in the Command Module:
		say "You aren't at the console." instead;
	if power-is-restored is false:
		say "The console is dead. No power to read anything." instead.

Carry out reading Petrov's log:
	now petrov-log-read is true.

Report reading Petrov's log:
	say "You pull up Petrov's last log entry. He dictated it to the console, timestamped minutes after the EMP, minutes before the impact.[paragraph break][italic type]Commander Vasili Petrov, Mir-3. Time is 03:52 Moscow. Status: EMP event confirmed at 03:47. All systems offline. Kozlova believes the isolated bus in this module is recoverable. We are assembling tools.[line break]Sensor scrape suggests a second object inbound. I do not know what it is. I do not recognize the profile. If this station survives the next hour, whoever is listening will need to know: the armament bay on this module is intact. The arming sequence is THREE-SEVEN-ONE-ONE. Use it if you have to. The weapon is aboard for a reason, and we may not have been told all of them.[line break]If you are reading this and I am not still talking — do what you can. Make it worth something.[roman type][paragraph break]The log ends. The console shows the timestamp of its last write: 03:53. One minute before the impact."

Part 3 - Classified Armament Reveal

The classified safe is scenery in the Command Module. Understand "safe" or "classified safe" or "armoury" or "armory" or "armament" or "panel" or "classified panel" as the classified safe. The description of the classified safe is "A wall-mounted safe with a four-digit keypad. Above it, a stenciled Cyrillic placard reads КАТАЛОГ ВМФ-07 — a military cataloging prefix. You did not know this was here before tonight.[if petrov-log-read is true] Petrov's log gave you an arming sequence: three-seven-one-one.[end if]"

[Opening the safe is deferred to a later PR along with the cannon mechanic.]
Instead of opening the classified safe:
	if petrov-log-read is false:
		say "The safe is keypad-locked. You do not have the code.";
	otherwise:
		say "You enter three-seven-one-one. A single green light acknowledges. A soft magnetic click somewhere behind the wall. But nothing else has power, and whatever this safe controls is not ready to answer you. Not yet."

Part 4 - Opening Scene

When play begins:
	say "You wake to a shout — not a voice, a physical shout: the station hitting you through your harness. Something enormous has just struck Mir-3.[paragraph break]The lights are out. The air is wrong — thinner than it should be, colder. Your ears are ringing from a pressure change you do not consciously remember. Alarms that must have been going a moment ago have already died. Somewhere, through the bulkhead, you hear the long whistle of venting atmosphere slowing, stopping.[paragraph break]Then: nothing. The absolute nothing of a station that is not running.[paragraph break]You float in your sleeping harness, tearing yourself free of its straps. You have no idea what just happened. You are certain it was not small."

Part 5 - Listening

Listening-to-station is a truth state that varies. Listening-to-station is false.

Instead of listening when the player is in the Crew Quarters and listening-to-station is false:
	now listening-to-station is true;
	decrease morale-level by 3;
	say "You hold your breath and listen.[paragraph break]The station groans — low metal stress, the long settling of something freshly deformed. Through the hatch you can hear the hiss of a slow leak somewhere well beyond the corridor, narrowing, gone.[paragraph break]And nothing else. No voices. No footsteps. No tapping of knuckles against the bulkhead.[paragraph break]If anyone else survived, they are not calling out.[paragraph break]You try to remember how many people were on watch. You try not to remember."

Instead of listening when the player is in the Crew Quarters:
	say "The station groans. Nothing else."

Instead of listening when the player is in the Main Corridor:
	say "The only sounds are thermal expansion of cold metal and the soft drift of objects that used to have a reason to stay in place."

Instead of listening when the player is in the Observation Cupola:
	say "The cupola is quiet. The glass ticks faintly with thermal stress."

Instead of listening when the player is in the Command Module and (power-is-restored is false or distress-call-heard is true):
	say "[if power-is-restored is true]The restored console hums faintly. The communications array crackles with static and, beneath it, the ghost of a signal.[otherwise]Dead silence. Not even the background hum of electronics you have lived with for months.[end if]"

Part 6 - Restoring Power

Restoring power is an action applying to nothing.
Understand "restore power" as restoring power.
Understand "restore systems" as restoring power.
Understand "hard-reset" or "hard reset" or "reset system" or "reset systems" as restoring power.
Understand "fix power" as restoring power.

Check restoring power:
	if the player is not in the Command Module:
		say "You would need to be in the command module to attempt this." instead;
	if power-is-restored is true:
		say "The isolated power bus is already restored. It is not much, but it is all there is." instead;
	if the player does not carry the multimeter:
		say "You need a multimeter to diagnose and restore the electrical systems. There should be one in the emergency toolkit." instead;
	if the player does not carry Yevgenia's notebook:
		say "You know the bus is recoverable — Yevgenia said as much before she died. But you do not remember the reset sequence. She kept notes in her flight notebook." instead.

Carry out restoring power:
	now power-is-restored is true;
	now the status console is switched on;
	increase morale-level by 10.

Report restoring power:
	say "You work alone, Yevgenia's notebook wedged open beside the console with a bent clip.[paragraph break]Her handwriting walks you through it. Test the capacitor bank first — green. Short the reset pin to ground for three seconds — you count under your breath. Reseat the isolation relay. You are not an engineer. You follow the instructions of a dead woman as carefully as anyone has ever followed anything.[paragraph break]With a sharp crack and a brief flash, the status console flickers to life.[paragraph break]Her notes have a short margin comment at this point: *if it sparks here, you did it right*. You let yourself breathe.[paragraph break]The screen is dim and half the pixels are dead, but it works. Status readouts begin scrolling — most of them bad."

Part 7 - Distress Call

Distress-call-heard is a truth state that varies. Distress-call-heard is false.

Instead of listening when the player is in the Command Module and power-is-restored is true and distress-call-heard is false:
	now distress-call-heard is true;
	increase morale-level by 3;
	say "You tune the communications array carefully through the static.[paragraph break]Through the noise, a voice. Faint, broken, but unmistakably human. And unmistakably speaking English.[paragraph break]'...this is Freedom Station, transmitting on emergency frequency... if anyone... we have sustained critical damage from the electromagnetic pulse... life support failing... request assistance from any station, any vessel... five crew, two injured... oxygen reserves critical...'[paragraph break]The transmission loops. An automated distress call.[paragraph break]Freedom Station. The American orbital platform. Your mirror image. The Americans are dying.[paragraph break]Below you, the nations that built both your stations are still destroying each other."

Part 8 - Responding to the Distress Call

Responded-to-americans is a truth state that varies. Responded-to-americans is false.
Chose-silence is a truth state that varies. Chose-silence is false.

Transmitting is an action applying to nothing.
Understand "transmit" as transmitting.
Understand "respond" as transmitting.
Understand "respond to distress call" as transmitting.
Understand "respond to americans" as transmitting.
Understand "answer distress call" as transmitting.
Understand "use radio" as transmitting.
Understand "use communications array" as transmitting.

Check transmitting:
	if the player is not in the Command Module:
		say "You would need to be at the communications array in the command module." instead;
	if power-is-restored is false:
		say "The communications array has no power." instead;
	if distress-call-heard is false:
		say "You turn on the radio but hear only static. Perhaps you should listen more carefully first." instead;
	if responded-to-americans is true:
		say "You are already in contact with Freedom Station. Commander Chen's crew is standing by." instead;
	if chose-silence is true:
		say "You chose silence. You can still change your mind, but you already heard the loop fade." instead.

Carry out transmitting:
	now responded-to-americans is true;
	increase morale-level by 8.

Report transmitting:
	say "You key the microphone yourself. There is no one else to key it for you.[paragraph break]'Freedom Station, this is Mir-3. We read your distress call. Say your status. Over.'[paragraph break]The loop cuts. A pause — long enough that you think the signal is gone. Then a new voice, live, shaking with relief and surprise.[paragraph break]'Mir-3... oh my God. This is Commander Diane Chen, Freedom Station. We... we did not expect anyone to answer.'[paragraph break]You trade damage reports with a stranger. Five crew on her side, two injured. One on yours, no injured. You skip over the word *alive*. She skips over it too.[paragraph break]You open Yevgenia's notebook. You tell Chen about Selengrad.[paragraph break]A pause. Then her voice again, quieter: 'You are proposing we fly to the Moon.'[paragraph break]'I am proposing we try. It is that or a slow death in orbit.'[paragraph break]Five American survivors. You. One lunar base in caretaker mode. One plan scribbled in a dead engineer's handwriting.[paragraph break]'Begin preparations,' Chen says, after a long silence. 'We have work to do.'"

Staying silent is an action applying to nothing.
Understand "stay silent" as staying silent.
Understand "remain silent" as staying silent.
Understand "ignore distress call" as staying silent.

Check staying silent:
	if the player is not in the Command Module:
		say "That does not make sense right now." instead;
	if distress-call-heard is false:
		say "There is no one to be silent toward." instead;
	if responded-to-americans is true:
		say "You have already answered them." instead;
	if chose-silence is true:
		say "You have already made your choice. The loop faded a while ago." instead.

Carry out staying silent:
	decrease morale-level by 8;
	now chose-silence is true.

Report staying silent:
	say "You listen to the loop. You do not key the microphone.[paragraph break]The first time it plays, you almost answer. The second time you almost answer. The third time you catch yourself already reaching for the mic, and you pull your hand back.[paragraph break]Chen's voice fades. Maybe her battery failed; maybe she gave up. Maybe she is still talking and the signal is too weak to reach you anymore.[paragraph break]You sit alone with the static and with the math in Yevgenia's notebook. Alone, you cannot make Selengrad. The combined fuel is not optional; it is arithmetic.[paragraph break]Unless Chen transmits again. Unless you change your mind.[paragraph break]You tell yourself you chose this for good reasons. You are not sure you believe yourself."

Part 9 - Scene-Specific Responses

Chapter 1 - Darkness Before Flashlight

Before going north from the Crew Quarters when the chemical flashlight is not lit:
	say "You fumble in the darkness toward the hatch, but you can barely see. You should find a light source first — the emergency locker might have something useful.";
	stop the action.

Chapter 2 - The Sealed Hatch Blocks Movement

Before going north from the Crew Quarters when corridor-pressurized is false:
	say "You push at the hatch. It does not budge. The porthole is fogged with frost. You can feel the cold of a vacuum on the other side through the metal — the corridor has vented. The valve beside the hatch is still closed.";
	stop the action.

Chapter 3 - Reasonable Default Responses

Instead of smelling when the player is in the Crew Quarters:
	say "The air tastes thin and metallic. You are breathing what is left of the module's reserves."

Instead of smelling when the player is in the Main Corridor:
	say "The corridor smells of ozone, cold metal, and — faintly, behind everything else — the smell of a person who has been dead for some minutes in a cold, low-pressure space."

Instead of pushing the control panels:
	say "You press buttons and flip switches, but nothing responds. The panels are completely dead."

Instead of pushing the status console when power-is-restored is false:
	say "The console is dead. No amount of pressing buttons will change that without power."

Instead of switching on the status console when power-is-restored is false:
	say "The console has no power. You need to restore the isolated power bus first."

Instead of taking the communications array:
	say "The communications array is built into the station's infrastructure. It is not going anywhere."

Instead of taking the manual pressure gauges:
	say "The gauges are permanently mounted to the bulkhead."

Instead of taking the sleeping harness:
	say "The sleeping harness is bolted to the bulkhead."

Part 10 - Score Tracking

Chapter 1 - Achievements

[Each After rule here must `continue the action`, otherwise the default
 Report narrative is suppressed — the player sees only the score bump
 and misses the intended response text. See issue #34.]

After switching on the chemical flashlight for the first time:
	increase the score by 1;
	continue the action.

After opening the emergency locker for the first time:
	increase the score by 1;
	continue the action.

After opening the pressure valve:
	increase the score by 1;
	continue the action.

After restoring power:
	increase the score by 3;
	continue the action.

After reading Petrov's log:
	increase the score by 1;
	continue the action.

After transmitting for the first time:
	increase the score by 5;
	continue the action.

The maximum score is 12.

Part 11 - Testing Support

Chapter 1 - Test Scripts

Test quarters with "open locker / take flashlight / switch on flashlight / examine photograph / listen".
Test hatch with "open locker / take flashlight / switch on flashlight / examine hatch / pull lever / n".
Test explore with "open locker / take flashlight / switch on flashlight / pull lever / n / e / examine viewport / w / n / open toolkit / take multimeter".
Test full with "open locker / take flashlight / switch on flashlight / listen / pull lever / n / examine yevgenia / take notebook / read notebook / e / examine viewport / examine petrov / w / n / open toolkit / take multimeter / restore power / read log / listen / transmit".
