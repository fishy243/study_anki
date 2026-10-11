# study_anki

A single, reusable workflow for turning source material into validated Anki
decks. OpenClaw may start with notes, Markdown, PDFs, textbooks, or raw text,
but the canonical builder consumes one JSON deck specification and produces
one Anki package.

## Single generation entry point

All deck generation uses the CLI in
[`anki_deck_builder.py`](anki_deck_builder.py). There are no deck-specific
builder scripts, `coursetext_anki` pipeline, or alternate source-family
pipelines. Source material is transformed into the JSON specification before
the shared builder is invoked.

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

The builder resolves relative image paths from the specification directory and
packages referenced local images into the `.apkg`. Text-only cards require no
media directory. The output is a standard Anki package; generated `.apkg`
files and build-cache files are not source files and should remain untracked.

## Core contract

The builder performs a mandatory final normalization pass before export and
then validates the normalized result. It fails loudly with a
`CardValidationError` or specification error; it never exports a
success-shaped package containing a malformed card. Each card must have:

- a non-empty, context-complete front;
- at least two meaningful explanatory `<p>` paragraphs in the back;
- exactly one Recall hook using blue, green, red, purple, or navy;
- exactly one NB footer, either an actionable computational note or an explicit
  `not_applicable` metadata declaration;
- preserved tags, valid HTML, images, equations, key-term markup, and tier-2
  styling.

The Recall-hook palette is independent from tier-2 highlighting. Tier-2
styling retains its existing palette, including gold, pink, orange, and teal.
The builder does not rewrite card meaning, remove valid HTML, or remove
referenced media.

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
python -m unittest discover -s . -p 'test_*.py' -v
```

## Supported specification shape

The required top-level fields are `deck_name` and `cards`. Optional fields
include `model_name`, `deck_id`, `model_id`, `output_file`, and `css`.
Each card uses `front`, `back`, optional `tags`, optional `images`, and
metadata objects named `recall_hook` and `nb` when the corresponding block is
not already present in the back. See
[`DECK_SPEC_TEMPLATE.md`](DECK_SPEC_TEMPLATE.md) for the authoring contract
and [`ANKI_CARD_GENERATION_PROMPT.md`](ANKI_CARD_GENERATION_PROMPT.md) for
the OpenClaw generation instructions.
