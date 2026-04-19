"MIR'S END" by "Seith Miller"

The story headline is "An Interactive Survival Story".
The story genre is "Science Fiction".
The story description is "You awaken aboard the Soviet space station Mir-3 after a catastrophic electromagnetic pulse. The world below has changed forever. Now you must survive."
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

The Crew Quarters is a room. "You float in the cramped sleeping bay of Mir-3.[if the chemical flashlight is lit] The warm yellow beam from the Zhuchok reveals chaos — personal effects drift in zero-g: a photograph, a pen, a sachet of reconstituted borscht. The status panel above your bunk is dead black.[otherwise] The darkness is absolute. You can barely see your hand in front of your face.[end if] The main corridor lies to the north."

The player is in the Crew Quarters.

The sleeping harness is scenery in the Crew Quarters. The description of the sleeping harness is "A standard-issue cosmonaut sleeping harness, bolted to the bulkhead. The velcro straps are frayed from months of use."

The emergency locker is a closed openable container in the Crew Quarters. The emergency locker is fixed in place. The description of the emergency locker is "A sturdy metal locker magnetically latched to the wall, marked with a red cross.[if the emergency locker is open and the chemical flashlight is in the emergency locker] Inside you can see a Zhuchok — the hand-dynamo flashlight every cosmonaut grew up with.[end if]"

[The flashlight's printed name is "flashlight" so players see familiar
 language everywhere. "Zhuchok" lives on in the description and the
 switch-on narrative as historical flavor. Understand synonyms cover
 both names.]

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

Chapter 2 - Main Corridor

The Main Corridor is north of the Crew Quarters. "The main corridor of Mir-3 stretches in both directions, a tunnel of drifting debris and dead screens. Without power, the station feels less like a spacecraft and more like a submarine at the bottom of an ocean.[paragraph break]The crew quarters lie to the south, the command module is to the north, and the observation cupola is to the east."

The drifting debris is scenery in the Main Corridor. The description of the drifting debris is "Cables hang loose from open maintenance panels. Frost is forming on the inner hull where insulation has lost power. Small droplets of condensation drift through the air."

The frost is scenery in the Main Corridor. The description of the frost is "A thin layer of frost is forming on the inner hull plates where the insulation has lost power. Without the station's thermal management systems, the cold of space is slowly creeping in."

The maintenance panel is scenery in the Main Corridor. The description of the maintenance panel is "An open maintenance panel reveals a tangle of loose cables and blown circuit breakers. Whatever hit the station burned through every system."

Chapter 3 - Observation Cupola

The Observation Cupola is east of the Main Corridor. "The observation cupola is a blister of reinforced glass on the station's nadir side.[if war-is-discovered is true] Through the viewport you can see the Earth below — scarred with blooms of orange and white across the nightside. The sight is devastating.[otherwise] Through the viewport you can see the Earth below. Something seems wrong with the nightside.[end if] The corridor lies to the west."

The viewport is scenery in the Observation Cupola.

War-is-discovered is a truth state that varies. War-is-discovered is false.

Instead of examining the viewport:
	if war-is-discovered is false:
		now war-is-discovered is true;
		decrease morale-level by 15;
		say "You press your face to the reinforced glass and look down at the Earth.[paragraph break]The planet below is scarred.[paragraph break]Across the nightside — which should be a field of glittering city lights — there are new lights. Not cities. These are blooms of orange and white, vast and spreading, dotting the continents in clusters. Some are fading. Some are fresh, expanding in slow-motion circles that your mind refuses to interpret.[paragraph break]But you know what they are.[paragraph break]Nuclear exchange. Full-scale. Both sides.[paragraph break]The silence that follows your realization is heavier than vacuum.";
	otherwise:
		say "The planet below is scarred. Blooms of orange and white dot the continents — nuclear fires, still burning. You force yourself to look away."

Understand "look through [something]" as examining.

The reinforced glass is scenery in the Observation Cupola. The description of the reinforced glass is "Thick reinforced glass designed to withstand micrometeorite impacts. Right now it frames the worst view in human history."

Chapter 4 - Command Module

