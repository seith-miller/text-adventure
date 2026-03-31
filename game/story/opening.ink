// Opening Scene – Illustrated Text Adventure
// Player wakes aboard a Soviet space station after an EMP knocks out power.

// ── Global variables ──
VAR oxygen = 100
VAR morale = 50
VAR has_flashlight = false

# ascii: darkness

You wake to nothing.

No hum of ventilation. No green glow of status panels. Just the hammering of your own pulse and a darkness so complete you cannot tell if your eyes are open.

Something has gone terribly wrong.

The emergency lighting should have kicked in by now. The station batteries alone could power the corridor strips for days. Whatever hit Mir-2 was not a simple power failure.

You float in your sleeping harness, weightless, breathing stale air that already tastes thin.

* [Search the darkness with your hands]
    -> search_darkness
* [Call out to the crew]
    -> call_out_opening
* [Hold still and listen]
    -> listen_carefully

== search_darkness ==
# ascii: bunks
Your fingers fumble along the wall of the crew quarters. You know this module by touch — every rivet, every velcro patch. The sleeping bay is two metres wide and four long. You could navigate it blindfolded.

Which is fortunate, because you are essentially blindfolded.

Your knuckles knock against the emergency locker. The latch is stiff — no electromagnetic assist — but you wrench it open with brute force.

Inside: a chemical flashlight. You crack it and a sickly green glow floods the compartment.

~ has_flashlight = true
~ morale = morale + 5

The light reveals chaos. Personal effects drift in zero-g: a photograph, a pen, a sachet of reconstituted borscht. The status panel above your bunk is dead black.

-> corridor_approach

== call_out_opening ==
# ascii: bunks
"Hello? Yevgenia? Petrov?"

Your voice sounds flat in the dead air — no ventilation fans to carry it, no intercom hum to mask it. The silence that follows is absolute.

Then, from somewhere aft, a clang. Metal on metal. Deliberate.

~ morale = morale + 2

Someone is alive.

"Over here!" A woman's voice — Yevgenia Kozlova, the station's engineer. "Don't move, I'm coming to you."

A chemical light blooms in the corridor hatch and Yevgenia's face appears, drawn and serious.

"The whole grid is dead," she says. "Every bus. Every backup. Something burned through everything at once."

~ has_flashlight = true

She hands you a second chemical stick. You crack it and clip it to your suit collar.

-> corridor_with_yevgenia

== listen_carefully ==
# ascii: darkness
You hold your breath and listen.

At first: nothing. The station is a tomb.

Then you start to pick out sounds. The faint creak of thermal expansion in the hull. A distant drip — condensation, without the ventilation system to manage humidity.

And something else. A rhythmic tapping, three-two-three, coming from the direction of the service corridor. The old knock code the crew uses when the intercom fails.

Three-two-three: "Status?"

You rap your knuckles against the bulkhead: two-one-two. "Alive."

~ morale = morale + 3

The tapping stops. Footsteps — magnetic boots clicking against the deck plates. A chemical light appears in the corridor hatch.

It's Petrov, the mission commander. His face is grim but controlled.

"Good. You're awake." He tosses you a flashlight from the emergency kit. "Come. We need to see the damage."

~ has_flashlight = true

-> corridor_with_petrov

== corridor_approach ==
# ascii: corridor
You pull yourself through the hatch into the main corridor. The green chemical glow turns every surface into a cave wall of shadow and pale light.

{has_flashlight: The flashlight helps, but it also reveals how bad things are. Cables hang loose from an open maintenance panel. Frost is already forming on the inner hull where insulation has lost power.}

~ oxygen = oxygen - 2

The air feels thinner already. Without the CO2 scrubbers, you are breathing on borrowed time.

A sound from ahead — a hatch cycling manually. Yevgenia emerges, pulling herself hand-over-hand along the guide rail.

"You're up." She doesn't waste words. "Main bus is gone. Backup bus is gone. Even the battery isolators tripped. I've never seen anything like it."

-> assess_situation

== corridor_with_yevgenia ==
# ascii: corridor
You follow Yevgenia through the hatch into the main corridor.

~ oxygen = oxygen - 2

The corridor is a tunnel of drifting debris and dead screens. Without power, the station feels less like a spacecraft and more like a submarine at the bottom of an ocean.

