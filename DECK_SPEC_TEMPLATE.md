# Deck Spec Template

Use this as the authoring contract for future `gcanki`-driven deck builds.
OpenClaw may obtain the source from notes, Markdown, PDFs, textbooks, or raw
text, but it must convert that material into this JSON specification before
calling the single canonical builder,
`anki_deck_builder.py --spec path/to/deck_spec.json`.

The builder performs a mandatory final normalization pass immediately before
export. It preserves valid authored HTML and semantics while adding metadata-
backed Recall and NB blocks when they are absent. It then validates every
normalized card and fails the build loudly if the contract is not satisfied.

## Card-writing register

Write every front and back in the formal, measured register of a well-edited
academic textbook or technical manual.

- Use complete, grammatically well-formed sentences and precise terminology.
- Prefer explicit logical relationships and subordinate clauses when they
  improve clarity, but do not add complexity merely for its own sake.
- Keep each card strictly atomic: test exactly one fact, relationship,
  definition, or procedure.
- Include the necessary context in the front so that the answer is
  unambiguous when reviewed on its own.
- Never reuse a concept already tested by another deck in this workspace.
  A new card must add distinct informational value rather than rephrasing an
  existing card from a different deck.
- Do not repeat, paraphrase, or hint at the answer in the front.
- Avoid slang, conversational fillers, rhetorical questions, unexplained
  abbreviations, fragments, telegraphic lists, and vague pronouns.
- Keep the answer concise enough for retrieval practice: normally one or two
  focused paragraphs, not an essay.
- Preserve technical notation, units, thresholds, and causal direction
  exactly.
- Use bullets only for a short ordered set or contrast. Each bullet must have
  clear parallel structure and must not introduce a second concept.
- Every card must contain exactly one Recall hook. It must use formal wording,
  summarize only the card's single concept, and must not introduce another
  fact.

### Few-shot register examples

Weak:

```text
Front: What is volume of distribution?
Back: Volume of distribution tells you where the drug likes to live.
```

Preferred:

```text
Front: What is the pharmacokinetic meaning of volume of distribution?
Back: Volume of distribution is a theoretical volume that relates the quantity
of drug in the body to the measured plasma concentration. A large value
generally indicates comparatively extensive distribution into tissues, whereas
a small value indicates that a greater proportion of the drug remains within
the vascular compartment.
```

Weak:

```text
Front: What does steady state mean?
Back: Steady state means input and removal balance out.
```

Preferred:

```text
Front: Under repeated dosing, what condition defines pharmacokinetic steady state?
Back: Pharmacokinetic steady state is the condition in which the average rate
of drug input equals the average rate of drug elimination. Concentrations may
continue to fluctuate within a dosing interval, but their pattern remains
stable from one interval to the next.
```

Weak:

```text
Front: Why does first-pass metabolism matter?
Back: It can lower how much drug gets in.
```

Preferred:

```text
Front: How does presystemic metabolism affect the systemic availability of an
orally administered drug?
Back: Presystemic metabolism reduces systemic availability by transforming a
portion of the absorbed dose before it reaches the systemic circulation.
```

## Mathematics and quantitative methods

Every mathematics-related card must include at least one equation or formula
written in compact Unicode notation that renders cleanly in Anki and Discord.
Do not use raw LaTeX. Prefer subscripts and superscripts such as `S₀`, `Iₜ`,
and `R₀`; operators such as `≈`, `→`, `≤`, `≥`, and `∈`; and inline fractions
such as `β/γ`, `SI/N`, and `dI/dt`. Place a complete equation on its own line
when doing so improves readability.

Weak:

```text
Front: What is R0?
Back: It’s beta over gamma.
```

Preferred:

```text
Front: In the classic SIR model, how is the basic reproduction number R₀ defined?
Back: In the normalized SIR system, the basic reproduction number is given by

R₀ = β/γ

where β is the transmission rate and γ is the recovery rate. When R₀ > 1, an
introduced infection can grow; when R₀ < 1, the infection dies out.
```

Weak:

```text
Front: When does the epidemic peak?
Back: When dI/dt is zero.
```

Preferred:

```text
Front: At what value of the susceptible population does the infected
compartment reach its peak in the classic continuous-time SIR model?
Back: The infected compartment reaches its peak when dI/dt = 0. Substituting
the incidence and recovery terms yields the condition

β (S/N) = γ

which rearranges to the explicit threshold

S = (γ N)/β

At this point, transmission exactly balances recovery, and the epidemic curve
stops rising.
```

Weak:

```text
Front: What does the early growth look like?
Back: It grows exponentially at first.
```

Preferred:

```text
Front: Under the early-phase approximation S ≈ S₀ of the classic SIR model,
what is the approximate trajectory of the infected population?
Back: When susceptibility remains near its initial value, the incidence
equation simplifies to

dI/dt ≈ (β S₀/N − γ) I

The solution is therefore the pure exponential

I(t) ≈ I(0) exp[(β S₀/N − γ) t]

This explains why the early epidemic phase often appears exponential on a
linear scale.
```

Weak:

```text
Front: What is the hazard in survival analysis?
Back: Instantaneous risk of the event.
```

Preferred:

```text
Front: How is the hazard function formally defined in continuous-time
survival analysis?
Back: The hazard function is the instantaneous rate of occurrence of the event
at time t, conditional on survival to t:

h(t) = lim₍Δt→0₎ P(t ≤ T < t+Δt | T ≥ t) / Δt

Equivalently, h(t) = f(t) / S(t), where f is the density and S is the
survival function.
```