The Command Module is north of the Main Corridor. "The command module is a cramped space packed with control panels.[if power-is-restored is true] A single console flickers with dim, partial life — the isolated power bus has been restored. The main corridor is to the south.[otherwise] Every panel is dead. The main corridor is to the south.[end if]"

Power-is-restored is a truth state that varies. Power-is-restored is false.

The control panels are scenery in the Command Module. The description of the control panels is "[if power-is-restored is true]Most panels remain dead, but the working console on the main bus flickers with partial life.[otherwise]Row upon row of switches, dials, and screens — all dark. The electromagnetic pulse killed every system simultaneously.[end if]"

The emergency toolkit is a closed openable container in the Command Module. The emergency toolkit is fixed in place. The description of the emergency toolkit is "A toolkit magnetically latched to the wall, containing essential repair instruments."

The multimeter is a thing in the emergency toolkit. The description of the multimeter is "A sturdy analogue multimeter — one of the few instruments unaffected by the EMP. Essential for diagnosing electrical faults."

The manual pressure gauges are scenery in the Command Module. The description of the manual pressure gauges is "Analogue pressure gauges — the only instruments still functioning. They show hull pressure is nominal, but CO2 levels are slowly rising."

The status console is a device in the Command Module. The status console is fixed in place. The status console is switched off. The description of the status console is "[if power-is-restored is true]The screen is dim and half the pixels are dead, but it works. Status readouts scroll across it — most of them bad. Hull integrity nominal. Life support offline. Communications array available. Oxygen reserves: critical.[otherwise]The main status console is completely dead. No power reaches it.[end if]"

To say comms-status-powered:
	if distress-call-heard is false:
		say "The communications array is patched into the restored power bus. You could try to use it to listen for signals.";
	otherwise if responded-to-americans is true:
		say "The radio crackles with the open channel to Freedom Station.";
	otherwise:
		say "Through the static, you can hear the faint American distress call repeating on the emergency frequency."

The communications array is a thing in the Command Module. The communications array is fixed in place. The description of the communications array is "[if power-is-restored is true][comms-status-powered][otherwise]The communications array is dead without power.[end if]"

Understand "radio" as the communications array.

Part 3 - NPCs

Chapter 1 - Yevgenia

Yevgenia is a woman in the Main Corridor. The printed name of Yevgenia is "Yevgenia Kozlova". Understand "kozlova" or "engineer" as Yevgenia. The description of Yevgenia is "Yevgenia Kozlova, the station's engineer. She is lean and focused, her dark hair pulled back in a practical knot. Her eyes carry the intensity of someone who solves problems for a living — and right now, the problems are existential."

Instead of talking to Yevgenia:
	try asking Yevgenia about "status".

Chapter 2 - Petrov

Petrov is a man in the Main Corridor. The printed name of Petrov is "Commander Petrov". Understand "commander" as Petrov. The description of Petrov is "Commander Petrov, mission commander. A career military officer with thirty years of service. His face is grim but controlled — training overriding horror. He wears a mechanical watch on his wrist, unaffected by the EMP."

The mechanical watch is a thing that is part of Petrov. The description of the mechanical watch is "A mechanical watch — no electronics, unaffected by the EMP. It reads [if power-is-restored is true]roughly two hours[otherwise]about an hour[end if] since the pulse hit."

Instead of talking to Petrov:
	try asking Petrov about "status".

Chapter 3 - NPC Movement

Every turn when power-is-restored is true and Yevgenia is not in the Command Module:
	now Yevgenia is in the Command Module;
	if the player is in the Command Module:
		say "Yevgenia arrives, already rolling up her sleeves. 'Let me work on the communications array,' she says."

Every turn when war-is-discovered is true and Petrov is in the Main Corridor and the player is in the Observation Cupola:
	now Petrov is in the Observation Cupola;
	say "Petrov drifts into the cupola behind you. He stares at the Earth in silence for a long moment. 'I was afraid of this,' he says quietly."

Part 4 - Conversation System

Chapter 1 - Talking Action

Talking to is an action applying to one visible thing.
Understand "talk to [someone]" as talking to.

Chapter 2 - Asking About Topics

