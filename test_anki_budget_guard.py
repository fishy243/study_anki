import json
import tempfile
import unittest
from pathlib import Path

from anki_deck_builder import CardValidationError, build_deck, normalize_card, should_skip_creation


class BudgetGuardTests(unittest.TestCase):
    @staticmethod
    def card(*, back=None, **overrides):
        card = {
            "front": "What condition defines pharmacokinetic steady state?",
            "back": back
            or (
                "<p>Pharmacokinetic <span class=\"key\">steady state</span> is the condition in which "
                "the average rate of drug input equals the average rate of drug elimination.</p>"
                "<p>Concentrations may continue to fluctuate within a dosing interval, "
                "but the pattern remains stable from one interval to the next.</p>"
            ),
            "recall_hook": {
                "color": "navy",
                "text": "Steady state represents balance between input and elimination."
            },
            "nb": {
                "mode": "actionable",
                "text": "In R, mrgsolve::mrgsim() can simulate concentration profiles under repeated dosing."
            },
        }
        card.update(overrides)
        return card

    def test_normalization_adds_recall_hook_and_nb_footer(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_dir = Path(tmpdir)
            spec = {
                "deck_name": "Normalized Mini Deck",
                "cards": [self.card()],
                "output_file": "normalized_mini_deck.apkg",
            }

            output_path, summary, cached = build_deck(spec, spec_dir)

            self.assertTrue(output_path.exists())
            self.assertFalse(cached)
            self.assertEqual(summary["cards"], 1)

    def test_normalization_rejects_missing_paragraph(self):
        with self.assertRaisesRegex(CardValidationError, "at least two meaningful"):
            with tempfile.TemporaryDirectory() as tmpdir:
                build_deck(
                    {
                        "deck_name": "Invalid Mini Deck",
                        "cards": [self.card(back="<p>Only one paragraph.</p>")],
                    },
                    Path(tmpdir),
                )

    def test_normalization_rejects_unsupported_recall_color(self):
        with self.assertRaisesRegex(CardValidationError, "unsupported Recall hook color"):
            with tempfile.TemporaryDirectory() as tmpdir:
                build_deck(
                    {
                        "deck_name": "Invalid Color Deck",
                        "cards": [self.card(recall_hook={"color": "gold", "text": "Invalid recall color."})],
                    },
                    Path(tmpdir),
                )

    def test_not_applicable_nb_footer_is_rendered(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_dir = Path(tmpdir)
            card = self.card()
            card.pop("nb")
            card["nb"] = {
                "mode": "not_applicable",
                "reason": "This definitional card has no direct computational operation.",
            }
            output_path, _, _ = build_deck(
                {"deck_name": "Noncomputational Mini Deck", "cards": [card]},
                spec_dir,
            )
            self.assertTrue(output_path.exists())

    def test_all_recall_colors_are_allowed_without_restricting_tier2_palette(self):
        for color in ("blue", "red", "purple", "navy"):
            card = self.card(
                recall_hook={"color": color, "text": "This is a valid recall hook."},
                back=(
                    '<p><span class="key">Concept</span> is stated here.</p>'
                    "<p>The second paragraph provides the required context.</p>"
                    '<span class="tier2 tier2-gold">tier-two term</span>'
                ),
            )
            normalized = normalize_card(card, deck_name="Color Deck", card_index=1)
            self.assertIn(f'class="callout {color}"', normalized["back"])
            self.assertIn("tier2-gold", normalized["back"])

    def test_green_recall_hook_is_rejected_while_tier2_green_remains_valid(self):
        card = self.card(
            recall_hook={"color": "green", "text": "Green is no longer an approved Recall-hook color."},
            back=(
                "<p>The concept is stated in the first paragraph.</p>"
                "<p>The second paragraph provides the required context.</p>"
                '<span class="tier2 tier2-green">tier-two term</span>'
            ),
        )
        with self.assertRaisesRegex(CardValidationError, "unsupported Recall hook color"):
            normalize_card(card, deck_name="Color Deck", card_index=1)

    def test_build_preserves_tags_and_writes_anki_package(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_dir = Path(tmpdir)
            spec = {
                "deck_name": "Tagged Mini Deck",
                "cards": [
                    {
                        **self.card(),
                        "tags": ["pk", "steady-state"],
                    }
                ],
                "output_file": "tagged_mini_deck.apkg",
            }

            output_path, summary, cached = build_deck(spec, spec_dir)

            self.assertTrue(output_path.exists())
            self.assertFalse(cached)
            self.assertEqual(summary["cards"], 1)
            self.assertEqual(summary["cards_with_key"], 1)

            import zipfile

            with zipfile.ZipFile(output_path) as package:
                self.assertIn("collection.anki2", package.namelist())

    def test_should_skip_creation_when_cache_signature_matches(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_dir = Path(tmpdir)
            output_path = spec_dir / "mini_deck.apkg"
            spec = {
                "deck_name": "Mini Deck",
                "cards": [self.card()],
                "output_file": str(output_path),
            }

            output_path, summary, cached = build_deck(spec, spec_dir)
            self.assertFalse(cached)
            self.assertTrue(output_path.exists())
            self.assertTrue(should_skip_creation(spec, spec_dir))

    def test_should_not_skip_creation_when_force_flag_asked(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_dir = Path(tmpdir)
            output_path = spec_dir / "mini_deck.apkg"
            spec = {
                "deck_name": "Mini Deck",
                "cards": [self.card()],
                "output_file": str(output_path),
            }

            build_deck(spec, spec_dir)
            self.assertFalse(should_skip_creation(spec, spec_dir, force=True))

    def test_rejects_cross_deck_duplicate_concepts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            primary_dir = root / "primary"
            other_dir = root / "other"
            primary_dir.mkdir()
            other_dir.mkdir()

            duplicate_front = "What does disposition mean after intravenous bolus dosing?"
            other_spec = {
                "deck_name": "Other Deck",
                "cards": [
                    {
                        "front": duplicate_front,
                        "back": "<p>Disposition is the combined process of distribution and elimination.</p>",
                    }
                ],
                "output_file": str(other_dir / "other.apkg"),
            }
            (other_dir / "other_spec.json").write_text(json.dumps(other_spec), encoding="utf-8")

            primary_spec = {
                "deck_name": "Primary Deck",
                "cards": [
                    {
                        "front": duplicate_front,
                        "back": "<p>Disposition is the combined process of distribution and elimination.</p>",
                    }
                ],
                "output_file": str(primary_dir / "primary.apkg"),
            }

            with self.assertRaises(ValueError):
                build_deck(primary_spec, primary_dir)


if __name__ == "__main__":
    unittest.main()
