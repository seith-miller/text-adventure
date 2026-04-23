# Mir's End Writing Style

Narrative prose for this project matches the voice in [`docs/writing-samples/`](writing-samples/). Before writing any room description, scene, or NPC text, re-read both samples. They are the ground truth; this document is the compression.

## Hard rules

- **No em-dashes. Ever.** Use period breaks, commas, parentheses, or sentence fragments. This is non-negotiable.
- Sentence fragments are tools, not errors. Use them for rhythm and emphasis.
- Emotional weight lives in objects and actions. Never in narration.
- Cause and effect happen off-page. The reader assembles the meaning.
- No adverbs of intensity (very, really, extremely).
- No direct emotional naming of the player character (sad, afraid, relieved).

## Voice DNA

1. **Fragmentation is the rhythm engine.** The break is the emphasis. Many sentences lack verbs or subjects.
2. **Ritual exactness.** Exact numbers. Prescribed gestures. Punctuated time. "At precisely nine." "Exactly thirteen spoonfuls."
3. **Proper nouns as incantation.** Capitalized compound names carry mythic weight. Vestments of Sorrow. Boiling of the Pacific. Apply to Mir's End: КАТАЛОГ ВМФ-07. Garden of Remembrance.
4. **Sensory specifics paired with cosmic stakes.** Beetles' feet on a cheek and the end of the world. Plastic bag whispering and a curse across the block. Small concrete thing, large implied force.
5. **The supernatural is ambient, not introduced.** "Something that has always been there." The force precedes the story. The player does not learn it exists. It is already there.
6. **Short sentence closes the paragraph.** The punch lands on brevity. "Your body belongs to the faithful." "Just Dad." "Always hears."
7. **"Or so it is said."** The ritualistic hedge. The narrator declines to confirm. The reader chooses whether to believe.
8. **Negative space where explanation would go.** When a causal link would normally be filled in, leave the gap. Let the reader supply it.

## Registers

The samples exercise two registers under one voice.

- **Mystic** (Darkling Beetles): second person, ecclesiastical vocabulary, ritual-heavy, longer clauses within sentences even while fragmenting. Best for the parts of Mir's End that are most like liturgy. The WWIII reveal in the cupola. The opening. The Reactor thrum. The restoring of power.
- **Elemental** (the man, Ava): third-person close, McCarthy-influenced, no quotation marks on dialogue, heavy fragmentation, bare vocabulary. Best for action beats and encounters. Yevgenia's body. Petrov's body. The distress call. The choice to stay silent.

A single scene can shift register across paragraphs. Use the mystic for ritual moments. Drop to elemental for action and loss.

## Mir's End application

The station is a ritual environment in a collapsing world. Cosmonaut routines, classified safes with Cyrillic placards, dead crew suspended in zero-g, a reactor that never stops thrumming. All of it fits the mystic register natively.

**Supernatural lean at distress.** Under extreme morale loss or cumulative radiation dose, the narration should interpret ordinary station phenomena as metaphysical events. The objective facts stay constant. The player character's reading of them shifts.

Examples of the shift:
- Baseline: "The coolant pumps thrum."
- Distressed: "The coolant pumps speak. A low devotional sound, the station at prayer."
- Baseline: "Yevgenia's eyelashes are rimed with frost."
- Distressed: "The frost on Yevgenia's lashes catches the light in the pattern of a constellation you do not recognize. Someone made this. Someone left it for you to see."
- Baseline: "Your dosimeter ticks."
- Distressed: "Your dosimeter counts. Counting has never meant what it means now. Each number a saint."

The perception layer (issue #41) will carry most of this weight once implemented. Baseline prose should stay readable and let the perception variants lean supernatural.

## Do

- Short declarative sentences stacked.
- Fragments for weight and rhythm.
- Concrete sensory detail, often incongruous.
- Capitalize objects and events that carry mythic weight.
- End paragraphs on the shortest line.
- Let the reader assemble meaning.
- Use "or so it is said" when the narrator wants distance from a claim.
- Allow proper nouns to do the work of description.

## Don't

- Em-dashes. Ever. If tempted, break into two sentences.
- Adverbs of intensity.
- Direct emotional naming.
- Complete clause cleanliness at a climax. Break it.
- Explaining what just happened. If the player saw it, trust them.
- Two clauses of reflection after a beat. One line, or zero.

## Workflow for writing narrative prose

Every time you are about to write prose for `game/inform/Source/story.ni`, a design doc, or any player-facing text:

1. Read both files in `docs/writing-samples/`. Do not skip this step.
2. Draft.
3. Search the draft for em-dashes (`—` or `--`). Remove every one. Replace with period break, comma, or fragment.
4. Count complete grammatical sentences versus fragments. If the ratio is above 3 to 1, break sentences.
5. Read the final line of each paragraph out loud. If it runs longer than ten words, shorten or split.
6. Scan for adverbs of intensity and direct emotional naming. Strike them.