After asking Yevgenia about "emp/pulse/electromagnetic":
	say "'A military-grade electromagnetic pulse,' Yevgenia says. 'It burned through every bus, every backup, even the battery isolators. I have never seen anything kill every system on a station simultaneously. Whatever happened down there was deliberate.'";

After asking Yevgenia about "station/mir/damage/status":
	say "'The whole grid is dead,' Yevgenia says. 'Every bus. Every backup. Something burned through everything at once.[if power-is-restored is false] I think I can restore the isolated power bus in the command module, but I will need help.'[otherwise] At least we have partial power now. The isolated bus is holding.'[end if]";

After asking Yevgenia about "power/restore/bus":
	if power-is-restored is true:
		say "'The isolated bus is holding,' Yevgenia says. 'It is not much, but it gives us the command console and communications. Do not ask for miracles — the main grid is gone.'";
	otherwise:
		say "'The command module has its own isolated power bus,' Yevgenia explains. 'If the surge did not physically destroy the capacitors, I might be able to hard-reset the system. I need to get to the command module.'";

After asking Yevgenia about "oxygen/air/life support/co2":
	say "'The CO2 scrubbers are unpowered but the lithium hydroxide canisters are passive,' Yevgenia calculates. 'We have maybe eighteen hours before CO2 levels become dangerous. Oxygen reserves give us roughly the same.'";

After asking Yevgenia about "selengrad/moon/lunar":
	say "'Selengrad was designed to be self-sustaining,' Yevgenia says, her eyes lighting up despite everything. 'Closed-loop atmosphere, water recycling, hydroponics. It has been in caretaker mode for two years, but the systems should still be functional. It is our best chance.'";

After asking Yevgenia about "freedom/americans/chen/distress":
	say "'Those people did not launch anything,' Yevgenia says firmly. 'They are cosmonauts. Like us. Whatever happened down there, we might need each other before this is over.'";

After asking Yevgenia about "war/nuclear/earth/attack":
	say "'I do not want to think about who pushed which button first,' Yevgenia says, her hands clenching. 'That is a problem for people who still have a ground under their feet. Our problem is air, water, and power — in that order. Grieving can wait. Surviving cannot.'";

After asking Petrov about "emp/pulse/electromagnetic":
	say "'In thirty years of service I have seen equipment failures, solar storms, even a depressurisation drill that turned real,' Petrov says. 'I have never seen anything kill every system on a station simultaneously. This was military grade.'";

After asking Petrov about "war/nuclear/earth/attack":
	say "'Nuclear exchange,' Petrov says, his voice barely above a whisper. 'Full-scale. Both sides. The pattern is unmistakable — military targets first, then cities. The textbook escalation everyone prayed would remain theoretical.'";

After asking Petrov about "status/situation/damage":
	say "'We are alive. The station is crippled but intact,' Petrov says with military precision. 'We need to restore what systems we can, assess our supplies, and make a plan. We cannot afford to waste time.'";

After asking Petrov about "freedom/americans/chen/distress":
	say "'Their country just tried to kill everyone I have ever loved,' Petrov says. His jaw works. 'But those people up there — they did not launch anything. They are cosmonauts. Like us.' He pauses. 'Up here, there are no sides. There is only survival.'";

After asking Petrov about "selengrad/moon/lunar":
	say "'It is insane,' Petrov says. Then, after a pause: 'It is also the only option that does not end with eight people suffocating in orbit. We plan for the Moon.'";

After asking Petrov about "watch/time":
	say "'The pulse hit us at 03:47 Moscow time,' Petrov says, checking his mechanical watch. 'It has been [if power-is-restored is true]roughly two hours[otherwise]about one hour[end if] since then.'";

Part 5 - Story Progression

Chapter 1 - Opening Scene

When play begins:
	say "You wake to nothing.[paragraph break]No hum of ventilation. No green glow of status panels. Just the hammering of your own pulse and a darkness so complete you cannot tell if your eyes are open.[paragraph break]Something has gone terribly wrong.[paragraph break]The emergency lighting should have kicked in by now. The station batteries alone could power the corridor strips for days. Whatever hit Mir-3 was not a simple power failure.[paragraph break]You float in your sleeping harness, weightless, breathing stale air that already tastes thin."

