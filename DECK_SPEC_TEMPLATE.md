# Deck Spec Template

Use this as the shape for future `gcanki`-driven deck builds.
Prefer one orchestrator script that generates the full spec, runs a light validation pass, and then exports the `.apkg`.

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
- Recall hooks, when used, must also use formal wording and must not introduce
  another fact.

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
- `back`: 2-paragraph answer by default
- `tags`: optional note tags
- `front` should render bold in the question side for visual distinction
- `back` should include at least one pointed red-bolded high-yield term when the concept warrants emphasis
- Add exactly one `NB:` footer to every card. Use an actionable footer only when it supplies a concrete computational step that matches the exact concept; otherwise use the controlled `nb.mode="not_applicable"` metadata form with a truthful reason. Actionable notes should name a specific package, function, method, or short workflow that the learner can run within a few minutes, use the ecosystem that best fits the concept, and remain one short sentence or two clauses..
- Make each `NB:` concept-specific: the function or workflow must operationalize the fact being tested rather than restate its definition. Aim for diversity across the deck instead of repeating the same packages on every card. Good patterns include `naniar::vis_miss()` for missing-data patterns, `MatchIt::matchit()` followed by `cobalt::bal.tab()` for propensity-score balance, `AER::ivreg()` for instrumental variables, `survival::Surv()` plus `survival::survfit()` for censoring and Kaplan–Meier curves, `deSolve::ode()` for SIR dynamics, `stats::acf()` for autocorrelation, and `sklearn.model_selection.TimeSeriesSplit` inside a `Pipeline` for leakage-resistant validation.
- For opaque technical or scientific terms, try a sound-alike or near-homophone first, then build the picture around that substitute.
- When the card depends on exact counts, ordered lists, thresholds, or small sequences, consider a phonetic-number or peg-word cue so the numbers themselves become memorable.
- For tier-2 yield terms, use soft background highlights that vary within the deck instead of reusing one flat accent for the whole deck.
- Recall hooks must use exactly one of the five approved hook colors: blue, green, red, purple, or navy. Tier-2 highlighting is independent and may continue using gold, pink, orange, and teal.
- Validate the full spec before export and keep the generator step in one obvious command.

## Back HTML Pattern

Prefer this order when the concept supports it:

1. Short opening explanation
2. Second paragraph that tightens the causal or practical point
3. Optional bullet list for contrasts or breakdowns
4. A short `.callout` recall hook when useful

## Visual Rules

- Keep visuals manual and optional.
- Avoid screenshots of source notes.
- Keep captions short and useful.
- Do not rely on raw local paths in final note HTML if you use any packaged assets.

## Useful HTML Classes

- `.key` for high-yield terms
- `.callout`, `.callout.green`, `.callout.gold`, `.callout.red`
- `.nb` for tiny applied-footnote hints
- Add a rotating family of `.tier2-*` or equivalent soft-highlight styles for second-tier yield words and definitions, including `.tier2-red` when useful.
- `.blue`, `.red`, `.green`, `.gold`, `.pink`, `.orange`, `.purple`, `.teal`
- Use blue, red, green, gold, pink, orange, purple, teal, and nearby variants sparingly for structure, contrast, and callout boxes: `#255d8c`, `#b00000`, `#2e7d73`, `#2e7d73`, `#c65b7c`, `#d9822b`, `#7a4fb0`, `#5aa6a1`, plus slight nearby shade shifts when it improves variety.
- Use these deliberately, especially when you need to make the recall path obvious.

## Example Card

```json
{
  "front": "What are instrumental variables?",
  "back": "<p>...</p><p>...</p><div class=\"callout green\"><span class=\"green\">Recall hook:</span> ...</div>",
  "tags": ["Tag"]
}
```
