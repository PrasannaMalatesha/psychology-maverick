# Corpus Sources & Licensing

The Knowledge Assistant answers **only** from the material below. Everything here is openly
licensed and legally ingestible. Reproduce the whole corpus with `data/fetch_corpus.sh`.

## Textbook backbone

- **OpenStax — *Psychology 2e*** (`corpus/textbooks/Psychology2e_OpenStax.pdf`)
  - Publisher: OpenStax, Rice University (2020)
  - License: **CC BY-NC-SA 4.0** (attribution, non-commercial, share-alike)
  - Source: https://openstax.org/details/books/psychology-2e
  - Role: broad, stable ground truth across all major psychology subfields.

## Research articles

- **PLOS ONE — Psychology research articles** (`corpus/articles/plos_pone_*.pdf`)
  - Publisher: Public Library of Science (PLOS)
  - License: **CC BY 4.0** (attribution)
  - Fetched via the public PLOS Search API (`api.plos.org`); DOIs recorded in
    `corpus/articles/plos_results.json`.
  - Role: current-research register (different voice from the textbook) for
    "what does research say about X" queries.

- **PLOS ONE — Mental health & psychiatry research articles** (`corpus/articles/plos_psychiatry_*.pdf`)
  - Publisher: Public Library of Science (PLOS)
  - License: **CC BY 4.0** (attribution)
  - Fetched via the PLOS Search API (subject: "Mental health and psychiatry");
    DOIs in `corpus/articles/plos_psychiatry.json`.
  - Role: extends the research register into **psychiatry** topics, supporting the
    app's learning purpose across psychology *and* psychiatry.

## Consumer mental-health information

- **NIMH (National Institute of Mental Health) brochures** (`corpus/mental_health/nimh_*.pdf`)
  - Publisher: NIMH, U.S. National Institutes of Health
  - License: **Public domain** (U.S. government work — free to use; citation of NIMH appreciated)
  - Current set: depression, bipolar disorder, PTSD, and "5 action steps to help
    someone having thoughts of suicide."
  - Role: **authoritative, plain-language health information** — this is the register the
    assistant should prefer when a user is seeking mental-health clarity (as opposed to
    the academic textbook/research registers). Chosen because it is authoritative, safe,
    and public domain.

> **Safety note:** this material is *informational*, not clinical advice. The assistant
> is an educational tool, not a diagnostic or therapeutic service, and must surface crisis
> resources rather than attempt to handle a crisis. See the safety posture in the project spec.

## Deliberately excluded

Paywalled / ToS-restricted sources are **not** used: APA PsycNet, ScienceDirect,
Sci-Hub, or any content behind a paywall. Ingesting those would be a legal and
reputational problem.

## Attribution note

Because the textbook is NC (non-commercial), this project is a **non-commercial
portfolio/education demonstration**. Any answer surfaced by the assistant should
carry a citation back to its source document (see the `Citation` concept in
[CONTEXT.md](../../CONTEXT.md)).