Weak:

```text
Front: What is an instrumental variable?
Back: Something that affects treatment but not the outcome directly.
```

Preferred:

```text
Front: In the linear causal model Y = α + βX + ε, what two formal conditions
must a valid instrumental variable Z satisfy?
Back: A valid instrument Z must satisfy relevance and exclusion:

Cov(Z, X) ≠ 0  (relevance)
Cov(Z, ε) = 0  (exclusion / exogeneity)

Under these conditions, the two-stage least-squares estimator recovers the
causal parameter β.
```

Weak:

```text
Front: What does stationarity mean for a time series?
Back: Mean and variance stay constant.
```

Preferred:

```text
Front: What are the defining second-order conditions for weak stationarity of
a stochastic process {Xₜ}?
Back: A process is weakly stationary if its first two moments are time-invariant:

E[Xₜ] = μ  (constant mean)
Cov(Xₜ, Xₜ₊ₖ) = γ(k)  (autocovariance depends only on lag k)

Under these conditions, the autocovariance function and the spectral density
are well-defined and time-independent.
```

## Required Fields

- `deck_name`
- `cards`

## Optional Fields

- `model_name`
- `deck_id`
- `model_id`
- `output_file`
- `css`

## Card Shape

Each card should follow the example deck pattern:

- `front`: concise, context-complete question written in the formal register
- `back`: at least two meaningful explanatory `<p>` paragraphs
- `tags`: optional note tags
- `front` should render bold in the question side for visual distinction
- `back` should include at least one pointed red-bolded high-yield term when the concept warrants emphasis
- Add exactly one non-empty, actionable `NB:` footer to every card. Derive it
  from the card's concept, preferring a direct implementation whenever
  possible. If no direct implementation exists, use an honest adjacent
  workflow that investigates, measures, visualizes, simulates, queries, tests,
  or automates something meaningfully related to the concept. Always name a
  specific package, function, method, command, application, or short workflow
  and keep the note to one short sentence or two clauses. There is no
  `not_applicable` option.
- Actively search for the best NB application rather than adding a generic
  footer after drafting the card. Never repeat the same exact NB idea,
  operation, function, or workflow across cards; vary the tool, operation,
  data task, or analytical angle while preserving a truthful connection.
  Suitable ecosystems include Python, R and RStudio, SQL and PostgreSQL
  (including SQLWorkbench), NoSQL, Excel and Microsoft 365, Google Sheets,
  MATLAB or Octave, Julia, SAS, SPSS, Stata, Tableau, Power BI, Spark,
  PySpark, dbt, Git, GitHub Actions, Linux, Bash, Docker, Jupyter, Quarto,
  REST and JSON tools, C, C++, Java, JavaScript, and domain tools such as
  NONMEM, Monolix, Phoenix WinNonlin, REDCap, QGIS, and ImageJ.
- For opaque technical or scientific terms, try a sound-alike or near-homophone first, then build the picture around that substitute.
- When the card depends on exact counts, ordered lists, thresholds, or small sequences, consider a phonetic-number or peg-word cue so the numbers themselves become memorable.
- For tier-2 yield terms, use soft background highlights that vary within the deck instead of reusing one flat accent for the whole deck.
- Recall hooks must use exactly one of the four approved hook colors: blue,
  red, purple, or navy. Tier-2 highlighting is independent and may continue
  using green, gold, pink, orange, purple, and teal.
- Validate the full spec before export and keep the generator step in one obvious command.

## Back HTML Pattern

Prefer this order when the concept supports it:

1. Short opening explanation
2. Second paragraph that tightens the causal or practical point
3. Optional bullet list for contrasts or breakdowns
4. Exactly one `.callout` Recall hook
5. Exactly one `.nb` NB footer

## Visual Rules

- Keep visuals manual and optional.
- Avoid screenshots of source notes.
- Keep captions short and useful.
- Do not rely on raw local paths in final note HTML if you use any packaged assets.

## Useful HTML Classes

- `.key` for high-yield terms
- `.callout`, `.callout.blue`, `.callout.navy`, `.callout.red`,
  `.callout.purple`
- `.nb` for tiny applied-footnote hints
- Add a rotating family of `.tier2-*` or equivalent soft-highlight styles for second-tier yield words and definitions, including `.tier2-red` when useful.
- `.blue`, `.red`, `.green`, `.gold`, `.pink`, `.orange`, `.purple`, `.teal`
- Use blue, red, green, gold, pink, orange, purple, teal, and nearby variants sparingly for structure, contrast, and callout boxes: `#255d8c`, `#b00000`, `#2e7d73`, `#2e7d73`, `#c65b7c`, `#d9822b`, `#7a4fb0`, `#5aa6a1`, plus slight nearby shade shifts when it improves variety.
- Use these deliberately, especially when you need to make the recall path obvious.

## Example Card

```json
{
  "front": "What are instrumental variables?",
  "back": "<p>...</p><p>...</p><div class=\"callout navy\"><span class=\"navy\">Recall hook:</span> ...</div>",
  "recall_hook": {
    "color": "navy",
    "text": "..."
  },
  "nb": {
    "mode": "actionable",
    "text": "In Python, pandas.DataFrame.value_counts() can quantify the observed categories."
  },
  "tags": ["Tag"]
}
```