"I was in the service module when it hit," Yevgenia says, pulling herself along the guide rail. "Every breaker in the panel blew simultaneously. Not a surge — an electromagnetic pulse. Military grade."

Her eyes meet yours in the chemical glow.

"Something happened down there," she says quietly. "Something big."

-> assess_situation

== corridor_with_petrov ==
# ascii: corridor
You follow Petrov through the darkened corridor. His magnetic boots give him a steady, measured pace.

~ oxygen = oxygen - 2

"The station took a massive electromagnetic pulse," Petrov says, not looking back. "I was in the command module running the overnight checklist. Every screen went white, then black. Every system, gone."

He stops at a junction and turns to face you.

"In thirty years of service I have seen equipment failures, solar storms, even a depressurisation drill that turned real. I have never seen anything kill every system on a station simultaneously."

-> assess_situation

== assess_situation ==
The three of you — you, Yevgenia, and Petrov — converge at the junction near the observation cupola. The station drifts in silence around you.

~ oxygen = oxygen - 3

Petrov speaks first. "Before we do anything else, we need to understand what hit us. And we need to check the viewport."

* [Head to the observation cupola]
    -> viewport_discovery
* [Insist on checking life support first]
    -> check_life_support_first

== check_life_support_first ==
"Life support," you say. "If we don't have air, nothing else matters."

Yevgenia nods. "The CO2 scrubbers are unpowered but the lithium hydroxide canisters are passive. We have..." She does the mental arithmetic. "Maybe eighteen hours before CO2 levels become dangerous. Oxygen reserves in the emergency tanks give us roughly the same."

~ morale = morale - 2

"Eighteen hours." Petrov absorbs this. "Then we cannot waste time. The viewport first — I need to know if what I think happened actually happened."

There is something in his voice — a dread that goes beyond a station malfunction.

-> viewport_discovery

== viewport_discovery ==
# ascii: earth_from_orbit

The observation cupola is a blister of reinforced glass on the station's nadir side. Normally it offers a breathtaking view of Earth below, framed by the gentle curve of the horizon and the thin blue line of atmosphere.

What you see now stops all three of you cold.

* [Look at the Earth]
    -> see_the_war

== see_the_war ==
# ascii: earth_burning

The planet below is scarred.

Across the nightside — which should be a field of glittering city lights — there are new lights. Not cities. These are blooms of orange and white, vast and spreading, dotting the continents in clusters. Some are fading. Some are fresh, expanding in slow-motion circles that your mind refuses to interpret.

But you know what they are.

Yevgenia makes a small sound. Petrov says nothing for a long time.

~ morale = morale - 15

"Nuclear exchange," Petrov says finally. His voice is barely above a whisper. "Full-scale. Both sides."

The silence that follows is heavier than vacuum.

* [Ask how long ago]
    -> how_long_ago
* [Count the impacts]
    -> count_impacts

== how_long_ago ==
"How long?" you ask. "When did it start?"

Petrov checks his watch — a mechanical one, unaffected by the EMP. "The pulse hit us at 03:47 Moscow time. It is now 04:52. Just over an hour."

"Some of those fires are already spreading," Yevgenia says softly, staring down. "The atmospheric effects alone..."

She doesn't finish the sentence. She doesn't need to.

-> command_module_decision

== count_impacts ==
You try to count the impact sites. You lose count after forty.

They span continents — North America, Europe, Central Asia. The pattern is unmistakable: military targets first, then cities. The textbook escalation they taught in officer training, the one everyone prayed would remain theoretical.

"Both sides launched everything," Yevgenia says. "This is not a limited strike. This is..."

She trails off. There is no word adequate enough.

-> command_module_decision

== command_module_decision ==
# ascii: corridor
~ oxygen = oxygen - 5

Petrov straightens. The commander reasserts himself — training overriding horror.

"We cannot help them from here by staring. We need the station operational. Yevgenia — what can you restore?"

"Maybe the command module," she says. "It has its own isolated power bus. If the surge didn't physically destroy the capacitors, I might be able to hard-reset the system. But I need hands."

Petrov nods. "Then that is what we do." He looks at you. "We restore what we can. We survive. And then we figure out what comes next."

* [Follow them to the command module]
    -> command_module
