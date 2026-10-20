from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

PALETTE: dict[str, str] = {
    "blue": "#255d8c",
    "red": "#b00000",
    "green": "#2e7d73",
    "gold": "#7bbddc",
    "pink": "#c65b7c",
    "orange": "#d9822b",
    "purple": "#7a4fb0",
    "teal": "#5aa6a1",
}

TIER2_VARIANTS: tuple[str, ...] = (
    "tier2-blue",
    "tier2-red",
    "tier2-green",
    "tier2-gold",
    "tier2-pink",
    "tier2-orange",
    "tier2-purple",
    "tier2-teal",
)


def p(text: str) -> str:
    return f"<p>{text}</p>"


def ul(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>"


def fig(src: str, caption: str) -> str:
    return f'<figure><img src="{src}" alt="{caption}"><figcaption>{caption}</figcaption></figure>'


def callout(text: str, tone: str = "blue", label: str = "Recall hook:") -> str:
    normalized_tone = tone.casefold()
    if normalized_tone == "navy-blue":
        normalized_tone = "navy"
    if normalized_tone not in {"blue", "red", "purple", "navy"}:
        normalized_tone = "blue"
    return f'<div class="callout {normalized_tone}"><span class="{normalized_tone}">{label}</span> {text}</div>'


def memory_anchor(text: str, tone: str = "blue") -> str:
    return ""


def nb(text: str) -> str:
    return f'<div class="nb"><strong>NB:</strong> {text}</div>'


_NB_RULES: list[tuple[set[str], str]] = [
    (
        {"survey", "questionnaire", "kobocollect", "data entry", "missing"},
        "KoboCollect helps capture field data; in R, `janitor::clean_names()` and `naniar::vis_miss()` help clean and inspect missingness.",
    ),
    (
        {"civil registration", "vital registration", "census", "population register", "demographic data", "survey"},
        "In R, `tidycensus::get_decennial()` is useful for census data and `survey::svydesign()` helps analyze complex survey samples.",
    ),
    (
        {"selection bias", "matching", "propensity score", "balance", "propensity", "stratification"},
        "In R, `MatchIt::matchit()` pairs subjects and `cobalt::bal.tab()` checks covariate balance after adjustment.",
    ),
    (
        {"measurement bias", "validity", "reliability", "misclassification", "inter-rater", "internal consistency", "test-retest"},
        "In R, `psych::alpha()` checks internal consistency and `irr::kappa2()` helps with agreement checks.",
    ),
    (
        {"reporting bias", "publication bias"},
        "In R, `metafor::trimfill()` and funnel plots can help inspect publication bias.",
    ),
    (
        {"recall bias"},
        "In R, `dplyr::count()` and `ggplot2::geom_col()` help compare recall patterns by group.",
    ),
    (
        {"confounding bias", "back-door path", "confounding"},
        "In R, `fixest::feols()` with covariates and `sandwich::vcovHC()` for robust SEs are common adjustment tools.",
    ),
    (
        {"causal inference", "regression", "adjustment", "sensitivity"},
        "In R, `fixest::feols()` and `lmtest::coeftest()` are useful for adjusted regression and quick robustness checks.",
    ),
    (
        {"instrumental variables", "instrumental variable", "endogeneity", "exogeneity", "relevance", "2sls", "iv"},
        "In R, `AER::ivreg()` or `ivreg::ivreg()` fits 2SLS models, and `sandwich::vcovHC()` adds robust standard errors.",
    ),
    (
        {"sample size", "power"},
        "In R, `pwr::pwr.t.test()` is a simple starting point for power and sample-size planning.",
    ),
    (
        {"sample size", "threshold", "sequence", "ordered list", "exact number", "count", "number of"},
        "When the exact count or order matters, a phonetic-number or peg-word cue can make the number itself easier to recall.",
    ),
    (
        {"survival analysis", "censoring", "kaplan-meier", "survivor curve", "risk set", "median survival", "time-to-event"},
        "In R, `survival::Surv()` stores follow-up and censoring, and `survival::survfit()` estimates Kaplan-Meier curves.",
    ),
    (
        {"right censoring", "left censoring", "interval censoring", "survival function", "event indicator", "time-to-event"},
        "In R, `survival::Surv(time, status)` is the standard way to encode censored time-to-event data before fitting survival models.",
    ),
    (
        {"infectious disease", "infectious diseases", "mathematical modeling", "sir", "seir", "compartmental", "differential equation", "epidemic"},
        "In R, `deSolve::ode()` is a common way to simulate compartmental differential-equation models like SIR.",
    ),
    (
        {"force of infection", "density-dependent", "frequency-dependent", "mass-action", "proportionate mixing", "recovery", "infectious period"},
        "In R, `deSolve::ode()` is useful for exploring force-of-infection models, and `ggplot2` helps visualize density- versus frequency-dependent transmission curves.",
    ),
    (
        {"stationary", "stationarity", "autocovariance", "autocorrelation", "correlogram", "time series", "acf", "random walk", "seasonal"},
        "In R, `forecast` and `tseries` are useful for stationarity checks, while `acf()` and `pacf()` help inspect serial correlation.",
    ),
    (
        {"autoregressive", "moving average", "arma", "arima", "airpassengers", "differencing", "time series models"},
        "In R, `forecast::Arima()` and `forecast::auto.arima()` are the usual tools for fitting ARIMA-style time series models.",
    ),
    (
        {"moving average", "ma(1)", "ma(2)", "arma", "arima", "invertibility", "white noise", "residual"},
        "In R, `forecast::Arima()` handles ARMA/ARIMA workflows, and `acf()` helps inspect the moving-average cut-off pattern.",
    ),
    (
        {"arima", "differences", "differencing", "stationary", "stationarity", "time series model selection"},
        "In R, `forecast::auto.arima()` helps compare stationary and differenced models, and `diff()` is useful for removing trend.",
    ),
    (
        {"machine learning", "ml", "prediction", "modeling", "classification"},
        "In Python, `scikit-learn` pipelines with `train_test_split()` and cross-validation are standard for prediction workflows.",
    ),
    (
        {"data science", "analytics"},
        "In R, `dplyr` and `ggplot2`; in Python, `pandas` and `seaborn` are the usual cleaning and visualization stack.",
    ),
]


def infer_nb_text(front: str, back: str, tags: list[str] | None = None) -> str | None:
    front_haystack = " ".join([front, " ".join(tags or [])]).lower()
    haystack = " ".join([front, back, " ".join(tags or [])]).lower()
    for keywords, text in _NB_RULES:
        if any(keyword_matches(front_haystack, keyword) for keyword in keywords):
            return text
    for keywords, text in _NB_RULES:
        if any(keyword_matches(haystack, keyword) for keyword in keywords):
            return text
    return None


def keyword_matches(haystack: str, keyword: str) -> bool:
    if " " in keyword:
        return keyword in haystack
    return re.search(rf"\b{re.escape(keyword)}\b", haystack) is not None


def _wrap_first_occurrence(text: str, phrase: str) -> str:
    if " " in phrase:
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
    else:
        pattern = re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)
    return pattern.sub(lambda match: f'<span class="key">{match.group(0)}</span>', text, count=1)