Chapter 2 - Listening Action

Listening-to-tapping is a truth state that varies. Listening-to-tapping is false.

Instead of listening when the player is in the Crew Quarters and listening-to-tapping is false:
	now listening-to-tapping is true;
	increase morale-level by 3;
	say "You hold your breath and listen.[paragraph break]At first: nothing. The station is a tomb.[paragraph break]Then you start to pick out sounds. The faint creak of thermal expansion in the hull. A distant drip — condensation, without the ventilation system to manage humidity.[paragraph break]And something else. A rhythmic tapping, three-two-three, coming from the direction of the main corridor. The old knock code the crew uses when the intercom fails.[paragraph break]Three-two-three: 'Status?'[paragraph break]You rap your knuckles against the bulkhead: two-one-two. 'Alive.'[paragraph break]Someone else survived."

Instead of listening when the player is in the Main Corridor:
	say "You hear the faint creak of thermal expansion in the hull and the distant drip of condensation. The station groans softly around you, settling into its unpowered state."

Instead of listening when the player is in the Observation Cupola:
	say "Silence. The observation cupola is eerily quiet — just the faint tick of thermal stress in the glass panels and the sound of your own breathing."

Instead of listening when the player is in the Command Module and (power-is-restored is false or distress-call-heard is true):
	say "[if power-is-restored is true]The restored console hums faintly. The communications array crackles with static and, beneath it, the ghost of a signal.[otherwise]Dead silence. Not even the background hum of electronics that you have grown so accustomed to over months aboard the station.[end if]"

Chapter 3 - Restoring Power

Restoring power is an action applying to nothing.
Understand "restore power" as restoring power.
Understand "restore systems" as restoring power.
Understand "hard-reset" or "hard reset" or "reset system" or "reset systems" as restoring power.
Understand "fix power" as restoring power.

Check restoring power:
	if the player is not in the Command Module:
		say "You would need to be in the command module to attempt restoring power." instead;
	if power-is-restored is true:
		say "The isolated power bus is already restored. It is not much, but it is all you are going to get." instead;
	if the player does not carry the multimeter:
		say "You need a multimeter to diagnose and restore the electrical systems. There should be one in the emergency toolkit." instead.

Carry out restoring power:
	now power-is-restored is true;
	now the status console is switched on;
	increase morale-level by 10.

Report restoring power:
	say "You work alongside Yevgenia, using the multimeter to trace circuits and test capacitors. For twenty minutes you work in near-silence, punctuated by occasional muttered Russian from Yevgenia.[paragraph break]Then, with a sharp crack and a brief flash, the status console flickers to life.[paragraph break]'Ha!' Yevgenia pulls her hands back from the wiring, grinning despite everything. 'Isolated bus is intact. I have got partial power to the command console.'[paragraph break]The screen is dim and half the pixels are dead, but it works. Status readouts begin scrolling — most of them bad."

Chapter 4 - Distress Call

Distress-call-heard is a truth state that varies. Distress-call-heard is false.

Instead of listening when the player is in the Command Module and power-is-restored is true and distress-call-heard is false:
	now distress-call-heard is true;
	increase morale-level by 3;
	say "You tune the communications array carefully through the static.[paragraph break]Through the noise, a voice. Faint, broken, but unmistakably human. And unmistakably speaking English.[paragraph break]'...this is Freedom Station, transmitting on emergency frequency... if anyone... we have sustained critical damage from the electromagnetic pulse... life support failing... request assistance from any station, any vessel... five crew, two injured... oxygen reserves critical...'[paragraph break]The transmission loops. An automated distress call.[paragraph break]Freedom Station. The American orbital platform. Your mirror image. The Americans are dying.[paragraph break]Twelve hours ago, your nations tried to destroy each other."

Chapter 5 - Responding to Distress Call

Responded-to-americans is a truth state that varies. Responded-to-americans is false.

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
		say "You are already in contact with Freedom Station. Commander Chen's crew is standing by." instead.

Carry out transmitting:
	now responded-to-americans is true;
	increase morale-level by 8.

