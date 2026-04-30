"MIR'S END" by "Seith Miller"

The story headline is "An Interactive Survival Story".
The story genre is "Science Fiction".
The story description is "You wake aboard the Soviet space station Mir-3 after a catastrophic impact. The rest of the crew is dead. The world below is ending. You must survive."
The release number is 1.

Use scoring.

Part 1 - Resources and Status

Chapter 1 - Resource Variables

Oxygen-level is a number that varies. Oxygen-level is 100.
Morale-level is a number that varies. Morale-level is 50.
Dose-level is a number that varies. Dose-level is 0.

B1-beats-completed is a number that varies. B1-beats-completed is 0.
B2-beats-completed is a number that varies. B2-beats-completed is 0.
Dominant-act2-path is text that varies. Dominant-act2-path is "none".

[Beat-counting guards — each beat increments its path counter once.]
Notebook-beat-counted is a truth state that varies. Notebook-beat-counted is false.
Yevgenia-beat-counted is a truth state that varies. Yevgenia-beat-counted is false.
Petrov-beat-counted is a truth state that varies. Petrov-beat-counted is false.
Dosimeter-beat-counted is a truth state that varies. Dosimeter-beat-counted is false.

B1-beats-completed is a number that varies. B1-beats-completed is 0.
B2-beats-completed is a number that varies. B2-beats-completed is 0.
Dominant-act2-path is text that varies. Dominant-act2-path is "none".

[Beat-counting guards — each beat increments its path counter once.]
Notebook-beat-counted is a truth state that varies. Notebook-beat-counted is false.
Yevgenia-beat-counted is a truth state that varies. Yevgenia-beat-counted is false.
Petrov-beat-counted is a truth state that varies. Petrov-beat-counted is false.
Dosimeter-beat-counted is a truth state that varies. Dosimeter-beat-counted is false.

[Descent arc state — set by DEORBIT, guards oxygen timer and D3 sequence.]
Chose-descent is a truth state that varies. Chose-descent is false.
D3-beat-counter is a number that varies. D3-beat-counter is 0.

Chapter 2 - Status Bar

