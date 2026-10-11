# study_anki

A clean, reusable workflow for generating and validating Anki decks.

This repository is intentionally separate from the legacy `FS_2026_Anki` workspace.

## Core contract

The single builder validates every card before export. Each card must have:

- at least two meaningful explanatory `<p>` paragraphs;
- exactly one Recall hook using blue, green, red, purple, or navy;
- exactly one NB footer, either an actionable computational note or an explicit
  `not_applicable` metadata declaration;
- preserved tags, valid HTML, images, equations, key-term markup, and tier-2
  styling.

Tier-2 styling retains its independent palette, including gold, pink, orange,
and teal.

## Card metadata

```json
{
  "front": "What condition defines pharmacokinetic steady state?",
  "back": "<p>...</p><p>...</p>",
  "recall_hook": {
    "color": "navy",
    "text": "Steady state represents balance between input and elimination."
  },
  "nb": {
    "mode": "actionable",
    "text": "In R, mrgsolve::mrgsim() can simulate repeated dosing."
  },
  "tags": ["pharmacokinetics"]
}
```

For genuinely non-computational concepts, use:

```json
"nb": {
  "mode": "not_applicable",
  "reason": "This definitional card has no direct computational operation."
}
```

Run the focused tests with:

```bash
python -m unittest -v test_anki_budget_guard.py
```