_HIGH_YIELD_RULES: list[tuple[set[str], tuple[str, ...]]] = [
    (
        {"time series", "airpassengers", "decomposition", "autocorrelation", "partial autocorrelation", "acf", "pacf", "forecast", "stationary", "trend", "seasonality"},
        ("time series", "AirPassengers", "decomposition", "autocorrelation", "partial autocorrelation", "ACF", "PACF", "forecast", "stationary", "trend", "seasonality"),
    ),
    (
        {"survival analysis", "survivor function", "survival function", "hazard function", "kaplan-meier", "kaplan meier", "censoring", "censored", "risk set", "median survival", "failure time"},
        ("survival analysis", "survivor function", "survival function", "hazard function", "Kaplan-Meier", "censoring", "censored", "risk set", "median survival", "failure time"),
    ),
    (
        {"right censoring", "left censoring", "interval censoring", "survival function", "event indicator", "time-to-event"},
        ("right censoring", "left censoring", "interval censoring", "survival function", "event indicator", "time-to-event", "survival time", "censored"),
    ),
    (
        {"population composition", "population structure", "population pyramids", "sex ratio", "sex imbalance", "age-dependency", "child-dependency", "old-age dependency"},
        ("population composition", "population structure", "population pyramids", "sex ratio", "age-dependency", "child-dependency", "old-age dependency", "sex imbalance"),
    ),
    (
        {"fecundity", "infecundity", "fecundability", "fertility", "natality", "natural fertility", "reproductivity", "gravidity", "parity", "birth interval", "pregnancy interval"},
        ("fecundity", "infecundity", "fecundability", "fertility", "natural fertility", "reproductivity", "gravidity", "parity", "birth interval", "pregnancy interval"),
    ),
    (
        {"crude birth rate", "cbr", "general fertility rate", "gfr", "age-specific fertility rate", "asfr", "total fertility rate", "tfr", "gross reproduction rate", "grr", "net reproduction rate", "nrr", "children ever born", "ceb", "replacement fertility", "population momentum"},
        ("crude birth rate", "general fertility rate", "age-specific fertility rate", "total fertility rate", "gross reproduction rate", "net reproduction rate", "children ever born", "replacement fertility", "population momentum", "cbr", "gfr", "asfr", "tfr", "grr", "nrr", "ceb"),
    ),
    (
        {"seasonal variation", "seasonal index", "simple averages method", "ratio to trend method", "percentage moving average method", "link relatives method"},
        ("seasonal variation", "seasonal index", "simple averages method", "ratio to trend method", "percentage moving average method", "link relatives method"),
    ),
    (
        {"non-compliance", "drop-ins", "recruitment", "retention", "phase i", "phase ii", "phase iii", "phase iv", "comparative effectiveness research", "cer", "propensity score matching", "instrumental variables"},
        ("non-compliance", "drop-ins", "recruitment", "retention", "Phase I", "Phase II", "Phase III", "Phase IV", "comparative effectiveness research", "propensity score matching", "instrumental variables"),
    ),
    (
        {"selection bias", "measurement bias", "reporting bias", "publication bias", "recall bias", "confounding bias", "causal inference"},
        ("selection bias", "measurement bias", "reporting bias", "publication bias", "recall bias", "confounding bias", "causal inference"),
    ),
    (
        {"sex ratio", "age", "median age", "mean age", "dependency ratio", "child-dependency ratio", "old-age dependency ratio"},
        ("sex ratio", "age", "median age", "mean age", "dependency ratio", "child-dependency ratio", "old-age dependency ratio"),
    ),
    (
        {"summary", "plot", "visualization", "forecasting", "package", "library", "ts_data"},
        ("summary", "plot", "visualization", "forecasting", "package", "library", "ts_data"),
    ),
]


