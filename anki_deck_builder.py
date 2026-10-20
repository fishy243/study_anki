from __future__ import annotations

import argparse
import html
import hashlib
import json
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

import genanki

from deck_spec_helpers import (
    auto_highlight_key_terms,
    memory_anchor,
    tier2_variant_for,
)


BUILD_CACHE_SUFFIX = ".build-cache.json"
NORMALIZATION_CONTRACT_VERSION = "1"
RECALL_HOOK_COLORS = {"blue", "red", "purple", "navy"}
NB_NOT_APPLICABLE_TEXT = "Not applicable — this concept has no direct computational operation."


DEFAULT_CSS = """
.card {
 font-family: Helvetica, Arial, sans-serif;
 font-size: 200%;
 text-align: left;
 color: black;
 background-color: #faebd7;
 max-width: 40rem;
 padding: 2rem;
 margin: 0 auto;
 line-height: 1.35;
}
.question {
 font-weight: 700;
}
.key { color: #b00000; font-weight: 700; }
.red { color: #b00000; font-weight: 700; }
.tier2 {
 font-weight: 700;
 padding: 0.05rem 0.22rem;
 border-radius: 0.25rem;
 box-decoration-break: clone;
 -webkit-box-decoration-break: clone;
}
.tier2-blue { background: #eaf2fb; color: #255d8c; }
.tier2-red { background: #fdeceb; color: #b00000; }
.tier2-green { background: #eaf6f1; color: #2e7d73; }
.tier2-gold { background: #eaf2fb; color: #7bbddc; }
.tier2-pink { background: #fdf0f4; color: #c65b7c; }
.tier2-orange { background: #fff1e4; color: #d9822b; }
.tier2-purple { background: #f2ecfb; color: #7a4fb0; }
.tier2-teal { background: #edf9f7; color: #5aa6a1; }
.blue { color: #255d8c; font-weight: 700; }
.green { color: #2e7d73; font-weight: 700; }
.navy { color: #17365d; font-weight: 700; }
.gold { color: #7bbddc; font-weight: 700; }
.pink { color: #c65b7c; font-weight: 700; }
.orange { color: #d9822b; font-weight: 700; }
.purple { color: #7a4fb0; font-weight: 700; }
.teal { color: #5aa6a1; font-weight: 700; }
.callout {
 border-left: 6px solid #255d8c;
 background: #eaf2fb;
 padding: 0.9rem 1rem;
 margin: 1rem 0;
 border-radius: 0.3rem;
}
.callout.navy { background: #edf2f8; border-left-color: #17365d; }
.callout.gold { background: #eaf2fb; border-left-color: #2e7d73; }
.callout.red { background: #fdeceb; border-left-color: #b00000; }
.callout.pink { background: #fdf0f4; border-left-color: #c65b7c; }
.callout.orange { background: #fff1e4; border-left-color: #d9822b; }
.callout.purple { background: #f2ecfb; border-left-color: #7a4fb0; }
.callout.teal { background: #edf9f7; border-left-color: #5aa6a1; }
.nb {
 font-size: 0.75em;
 color: #5b6572;
 background: #f4f7fb;
 border-left: 4px solid #8ba8c9;
 padding: 0.55rem 0.8rem;
 margin: 0.85rem 0 0;
 border-radius: 0.25rem;
}
.nb strong { color: #255d8c; }
.image-row {
 display: flex;
 gap: 0.75rem;
 flex-wrap: wrap;
 margin-top: 0.75rem;
}
.image-row figure {
 flex: 1 1 14rem;
 margin: 0;
}
figure { margin: 1rem 0; }
figcaption {
 font-size: 0.78em;
 color: #3d3d3f;
 margin-top: 0.35rem;
}
img {
 max-width: 100%;
 height: auto;
 display: block;
 border-radius: 0.35rem;
}
ul {
 margin: 0.5rem 0 0.75rem 1.3rem;
}
li { margin: 0.2rem 0; }
""".strip()


