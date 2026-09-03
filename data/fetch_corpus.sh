#!/usr/bin/env bash
# Reproducibly fetch the Knowledge Assistant corpus (psychology).
# All sources are openly licensed. See data/corpus/SOURCES.md for licenses + attribution.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEXTBOOKS="$HERE/corpus/textbooks"
ARTICLES="$HERE/corpus/articles"
mkdir -p "$TEXTBOOKS" "$ARTICLES"

echo ">> Textbook: OpenStax Psychology 2e (CC BY-NC-SA 4.0)"
curl -fSL --max-time 300 \
  -o "$TEXTBOOKS/Psychology2e_OpenStax.pdf" \
  "https://assets.openstax.org/oscms-prodcms/media/documents/Psychology2e_WEB.pdf"

echo ">> Articles: PLOS ONE, Psychology research articles (CC BY 4.0)"
# Query the public PLOS search API for the most-read psychology research articles.
curl -fsG --max-time 60 "https://api.plos.org/search" \
  --data-urlencode 'q=subject:"Psychology" AND journal:"PLOS ONE" AND article_type:"Research Article"' \
  --data-urlencode 'fl=id' \
  --data-urlencode 'rows=15' \
  --data-urlencode 'sort=counter_total_all desc' \
  --data-urlencode 'wt=json' > "$ARTICLES/plos_results.json"

python3 - "$ARTICLES" <<'PY'
import json, os, subprocess, sys
outdir = sys.argv[1]
docs = json.load(open(os.path.join(outdir, "plos_results.json")))["response"]["docs"]
for d in docs:
    doi = d["id"]
    slug = "plos_pone_" + doi.split("journal.pone.")[-1]
    url = f"https://journals.plos.org/plosone/article/file?id={doi}&type=printable"
    dest = os.path.join(outdir, f"{slug}.pdf")
    subprocess.run(["curl", "-fsSL", "--max-time", "60", "-o", dest, url], check=True)
    with open(dest, "rb") as f:
        assert f.read(4) == b"%PDF", f"not a PDF: {doi}"
    print("  ok", slug)
print(f"Downloaded {len(docs)} articles.")
PY

echo ">> Articles: PLOS ONE, Mental health & psychiatry (CC BY 4.0)"
curl -fsG --max-time 60 "https://api.plos.org/search" \
  --data-urlencode 'q=subject:"Mental health and psychiatry" AND journal:"PLOS ONE" AND article_type:"Research Article"' \
  --data-urlencode 'fl=id' \
  --data-urlencode 'rows=10' \
  --data-urlencode 'sort=counter_total_all desc' \
  --data-urlencode 'wt=json' > "$ARTICLES/plos_psychiatry.json"
python3 - "$ARTICLES" <<'PY'
import json, os, subprocess, sys
outdir = sys.argv[1]
docs = json.load(open(os.path.join(outdir, "plos_psychiatry.json")))["response"]["docs"]
for d in docs:
    doi = d["id"]
    slug = "plos_psychiatry_" + doi.split("journal.pone.")[-1]
    dest = os.path.join(outdir, f"{slug}.pdf")
    subprocess.run(["curl", "-fsSL", "--max-time", "60", "-o", dest,
                    f"https://journals.plos.org/plosone/article/file?id={doi}&type=printable"], check=True)
print(f"Downloaded {len(docs)} psychiatry articles.")
PY

echo ">> Mental-health info: NIMH brochures (public domain)"
MH="$HERE/corpus/mental_health"
mkdir -p "$MH"
declare -a MH_NAMES=(nimh_depression.pdf nimh_bipolar_disorder.pdf nimh_ptsd.pdf nimh_help_someone_suicidal.pdf)
declare -a MH_URLS=(
  "https://www.nimh.nih.gov/sites/default/files/health/publications/depression/depression.pdf"
  "https://www.nimh.nih.gov/sites/default/files/health/publications/bipolar-disorder/bipolar-disorder.pdf"
  "https://www.nimh.nih.gov/sites/default/files/documents/health/publications/post-traumatic-stress-disorder-ptsd/post-traumatic-stress-disorder_1.pdf"
  "https://www.nimh.nih.gov/sites/default/files/documents/health/publications/5-action-steps-help-someone-having-thoughts-suicide.pdf"
)
for i in "${!MH_NAMES[@]}"; do
  curl -fSL --max-time 60 -o "$MH/${MH_NAMES[$i]}" "${MH_URLS[$i]}"
  head -c4 "$MH/${MH_NAMES[$i]}" | grep -q "%PDF" && echo "  ok ${MH_NAMES[$i]}"
done

echo ">> Done. Corpus is in $HERE/corpus/"