[In-story status bar intentionally omitted. The Web UI renders
 O2 / Morale / Inventory from window.MirsEnd.setState, driven by
 the MIRSEND status line emitted below. The Inform 7 v10.1.2
 compiler we use doesn't recognize "fill status bar with ...", and
 we don't need an in-game bar since the Web UI covers it.]

Chapter 3 - Climax Commitment

[Tracks whether the player has locked into any Act 4/5 arc.
 Set by C1 (transmit), C2 (de-orbit), or C3 (cannon). When true,
 passive-timer deaths yield to the scripted denouement.]
Chose-descent is a truth state that varies. Chose-descent is false.
Cannon-fired is a truth state that varies. Cannon-fired is false.

To decide whether player has committed climax:
	if responded-to-americans is true, decide yes;
	if chose-descent is true, decide yes;
	if cannon-fired is true, decide yes;
	decide no.

Chapter 4 - Oxygen Timer

Every turn:
	if player has committed climax:
		do nothing;
	otherwise:
		decrease oxygen-level by 1;
		if oxygen-level <= 0:
			carry out e5 dispatching.

Chapter 5 - E5 Passive-Failure Dispatcher

[When a passive timer expires and the player has not committed to a
 climax, this dispatcher selects the correct sub-variant and ends
 the game. Only the oxygen hook is wired today; CO2, freeze, and
 radiation plug in here when their timers are wired.]

E5 dispatching is an action applying to nothing.

Carry out e5 dispatching:
	if oxygen-level <= 0:
		say "[bracket]TODO prose: #60 — e5-suffocate[close bracket]";
		end the story saying "You have suffocated".

Chapter 6 - UI Status Bridge

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
	say "[line break][bracket]MIRSEND o2=[oxygen-level] morale=[morale-level] inv=[mirsend-inventory-list] b1=[b1-beats-completed] b2=[b2-beats-completed] act2=[dominant-act2-path][close bracket][line break]".

Part 1B - Direction Synonyms

[Spaceflight uses axis-relative names. Mir-3's crews think in fore/aft,
 port/starboard, zenith/nadir, so the parser accepts those alongside
 the compass directions.]
Understand "fore" or "forward" as north.
Understand "aft" or "stern" as south.
Understand "starboard" as east.
Understand "port" as west.
Understand "zenith" as up.
Understand "nadir" as down.

Part 2 - The Station

Chapter 1 - Crew Quarters

The Crew Quarters is a room. "You float in the sleeping bay of Mir-3. Four bunks in slots along the port wall. Yours is the second from forward.[if the chemical flashlight is lit][paragraph break]The Zhuchok throws a warm yellow beam. Personal effects drift in zero-g. A photograph. A pen. A sachet of reconstituted borscht. The status panel above your bunk is dead. The emergency locker sits on the starboard wall. Overhead, a dead reading light. The aft bulkhead wears the reactor warning triangle.[otherwise][paragraph break]The darkness is absolute. You can barely see your hand.[end if][paragraph break]A sealed hatch forward to the main corridor. A second hatch aft, trefoil-marked, to the Reactor Module."

The player is in the Crew Quarters.

The sleeping harness is scenery in the Crew Quarters. The description of the sleeping harness is "A standard cosmonaut harness bolted to the bulkhead. Half the straps are torn. You tore them yourself in the first confused seconds after the shock that woke you."

The emergency locker is a closed openable container in the Crew Quarters. The emergency locker is fixed in place. The description of the emergency locker is "A metal locker, magnetically latched. A red cross stenciled on its door.[if the emergency locker is open and the chemical flashlight is in the emergency locker] Inside: a Zhuchok. The hand-dynamo every cosmonaut grew up with.[end if]"

Instead of taking the emergency locker:
	say "The locker is bolted to the bulkhead. It is not going anywhere."

[The Inform name "chemical flashlight" is kept for schema stability with
 save files and tests; the player sees "Zhuchok" via the printed name
 and Understand synonyms below.]
The chemical flashlight is a thing in the emergency locker. The printed name of the chemical flashlight is "flashlight". Understand "zhuchok" or "zhuk" or "torch" or "dynamo" or "lamp" as the chemical flashlight. The description of the chemical flashlight is "A Zhuchok. Bakelite body. A small folding squeeze-lever. Made in Krasnodar sometime in the last thirty years. No batteries. The lever spins a tiny generator against a rotor. The whole thing whirs like its namesake beetle when you pump it.[if lit] It throws a warm unsteady yellow beam right now.[otherwise] Give it a few squeezes and the lamp will glow for as long as you keep pumping.[end if]".

The chemical flashlight can be lit or unlit. The chemical flashlight is unlit.

The chemical flashlight is a device.

Flashlight-first-lit is a truth state that varies. Flashlight-first-lit is false.

Instead of switching on the chemical flashlight:
	if the chemical flashlight is not carried by the player:
		try silently taking the chemical flashlight;
	if the chemical flashlight is lit:
		say "The Zhuchok is already glowing.";
	otherwise:
		now the chemical flashlight is lit;
		now the chemical flashlight is switched on;
		increase morale-level by 5;
		[Score the achievement here; Inform's Instead rule short-circuits
		 the action chain so an "After switching on" rule never fires.]
		if flashlight-first-lit is false:
			now flashlight-first-lit is true;
			increase the score by 1;
		say "You squeeze the lever. Quick rhythm. The dynamo whirs up with that familiar beetle-drone. The little lamp throws a warm yellow beam across the bay. Cables. Straps. The edges of your bunk. Shadows resolve into real objects again."

Instead of switching off the chemical flashlight:
	if the chemical flashlight is lit:
		now the chemical flashlight is unlit;
		now the chemical flashlight is switched off;
		say "You stop pumping. The dynamo winds down. The little lamp fades to dark.";
	otherwise:
		say "It is not pumping. There is nothing to switch off."

[Verb synonyms for switching on the flashlight, matching the
 description's "squeeze the lever" / "give it a few squeezes" prose.
 SQUEEZE defaults to RUB, LIGHT defaults to BURN; clear those first,
 then bind the grammar we want.]
Understand the command "squeeze" as something new.
Understand the command "light" as something new.
Understand "squeeze [something]" as switching on.
Understand "pump [something]" as switching on.
Understand "crank [something]" as switching on.
Understand "wind [something]" as switching on.
Understand "light [something]" as switching on.

The photograph is a thing in the Crew Quarters. The description of the photograph is "A family standing before a dacha in winter. The faces smile from another lifetime."

The pen is a thing in the Crew Quarters. The description of the pen is "A ballpoint pen. Standard issue. Drifting."

The borscht is scenery in the Crew Quarters. Understand "sachet" or "borscht" or "borshch" or "soup" or "rations" or "ration" as the borscht. The printed name of the borscht is "sachet of reconstituted borscht". The description of the borscht is "A foil sachet of reconstituted beet borscht. Cold. The label is in Cyrillic. You have eaten thousands of these. The thought of opening one now turns your stomach."

Instead of taking the borscht:
	say "The sachet drifts away. You have no appetite for it."

Instead of eating the borscht:
	say "Not now."

The bunk status panel is scenery in the Crew Quarters. The description of the bunk status panel is "Dead black. Not even the emergency indicators are lit."

[Backdrops for prose-mentioned scenery players reach for. Without these
 the parser says "You can't see any such thing" on bunks/vent and breaks
 trust in the prose. Each gives a one-line description that fits the
 voice without inventing new mechanics.]
The bunks are scenery in the Crew Quarters. Understand "bunk" or "bunks" or "first bunk" or "second bunk" or "third bunk" or "fourth bunk" as the bunks. The description of the bunks is "Four bunks in their slots. Three are empty harnesses. The fourth was yours."

Instead of taking the bunks:
	say "The bunks are bolted to the hull. They are not going anywhere."

The reading light is scenery in the Crew Quarters. Understand "reading light" or "lamp" or "overhead light" as the reading light. The description of the reading light is "A small dome lamp clipped above your bunk. Dead, like everything else not running on batteries."

The air vent is scenery in the Crew Quarters. Understand "vent" or "air vent" or "ventilation" or "duct" as the air vent. The description of the air vent is "An air vent overhead. The fan behind it is silent. Without circulation, the bay's air is going to settle in layers."

The reactor warning triangle is scenery in the Crew Quarters. Understand "trefoil" or "warning" or "triangle" or "warning triangle" or "reactor warning" or "radiation symbol" as the reactor warning triangle. The description of the reactor warning triangle is "The trefoil radiation symbol painted on the aft bulkhead. Just past the hatch is the Reactor Module. The trefoil exists for this exact moment."

[The two named hatches in Crew Quarters: the parser accepts "aft hatch"
 and "forward hatch" as synonyms for the existing sealed hatch, so the
 LLM player's natural phrasing doesn't get rewritten to "examine south".]
Understand "aft hatch" or "forward hatch" or "fore hatch" or "fwd hatch" as the sealed hatch.

The chocolate bar is an edible thing in the Crew Quarters. The printed name of the chocolate bar is "chocolate bar". Understand "chocolate" or "shokolad" or "shoko" or "bar" or "ration bar" or "ration" as the chocolate bar. The description of the chocolate bar is "A small dark Soviet ration bar. Foil-wrapped, slightly crushed. Аленка on the label. Probably stale. Probably the only thing within reach that is not trying to kill you."

After eating the chocolate bar:
	if morale-level + 12 > 100:
		now morale-level is 100;
	otherwise:
		now morale-level is morale-level + 12;
	say "You unwrap the bar. It tastes like dust and cocoa and something faintly like the past. You eat it slowly because you have nothing else.[paragraph break][bracket]You feel a little less broken.[close bracket]"

[Resting in the bunk: lets the player trade O2 for morale. The harness
 is in Crew Quarters; resting only works there. Each rest costs 4 O2
 above the per-turn baseline tick and pays back 10 morale.]
Resting is an action applying to nothing.
[Inform 7 binds "sleep" to its built-in Sleeping action by default. Clear
 it so our resting action gets the verb.]
Understand the command "sleep" as something new.
Understand "sleep" or "rest" or "nap" or "doze" or "lie down" or "sleep in harness" or "rest in harness" or "go to sleep" or "close eyes" as resting.

Check resting:
	if the location of the player is not the Crew Quarters:
		say "There is no good place to rest here. Not without the harness in the bay.";
		stop the action;
	if oxygen-level < 8:
		say "You start to drift, then jerk back. The air is too thin to slow your breathing now. Not without help.";
		stop the action.

Carry out resting:
	now oxygen-level is oxygen-level - 4;
	if morale-level + 10 > 100:
		now morale-level is 100;
	otherwise:
		now morale-level is morale-level + 10.

Report resting:
	say "You drift in the harness. Eyes closed. Eight breaths. Sixteen. The hammering behind your forehead settles into something duller. The cold pulls at the edge of you, but you let it. When you open your eyes, the room is still black, but you can hold its shape in your mind now.[paragraph break][bracket]You feel steadier. Time has passed.[close bracket]"

[Status check: prints the player's vitals and inventory in the prose
 stream. Useful for shell-mode play, but more importantly the LLM
 player has no UI bars; STATUS is how the agent reads its own state.]
Checking status is an action applying to nothing.
Understand "status" or "stats" or "vitals" or "check status" or "check stats" or "check vitals" or "condition" as checking status.

Carry out checking status:
	say "[bracket]STATUS[close bracket][line break]";
	say "  Location: [printed name of the location of the player][line break]";
	say "  O2: [oxygen-level]%[line break]";
	say "  Morale: [morale-level]%[line break]";
	say "  Score: [the score][line break]";
	if the number of things carried by the player > 0:
		say "  Carrying: ";
		let counter be 0;
		repeat with item running through things carried by the player:
			if counter > 0:
				say ", ";
			say "[printed name of item]";
			increment counter;
		say "[line break]";
	otherwise:
		say "  Carrying: nothing[line break]";
	if morale-level <= 50:
		say "  [bracket]Tip: REST or SLEEP recovers morale (costs O2). EAT something for a smaller boost.[close bracket][line break]";
	if oxygen-level <= 50:
		say "  [bracket]Tip: O2 is dropping. Avoid wasting turns; restoring power and life support is the long-term answer.[close bracket][line break]".

[Help: a quick verb reference. Lower bar to discovery for the LLM
 player and for any new human player.]
Asking-for-help is an action applying to nothing.
Understand "help" or "verbs" or "commands" as asking-for-help.

Carry out asking-for-help:
	say "Common commands:[line break]";
	say "  LOOK            see your surroundings[line break]";
	say "  EXAMINE [bracket]thing[close bracket]  look at something closely[line break]";
	say "  INVENTORY (I)   list what you carry[line break]";
	say "  STATUS          show O2, morale, score, inventory[line break]";
	say "  TAKE [bracket]thing[close bracket]    pick something up[line break]";
	say "  OPEN [bracket]thing[close bracket]    open a container or hatch[line break]";
	say "  EAT [bracket]thing[close bracket]     consume food, restores morale[line break]";
	say "  REST or SLEEP   recover morale, costs O2 (Crew Quarters only)[line break]";
	say "  PULL [bracket]thing[close bracket]    operate a lever or valve[line break]";
	say "  Movement        N S E W (or fore aft port starboard), UP / DOWN[line break]";
	say "  SAVE / LOAD     save or load progress[line break]".

Chapter 2 - The Sealed Hatch

[The hatch north is held shut by a pressure differential: the corridor
 depressurized when the station was struck. The pressure-equalization
 valve bleeds your module's atmosphere into the corridor until
 pressures roughly match. Mechanical; works with no power.]

Corridor-pressurized is a truth state that varies. Corridor-pressurized is false.

The sealed hatch is scenery in the Crew Quarters. Understand "hatch" or "door" or "bulkhead" or "seal" as the sealed hatch. The description of the sealed hatch is "A heavy steel hatch. Emergency-sealed. The porthole is fogged with frost from the other side. You can feel the cold of vacuum coming through the metal. Beside the hatch, a red-painted emergency pressure-equalization valve with a three-language warning placard."

The pressure valve is scenery in the Crew Quarters. Understand "valve" or "lever" or "equalizer" or "equaliser" or "placard" or "emergency valve" as the pressure valve. The description of the pressure valve is "[if corridor-pressurized is true]The valve is open. A faint whisper still moves through it as the air in the Crew Quarters continues to equalize with the corridor beyond. Pressure is stable. Low. Breathable.[otherwise]A red-painted lever set into the bulkhead next to the sealed hatch. The placard reads in Russian, English, and German: EMERGENCY EQUALIZATION. OPERATE ONLY IF CORRIDOR VENTED. IRREVERSIBLE. The needle beside it reads zero on the corridor side.[end if]"

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
	say "You pull the lever.[paragraph break]A long wet hiss. Air rushes past you. The stale warm of your module bleeding through the valve into the cold beyond. Your ears pop. Objects not tethered down drift toward the hatch. The photograph. The pen. A drop of condensation. Pulled by the last of the pressure differential.[paragraph break]The hiss fades. The needle on the gauge swings up from zero and stops somewhere low. Sufficient. Your eardrums settle. The hatch releases with a soft mechanical clunk.[paragraph break]You have just shared half your air with a vacuum. It had to be done."

Chapter 3 - Main Corridor

The Main Corridor is north of the Crew Quarters. "The main corridor of Mir-3 is the central node. Six ports meeting at a single volume. It is wrong in every way you can parse. Cold. Low-pressure. Silent in a way that is not the silence of a machine at rest but the silence of a place something has happened to.[paragraph break]Frost glazes the inner hull where the breach vented. Loose objects drift in a slow parade. A mug. A clipboard. A flight manual open to a page no one will finish reading.[paragraph break]Yevgenia Kozlova floats near the maintenance panel. You look at her once. Then you look away.[paragraph break]Hatches lead in every direction. Fore (north) to the Command Module. Aft (south) to the Crew Quarters. Starboard (east) to the Armament Bay[if armament-bay-unlocked is false], its hatch marked КАТАЛОГ ВМФ-07 and dogged shut[end if]. Port (west) to the Hydroponics Lab. Zenith (up) to Life Support. Nadir (down) to the Observation Cupola."

The drifting debris is scenery in the Main Corridor. The description of the drifting debris is "Cables hang loose from open maintenance panels. Frost layers the inner hull where insulation has lost power. The air is thin and cold. Each breath stings the back of your throat."

The frost is scenery in the Main Corridor. The description of the frost is "Thick frost on the inner plates. The breach was fast. Fast enough that the moisture in the corridor's atmosphere flashed to ice on its way out."

The maintenance panel is scenery in the Main Corridor. The description of the maintenance panel is "An open panel. A tangle of loose cables and blown circuit breakers. Whatever hit the station punched through every system at once."

The drifting clipboard is scenery in the Main Corridor. Understand "clipboard" as the drifting clipboard. The printed name of the drifting clipboard is "clipboard". The description of the drifting clipboard is "A clipboard with the day's flight plan. The handwriting is Yevgenia's. It tumbles by, useless."

Instead of taking the drifting clipboard:
	say "You leave the clipboard floating. No more entries to make."

The drifting flight manual is scenery in the Main Corridor. Understand "flight manual" or "manual" or "book" as the drifting flight manual. The printed name of the drifting flight manual is "flight manual". The description of the drifting flight manual is "A flight manual open to the page on emergency repressurization. The author had not finished reading it."

Instead of taking the drifting flight manual:
	say "The manual drifts past. You know its contents by heart."

The drifting mug is scenery in the Main Corridor. Understand "mug" or "cup" or "drinking bulb" or "bulb" as the drifting mug. The printed name of the drifting mug is "mug". The description of the drifting mug is "A drinking bulb. Half-full of cold tea. It rotates slowly past you."

Instead of taking the drifting mug:
	say "You let the mug drift. The tea inside is long cold."

The loose cables are scenery in the Main Corridor. Understand "cables" or "cable" or "cabling" or "wires" or "wire" as the loose cables. The description of the loose cables is "A tangle of cabling. The blown breakers are obvious. The rest is too thick to trace by hand."

Instead of taking the loose cables:
	say "You tug at one. It holds fast. The rest disappears into conduit you cannot reach."

[Yevgenia's body: was an NPC, now scenery. Keep the Inform object
 name for save-state compatibility.]
Yevgenia is a woman. Yevgenia is scenery in the Main Corridor. The printed name of Yevgenia is "Yevgenia's body". Understand "yevgenia" or "kozlova" or "engineer" or "body" or "woman" as Yevgenia. The description of Yevgenia is "Yevgenia Kozlova. The station's engineer. Suspended in the middle of the corridor by zero-g. Her face is calm. She probably never registered what happened. A thin film of frost on her eyelashes.[if Yevgenia's notebook is part of Yevgenia] Her flight notebook is still clipped to the chest of her suit.[otherwise] The clip where her flight notebook was is empty. You have the notebook.[end if] The hand nearest the maintenance panel holds a screwdriver she will never put down."

After examining Yevgenia:
	if yevgenia-beat-counted is false:
		now yevgenia-beat-counted is true;
		increase b2-beats-completed by 1;
	now the prior named object is Yevgenia;
	if yevgenia-beat-counted is false:
		now yevgenia-beat-counted is true;
		increase b2-beats-completed by 1;
	continue the action.

Instead of taking Yevgenia:
	say "You cannot bring yourself to move her. Not yet."

Instead of attacking Yevgenia:
	say "She is beyond anything you could do."

The held screwdriver is scenery in the Main Corridor. Understand "screwdriver" or "tool" as the held screwdriver. The printed name of the held screwdriver is "screwdriver". The description of the held screwdriver is "She holds it the way you hold a tool when you have one second to decide if it goes in the panel or not."

Instead of taking the held screwdriver:
	say "You would have to pry it from her hand. You will not do that."

Yevgenia's notebook is a thing. Understand "notebook" or "book" or "journal" or "notes" or "her notebook" as Yevgenia's notebook. The printed name of Yevgenia's notebook is "Yevgenia's flight notebook". The description of Yevgenia's notebook is "A water-stained field notebook. Half in Cyrillic shorthand. Half in numbers. Yevgenia's handwriting. The last entries fill most of a page and are dated tonight. You could read it."

Instead of taking Yevgenia's notebook when Yevgenia's notebook is part of Yevgenia:
	now Yevgenia's notebook is in the Main Corridor;
	now the player carries Yevgenia's notebook;
	say "You unclip the notebook from the front of her suit. You try not to disturb her more than you have to."

Yevgenia's notebook is part of Yevgenia.

Talking to is an action applying to one thing.
Understand "talk to [something]" as talking to.
Understand "speak to [something]" as talking to.
Understand "speak with [something]" as talking to.

Instead of talking to Yevgenia:
	say "You try. The words catch. She does not move. You knew she would not."

Instead of talking to Petrov:
	say "You say his name. The word has nowhere to go. His hand does not leave the hatch wheel."

Instead of talking to something:
	say "There is no one here to speak with."

[Inform 7's standard rules bind "read" as a synonym for examining; clear
 it first so our Reading action gets the verb.]
Understand the command "read" as something new.
Reading is an action applying to one thing.
Understand "read [something]" as reading.

Notebook-read is a truth state that varies. Notebook-read is false.

Instead of reading Yevgenia's notebook:
	now notebook-read is true;
	if notebook-beat-counted is false:
		now notebook-beat-counted is true;
		increase b1-beats-completed by 1;
	say "You turn to the last full page.[paragraph break][italic type]EMP confirmed. Not solar. Not ours. Military grade. Every bus fried simultaneously.[line break]Reactor tripped clean. Isolated bus in the command module SHOULD still be intact. Capacitors look OK on external inspection. Requires multimeter and manual hard-reset sequence. See margin notes.[line break]Life support: twelve to eighteen hours on passive LiOH. After that, CO₂ wins.[line break]Selengrad burn: combined delta-v from Mir-3 and one American station. 1,247 m/s if we shed non-essential mass. Window opens in 9h. One station alone cannot make it. The Moon is a delta-v problem.[line break]КАТАЛОГ ВМФ-07. Code is [safe-code of the classified safe]. I am the only one on the station who knows it now.[line break]ARGON-87 still online. Backup telemetry AI on the isolated bus. Ask him about transmit if comms are restored. He may have heard something we cannot.[line break]Need Petrov to authorize the approach to the Americans. He will hate it. He will agree. He knows we have no other option.[roman type][paragraph break]There is nothing else in the notebook. The margin math confirms the Selengrad trajectory. Fuel. Time. The burn window. If Mir-3 combines reserves with Freedom Station."

[Inform 7's standard rules already define "consulting it about" with
 grammar "consult [something] about [text]". Just add a synonym for the
 common "look up X in Y" phrasing.]
Understand "look up [text] in [something]" as consulting it about (with nouns reversed).

Instead of consulting Yevgenia's notebook about a topic listed in the Table of Notebook Topics:
	now notebook-read is true;
	if notebook-beat-counted is false:
		now notebook-beat-counted is true;
		increase b1-beats-completed by 1;
	say "[response entry][paragraph break]".

Instead of consulting Yevgenia's notebook about:
	say "Yevgenia did not write about that. Her last entries cover the EMP damage, the Selengrad burn, the safe code for КАТАЛОГ ВМФ-07, and ARGON-87."

Table of Notebook Topics
topic	response
"safe" or "code" or "vmf" or "combination" or "keypad"	"[italic type]КАТАЛОГ ВМФ-07. Code is [safe-code of the classified safe]. I am the only one on the station who knows it now.[roman type]"
"burn" or "selengrad" or "moon" or "delta-v" or "trajectory" or "fuel" or "window"	"[italic type]Selengrad burn: combined delta-v from Mir-3 and one American station. 1,247 m/s if we shed non-essential mass. Window opens in 9h. One station alone cannot make it.[roman type][line break]The margin math fills half the page. Orbital mechanics in a dead woman's shorthand."
"argon" or "argon-87" or "ai" or "telemetry" or "backup"	"[italic type]ARGON-87 still online. Backup telemetry AI on the isolated bus. Ask him about transmit if comms are restored. He may have heard something we cannot.[roman type]"
"transmit" or "radio" or "comms" or "communications" or "distress" or "freedom" or "americans"	"[italic type]ARGON-87 still online. Backup telemetry AI on the isolated bus. Ask him about transmit if comms are restored. He may have heard something we cannot.[roman type][line break][italic type]Need Petrov to authorize the approach to the Americans. He will hate it. He will agree.[roman type]"
"emp" or "pulse" or "damage" or "power" or "bus" or "capacitor"	"[italic type]EMP confirmed. Not solar. Not ours. Military grade. Every bus fried simultaneously.[line break]Reactor tripped clean. Isolated bus in the command module SHOULD still be intact. Capacitors look OK on external inspection. Requires multimeter and manual hard-reset sequence.[roman type]"
"de-orbit" or "deorbit" or "re-entry" or "reentry" or "tonight"	"[italic type]Life support: twelve to eighteen hours on passive LiOH. After that, CO₂ wins.[roman type][line break][italic type]Selengrad burn: combined delta-v from Mir-3 and one American station. 1,247 m/s if we shed non-essential mass. Window opens in 9h.[roman type][line break]The numbers do not leave room for argument. Move or die."
"oxygen" or "air" or "life support" or "co2" or "lioh"	"[italic type]Life support: twelve to eighteen hours on passive LiOH. After that, CO₂ wins.[roman type]"
"reset" or "multimeter" or "hard-reset" or "sequence" or "repair"	"[italic type]Isolated bus in the command module SHOULD still be intact. Capacitors look OK on external inspection. Requires multimeter and manual hard-reset sequence. See margin notes.[roman type]"

Chapter 4 - Observation Cupola

The Observation Cupola is down from the Main Corridor. "The observation cupola is a blister of reinforced glass on the station's nadir side. Commander Petrov is here. He did not make it inside.[paragraph break][if war-is-discovered is true]Through the viewport, the Earth below. Fresh nuclear flashes keep blooming across the nightside. A constellation of deaths.[otherwise]Through the viewport, the Earth below. Something is wrong with the nightside.[end if][paragraph break]The hatch back to the central node is above you (zenith)."

The viewport is scenery in the Observation Cupola. Understand "earth" or "nightside" or "world" or "planet" or "window" as the viewport.

War-is-discovered is a truth state that varies. War-is-discovered is false.

Instead of examining the viewport:
	if war-is-discovered is false:
		now war-is-discovered is true;
		increase b2-beats-completed by 1;
		decrease morale-level by 15;
		say "You press your face to the reinforced glass and look down at the Earth.[paragraph break]The nightside should be a field of glittering city lights.[paragraph break]Instead, the Earth is on fire. Not continent-wide fire. Point fire. Hundreds of points. Blooms of orange and white. Some already fading. Some still expanding in slow-motion circles. Fresh ones joining them every few seconds.[paragraph break]You try to count the new flashes. Seven. Nine. Fourteen. The number keeps climbing.[paragraph break]This is not the aftermath of something. This is happening now. Thermonuclear weapons, in the hundreds, detonating beneath you in real time.[paragraph break]World War III. From three hundred kilometres up you have the clearest view of it ever captured by human eyes.[paragraph break]The silence that follows is heavier than vacuum.";
	otherwise:
		say "You look down. The flashes are still coming. Fewer now, perhaps. Or only harder to pick out from the smoke. You force yourself to look away."

Understand "look through [something]" as examining.

The reinforced glass is scenery in the Observation Cupola. The description of the reinforced glass is "Thick glass. Designed to withstand micrometeorite impacts. Tonight it frames the worst view in human history."

[Petrov's body: was an NPC, now scenery.]
Petrov is a man. Petrov is scenery in the Observation Cupola. The printed name of Petrov is "Commander Petrov's body". Understand "petrov" or "commander" or "body" as Petrov. The description of Petrov is "Commander Petrov. Thirty years of service. One hand still on the hatch wheel. He was trying to get inside the cupola. Trying to see for himself what was happening to the country that built him. The hatch was sealed by the breach before he could. His eyes are open. His face is the face of a man who worked it out in the last two seconds he had."

After examining Petrov:
	if petrov-beat-counted is false:
		now petrov-beat-counted is true;
		increase b2-beats-completed by 1;
	now the prior named object is Petrov;
	if petrov-beat-counted is false:
		now petrov-beat-counted is true;
		increase b2-beats-completed by 1;
	continue the action.

Instead of taking Petrov:
	say "You cannot."

Instead of attacking Petrov:
	say "He is beyond anything you could do."

The mechanical watch is a thing that is part of Petrov. The description of the mechanical watch is "Petrov's mechanical watch. No electronics. Unaffected by the EMP. It still ticks. The second hand sweeping placidly past a man who is no longer using it. 03:54 Moscow time. Only a few minutes since the impact."

Instead of taking the mechanical watch:
	say "You consider taking the watch. You decide against it. Let him keep the time."

Chapter 5 - Command Module

The Command Module is north of the Main Corridor. "The command module. Cramped. Packed with control panels.[if power-is-restored is true] A single console flickers with dim partial life. The isolated power bus has been restored.[otherwise] Every panel is dead.[end if] On the zenith wall, a small armored safe. КАТАЛОГ ВМФ-07. On the nadir wall, the emergency toolkit. Forward, external observation ports and dead navigational radar displays. The main corridor is aft (south). The Soyuz ferry is docked to starboard (east)."

Power-is-restored is a truth state that varies. Power-is-restored is false.
Armament-bay-unlocked is a truth state that varies. Armament-bay-unlocked is false.

The control panels are scenery in the Command Module. Understand "panels" or "panel" or "switches" or "dials" or "screens" as the control panels. The description of the control panels is "[if power-is-restored is true]Most panels remain dead. The working console on the main bus flickers with partial life.[otherwise]Every panel is dead. Status panels, navigation, comms. Without main power there is nothing to read here.[end if]"

The emergency toolkit is a closed openable container in the Command Module. The emergency toolkit is fixed in place. The description of the emergency toolkit is "A toolkit magnetically latched to the wall. Essential repair instruments inside."

The multimeter is a thing in the emergency toolkit. The description of the multimeter is "A sturdy analogue multimeter. One of the few instruments unaffected by the EMP. Essential for diagnosing electrical faults."

The manual pressure gauges are scenery in the Command Module. The description of the manual pressure gauges is "Analogue gauges. The only instruments still functioning. Hull pressure low but stable. CO₂ rising. A clear indication of a hull breach along the central service node. Whatever hit the station hit it there."

The status console is a device in the Command Module. The status console is fixed in place. The status console is switched off. The description of the status console is "[if power-is-restored is true]The screen is dim. Half the pixels are dead. But it works. Status readouts scroll across it. Most of them bad. Hull integrity compromised at the service node. Life support offline. Communications array available. Oxygen reserves: critical. The console also holds Commander Petrov's last log entry, flagged for review.[otherwise]The main status console is dead. No power reaches it.[end if]"

To say comms-status-powered:
	if distress-call-heard is false:
		say "The communications array is patched into the restored power bus. You could listen for signals.";
	otherwise if responded-to-americans is true:
		say "The radio crackles with the open channel to Freedom Station.";
	otherwise:
		say "Through the static, the faint American distress call repeating on the emergency frequency."

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
	now petrov-log-read is true;
	increase b1-beats-completed by 1.

Report reading Petrov's log:
	say "You pull up Petrov's last log entry. He dictated it to the console. Timestamped minutes after the EMP. Minutes before the impact.[paragraph break][italic type]Commander Vasili Petrov, Mir-3. Time is 03:52 Moscow. Status: EMP event confirmed at 03:47. All systems offline. Kozlova believes the isolated bus in this module is recoverable. We are assembling tools.[line break]Sensor scrape suggests a second object inbound. I do not know what it is. I do not recognize the profile. If this station survives the next hour, whoever is listening will need to know. The armament bay on this module is intact. Kozlova has the access code. Use it if you have to. The weapon is aboard for a reason. We may not have been told all of them.[line break]If you are reading this and I am not still talking. Do what you can. Make it worth something.[roman type][paragraph break]The log ends. The console shows the timestamp of its last write. 03:53. One minute before the impact."

Chapter 6 - Hydroponics Lab

The Hydroponics Lab is west of the Main Corridor. "A cylindrical compartment. Every inner surface is growing racks. The smell is shocking after the sterile corridor. Earthy. Green. Alive in a dying station.[paragraph break]Forward, racks of tomatoes, dill, and onion hang in zero-g troughs. Their leaves are yellowing. Aft, wheat, sugar beets, and beans are faring a little better. On the port wall, dead grow-lights and the small armored vault of the rescue-seed bank. Overhead, nutrient tanks. Below, the compost trap.[paragraph break]The hatch to the central node is to starboard (east)."

The growing racks are scenery in the Hydroponics Lab. Understand "plants" or "tomatoes" or "dill" or "onion" or "wheat" or "beets" or "beans" or "crops" or "vegetables" or "rack" or "racks" as the growing racks. The description of the growing racks is "The Soviet crop list. Tomatoes. Dill. Onion. Wheat. Sugar beets. Beans. The leaves go slack in the cold. Without grow-lights and heat they have hours at most."

The seed vault is scenery in the Hydroponics Lab. Understand "vault" or "seeds" or "seed bank" or "rescue vault" as the seed vault. The description of the seed vault is "A small armored vault on the port wall. Stenciled СЕМЕНА. It hums on its own battery. Heirloom seeds, stored cold, meant to outlive whatever might happen to the station. It is sealed against you. You are not the person it is for."

The nutrient tanks are scenery in the Hydroponics Lab. Understand "tanks" or "pumps" or "nutrient" or "solution" as the nutrient tanks. The description of the nutrient tanks is "Overhead tanks of green liquid and a pump that has stopped. Nutrient solution pools in zero-g. A shimmering wobbling sphere."

The compost trap is scenery in the Hydroponics Lab. Understand "compost" or "trap" or "compactor" or "trash" as the compost trap. The description of the compost trap is "A sealed trap on the nadir wall for plant waste. Not a thing you need."

Chapter 7 - Life Support Module

The Life Support Module is up from the Main Corridor. "A cylindrical compartment. Institutional green of Soviet spaceflight. Every inner surface is equipment.[paragraph break]Forward, the O₂ generator stands silent. Beneath it, a stack of lithium-hydroxide canisters tick passively. The only thing keeping you alive. Aft, a water recycler drips condensate into a catch-tray. On the port wall, CO₂ scrubbers hang dark. Their fans stopped by the EMP. On the starboard wall, a dosimeter panel glows faintly. It has its own power cell. Nothing else in here does. Overhead, an emergency EVA airlock is dogged shut.[paragraph break]The hatch to the central node is below you (nadir)."

The O2 generator is scenery in the Life Support Module. Understand "o2" or "generator" or "o2 generator" or "oxygen" or "oxygen generator" or "lioh" or "canisters" or "canister" as the O2 generator. The description of the O2 generator is "The active generator is dead. No power. Beneath it, a rack of lithium-hydroxide canisters absorb carbon dioxide passively. You can hear the faint tick of them doing their chemistry. Twelve to eighteen hours, Yevgenia's notebook said."

The water recycler is scenery in the Life Support Module. Understand "recycler" or "water" or "catch tray" as the water recycler. The description of the water recycler is "The condenser weeps a slow drip into a tray. Without heat the lines will freeze within hours. For now, you have water."

The CO2 scrubbers are scenery in the Life Support Module. Understand "co2" or "scrubbers" or "scrubber" or "fans" or "co2 scrubbers" as the CO2 scrubbers. The description of the CO2 scrubbers is "The active scrubbers are dead. Only the LiOH canisters are keeping the CO₂ down. When they are saturated, CO₂ wins."

The radiation sensor panel is scenery in the Life Support Module. Understand "panel" or "sensor panel" or "radiation panel" or "radiation sensor" or "sensors" as the radiation sensor panel. The description of the radiation sensor panel is "A small display glows faintly on the starboard wall. Ambient: 0.0018 mSv/h. Normal for low Earth orbit. Clipped into the panel is a personal pocket dosimeter. The kind you wear for a reactor walk."

The dosimeter is a thing in the Life Support Module. Understand "pocket dosimeter" or "meter" or "dosimeter panel" as the dosimeter. The description of the dosimeter is "A Soviet pocket dosimeter. A pen-sized ionization chamber with a tiny scale. Mechanical. EMP-proof. Reads accumulated dose. Essential for any walk past the reactor shield."

After taking the dosimeter:
	if dosimeter-beat-counted is false:
		now dosimeter-beat-counted is true;
		increase b2-beats-completed by 1;
	continue the action.

The EVA airlock is scenery in the Life Support Module. Understand "airlock" or "eva" or "eva airlock" as the EVA airlock. The description of the EVA airlock is "An emergency EVA airlock at zenith. Dogged shut. Without a suit and a reason, that hatch does not open tonight."

After taking the dosimeter:
	if dosimeter-beat-counted is false:
		now dosimeter-beat-counted is true;
		increase b2-beats-completed by 1;
	continue the action.

Chapter 8 - Armament Bay

The Armament Bay is east of the Main Corridor. "A narrow armored compartment. Lit only by the backwash from the corridor behind you. The air here is a little staler than elsewhere. It was never meant to be opened in flight.[paragraph break]Forward, bolted to a reinforced frame and aimed through a small armored port in the hull, the station's classified weapon. A Rikhter R-23. The same autocannon the Almaz program flew on Salyut-3 two decades ago. Aft, a rack of three 23mm shells and a maintenance kit. On the starboard wall, a fire-control console. Dark. Overhead, a manual optical periscope. Below, armored blast shielding and a spare barrel.[paragraph break]The hatch to the central node is to port (west)."

[Main Corridor blocks east until the safe is opened.]
Before going east from the Main Corridor when armament-bay-unlocked is false:
	say "The hatch is dogged shut. КАТАЛОГ ВМФ-07. A military cataloging prefix. Whatever is behind it is not for you unless someone with the code authorizes it.";
	stop the action.

The Rikhter cannon is scenery in the Armament Bay. Understand "cannon" or "r-23" or "r23" or "rikhter" or "gun" or "weapon" or "autocannon" as the Rikhter cannon. The description of the Rikhter cannon is "A Rikhter R-23. Mounted to a reinforced frame. Aimed through an armored port. Six barrels, revolver-style, gas-operated. Two thousand rounds a minute. Designed as an anti-satellite weapon by a generation of engineers who expected exactly the kind of night the Earth below is having.[paragraph break]Three 23mm shells in the rack behind it. It is not armed. The fire-control console has no power. Not tonight."

The ammunition rack is scenery in the Armament Bay. Understand "shells" or "ammo" or "ammunition" or "rack" or "kit" or "maintenance kit" as the ammunition rack. The description of the ammunition rack is "Three 23mm cannon shells in foam cradles. A maintenance kit beside them. Cleaning rod. Spare firing pin. Torque wrench."

The fire-control console is scenery in the Armament Bay. The fire-control console can be powered or unpowered. The fire-control console is unpowered. Understand "console" or "fire-control" or "fire control" or "targeting" or "radar" as the fire-control console. The description of the fire-control console is "A targeting console on the starboard wall. Radar display. Aim vector. Trigger guard. Dark. It is not on the isolated bus you just restored. It has its own armored power line. Whatever feeds that line is not live."

The optical periscope is scenery in the Armament Bay. Understand "periscope" or "optical" or "scope" as the optical periscope. The description of the optical periscope is "A manual optical periscope mounted at zenith. Backup targeting. The lens caps are still on it."

Chapter 9 - Reactor Module

The Reactor Module is south of the Crew Quarters. "A narrow compartment. Two armored bulkheads seal it off from the rest of the station. The noise in here is different. A low continuous thrum you feel more than hear. A reactor, even idled, never really stops.[paragraph break]Aft, the main engine bell and propellant control valves. Forward, the hatch back to the Crew Quarters. Port, coolant pumps and their control panels. Starboard, a docking tube to the Progress ferry. Zenith, reactor shielding access. Placards in three languages. Nadir, a sealed door stenciled СПЕНТ-ФУЕЛ.[paragraph break]Your dosimeter is ticking."

Every turn when the player is in the Reactor Module:
	decrease morale-level by 1;
	if a random chance of 1 in 4 succeeds:
		say "Your dosimeter ticks up another increment. Not lethal. Not tonight. But you cannot stay here."

The reactor shielding is scenery in the Reactor Module. Understand "shielding" or "reactor" or "placards" or "placard" or "warnings" as the reactor shielding. The description of the reactor shielding is "A wall of lead and polyethylene shielding between you and the reactor core proper. Placards in Russian, English, German. ИОНИЗИРУЮЩЕЕ ИЗЛУЧЕНИЕ. The reactor is a RORSAT-lineage uranium-235 unit. Small. Efficient. Designed to be ejected and boosted to graveyard orbit at end-of-life. It is not, this evening, being ejected."

The coolant pumps are scenery in the Reactor Module. Understand "pumps" or "coolant" or "cooling" or "panel" or "panels" as the coolant pumps. The description of the coolant pumps is "Coolant pumps on the port wall. Two of three run on mechanical inertia. The third has stopped. The EMP reached in here too. Even through the shielding."

The main engine is scenery in the Reactor Module. Understand "engine" or "bell" or "propellant" or "valves" as the main engine. The description of the main engine is "The main station-keeping engine. Aimed aft. Propellant valves in their closed positions. The burn you would need to make Selengrad is calculated in Yevgenia's notebook. Not here."

The spent fuel door is scenery in the Reactor Module. Understand "spent fuel" or "fuel door" or "sealed door" as the spent fuel door. The description of the spent fuel door is "A sealed door stenciled СПЕНТ-ФУЕЛ. Welded shut in flight. Not for you."

Chapter 10 - Progress Ferry

The Progress Ferry is east of the Reactor Module. "An unmanned cargo ferry. Docked to the station starboard of the Reactor. Not meant for crew but pressurized and warm. Warmer than the station. Its own small battery bus survived the EMP behind an armored bulkhead.[paragraph break]Cargo nets hold water packs. Sealed food. A spare multimeter in an anti-static bag. A pressurized tool kit. A small amber glass vial of potassium iodide. Radiation prophylaxis. Sealed. The hatch back to the Reactor is to port (west)."

The progress cargo is scenery in the Progress Ferry. Understand "cargo" or "water" or "food" or "supplies" or "nets" or "kit" or "tool kit" or "toolkit" as the progress cargo. The description of the progress cargo is "Water packs. Sealed food sachets. A pressurized tool kit. A second multimeter in an anti-static bag. None of it is what you need more urgently than what you already have. The water is the nicest surprise."

The potassium iodide is a thing in the Progress Ferry. The printed name of the potassium iodide is "vial of potassium iodide". Understand "iodide" or "ki" or "potassium" or "prophylaxis" or "vial" as the potassium iodide. The description of the potassium iodide is "A small amber glass vial of potassium iodide. Radiation prophylaxis. Saturates the thyroid so radioactive iodine cannot lodge there. Useful if you plan to spend real time near the reactor."

Chapter 11 - Soyuz Ferry

The Soyuz Ferry is east of the Command Module. "A three-couch Soyuz descent module. Docked starboard of the Command Module. Cold. Small. Smells of canvas and old rubber.[paragraph break]Three couches contoured to three absent cosmonauts. Commander. Flight engineer. Research cosmonaut. Overhead, a small supply locker. The hatch back to the Command Module is to port (west).[paragraph break]The de-orbit console is dark. The Soyuz has its own primary battery and small guidance system. It can still fly you home. If home is still a place you want to go."

The soyuz couches are scenery in the Soyuz Ferry. Understand "couches" or "couch" or "seat" or "seats" as the soyuz couches. The description of the soyuz couches is "Three contoured couches. Commander. Flight engineer. Research cosmonaut. All empty tonight."

The deorbit console is scenery in the Soyuz Ferry. Understand "deorbit" or "de-orbit" or "console" or "flight console" as the deorbit console. The description of the deorbit console is "A small flight console with a de-orbit initiation sequence. The Soyuz has its own guidance loop and battery. You could fly it home. Home this evening is a planet on fire."

The soyuz supply locker is scenery in the Soyuz Ferry. Understand "locker" or "supply" or "survival kit" or "kit" as the soyuz supply locker. The description of the soyuz supply locker is "A sealed supply locker. Emergency survival kit. Sealed food. A small sidearm. Nothing you need more than what you already carry."

Part 2B - Face Descriptions

[LOOK <direction> describes that face of the current module. Every module is
 mechanically rectangular (six faces). Without the flashlight lit, all faces
 read as darkness. Later, main-power-restore should flip this off-check so
 that module lighting takes over from the Zhuchok.]

Chapter 1 - Crew Quarters Faces

Instead of examining north when the location is the Crew Quarters:
	if the chemical flashlight is not lit:
		say "It is too dark forward to make much out.";
	otherwise:
		say "Forward. The sealed hatch to the main corridor. The porthole fogged with frost from the other side. Beside it, the red-painted emergency pressure-equalization lever. Its trilingual warning placard."

Instead of examining south when the location is the Crew Quarters:
	if the chemical flashlight is not lit:
		say "It is too dark aft to make much out.";
	otherwise:
		say "Aft. A heavier hatch. Radiation trefoil. Stenciled РЕАКТОР. The bulkhead around it is thicker than the forward one. Behind it, the nuclear heart of the station."

Instead of examining west when the location is the Crew Quarters:
	if the chemical flashlight is not lit:
		say "It is too dark to port to see much.";
	otherwise:
		say "Port wall. Four crew bunks in slots. Head to foot. Yours is the second from forward. You can see the loose strap you tore on your way out of the harness. The other three are empty and tidy. Two made up. One still open. Nobody will be coming back to any of them."

Instead of examining east when the location is the Crew Quarters:
	if the chemical flashlight is not lit:
		say "It is too dark to starboard to see much.";
	otherwise:
		say "Starboard wall. The emergency locker. Beside it a small personal shelf webbed under netting. Photographs. A pen. A sachet of reconstituted borscht. Small lives. Small objects. All of it wrong now."

Instead of examining up when the location is the Crew Quarters:
	if the chemical flashlight is not lit:
		say "It is too dark overhead to see anything.";
	otherwise:
		say "Overhead. Zenith. An air vent. A dead reading light. Above your bunk the little status panel that used to glow green when everything was fine. It is not glowing tonight."

Instead of examining down when the location is the Crew Quarters:
	if the chemical flashlight is not lit:
		say "It is too dark below to see anything.";
	otherwise:
		say "Below. Nadir. A net of personal storage. Dirty laundry. A second borscht sachet. A deck of Soviet playing cards drifting out of its pack. A pair of slippers no one will ever need again."

Chapter 2 - Main Corridor Faces

Instead of examining north when the location is the Main Corridor:
	if the chemical flashlight is not lit:
		say "It is too dark forward to see.";
	otherwise:
		say "Forward. The hatch to the Command Module. Partway open. Whatever hit the station left everything slightly out of alignment."

Instead of examining south when the location is the Main Corridor:
	if the chemical flashlight is not lit:
		say "It is too dark aft to see.";
	otherwise:
		say "Aft. The hatch back to the Crew Quarters. The porthole still fogged with frost from the other side."

Instead of examining west when the location is the Main Corridor:
	if the chemical flashlight is not lit:
		say "It is too dark to port to see.";
	otherwise:
		say "Port. The hatch to the Hydroponics Lab. You can smell the green leaking through the seal. Faint. Earthy. Startling."

Instead of examining east when the location is the Main Corridor:
	if the chemical flashlight is not lit:
		say "It is too dark to starboard to see.";
	otherwise if armament-bay-unlocked is true:
		say "Starboard. The hatch to the Armament Bay. The dogging bolts have withdrawn. It stands ready to open.";
	otherwise:
		say "Starboard. A dogged-shut hatch. КАТАЛОГ ВМФ-07. A military cataloging prefix you were not cleared to know about until tonight. Two heavy magnetic bolts hold it closed."

Instead of examining up when the location is the Main Corridor:
	if the chemical flashlight is not lit:
		say "It is too dark overhead to see.";
	otherwise:
		say "Overhead. Zenith. The hatch up to Life Support. You can hear the faint tick of the LiOH canisters through it."

Instead of examining down when the location is the Main Corridor:
	if the chemical flashlight is not lit:
		say "It is too dark below to see.";
	otherwise:
		say "Below. Nadir. The hatch down to the Observation Cupola. A thin line of Earthlight leaks around its seal. Brighter than it should be. The wrong color."

Chapter 3 - Reactor Module Faces

Instead of examining north when the location is the Reactor Module:
	say "Forward. The shielded hatch back to the Crew Quarters. The coolant loop runs forward through the bulkhead here. Bundled in grey lagging."

Instead of examining south when the location is the Reactor Module:
	say "Aft. The station's main engine bell. Wide. Matte-black. Pointed away from you. Propellant control valves cluster on the surrounding frame. All in their closed positions."

Instead of examining west when the location is the Reactor Module:
	say "Port. Coolant pumps and their control panels. Two of three pumps still run on mechanical inertia. A third has stopped. The control-panel screens are dead. A string of dark terminals waiting for a power bus that is not coming back soon."

Instead of examining east when the location is the Reactor Module:
	say "Starboard. A narrow docking tube to the Progress ferry. Its inner hatch is open. The ferry's warm air leaks into the compartment."

Instead of examining up when the location is the Reactor Module:
	say "Overhead. Zenith. The reactor shielding access panel. Lead and polyethylene layered in plates. Trilingual placards. Russian. English. German. ИОНИЗИРУЮЩЕЕ ИЗЛУЧЕНИЕ."

Instead of examining down when the location is the Reactor Module:
	say "Below. Nadir. A sealed door stenciled СПЕНТ-ФУЕЛ. Welded in flight. Not for you."

Chapter 4 - Command Module Faces

Instead of examining north when the location is the Command Module:
	if the chemical flashlight is not lit and power-is-restored is false:
		say "It is too dark forward to see.";
	otherwise:
		say "Forward. External observation ports along the curve of the hull. Beside them, navigational radar displays. Dead. Their screens stare back like black glass. Someday they will work. Half the reason this module exists."

Instead of examining south when the location is the Command Module:
	if the chemical flashlight is not lit and power-is-restored is false:
		say "It is too dark aft to see.";
	otherwise:
		say "Aft. The hatch down to the Main Corridor."

Instead of examining west when the location is the Command Module:
	if the chemical flashlight is not lit and power-is-restored is false:
		say "It is too dark to port to see.";
	otherwise:
		say "Port. The long-range communications array. The patched cables that feed it. Its dedicated console.[if power-is-restored is false] No power to either. A dark terminal waiting.[otherwise] Patched into the restored bus now. It crackles faintly.[end if]"

Instead of examining east when the location is the Command Module:
	if the chemical flashlight is not lit and power-is-restored is false:
		say "It is too dark to starboard to see.";
	otherwise:
		say "Starboard. The hatch to the Soyuz ferry. Docked to the side of the module. Through the small porthole in the hatch, you can see the ferry's dim interior."

Instead of examining up when the location is the Command Module:
	if the chemical flashlight is not lit and power-is-restored is false:
		say "It is too dark overhead to see.";
	otherwise:
		say "Overhead. Zenith. The wall-mounted armored safe. КАТАЛОГ ВМФ-07. Four-digit keypad below the placard. You did not know this was here before tonight.[if armament-bay-unlocked is true] Its green light is steady.[end if]"

Instead of examining down when the location is the Command Module:
	if the chemical flashlight is not lit and power-is-restored is false:
		say "It is too dark below to see.";
	otherwise:
		say "Below. Nadir. The main workstation. The manual pressure gauges. Still reading. Analogue. The EMP does not care. The emergency toolkit magnetically latched to the wall.[if power-is-restored is true] The status console beside them flickers with dim partial life.[end if]"

Chapter 5 - Soyuz Ferry Faces

Instead of examining north when the location is the Soyuz Ferry:
	say "Forward. The ferry's control console. A small forward porthole. Through the porthole you can see a curving edge of the Earth. The console is dark. Not dead. The Soyuz runs on its own primary battery."

Instead of examining south when the location is the Soyuz Ferry:
	say "Aft. The ferry's main engine and maneuvering thrusters. A manifold of small propellant lines. Everything here is cold. Tested. Exactly where the engineers left it."

Instead of examining west when the location is the Soyuz Ferry:
	say "Port. The hatch back to the Command Module."

Instead of examining east when the location is the Soyuz Ferry:
	say "Starboard. The outer hull of the ferry. Curving tight against a maintenance panel. No crew business on this wall."

Instead of examining up when the location is the Soyuz Ferry:
	say "Overhead. Zenith. A supply locker. Magnetically latched. Emergency survival kit. Sealed rations. A small sidearm in a foam cradle. The usual Soyuz kit."

Instead of examining down when the location is the Soyuz Ferry:
	say "Below. Nadir. Three contoured couches side by side. Commander. Flight engineer. Research cosmonaut. All empty. All waiting."

Chapter 6 - Observation Cupola Faces

Instead of examining north when the location is the Observation Cupola:
	say "Forward. A side viewport panel. A small rack of thermal-stress instruments. The cupola is instrumented because reinforced glass is tricky at these temperatures. The instrument dials are unlit."

Instead of examining south when the location is the Observation Cupola:
	say "Aft. A side viewport panel. A rolled emergency curtain in a recess beside it. The curtain is for when the Earth is too bright. Tonight it is the wrong kind of bright."

Instead of examining west when the location is the Observation Cupola:
	say "Port. A side viewport panel. Stars. The dark edge of the planet. If you watch for a moment, the silent bloom of another detonation at the limb."

Instead of examining east when the location is the Observation Cupola:
	say "Starboard. A side viewport panel. The panel's edge is cold to the touch. Even through your suit sleeve."

Instead of examining up when the location is the Observation Cupola:
	say "Overhead. Zenith. The hatch back to the Main Corridor. Commander Petrov is pinned near it. One hand still on the wheel."

Instead of examining down when the location is the Observation Cupola:
	if war-is-discovered is true:
		say "Below. Nadir. The main viewport. The Earth. The flashes. Still coming.";
	otherwise:
		say "Below. Nadir. The main viewport. The whole reason the cupola exists. Earth fills it. You have not looked down yet."

Chapter 7 - Life Support Faces

Instead of examining north when the location is the Life Support Module:
	say "Forward. The O₂ generator. A dead cylinder on its rack. Beneath it, the stack of lithium-hydroxide canisters doing the passive work of keeping you alive. You can hear them ticking."

Instead of examining south when the location is the Life Support Module:
	say "Aft. The water recycler. The condenser drips condensate into a catch-tray. The lines will freeze within hours without heat. For now, you have water."

Instead of examining west when the location is the Life Support Module:
	say "Port. The CO₂ scrubber bank. Fans dark. Filters still. A dead terminal mounted between them for system status. Nothing to see until power returns."

Instead of examining east when the location is the Life Support Module:
	say "Starboard. The radiation sensor panel. It glows faintly on its own small battery. The only live display in the module. [if the dosimeter is in the Life Support Module]Clipped into it: a pocket dosimeter.[otherwise]The slot where the dosimeter lived is empty. You are carrying it now.[end if]"

Instead of examining up when the location is the Life Support Module:
	say "Overhead. Zenith. The emergency EVA airlock. Dogged shut. Without a suit and a reason, it does not open."

Instead of examining down when the location is the Life Support Module:
	say "Below. Nadir. The hatch back down to the central node."

Chapter 8 - Hydroponics Faces

Instead of examining north when the location is the Hydroponics Lab:
	say "Forward. Growing racks. Tomatoes. Dill. Onion. The Soviet crop list in zero-g troughs. Leaves yellowing in the cold. Without heat and light they have hours."

Instead of examining south when the location is the Hydroponics Lab:
	say "Aft. Growing racks. Wheat. Sugar beets. Beans. Hardier than the forward crops. Faring a little better. Not by much."

Instead of examining west when the location is the Hydroponics Lab:
	say "Port. Dead grow-lights hanging in rows. Below them the small armored seed vault. СЕМЕНА. Beside it a tray of unlabeled experimental shoots. Still green."

Instead of examining east when the location is the Hydroponics Lab:
	say "Starboard. The hatch back to the central node."

Instead of examining up when the location is the Hydroponics Lab:
	say "Overhead. Zenith. Nutrient tanks and the dead pump that cycles them. A shimmering wobbling sphere of green solution has formed in zero-g where the pump stopped."

Instead of examining down when the location is the Hydroponics Lab:
	say "Below. Nadir. The compost trap. Sealed. Plant waste in. Fertilizer out. Not a thing you need."

Chapter 9 - Armament Bay Faces

Instead of examining north when the location is the Armament Bay:
	say "Forward. The Rikhter R-23 autocannon. Six-barrelled. Bolted to a reinforced frame. Aimed through a small armored port in the hull. It is where the station's classified weapon was always going to be."

Instead of examining south when the location is the Armament Bay:
	say "Aft. The ammunition rack. Three 23mm cannon shells in foam cradles. A maintenance kit. Cleaning rod. Spare firing pin. Torque wrench."

Instead of examining west when the location is the Armament Bay:
	say "Port. The hatch back to the central node."

Instead of examining east when the location is the Armament Bay:
	say "Starboard. The fire-control console. Radar. Aim vector. Trigger guard. Dark. It is not on the isolated bus you just restored. Whatever feeds its armored power line is not live tonight."

Instead of examining up when the location is the Armament Bay:
	say "Overhead. Zenith. A manual optical periscope. Backup targeting for when the console is unavailable. The lens caps are still on it."

Instead of examining down when the location is the Armament Bay:
	say "Below. Nadir. Armored blast shielding. A spare cannon barrel in a bracket."

Chapter 10 - Progress Ferry Faces

Instead of examining north when the location is the Progress Ferry:
	say "Forward. The forward cargo bulkhead. A manifest clipboard magnetically latched to it. Listing supplies by number. Most of the numbers are ticks."

Instead of examining south when the location is the Progress Ferry:
	say "Aft. The ferry's aft cargo bulkhead. The de-orbit thrusters behind it. Progress ferries are expendable. Their life ends as a flash over the Pacific."

Instead of examining west when the location is the Progress Ferry:
	say "Port. The hatch back to the Reactor Module."

Instead of examining east when the location is the Progress Ferry:
	say "Starboard. Cargo nets. Water packs. Sealed food sachets. A spare multimeter in an anti-static bag."

Instead of examining up when the location is the Progress Ferry:
	say "Overhead. Zenith. More cargo. A pressurized tool kit[if the potassium iodide is in the Progress Ferry]. A small amber glass vial of potassium iodide in a cradle[end if]."

Instead of examining down when the location is the Progress Ferry:
	say "Below. Nadir. A drifting plastic clamshell. Empty. A length of unused tie-down webbing. Nothing useful."

Part 3 - Classified Armament Reveal

The classified safe is scenery in the Command Module. Understand "safe" or "classified safe" or "armoury" or "armory" or "armament" or "panel" or "classified panel" or "keypad" as the classified safe.

The classified safe has a number called the safe-code. The safe-code of the classified safe is 0.

The description of the classified safe is "A wall-mounted safe. Four-digit keypad. Above it, a stenciled Cyrillic placard reads КАТАЛОГ ВМФ-07. A military cataloging prefix. You did not know this was here before tonight.[if notebook-read is true] Yevgenia's notebook had the code. [safe-code of the classified safe].[end if]"

To say (N - a number) as spoken digits:
	let T be N;
	let D4 be T / 1000;
	let T be T - (D4 * 1000);
	let D3 be T / 100;
	let T be T - (D3 * 100);
	let D2 be T / 10;
	let D1 be T - (D2 * 10);
	say "[D4]-[D3]-[D2]-[D1]".

Chapter 2 - Code Entry Action

[Generic keypad code-entry action. Works for the classified safe and any
 future keypad-locked object (e.g. armament bay door). The grammar accepts
 "enter NNNN on <thing>", "type NNNN on <thing>", and "enter code NNNN".]

Code-entering it on is an action applying to one number and one thing.
Understand "enter [number] on [something]" as code-entering it on.
Understand "type [number] on [something]" as code-entering it on.
Understand "enter code [number] on [something]" as code-entering it on.
Understand "type code [number] on [something]" as code-entering it on.

[Bare "enter code NNNN" targets the classified safe when in the Command Module.]
Code-entering it on the safe is an action applying to one number.
Understand "enter code [number]" as code-entering it on the safe.
Understand "enter [number]" as code-entering it on the safe.
Understand "type [number]" as code-entering it on the safe.

Check code-entering it on:
	let N be the number understood;
	if N < 1 or N > 9999:
		say "The keypad accepts four-digit codes only." instead.

Instead of code-entering a number on the classified safe:
	let N be the number understood;
	if armament-bay-unlocked is true:
		say "The safe's green light is still on. The armament bay is open.";
	otherwise if N is the safe-code of the classified safe:
		now armament-bay-unlocked is true;
		increase the score by 2;
		say "You enter [safe-code of the classified safe as spoken digits]. A single green light acknowledges. Somewhere behind the wall a heavy magnetic bolt withdraws with a dull metallic tock. Then a second, further away. The hatch to the armament bay has dogged itself open.[paragraph break]You have just armed yourself in space. Whatever that means now.";
	otherwise:
		say "The keypad blinks once. Wrong code."

Instead of opening the classified safe:
	if notebook-read is false:
		say "The safe is keypad-locked. You do not have the code.";
	otherwise if armament-bay-unlocked is true:
		say "The safe's green light is still on. The armament bay is open.";
	otherwise:
		now armament-bay-unlocked is true;
		increase the score by 2;
		increase b1-beats-completed by 1;
		say "You enter [safe-code of the classified safe as spoken digits]. A single green light acknowledges. Somewhere behind the wall a heavy magnetic bolt withdraws with a dull metallic tock. Then a second, further away. The hatch to the armament bay has dogged itself open.[paragraph break]You have just armed yourself in space. Whatever that means now."

Part 3B - Map Command

Showing the map is an action applying to nothing.
Understand "map" or "show map" or "schematic" or "layout" or "station map" or "show schematic" as showing the map.

Carry out showing the map:
	say "[line break]Mir-3 Orbital Station. Schematic.[line break]";
	say "--------------------------------[line break]";
	say "                 [bracket]Life Support[close bracket][line break]";
	say "                      | UP[line break]";
	say "  [bracket]Hydroponics[close bracket] <-- NODE --> [bracket]Armament Bay[close bracket][if armament-bay-unlocked is true] (open)[otherwise] (locked)[end if][line break]";
	say "                      | DOWN[line break]";
	say "                 [bracket]Observation Cupola[close bracket][line break]";
	say "[line break]";
	say "  [bracket]Crew Quarters[close bracket] <----- NODE -----> [bracket]Command Module[close bracket][line break]";
	say "         | AFT                             | STBD[line break]";
	say "  [bracket]Reactor[close bracket] (hot)                       [bracket]Soyuz[close bracket] (docked)[line break]";
	say "         | STBD[line break]";
	say "  [bracket]Progress[close bracket] (docked)[line break]";
	say "[line break]";
	say "  You are in the [printed name of the location of the player].[line break]"



When play begins:
	now oxygen-level is a random number between 75 and 95;
	now morale-level is a random number between 30 and 55;
	now dose-level is a random number between 0 and 3;
	now the safe-code of the classified safe is a random number from 1000 to 9999;
	say "You were sleeping. The bunk warm. The harness loose against you. The station thrumming the way it always does. Three small comforts you were not aware of having.[paragraph break]Then the crash. Not a sound. A weight. The whole station shoved sideways like a bottle off a shelf. A light went off behind your eyes. Not a flash. A whole room of sun. Inside your skull. For one impossible second.[paragraph break]Then nothing.[paragraph break]Now. You are floating. Your face is wet. You touch your forehead and your hand comes back warm and dark. You bang the back of your head on the bulkhead trying to right yourself and that is what brings you all the way back into the room.[paragraph break]The room is black. The kind of black that does not have lights coming back on in it. You can hear your own breath. You can hear the long whistle of air leaving somewhere it shouldn't. Slowing. Stopping. Then nothing. The absolute nothing of a station that is not running.[paragraph break]You are bleeding. You do not know how badly. You float in your sleeping harness. Second bunk from forward. Port wall. Crew Quarters. Whatever happened was not small.[paragraph break][bracket]New here? Type HELP for a list of commands. STATUS shows your vitals. LOOK describes the room. EXAMINE [bracket]thing[close bracket] inspects an object.[close bracket]"

Part 5 - Listening

Listening-to-station is a truth state that varies. Listening-to-station is false.

Instead of listening when the player is in the Crew Quarters and listening-to-station is false:
	now listening-to-station is true;
	decrease morale-level by 3;
	say "You hold your breath and listen.[paragraph break]The station groans. Low metal stress. The long settling of something freshly deformed. Through the hatch you can hear the hiss of a slow leak somewhere well beyond the corridor. Narrowing. Gone.[paragraph break]And nothing else. No voices. No footsteps. No human sound at all.[paragraph break]If anyone else survived, they are not calling out.[paragraph break]You try to remember how many people were on watch. You try not to remember."

Instead of listening when the player is in the Crew Quarters:
	say "The station groans. Nothing else."

Instead of listening when the player is in the Main Corridor:
	say "Thermal expansion of cold metal. The soft drift of objects that used to have a reason to stay in place."

Instead of listening when the player is in the Observation Cupola:
	say "The cupola is quiet. The glass ticks faintly with thermal stress."

Instead of listening when the player is in the Command Module and (power-is-restored is false or distress-call-heard is true):
	say "[if power-is-restored is true]The restored console hums faintly. The communications array crackles with static. Beneath it, the ghost of a signal.[otherwise]Dead silence. Not even the background hum of electronics you have lived with for months.[end if]"

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
		say "The isolated power bus is already restored. It is not much. It is all there is." instead;
	if the player does not carry the multimeter:
		say "You need a multimeter to diagnose the electrical systems. There should be one in the emergency toolkit." instead;
	if the player does not carry Yevgenia's notebook:
		say "You know the bus is recoverable. Yevgenia said as much before she died. You do not remember the reset sequence. She kept notes in her flight notebook." instead.

Carry out restoring power:
	now power-is-restored is true;
	now the status console is switched on;
	increase morale-level by 10;
	increase b1-beats-completed by 1.

Report restoring power:
	say "You work alone. Yevgenia's notebook wedged open beside the console with a bent clip.[paragraph break]Her handwriting walks you through it. Test the capacitor bank first. Green. Short the reset pin to ground for three seconds. You count under your breath. Reseat the isolation relay. You are not an engineer. You follow the instructions of a dead woman as carefully as anyone has ever followed anything.[paragraph break]With a sharp crack and a brief flash, the status console flickers to life.[paragraph break]Her notes have a short margin comment at this point. [italic type]if it sparks here, you did it right[roman type]. You let yourself breathe.[paragraph break]The screen is dim. Half the pixels are dead. But it works. Status readouts begin scrolling. Most of them bad."

Part 7 - Distress Call

Distress-call-heard is a truth state that varies. Distress-call-heard is false.

Instead of listening when the player is in the Command Module and power-is-restored is true and distress-call-heard is false:
	now distress-call-heard is true;
	increase morale-level by 3;
	say "You tune the communications array carefully through the static.[paragraph break]Through the noise, a voice. Faint. Broken. Unmistakably human. Unmistakably English.[paragraph break][italic type]...this is Freedom Station, transmitting on emergency frequency... if anyone... we have sustained critical damage from the electromagnetic pulse... life support failing... request assistance from any station, any vessel... five crew, two injured... oxygen reserves critical...[roman type][paragraph break]The transmission loops. An automated distress call.[paragraph break]Freedom Station. The American orbital platform. Your mirror image. The Americans are dying.[paragraph break]Below you, the nations that built both your stations are still destroying each other."

Part 8 - Responding to the Distress Call

Responded-to-americans is a truth state that varies. Responded-to-americans is false.
Chose-silence is a truth state that varies. Chose-silence is false.
Selengrad-prep-begun is a truth state that varies. Selengrad-prep-begun is false.

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
	if b1-beats-completed < 3 and b2-beats-completed < 3:
		say "You reach for the microphone but something holds you back. You have barely begun to understand what has happened here. The station still has secrets. The dead still have things to tell you. You are not ready to answer." instead;
	if responded-to-americans is true:
		say "You are already in contact with Freedom Station. Commander Chen's crew is standing by." instead;
	if chose-silence is true:
		say "You chose silence. The loop is gone. There is no one on the other end anymore." instead.

Carry out transmitting:
	now responded-to-americans is true;
	now selengrad-prep-begun is true;
	increase morale-level by 8;
	if b1-beats-completed >= b2-beats-completed:
		now dominant-act2-path is "engineer";
	otherwise:
		now dominant-act2-path is "witness".

Report transmitting:
	say "You key the microphone yourself. There is no one else to key it for you.[paragraph break][italic type]Freedom Station, this is Mir-3. We read your distress call. Say your status. Over.[roman type][paragraph break]The loop cuts. A pause. Long enough that you think the signal is gone. Then a new voice. Live. Shaking with relief and surprise.[paragraph break][italic type]Mir-3... oh my God. This is Commander Diane Chen, Freedom Station. We... we did not expect anyone to answer.[roman type][paragraph break]You trade damage reports with a stranger. Five crew on her side. Two injured. One on yours. No injured. You skip over the word [italic type]alive[roman type]. She skips over it too.[paragraph break]You open Yevgenia's notebook. You tell Chen about Selengrad.[paragraph break]A pause. Then her voice again. Quieter. [italic type]You are proposing we fly to the Moon.[roman type][paragraph break][italic type]I am proposing we try. It is that or a slow death in orbit.[roman type][paragraph break]Five American survivors. You. One lunar base in caretaker mode. One plan scribbled in a dead engineer's handwriting.[paragraph break][italic type]Begin preparations[roman type], Chen says, after a long silence. [italic type]We have work to do.[roman type]"

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
	say "You listen to the loop. You do not key the microphone.[paragraph break]The first time it plays, you almost answer. The second time, you almost answer. The third time, you catch yourself already reaching for the mic. You pull your hand back.[paragraph break]Chen's voice fades. Maybe her battery failed. Maybe she gave up. Maybe she is still talking and the signal is too weak to reach you. Whichever it is, the channel is gone.[paragraph break]You sit alone with the static and with the math in Yevgenia's notebook. Alone, you cannot make Selengrad. The combined fuel is not optional. It is arithmetic.[paragraph break]You tell yourself you chose this for good reasons. You are not sure you believe yourself."

Part 8B - Selengrad Arc (D1 / E1 / E2)

Chapter 1 - D1 Fuel Choice State

Chose-split-fuel is a truth state that varies. Chose-split-fuel is false.
Chose-martyr is a truth state that varies. Chose-martyr is false.
Fuel-choice-made is a truth state that varies. Fuel-choice-made is false.
D1-counter is a number that varies. D1-counter is 0.

Chapter 2 - D1 Trigger Prepare Selengrad

Preparing selengrad is an action applying to nothing.
Understand "prepare selengrad" as preparing selengrad.
Understand "prepare for selengrad" as preparing selengrad.
Understand "begin preparations" as preparing selengrad.
Understand "coordinate" as preparing selengrad.
Understand "prepare" as preparing selengrad.

Check preparing selengrad:
	if the player is not in the Command Module:
		say "You would need to be at the command module to coordinate preparations." instead;
	if selengrad-prep-begun is false:
		say "There is nothing to prepare for yet." instead;
	if fuel-choice-made is true:
		say "The fuel decision has been made. There is nothing left to do but wait." instead.

Report preparing selengrad:
	say "[bracket]TODO prose: #55[close bracket][paragraph break]Chen's voice crackles through the static. The Selengrad plan requires a decision about fuel allocation. You must choose.[paragraph break]You can SPLIT FUEL between the two stations for a shared burn, or GIVE FUEL — sacrifice Mir-3's reserves entirely so Freedom Station can make the transit alone."

Chapter 3 - D1 Sub-Choice Split Fuel

Splitting fuel is an action applying to nothing.
Understand "split fuel" as splitting fuel.
Understand "split the fuel" as splitting fuel.
Understand "share fuel" as splitting fuel.

Check splitting fuel:
	if selengrad-prep-begun is false:
		say "That does not make sense right now." instead;
	if fuel-choice-made is true:
		say "The fuel decision has already been made." instead.

Carry out splitting fuel:
	now chose-split-fuel is true;
	now fuel-choice-made is true.

Report splitting fuel:
	say "[bracket]TODO prose: #55[close bracket][paragraph break]You radio Chen. Split burn. Both stations commit their reserves. The math is tight but it works. Selengrad or nothing, together."

Chapter 4 - D1 Sub-Choice Give Fuel Martyr

Giving fuel is an action applying to nothing.
Understand "give fuel" as giving fuel.
Understand "give the fuel" as giving fuel.
Understand "sacrifice fuel" as giving fuel.
Understand "sacrifice" as giving fuel.

Check giving fuel:
	if selengrad-prep-begun is false:
		say "That does not make sense right now." instead;
	if fuel-choice-made is true:
		say "The fuel decision has already been made." instead.

Carry out giving fuel:
	now chose-martyr is true;
	now fuel-choice-made is true.

Report giving fuel:
	say "[bracket]TODO prose: #55[close bracket][paragraph break]You radio Chen. All of Mir-3's fuel. Every drop. Freedom Station will make Selengrad alone. You will remain in orbit. You know what that means."

Chapter 5 - E1 / E2 Dispatch

Every turn when fuel-choice-made is true:
	increase D1-counter by 1;
	if D1-counter >= 3:
		if chose-split-fuel is true:
			say "[line break][bracket]TODO prose: #55[close bracket][paragraph break]The burn sequence completes. Both stations arc toward the Moon. Selengrad's beacon answers. The caretaker systems wake. Against all odds, you are going to live.[paragraph break][italic type]End of the Selengrad arc — E1: Arrival.[roman type]";
			end the story saying "You have reached Selengrad";
		if chose-martyr is true:
			say "[line break][bracket]TODO prose: #55[close bracket][paragraph break]Freedom Station's engines fire on Mir-3's fuel. You watch from the cupola as Chen's station pulls away toward the Moon. Your orbit is stable. For now. The oxygen will not last. But they will make it.[paragraph break][italic type]End of the Selengrad arc — E2: Martyr.[roman type]";
			end the story saying "You gave them the Moon".

Part 8C - De-orbiting Gate Stub

The Soyuz Reentry Capsule is a room. The printed name of the Soyuz Reentry Capsule is "Soyuz Reentry Capsule". "You are strapped into the descent module. The capsule shudders around you. There is nothing to do but wait."

Deorbiting is an action applying to nothing.
Understand "deorbit" as deorbiting.
Understand "de-orbit" as deorbiting.
Understand "descend" as deorbiting.
Understand "reenter" as deorbiting.
Understand "re-enter" as deorbiting.
Understand "initiate deorbit" as deorbiting.
Understand "initiate de-orbit" as deorbiting.
Understand "initiate descent" as deorbiting.
Understand "fire retrorockets" as deorbiting.
Understand "use de-orbit console" as deorbiting.
Understand "use deorbit console" as deorbiting.

Check deorbiting:
	if the player is not in the Soyuz Ferry:
		say "You would need to be aboard the Soyuz ferry to initiate a de-orbit sequence." instead;
	if b1-beats-completed < 3 and b2-beats-completed < 3:
		say "You reach for the de-orbit console but something holds you back. You have barely begun to understand what has happened here. The station still has secrets. The dead still have things to tell you. You are not ready to leave." instead;
	if responded-to-americans is true:
		say "You have already committed to the Selengrad plan with Freedom Station. The de-orbit path is closed to you now." instead.

Carry out deorbiting:
	now chose-descent is true;
	now d3-beat-counter is 1;
	if b1-beats-completed >= b2-beats-completed:
		now dominant-act2-path is "engineer";
	otherwise:
		now dominant-act2-path is "witness";
	move the player to the Soyuz Reentry Capsule.

Report deorbiting:
	say "[bracket]TODO prose: #56[close bracket][paragraph break]You seal the hatch. You strap in. You key the de-orbit sequence. The retrorockets fire. Mir-3 falls away behind you."

Part 8CA - D3 Reentry Sequence

[The D3 reentry fires one beat per turn on a counter. The player has no
 agency during reentry — the interpreter prints scripted beats. Six beats
 total, then transition to E3.]

Every turn when chose-descent is true and d3-beat-counter > 0 and d3-beat-counter <= 6:
	if d3-beat-counter is 1:
		say "[line break][bracket]TODO prose: #56 — d3-deorbit-burn[close bracket]";
	otherwise if d3-beat-counter is 2:
		say "[line break][bracket]TODO prose: #56 — d3-atmosphere-entry[close bracket]";
	otherwise if d3-beat-counter is 3:
		say "[line break][bracket]TODO prose: #56 — d3-no-ground-control[close bracket]";
	otherwise if d3-beat-counter is 4:
		say "[line break][bracket]TODO prose: #56 — d3-continents-visible[close bracket]";
	otherwise if d3-beat-counter is 5:
		say "[line break][bracket]TODO prose: #56 — d3-soot-layers[close bracket]";
	otherwise if d3-beat-counter is 6:
		say "[line break][bracket]TODO prose: #56 — d3-touchdown[close bracket]";
	increase d3-beat-counter by 1.

Part 8CB - E3 Return Denouement

[E3 fires the turn after d3-touchdown (beat counter reaches 7). Terminal.]

Every turn when chose-descent is true and d3-beat-counter is 7:
	say "[line break][bracket]TODO prose: #56 — e3-return[close bracket]";
	end the story saying "You have returned".

Part 8D - Firing the Cannon Gate Stub

Firing the cannon is an action applying to nothing.
Understand "fire cannon" as firing the cannon.
Understand "fire r-23" as firing the cannon.
Understand "fire rikhter" as firing the cannon.
Understand "fire gun" as firing the cannon.
Understand "fire weapon" as firing the cannon.
Understand "shoot cannon" as firing the cannon.

Check firing the cannon:
	if the player is not in the Armament Bay:
		say "You would need to be in the armament bay to fire the cannon." instead;
	if b1-beats-completed < 3 and b2-beats-completed < 3:
		say "You reach for the fire-control console but something holds you back. You have barely begun to understand what has happened here. The station still has secrets. The dead still have things to tell you. You are not ready to fire." instead.

Report firing the cannon:
	say "The fire-control console is dark. The cannon is inert. Whatever feeds its armored power line is not live tonight."

Part 9 - Scene-Specific Responses

Chapter 1 - Darkness Before Flashlight

Before going north from the Crew Quarters when the chemical flashlight is not lit:
	say "You fumble in the darkness toward the hatch. You can barely see. You should find a light source first. The emergency locker might have something useful.";
	stop the action.

Chapter 2 - The Sealed Hatch Blocks Movement

Before going north from the Crew Quarters when corridor-pressurized is false:
	say "You push at the hatch. It does not budge. The porthole is fogged with frost. You can feel the cold of a vacuum on the other side through the metal. The corridor has vented. The valve beside the hatch is still closed.";
	stop the action.

Chapter 2B - The Reactor Hatch Needs a Dosimeter

Before going south from the Crew Quarters when the player does not carry the dosimeter:
	say "You crack the aft hatch. The ambient radiation warning in your head does the rest. Without a dosimeter on you, walking into a reactor compartment is how people get cooked quietly. You close it again. You need the dosimeter in Life Support first.";
	stop the action.

Chapter 3 - Reasonable Default Responses

Instead of smelling when the player is in the Crew Quarters:
	say "The air tastes thin and metallic. You are breathing what is left of the module's reserves."

Instead of smelling when the player is in the Main Corridor:
	say "Ozone. Cold metal. Faintly, behind everything else, the smell of a person who has been dead for some minutes in a cold low-pressure space."

Instead of pushing the control panels:
	say "You press buttons. Flip switches. Nothing responds. The panels are dead."

Instead of pushing the status console when power-is-restored is false:
	say "The console is dead. No amount of pressing buttons will change that without power."

[switching on the status console now redirects to operating (Part 9B).]

Instead of taking the communications array:
	say "The communications array is built into the station's infrastructure. It is not going anywhere."

Instead of taking the manual pressure gauges:
	say "The gauges are permanently mounted to the bulkhead."

Instead of taking the sleeping harness:
	say "The sleeping harness is bolted to the bulkhead."

Part 9B - Argon-87 grammar (m8 in-game runtime)

[The player addresses the Station AI through a small set of commands.
 Each emits an [AI-PROMPT: topic=...] tag that ui.js intercepts and
 routes to either the warm AI runtime or the canned offline line,
 depending on the MIRSEND_AI_ENABLED feature flag.]

Talking to argon is an action applying to nothing.
Understand "talk to argon" or "talk to station ai" or "speak to argon" or "speak to ship" or "call argon" or "call station ai" as talking to argon.

Asking argon about is an action applying to one topic.
Understand "ask argon about [text]" or "ask station ai about [text]" as asking argon about.

Carry out talking to argon:
	say "[bracket]AI-PROMPT: topic=general[close bracket]".

Carry out asking argon about:
	say "[bracket]AI-PROMPT: topic=[the topic understood][close bracket]".

Part 9C - Console Interaction Verbs

[Issue #117. Playtest agents find the consoles, try every verb in the
 dictionary, and bounce off unhelpful default refusals. This action
 catches USE / ACTIVATE / TURN ON / POWER ON / INTERACT WITH when
 applied to a console and branches on the power state.]

Chapter 1 - Operating Console Action

Operating is an action applying to one thing.
Understand "use [something]" as operating.
Understand "activate [something]" as operating.
Understand "interact with [something]" as operating.
Understand "power on [something]" as operating.
Understand the command "power" as something new.
Understand "power on [something]" as operating.
Understand "power [something]" as operating.

[TURN ON already maps to switching on in the Standard Rules. Redirect
 switching on for consoles to operating so all verbs share one path.]

Instead of switching on the deorbit console:
	try operating the deorbit console.

Instead of switching on the status console:
	try operating the status console.

Instead of switching on the fire-control console:
	try operating the fire-control console.

Chapter 2 - Unpowered Console Refusals

Instead of operating the deorbit console when power-is-restored is false:
	say "The console is dark. No power reaches the Command Module bus. Even if it had power, the de-orbit sequence requires an authorization that has not yet come from the Command Module status loop. You will need power on this side of the station first."

Instead of operating the status console when power-is-restored is false:
	say "The status console is dead. None of these panels will tell you anything until something puts power back into the bus."

Instead of operating the fire-control console when the fire-control console is unpowered:
	say "The fire-control console is dark. It is not on the isolated bus. Whatever feeds its armored power line is not live tonight."

Chapter 3 - Powered Console Responses

Instead of operating the status console when power-is-restored is true:
	say "The screen flickers. Status readouts scroll. Most of them bad. Hull integrity compromised. Life support offline. Oxygen reserves critical.[if petrov-log-read is false] The console holds Commander Petrov's last log entry, flagged for review.[end if]"

Instead of operating the deorbit console when power-is-restored is true:
	say "The console lights respond to your touch. The Soyuz guidance loop is live. Its own battery held through the pulse. The de-orbit initiation sequence waits behind a final confirmation you are not ready to give. Not yet."

Instead of operating the fire-control console when the fire-control console is powered:
	say "The targeting console hums. Radar sweep. Aim vector. The trigger guard is still locked. The weapon is ready but the decision is not yours alone."

Part 10 - Score Tracking

Chapter 1 - Achievements

[Each After rule here must `continue the action`, otherwise the default
 Report narrative is suppressed, so the player sees only the score bump
 and misses the intended response text. See issue #34.]

[Switching on the flashlight scores +1 inside the Instead rule above.
 Inform's Instead short-circuits action processing so After never fires.]

After opening the emergency locker for the first time:
	increase the score by 1;
	continue the action.

After opening the pressure valve:
	increase the score by 1;
	continue the action.

After restoring power:
	increase the score by 3;
	continue the action.

After reading Petrov's log for the first time:
	increase the score by 1;
	continue the action.

After transmitting for the first time:
	increase the score by 5;
	continue the action.

The maximum score is 14.

Part 11 - Testing Support

Chapter 1 - Test Scripts

Test quarters with "open locker / take flashlight / switch on flashlight / examine photograph / listen".
Test hatch with "open locker / take flashlight / switch on flashlight / examine hatch / pull lever / n".
Test explore with "open locker / take flashlight / switch on flashlight / pull lever / n / e / examine viewport / w / n / open toolkit / take multimeter".
Test full with "open locker / take flashlight / switch on flashlight / listen / pull lever / n / examine yevgenia / take notebook / read notebook / e / examine viewport / examine petrov / w / n / open toolkit / take multimeter / restore power / read log / listen / transmit".
Test selengrad-e1 with "open locker / take flashlight / switch on flashlight / listen / pull lever / n / examine yevgenia / take notebook / read notebook / e / examine viewport / examine petrov / w / n / open toolkit / take multimeter / restore power / read log / listen / transmit / prepare selengrad / split fuel / z / z / z".
Test selengrad-e2 with "open locker / take flashlight / switch on flashlight / listen / pull lever / n / examine yevgenia / take notebook / read notebook / e / examine viewport / examine petrov / w / n / open toolkit / take multimeter / restore power / read log / listen / transmit / prepare selengrad / give fuel / z / z / z".