def stable_id(text: str) -> int:
    digest = hashlib.sha1(text.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") & 0x7FFFFFFF


def file_digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def read_spec(spec_path: Path) -> dict[str, Any]:
    with spec_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_image(value: Any) -> dict[str, str]:
    if isinstance(value, str):
        return {"src": value, "caption": ""}
    if isinstance(value, dict) and "src" in value:
        return {"src": str(value["src"]), "caption": str(value.get("caption", ""))}
    raise ValueError(f"Invalid image spec: {value!r}")


def packaged_media_name(path: Path, used_names: set[str]) -> str:
    digest = hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:8]
    candidate = f"{path.stem}-{digest}{path.suffix}"
    if candidate not in used_names:
        used_names.add(candidate)
        return candidate

    suffix = 2
    while True:
        candidate = f"{path.stem}-{digest}-{suffix}{path.suffix}"
        if candidate not in used_names:
            used_names.add(candidate)
            return candidate
        suffix += 1


def rewrite_image_src(back: str, image_src: str, replacement: str) -> str:
    variants = {
        image_src,
        image_src.replace("\\", "/"),
        image_src.replace("/", "\\"),
        Path(image_src).name,
    }
    for variant in variants:
        if not variant:
            continue
        back = re.sub(
            rf'(<img[^>]*\bsrc=["\']){re.escape(variant)}(["\'])',
            rf"\g<1>{replacement}\2",
            back,
        )
    return back


def has_tier2(back: str) -> bool:
    return bool(re.search(r'class="[^"]*\btier2\b[^"]*"', back))


class CardValidationError(ValueError):
    """Raised when a card cannot satisfy the final export contract."""


def _card_error(deck_name: str, card_index: int, message: str) -> CardValidationError:
    return CardValidationError(f"Deck {deck_name!r}, card {card_index}: {message}")


def _meaningful_paragraph_count(back: str) -> int:
    paragraphs = re.findall(r"<p\b[^>]*>(.*?)</p\s*>", back, flags=re.IGNORECASE | re.DOTALL)
    count = 0
    for paragraph in paragraphs:
        text = re.sub(r"<[^>]+>", " ", paragraph)
        text = html.unescape(text)
        if re.sub(r"\s+", " ", text).strip():
            count += 1
    return count


def _recall_hook_matches(back: str) -> list[re.Match[str]]:
    return list(
        re.finditer(
            r'<div\b[^>]*class="[^"]*\bcallout\b[^"]*"[^>]*>'
            r'.*?<span\b[^>]*class="([^"]*)"[^>]*>\s*Recall hook:\s*</span>',
            back,
            flags=re.IGNORECASE | re.DOTALL,
        )
    )


def _recall_hook_color(match: re.Match[str]) -> str:
    classes = set(match.group(1).split())
    for color in ("navy", "purple", "red", "blue"):
        if color in classes:
            return color
    return ""


def _nb_block_count(back: str) -> int:
    return len(re.findall(r'<div\b[^>]*class="[^"]*\bnb\b[^"]*"[^>]*>', back, flags=re.IGNORECASE))