_TITLE_RULES: list[tuple[set[str], tuple[str, ...]]] = [
    (
        {"time series"},
        ("time series", "AirPassengers", "autocorrelation", "partial autocorrelation", "ACF", "PACF", "forecast", "seasonality", "decomposition", "stationary"),
    ),
    (
        {"population composition", "population structure"},
        ("population composition", "population structure", "sex ratio", "population pyramids", "dependency ratio", "child-dependency ratio", "old-age dependency ratio"),
    ),
    (
        {"fertility", "measures and determinants"},
        ("fertility", "fecundity", "fecundability", "general fertility rate", "age-specific fertility rate", "total fertility rate", "gross reproduction rate", "net reproduction rate", "replacement fertility"),
    ),
    (
        {"survival analysis"},
        ("survival analysis", "censoring", "survival function", "hazard function", "Kaplan-Meier", "event indicator", "time-to-event", "median survival"),
    ),
    (
        {"infectious disease", "infectious diseases", "mathematical modeling", "sir", "seir", "compartmental", "epidemic", "pandemic", "outbreak"},
        ("infectious disease", "infectious diseases", "mathematical modeling", "SIR", "SEIR", "compartmental", "epidemic", "pandemic", "outbreak", "transmission", "recovery"),
    ),
    (
        {"force of infection", "density-dependent", "frequency-dependent", "mass-action", "proportionate mixing", "recovery", "infectious period"},
        ("force of infection", "density-dependent transmission", "frequency-dependent transmission", "mass-action transmission", "proportionate mixing", "recovery", "infectious period", "contact rate", "transmission rate"),
    ),
    (
        {"stationary", "stationarity", "autocovariance", "autocorrelation", "correlogram", "time series", "acf", "random walk", "seasonal"},
        ("stationary process", "stationarity", "autocovariance", "autocorrelation", "correlogram", "time series", "ACF", "random walk", "seasonal", "trend"),
    ),
    (
        {"autoregressive", "moving average", "arma", "arima", "airpassengers", "differencing", "time series models"},
        ("autoregressive", "moving average", "ARMA", "ARIMA", "AirPassengers", "differencing", "time series", "ACF", "PACF"),
    ),
    (
        {"moving average", "ma(1)", "ma(2)", "arma", "arima", "invertibility", "white noise", "residual"},
        ("moving average", "MA(1)", "MA(2)", "ARMA", "ARIMA", "invertibility", "white noise", "residual", "ACF"),
    ),
    (
        {"arima", "differences", "differencing", "stationary", "stationarity", "time series model selection"},
        ("ARIMA", "differencing", "stationary", "nonstationary", "stationarity", "trend", "auto.arima", "diff"),
    ),
    (
        {"design concepts iii", "clinical trials", "methods"},
        ("non-compliance", "drop-ins", "recruitment", "retention", "Phase I", "Phase II", "Phase III", "Phase IV", "comparative effectiveness research", "propensity score matching", "instrumental variables"),
    ),
]


