# m5 perception overlay — Playwright transcript dump — 2026-05-05

**Run by:** `node scripts/dump-perception-transcripts.mjs`. Drives the
canonical cupola-nadir-war path three times, once per morale bucket
override (`window.MIRSEND_PERCEPTION_BUCKET`), captures the resulting
transcript from `#story-output`, excerpts the cupola section.

**Verifies:**

- `[PERCEIVE cupola-nadir-war]` markers never appear in visible output
- The placeholder variant for each bucket lands at the head of the reveal
- The post-marker paragraphs ("The nightside should be …", the count,
  the framing) render unchanged across all three buckets

Real prose for these placeholders is pending issue #54
([m7][story] Write morale-axis perception variants for five key descriptions).

---

## morale:low excerpt

```
Observation Cupola.

>‍

Observation Cupola

[Auto-saved]
The observation cupola is a blister of reinforced glass on the station's nadir side. Commander Petrov is here. He did not make it inside.

Through the viewport, the Earth below. Something is wrong with the nightside.

The hatch back to the central node is above you (zenith).

>‍



[PLACEHOLDER morale:low cupola-nadir-war] You press your face to the glass.

The nightside should be a field of glittering city lights.

Instead, the Earth is on fire. Not continent-wide fire. Point fire. Hundreds of points. Blooms of orange and white. Some already fading. Some still expanding in slow-motion circles. Fresh ones joining them every few seconds.

You try to count the new flashes. Seven. Nine. Fourteen. The number keeps climbing.

This is not the aftermath of something. This is happening now. Thermonuclear weapons, in the hundreds, detonating beneath you in real time.

World War III. From three hundred kilometres up you have the clearest view of it ever captured by human eyes.

The silence that follows is heavier than vacuum.

>‍


```

## morale:mid excerpt

```
Observation Cupola.

>‍

Observation Cupola

[Auto-saved]
The observation cupola is a blister of reinforced glass on the station's nadir side. Commander Petrov is here. He did not make it inside.

Through the viewport, the Earth below. Something is wrong with the nightside.

The hatch back to the central node is above you (zenith).

>‍



[PLACEHOLDER morale:mid cupola-nadir-war] You press your face to the glass.

The nightside should be a field of glittering city lights.

Instead, the Earth is on fire. Not continent-wide fire. Point fire. Hundreds of points. Blooms of orange and white. Some already fading. Some still expanding in slow-motion circles. Fresh ones joining them every few seconds.

You try to count the new flashes. Seven. Nine. Fourteen. The number keeps climbing.

This is not the aftermath of something. This is happening now. Thermonuclear weapons, in the hundreds, detonating beneath you in real time.

World War III. From three hundred kilometres up you have the clearest view of it ever captured by human eyes.

The silence that follows is heavier than vacuum.

>‍


```

## morale:high excerpt

```
Observation Cupola.

>‍

Observation Cupola

[Auto-saved]
The observation cupola is a blister of reinforced glass on the station's nadir side. Commander Petrov is here. He did not make it inside.

Through the viewport, the Earth below. Something is wrong with the nightside.

The hatch back to the central node is above you (zenith).

>‍



[PLACEHOLDER morale:high cupola-nadir-war] You press your face to the glass.

The nightside should be a field of glittering city lights.

Instead, the Earth is on fire. Not continent-wide fire. Point fire. Hundreds of points. Blooms of orange and white. Some already fading. Some still expanding in slow-motion circles. Fresh ones joining them every few seconds.

You try to count the new flashes. Seven. Nine. Fourteen. The number keeps climbing.

This is not the aftermath of something. This is happening now. Thermonuclear weapons, in the hundreds, detonating beneath you in real time.

World War III. From three hundred kilometres up you have the clearest view of it ever captured by human eyes.

The silence that follows is heavier than vacuum.

>‍


```