def _nb_text(back: str) -> str:
    match = re.search(
        r'<div\b[^>]*class="[^"]*\bnb\b[^"]*"[^>]*>.*?<strong>\s*NB:\s*</strong>(.*?)</div>',
        back,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return ""
    text = html.unescape(re.sub(r"<[^>]+>", " ", match.group(1)))
    return re.sub(r"\s+", " ", text).strip()


def _validate_nb_footer(back: str, deck_name: str, card_index: int) -> None:
    text = _nb_text(back)
    if not text:
        raise _card_error(deck_name, card_index, "NB footer must contain non-empty actionable content")
    if text.casefold() == NB_NOT_APPLICABLE_TEXT.casefold():
        raise _card_error(deck_name, card_index, "NB footer must be actionable; not_applicable is no longer supported")


def _render_recall_hook(metadata: Any, deck_name: str, card_index: int) -> str:
    if not isinstance(metadata, dict):
        raise _card_error(deck_name, card_index, "recall_hook metadata must be an object")
    text = str(metadata.get("text", "")).strip()
    color = str(metadata.get("color", "blue")).strip().casefold()
    if color == "navy-blue":
        color = "navy"
    if color not in RECALL_HOOK_COLORS:
        allowed = ", ".join(sorted(RECALL_HOOK_COLORS))
        raise _card_error(deck_name, card_index, f"unsupported Recall hook color {color!r}; allowed colors are {allowed}")
    if not text:
        raise _card_error(deck_name, card_index, "recall_hook.text must be non-empty")
    safe_text = html.escape(text, quote=False)
    return f'<div class="callout {color}"><span class="{color}">Recall hook:</span> {safe_text}</div>'


def _render_nb(metadata: Any, deck_name: str, card_index: int) -> str:
    if not isinstance(metadata, dict):
        raise _card_error(deck_name, card_index, "nb metadata must be an object")
    mode = str(metadata.get("mode", "")).strip().casefold()
    if mode != "actionable":
        raise _card_error(deck_name, card_index, "nb.mode must be 'actionable'")
    text = str(metadata.get("text", "")).strip()
    if not text:
        raise _card_error(deck_name, card_index, "actionable NB metadata requires non-empty text")
    return f'<div class="nb"><strong>NB:</strong> {html.escape(text, quote=False)}</div>'


def normalize_card(card: dict[str, Any], *, deck_name: str, card_index: int) -> dict[str, Any]:
    if not isinstance(card, dict):
        raise _card_error(deck_name, card_index, "card must be an object")
    if "front" not in card:
        raise _card_error(deck_name, card_index, "missing front")
    if "back" not in card:
        raise _card_error(deck_name, card_index, "missing back")

    normalized = dict(card)
    front = str(card["front"]).strip()
    back = str(card["back"])
    if not front:
        raise _card_error(deck_name, card_index, "front must be non-empty")
    if _meaningful_paragraph_count(back) < 2:
        raise _card_error(deck_name, card_index, "back must contain at least two meaningful <p> paragraphs")

    hooks = _recall_hook_matches(back)
    if len(hooks) > 1:
        raise _card_error(deck_name, card_index, f"exactly one Recall hook is required; found {len(hooks)}")
    if hooks:
        color = _recall_hook_color(hooks[0])
        if color not in RECALL_HOOK_COLORS:
            raise _card_error(deck_name, card_index, "Recall hook must use blue, red, purple, or navy")
    elif "recall_hook" in card:
        back += _render_recall_hook(card["recall_hook"], deck_name, card_index)
    else:
        raise _card_error(deck_name, card_index, "missing Recall hook and recall_hook metadata")

    nb_blocks = _nb_block_count(back)
    if nb_blocks > 1:
        raise _card_error(deck_name, card_index, f"exactly one NB footer is required; found {nb_blocks}")
    if nb_blocks == 0:
        if "nb" not in card:
            raise _card_error(deck_name, card_index, "missing NB footer and nb metadata")
        back += _render_nb(card["nb"], deck_name, card_index)
    _validate_nb_footer(back, deck_name, card_index)

    normalized["front"] = front
    normalized["back"] = back
    return normalized


def validate_normalized_card(card: dict[str, Any], *, deck_name: str, card_index: int) -> None:
    if _meaningful_paragraph_count(str(card["back"])) < 2:
        raise _card_error(deck_name, card_index, "normalized back has fewer than two meaningful paragraphs")
    hooks = _recall_hook_matches(str(card["back"]))
    if len(hooks) != 1 or _recall_hook_color(hooks[0]) not in RECALL_HOOK_COLORS:
        raise _card_error(deck_name, card_index, "normalized card must have exactly one approved Recall hook")
    back = str(card["back"])
    if _nb_block_count(back) != 1:
        raise _card_error(deck_name, card_index, "normalized card must have exactly one NB footer")
    _validate_nb_footer(back, deck_name, card_index)


def fix_light_hook_text_colors(back: str) -> str:
    back = back.replace('<span class="blue">Recall hook:</span>', '<span class="blue">Recall hook:</span>')
    back = back.replace('<span class="gold">Recall hook:</span>', '<span class="gold">Recall hook:</span>')
    back = back.replace('<span class="red">Exam anchor:</span>', '<span class="red">Exam anchor:</span>')
    back = back.replace('<div class="callout red">', '<div class="callout gold">')
    return back


def normalize_concept_text(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[^0-9A-Za-z]+", " ", text)
    return re.sub(r"\s+", " ", text).strip().casefold()


def workspace_spec_paths(spec_dir: Path) -> list[Path]:
    workspace_root = spec_dir.parent
    paths: list[Path] = []
    for path in workspace_root.rglob("*_spec.json"):
        if "archive" in path.parts:
            continue
        paths.append(path)
    return paths


def collect_front_index(spec_dir: Path, current_deck_name: str) -> dict[str, list[str]]:
    front_index: dict[str, list[str]] = {}
    for spec_path in workspace_spec_paths(spec_dir):
        try:
            candidate = read_spec(spec_path)
        except Exception:
            continue

        if str(candidate.get("deck_name")) == current_deck_name:
            continue

        cards = candidate.get("cards", [])
        if not isinstance(cards, list):
            continue

        for entry in cards:
            if not isinstance(entry, dict) or "front" not in entry:
                continue
            front = normalize_concept_text(str(entry["front"]))
            if not front:
                continue
            front_index.setdefault(front, []).append(str(spec_path))
    return front_index


def assert_unique_concepts(spec: dict[str, Any], spec_dir: Path) -> None:
    deck_name = str(spec["deck_name"])
    seen: dict[str, int] = {}
    duplicates_in_spec: set[str] = set()

    for entry in spec["cards"]:
        front = normalize_concept_text(str(entry["front"]))
        if front in seen:
            duplicates_in_spec.add(front)
        seen[front] = seen.get(front, 0) + 1

    if duplicates_in_spec:
        sample = sorted(duplicates_in_spec)[0]
        raise ValueError(
            f"Duplicate concept detected inside deck '{deck_name}': {sample!r}. "
            "Split or rewrite the repeated card."
        )

    front_index = collect_front_index(spec_dir, deck_name)
    collisions: list[str] = []
    for entry in spec["cards"]:
        front = normalize_concept_text(str(entry["front"]))
        matches = front_index.get(front, [])
        if matches:
            collisions.append(f"{entry['front']!r} -> {', '.join(matches[:3])}")

    if collisions:
        raise ValueError(
            "Cross-deck concept reuse is blocked for this workspace. "
            "Rewrite the card so it tests a distinct concept.\n"
            + "\n".join(collisions[:5])
        )


def resolve_path(value: str | Path, base_dir: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return base_dir / path


def build_signature(spec: dict[str, Any], spec_dir: Path) -> str:
    normalized = dict(spec)
    normalized.pop("output_file", None)
    local_images: list[dict[str, str]] = []

    for entry in normalized["cards"]:
        for image in [normalize_image(value) for value in entry.get("images", [])]:
            src = image["src"]
            if src.startswith("http://") or src.startswith("https://"):
                continue
            path = Path(src)
            if not path.is_absolute():
                path = spec_dir / path
            local_images.append({
                "src": str(path.resolve()),
                "digest": file_digest(path),
            })

    payload = {
        "builder_digest": file_digest(Path(__file__).resolve()),
        "helpers_digest": file_digest(Path(__file__).resolve().with_name("deck_spec_helpers.py")),
        "normalization_contract_version": NORMALIZATION_CONTRACT_VERSION,
        "spec": normalized,
        "local_images": local_images,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def should_skip_creation(spec: dict[str, Any], spec_dir: Path, *, output_file: str | Path | None = None, force: bool = False) -> bool:
    if force:
        return False

    deck_name = str(spec["deck_name"])
    resolved_output = resolve_path(output_file or spec.get("output_file", spec_dir / f"{deck_name}.apkg"), spec_dir)
    if not resolved_output.exists():
        return False

    cache_path = cache_path_for(resolved_output)
    if not cache_path.exists():
        return False

    try:
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False

    return cache.get("signature") == build_signature(spec, spec_dir)


def cache_path_for(output_file: Path) -> Path:
    return output_file.with_name(f"{output_file.name}{BUILD_CACHE_SUFFIX}")


def inspect_spec(spec: dict[str, Any], spec_dir: Path) -> dict[str, int]:
    if "deck_name" not in spec:
        raise KeyError("Missing required field: deck_name")
    if "cards" not in spec:
        raise KeyError("Missing required field: cards")
    if not isinstance(spec["cards"], list):
        raise TypeError("cards must be a list")

    assert_unique_concepts(spec, spec_dir)

    cards = spec["cards"]
    total_cards = len(cards)
    cards_with_images = 0
    cards_with_tier2 = 0
    cards_with_key = 0
    distinct_images: set[str] = set()

    for index, entry in enumerate(cards, start=1):
        if not isinstance(entry, dict):
            raise TypeError(f"Card {index} must be an object")
        if "front" not in entry:
            raise KeyError(f"Card {index} is missing front")
        if "back" not in entry:
            raise KeyError(f"Card {index} is missing back")

        normalized = normalize_card(entry, deck_name=str(spec["deck_name"]), card_index=index)
        back = str(normalized["back"])
        has_key = '<span class="key">' in back
        if has_key:
            cards_with_key += 1
        if has_tier2(back) or has_key or "tier2" in [str(tag) for tag in entry.get("tags", [])]:
            cards_with_tier2 += 1

        images = [normalize_image(value) for value in entry.get("images", [])]
        if images:
            cards_with_images += 1
        for image in images:
            src = image["src"]
            distinct_images.add(src)
            if src.startswith("http://") or src.startswith("https://"):
                if not any(host in src for host in ("upload.wikimedia.org", "nih.gov", "cdc.gov")):
                    raise ValueError(f"Unsupported remote image host: {src}")
                if "transparent" in src.lower():
                    raise ValueError(f"Transparent image URL not allowed: {src}")
                continue
            path = Path(src)
            if not path.is_absolute():
                path = spec_dir / path
            if not path.exists():
                raise FileNotFoundError(f"Image not found: {path}")

    return {
        "cards": total_cards,
        "cards_with_images": cards_with_images,
        "cards_with_key": cards_with_key,
        "cards_with_tier2": cards_with_tier2,
        "distinct_images": len(distinct_images),
    }


def build_deck(spec: dict[str, Any], spec_dir: Path, *, force: bool = False) -> tuple[Path, dict[str, int], bool]:
    summary = inspect_spec(spec, spec_dir)
    signature = build_signature(spec, spec_dir)

    deck_name = str(spec["deck_name"])
    model_name = str(spec.get("model_name", deck_name))
    deck_id = int(spec.get("deck_id", stable_id(deck_name)))
    model_id = int(spec.get("model_id", stable_id(model_name)))
    output_file = resolve_path(spec.get("output_file", spec_dir / f"{deck_name}.apkg"), spec_dir)
    cache_path = cache_path_for(output_file)
    css = str(spec.get("css", DEFAULT_CSS))

    if not force and should_skip_creation(spec, spec_dir, output_file=output_file):
        return output_file, summary, True

    model = genanki.Model(
        model_id,
        model_name,
        fields=[
            {"name": "Front"},
            {"name": "Back"},
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": "<div class=\"question\">{{Front}}</div>",
                "afmt": "{{FrontSide}}\n\n<hr id=\"answer\">\n\n{{Back}}",
            }
        ],
        css=css,
    )

    deck = genanki.Deck(deck_id, deck_name)
    media_files: list[Path] = []
    media_dir = Path(tempfile.mkdtemp(prefix="anki-media-"))
    used_names: set[str] = set()
    staged_media: dict[Path, Path] = {}

    for index, entry in enumerate(spec["cards"], start=1):
        normalized = normalize_card(entry, deck_name=deck_name, card_index=index)
        front = str(normalized["front"])
        tags = [str(tag) for tag in normalized.get("tags", [])]
        back = str(normalized["back"])
        back = auto_highlight_key_terms(front, back, tags, title=deck_name)
        tier2_variant = tier2_variant_for(deck_name, front, back, index, tags)
        if 'class="tier2"' not in back and 'tier2' not in tags:
            back = back.replace('<span class="key">', f'<span class="key tier2 {tier2_variant}">', 1)
        else:
            back = re.sub(
                r'class="(?:key\s+)?tier2(?:\s+key)?"',
                f'class="key tier2 {tier2_variant}"',
                back,
                count=1,
            )
        normalized["back"] = back
        validate_normalized_card(normalized, deck_name=deck_name, card_index=index)
        images = [normalize_image(value) for value in normalized.get("images", [])]
        for image in images:
            src = image["src"]
            if src.startswith("http://") or src.startswith("https://"):
                continue
            path = Path(src)
            if not path.is_absolute():
                path = spec_dir / path
            if not path.exists():
                raise FileNotFoundError(f"Image not found: {path}")
            resolved = path.resolve()
            staged_path = staged_media.get(resolved)
            if staged_path is None:
                media_name = packaged_media_name(path, used_names)
                staged_path = media_dir / media_name
                shutil.copy2(path, staged_path)
                media_files.append(staged_path)
                staged_media[resolved] = staged_path
            media_name = staged_path.name
            back = rewrite_image_src(back, image["src"], media_name)
            back = rewrite_image_src(back, str(path), media_name)
            back = rewrite_image_src(back, str(resolved), media_name)
            back = rewrite_image_src(back, path.name, media_name)
        if has_tier2(back):
            tags.append("tier2")
        deck.add_note(genanki.Note(model=model, fields=[front, back], tags=tags))

    pkg = genanki.Package(deck, media_files=media_files)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        pkg.write_to_file(str(output_file))
        cache_path.write_text(
            json.dumps({"signature": signature, "summary": summary}, indent=2),
            encoding="utf-8",
        )
    finally:
        shutil.rmtree(media_dir, ignore_errors=True)
    return output_file, summary, False


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a reusable Anki .apkg from a JSON deck spec.")
    parser.add_argument("--spec", required=True, help="Path to a JSON deck spec file.")
    parser.add_argument("--output", required=False, help="Optional output .apkg path override.")
    parser.add_argument("--force", action="store_true", help="Force regeneration even when the cache signature matches.")
    parser.add_argument("--check", action="store_true", help="Exit 0 if the deck can be reused from cache and 1 if it needs regeneration.")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    spec = read_spec(spec_path)
    if args.output:
        spec = dict(spec)
        spec["output_file"] = args.output

    if args.check:
        if should_skip_creation(spec, spec_path.parent, force=args.force):
            print("Cache hit: deck can be reused. No regeneration needed; billing cost stays at $0.00.")
            return 0
        print("Cache miss: deck rebuild required for current inputs.")
        return 1

    output_path, summary, cached = build_deck(spec, spec_path.parent, force=args.force)
    print(f"{'Reused' if cached else 'Wrote'} {output_path}")
    print(f"Cards: {summary['cards']}")
    print(f"Cards with images: {summary['cards_with_images']}")
    print(f"Cards with tier-2 highlights: {summary['cards_with_tier2']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