def auto_highlight_key_terms(front: str, back: str, tags: list[str] | None = None, *, title: str | None = None) -> str:
    if "class=\"key\"" in back:
        return back

    haystack = " ".join([front, back, " ".join(tags or [])]).lower()
    title_haystack = (title or "").lower()

    for keywords, candidates in _TITLE_RULES:
        if title_haystack and any(keyword_matches(title_haystack, keyword) for keyword in keywords):
            for candidate in candidates:
                updated = _wrap_first_occurrence(back, candidate)
                if updated != back:
                    return updated

    for keywords, candidates in _HIGH_YIELD_RULES:
        if any(keyword_matches(haystack, keyword) for keyword in keywords):
            for candidate in candidates:
                updated = _wrap_first_occurrence(back, candidate)
                if updated != back:
                    return updated
    return back


def attach_nb_footnote(card: dict[str, Any]) -> dict[str, Any]:
    back = str(card.get("back", ""))
    updated = dict(card)
    if "class=\"nb\"" in back or "<strong>NB:</strong>" in back or "NB:" in back:
        return updated

    front = str(card.get("front", ""))
    tags = [str(tag) for tag in card.get("tags", [])]
    note = infer_nb_text(front, back, tags)
    if not note:
        return updated

    updated["back"] = back + nb(note)
    return updated


def tier2_variant_for(*parts: object) -> str:
    key = "|".join("" if part is None else str(part) for part in parts)
    digest = hashlib.sha1(key.encode("utf-8")).digest()
    return TIER2_VARIANTS[digest[0] % len(TIER2_VARIANTS)]


def tier2(text: str, tone: str | None = None, *, seed: object | None = None) -> str:
    selected = tone or tier2_variant_for(seed if seed is not None else text)
    selected = selected.removeprefix("tier2-")
    return f'<span class="tier2 tier2-{selected}">{text}</span>'
