# study_anki

A clean, reusable workflow for generating and validating Anki decks.

This repository is intentionally separate from the legacy `FS_2026_Anki` workspace.

## Single generation entry point

All deck generation uses the CLI in `anki_deck_builder.py`. There are no
deck-specific builder scripts or alternate source-family pipelines.

Install the runtime dependency:

```bash
python -m pip install -r requirements.txt
```

Build one validated deck from a JSON specification:

```bash
python anki_deck_builder.py --spec path/to/deck_spec.json
```

Check whether the cached `.apkg` is current without rebuilding it:

```bash
python anki_deck_builder.py --spec path/to/deck_spec.json --check
```

Force regeneration when the cache is current:

```bash
python anki_deck_builder.py --spec path/to/deck_spec.json --force
```

The specification may override the output location with `output_file`, or the
CLI may override it for a one-off build:

```bash
python anki_deck_builder.py \
  --spec path/to/deck_spec.json \
  --output build/deck.apkg
```

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
