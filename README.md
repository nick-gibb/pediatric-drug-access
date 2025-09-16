# Pediatric Oncology Drug Access Metrics

Minimal computations for the manuscript:

> **Impact of regulatory approval on access to novel paediatric cancer drugs: a Canadian perspective**

Reads one CSV and prints all counts and time-to-event metrics cited in the paper (HC/CADTH/pCPA/CCO; medians & IQRs).

## Contents
- `pediatric_drug_access_metrics.py` — analysis script
- `data/pediatric_oncology_access_canada_1997_2023.csv` — aggregated dataset (public sources; no patient data)
- `requirements.txt` — pinned deps
- `LICENSE` — MIT (code)
- `LICENSE-data` — CC BY 4.0 (dataset)

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python pediatric_drug_access_metrics.py data/pediatric_oncology_access_canada_1997_2023.csv
```

## Data provenance

Compiled from FDA, Health Canada, CADTH, pCPA, and CCO public records (see manuscript references).

## License
Code: MIT (see `LICENSE`)
Data: CC BY 4.0 (see `LICENSE-data`)