Report transmitting:
	say "You key the microphone.[paragraph break]'Freedom Station, this is Mir-3. We read your distress call. We have sustained similar damage but have partial systems restored. What is your status? Over.'[paragraph break]The loop cuts. A pause. Then a new voice — live this time, shaking with relief and surprise.[paragraph break]'Mir-3... oh my God. This is Commander Diane Chen, Freedom Station. We... we did not expect anyone to answer.'[paragraph break]The conversation unfolds over twenty minutes. You trade damage reports, crew status, supply inventories. Between both crews — eight people, maybe thirty hours of oxygen, patchy communications, no ground support, and a planet below that can no longer help you.[paragraph break]Petrov straightens. 'We cannot stay in orbit,' he says. 'Yevgenia — tell them about Selengrad.'[paragraph break]Yevgenia pulls up the navigational chart. 'Selengrad. The lunar base. Self-sustaining — closed-loop atmosphere, water recycling, hydroponics. If we combine both stations['] fuel reserves, we can make it.'[paragraph break]Chen's voice crackles: 'You are proposing we fly to the Moon?'[paragraph break]Eight people. Two crippled stations. One destination.[paragraph break]Petrov looks at you. 'This is the moment. Everything we do from here is a step toward the Moon or a step toward a slow death in orbit. There is no middle ground.'[paragraph break]He straightens, and for the first time since the lights went out, something like resolve settles over his features.[paragraph break]'Begin preparations. We have work to do.'"

Chapter 6 - Staying Silent

Staying silent is an action applying to nothing.
Understand "stay silent" as staying silent.

Check staying silent:
	if the player is not in the Command Module:
		say "That does not make sense right now." instead;
	if distress-call-heard is false:
		say "There is no one to be silent toward." instead;
	if responded-to-americans is true:
		say "You have already answered them." instead.

Carry out staying silent:
	decrease morale-level by 8;
	now responded-to-americans is true.

Report staying silent:
	say "You look at Petrov. He looks at the radio. The distress call loops again.[paragraph break]Petrov closes his eyes. 'Their country just tried to kill everyone I have ever loved.' His jaw works. 'But those people up there — they did not launch anything. They are cosmonauts. Like us.'[paragraph break]He opens his eyes. 'We answer. That is not a political decision. It is a human one.'[paragraph break]He keys the microphone himself.[paragraph break]'Freedom Station, this is Commander Petrov, Mir-3. We hear you. What is your status? Over.'[paragraph break]A stunned silence. Then: 'Mir-3... this is Commander Chen. I... thank you. Thank you for answering.'[paragraph break]The conversation unfolds. Between both crews — eight people, dwindling oxygen, and a burning planet below. Yevgenia proposes the only plan that makes sense: Selengrad, the lunar base.[paragraph break]'Begin preparations,' Petrov orders. 'We have work to do.'"

Part 6 - Scene-Specific Responses

Chapter 1 - Darkness Before Flashlight

Before going north from the Crew Quarters when the chemical flashlight is not lit:
	say "You fumble in the darkness toward the hatch, but you can barely see. You should find a light source first — the emergency locker might have something useful.";
	stop the action.

Chapter 2 - Reasonable Default Responses

Instead of smelling when the player is in the Crew Quarters:
	say "The air tastes thin and stale. Without the ventilation system, the station's atmosphere is slowly deteriorating."

Instead of smelling when the player is in the Main Corridor:
	say "The corridor smells of ozone and cold metal. Something electrical burned out during the pulse."

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

Part 7 - Score Tracking

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

After restoring power:
	increase the score by 3;
	continue the action.

After transmitting for the first time:
	increase the score by 5;
	continue the action.

The maximum score is 10.

Part 8 - Testing Support

Chapter 1 - Test Scripts

Test quarters with "open locker / take flashlight / switch on flashlight / examine photograph / listen".
Test explore with "open locker / take flashlight / switch on flashlight / n / e / examine viewport / w / n / open toolkit / take multimeter".
Test power with "open locker / take flashlight / switch on flashlight / n / n / open toolkit / take multimeter / restore power".
Test full with "open locker / take flashlight / switch on flashlight / listen / n / talk to yevgenia / talk to petrov / e / examine viewport / w / n / open toolkit / take multimeter / restore power / listen / transmit".