* [Take one last look at Earth before going]
    -> last_look_earth

== last_look_earth ==
# ascii: earth_burning
You linger at the viewport for a moment longer.

Down below, the planet that built you, trained you, launched you into the sky — it is tearing itself apart. Everyone you knew. Every street you walked. Every person who ever looked up at the stars and wondered.

~ morale = morale - 5

You turn away. There is nothing you can do from up here except survive.

-> command_module

== command_module ==
# ascii: command_module
The command module is a cramped space packed with control panels, all currently dead. Yevgenia has already opened three access panels and is elbow-deep in wiring.

"Hand me the multimeter from the emergency toolkit," she says without looking up.

You find the toolkit magnetically latched to the wall and pass her the instrument.

~ oxygen = oxygen - 3

For twenty minutes, Yevgenia works in near-silence, punctuated by occasional muttered Russian. Petrov monitors the manual pressure gauges — the only instruments still functioning.

Then, with a sharp crack and a brief flash, a single console flickers to life.

"Ha!" Yevgenia pulls her hands back from the wiring, grinning despite everything. "Isolated bus is intact. I've got partial power to the command console."

~ morale = morale + 10

The screen is dim and half the pixels are dead, but it works. Status readouts begin scrolling — most of them bad.

* [Check the communications system]
    -> check_comms
* [Check oxygen reserves]
    -> check_oxygen_status

== check_oxygen_status ==
The environmental display confirms Yevgenia's estimate. Emergency oxygen reserves: approximately sixteen hours at current consumption for three crew.

~ oxygen = oxygen - 2

"We need to reduce exertion," Petrov says. "And we need a plan before those sixteen hours run out."

Yevgenia is already at the next panel. "Let me see if the radio survived."

-> check_comms

== check_comms ==
# ascii: radio
Yevgenia patches power to the communications array. The radio crackles — static at first, then a wash of noise across multiple frequencies.

"Most of the spectrum is garbage," she reports, adjusting the tuning. "EMP ionised the upper atmosphere. But shortwave might—"

She stops. Her hand freezes on the dial.

Through the static, a voice. Faint, broken, but unmistakably human. And unmistakably speaking English.

"...this is Freedom Station, transmitting on emergency frequency... if anyone... we have sustained critical damage from the electromagnetic pulse... life support failing... request assistance from any station, any vessel... five crew, two injured... oxygen reserves critical..."

The transmission loops. An automated distress call.

~ morale = morale + 3

Freedom Station. The American orbital platform. Your mirror image — a crew of five, orbiting alongside you for the past eight months. You have exchanged polite radio greetings during orbital passes. You have never set foot aboard.

Petrov stares at the radio. Yevgenia stares at Petrov.

The Americans are dying.

Twelve hours ago, your nations tried to destroy each other.

* [Respond to the distress call]
    -> respond_to_americans
* [Stay silent]
    -> stay_silent
* [Ask the crew what they think]
    -> crew_debate

== respond_to_americans ==
~ morale = morale + 8

You reach for the transmitter. Petrov catches your wrist — not hard, but firm.

"Wait," he says. "Think about what you are doing."

"They're dying, Commander."

Petrov holds your gaze for a long moment. Then he releases your wrist and nods slowly.

"You are right. Up here, there are no sides. There is only survival." He pauses. "Transmit."

You key the microphone.

"Freedom Station, this is Mir-2. We read your distress call. We have sustained similar damage but have partial systems restored. What is your status? Over."

The loop cuts. A pause. Then a new voice — live this time, shaking with relief and surprise.

"Mir-2... oh my God. This is Commander Diane Chen, Freedom Station. We... we didn't expect anyone to answer."

-> moon_base_idea

== stay_silent ==
~ morale = morale - 8

You look at Petrov. He looks at the radio. The distress call loops again.

"Commander?" Yevgenia asks quietly.

Petrov closes his eyes. "Their country just tried to kill everyone I have ever loved." His jaw works. "But those people up there — they didn't launch anything. They are cosmonauts. Like us."

He opens his eyes. "We answer. That is not a political decision. It is a human one."

He keys the microphone himself.

"Freedom Station, this is Commander Petrov, Mir-2. We hear you. What is your status? Over."

A stunned silence. Then: "Mir-2... this is Commander Diane Chen. I... thank you. Thank you for answering."

~ morale = morale + 5

-> moon_base_idea

== crew_debate ==
"What do you think?" you ask.

Yevgenia speaks first. "Answer them. Whatever happened down there, those people didn't do it. And we might need each other before this is over."

Petrov is silent for a long time, staring at the radio. The distress call loops again.

"Six months ago," he says slowly, "my daughter sent me a message. She said: 'Papa, be careful of the Americans.' She was ten years old and already afraid." His voice is steady but his eyes are not. "Now my daughter is..."

He doesn't finish. He keys the microphone.

"Freedom Station, this is Mir-2. We read you. We are damaged but operational. How can we assist? Over."

The response comes with audible relief. "Mir-2, this is Commander Chen. We have five crew, two with injuries. Life support is critical. We need help."

~ morale = morale + 5

-> moon_base_idea

== moon_base_idea ==
# ascii: command_module
The conversation with Freedom Station lasts twenty minutes. You trade damage reports, crew status, supply inventories. The picture that emerges is grim for both stations.

Between both crews — eight people, maybe thirty hours of oxygen if you pool resources, patchy communications, no ground support, and a planet below that can no longer help you.

It is Yevgenia who says it first.

"We cannot stay in orbit."

Everyone looks at her.

"The stations are damaged. Supplies are finite. Even if we restore full life support, we have weeks, not months. And there will be no resupply from below. Not for a very long time, if ever."

~ oxygen = oxygen - 5

"What are you suggesting?" Petrov asks.

Yevgenia pulls up the navigational chart on the damaged console. A wireframe model of lunar orbit rotates on the half-dead screen.

"Selengrad," she says. "The lunar base. It was designed to be self-sustaining — closed-loop atmosphere, water recycling, hydroponics. It has been in caretaker mode for two years, but the systems should still be functional."

"That's a three-day transit," Petrov says. "We don't have the fuel."

"We do if we combine both stations' reserves. Strip what we need, dock the modules, and make one ship out of two."

Silence. The idea is insane. It is also the only option that doesn't end with eight people suffocating in orbit.

Commander Chen's voice crackles through the radio. "Mir-2, did I hear that correctly? You're proposing we fly to the Moon?"

* [Support Yevgenia's plan]
    -> support_moon_plan
* [Express doubts but acknowledge there's no alternative]
    -> reluctant_agreement

== support_moon_plan ==
~ morale = morale + 10

"It's the only move that gives us a future," you say. "Not just days — a real future. If Selengrad's systems are intact, we could sustain ourselves indefinitely."

Petrov nods slowly. "The engineer is right. And so are you. We have no future in orbit." He keys the radio. "Commander Chen, we are proposing a joint mission to the Selengrad lunar installation. We believe it is our best chance of long-term survival. Are you willing to cooperate?"

A long pause. Then Chen's voice, steady now: "We're in. What do you need from us?"

-> command_decision_point

== reluctant_agreement ==
~ morale = morale + 5

"It's insane," you say. "The fuel margins alone—"

"Are possible," Yevgenia interrupts. "Tight, but possible. I've been running the numbers in my head since the lights went out."

You look at her. "You were already thinking about this?"

"I am an engineer. I solve problems. This is the problem." She gestures at the viewport, at the burning Earth below. "That is not getting better. We need to go somewhere that can keep us alive."

Petrov straightens. "Agreed. We plan for the Moon." He keys the radio. "Commander Chen, we are proposing a joint mission to the Selengrad lunar base. Will Freedom Station cooperate?"

Chen's response is immediate. "Yes. God, yes. Tell us what to do."

-> command_decision_point

== command_decision_point ==
# ascii: command_module
~ oxygen = oxygen - 3

The command module hums with fragile, partial life. The single working console displays a navigational plot — Earth, the two stations, and the Moon, connected by a thin dotted line that represents either salvation or a very complicated way to die.

Eight people. Two crippled stations. One destination.

Petrov looks at you and Yevgenia. Through the radio, Chen and her crew wait.

"This is the moment," Petrov says. "Everything we do from here is a step toward the Moon or a step toward a slow death in orbit. There is no middle ground."

He straightens, and for the first time since the lights went out, something like resolve settles over his features.

"Begin preparations. We have work to do."

-> END
