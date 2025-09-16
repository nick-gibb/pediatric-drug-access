#!/usr/bin/env python3
# pediatric_drug_access_metrics.py
#
# Script to compute the values reported in:
# “Impact of regulatory approval on access to novel paediatric cancer drugs: a Canadian perspective”
#
# Input: CSV as provided
#
# Output: printed metrics matching the manuscript.

import sys

import numpy as np
import pandas as pd


def parse_dates(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce", dayfirst=False)
    return df


def med_iqr(s):
    s = pd.to_numeric(s, errors="coerce").dropna()
    if s.empty:
        return np.nan, np.nan, np.nan, 0
    med = float(s.median())
    q1 = float(s.quantile(0.25))
    q3 = float(s.quantile(0.75))
    return med, q1, q3, int(s.shape[0])


def fmt_days(s):
    med, q1, q3, n = med_iqr(s)
    return f"median={med:.1f} days (IQR {q1:.1f}-{q3:.1f}), n={n}"


def main():
    # Path
    path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "data/pediatric_oncology_access_canada_1997_2023.csv"
    )
    print(f"Loading data from {path}")

    # Load (semicolon-delimited)
    df = pd.read_csv(path, sep=None, engine="python")

    # Parse dates
    date_cols = [
        "adult_fda_approval_indication_specific",
        "adult_hc_approval",
        "pediatric_fda_approval",
        "pediatric_hc_approval",
        "pediatric_hc_submission",
        "pediatric_cadth_submission",
        "pediatric_cadth_recommendation",
        "pediatric_pcpa_consideration",
        "pediatric_pcpa_negotiation_completed",
    ]
    parse_dates(df, date_cols)

    # Basic totals
    N = len(df)  # FDA pediatric indications (after manual de-dup in dataset)
    print("=== Totals ===")
    print(f"FDA pediatric indications (1997–2023): {N}")

    # Adult FDA approval for same indication
    n_fda_adult = df["adult_fda_approval_indication_specific"].notna().sum()
    print(
        f"Also FDA adult approvals (same indication): {n_fda_adult} ({100 * n_fda_adult / N:.1f}%)"
    )

    # Unique drugs and unique drugs with HC pediatric approval
    n_unique_drugs = df["drug"].nunique()
    n_unique_drugs_with_hc_ped = (
        df.groupby("drug")["pediatric_hc_approval"]
        .apply(lambda s: s.notna().any())
        .sum()
    )
    print(f"Unique drug entities: {n_unique_drugs}")
    print(
        f"Unique drugs with HC pediatric approval: {n_unique_drugs_with_hc_ped}/{n_unique_drugs}"
    )

    # HC pediatric approvals
    hc_ped = df["pediatric_hc_approval"].notna()
    n_hc_ped = int(hc_ped.sum())
    print("\n=== Health Canada (HC) pediatric approvals ===")
    print(f"HC pediatric approvals: {n_hc_ped} ({100 * n_hc_ped / N:.1f}%)")

    # Split ped-only vs ped+adult use (by adult HC approval date presence)
    ped_only = df.loc[hc_ped, "adult_hc_approval"].isna().sum()
    ped_and_adult = df.loc[hc_ped, "adult_hc_approval"].notna().sum()
    print(f"… pediatric-only approvals: {ped_only}")
    print(f"… pediatric+adult approvals: {ped_and_adult}")

    # NOC vs NOC/c among HC pediatric approvals
    noc_counts = df.loc[hc_ped, "noc_status"].value_counts()
    noc = int(noc_counts.get("NOC", 0))
    nocc = int(noc_counts.get("NOC/c", 0))
    print(f"NOC among HC pediatric approvals: {noc} ({noc / (noc + nocc) * 100:.0f}%)")
    print(
        f"NOC/c among HC pediatric approvals: {nocc} ({nocc / (noc + nocc) * 100:.0f}%)"
    )

    # Reasons for no HC pediatric approval
    print("\n=== No HC pediatric approval: reasons ===")
    no_hc_ped = df[df["pediatric_hc_status"] != "approved"]
    print(f"Count: {len(no_hc_ped)}")
    print(no_hc_ped["hc_pediatric_reason"].value_counts().to_string())

    # Manufacturer did not submit or cancelled
    didnt_submit_or_cancelled = int(
        (no_hc_ped["hc_pediatric_reason"].isin(["not found", "cancelled"])).sum()
    )
    print(
        f"… of which no submission/cancelled: {didnt_submit_or_cancelled} ({100 * didnt_submit_or_cancelled / N:.1f}%)"
    )

    # Timings: FDA -> HC (adult and pediatric)
    adult_delta = (
        df["adult_hc_approval"] - df["adult_fda_approval_indication_specific"]
    ).dt.days
    ped_delta = (df["pediatric_hc_approval"] - df["pediatric_fda_approval"]).dt.days
    print("\n=== Timelines: FDA → HC ===")
    print(f"Adult indications:   {fmt_days(adult_delta)}")
    print(f"Pediatric indications:{fmt_days(ped_delta)}")

    # Cases where HC preceded FDA (adult & pediatric)
    adult_hc_before_fda = df[adult_delta < 0][["drug", "fda_indication_pediatric"]]
    ped_hc_before_fda = df[ped_delta < 0][["drug", "fda_indication_pediatric"]]
    print("\nHC before FDA (adult):")
    for _, r in adult_hc_before_fda.iterrows():
        print(f"- {r['drug']}")
    print("HC before FDA (pediatric):")
    for _, r in ped_hc_before_fda.iterrows():
        print(f"- {r['drug']}")

    # HC submission → HC approval
    print("\n=== HC submission → HC approval (pediatric) ===")
    hc_sub_to_appr = (
        df["pediatric_hc_approval"] - df["pediatric_hc_submission"]
    ).dt.days
    print(fmt_days(hc_sub_to_appr))

    # CADTH status summary over all FDA pediatric indications
    print("\n=== CADTH (pediatric) ===")
    cadth_counts = df["pediatric_cadth_status"].value_counts()
    print(cadth_counts.to_string())

    # Submitted to CADTH but NOT HC-approved pediatric
    submitted_not_hc_ped = df[
        (df["pediatric_cadth_status"] != "not reviewed")
        & (df["pediatric_hc_status"] != "approved")
    ]
    print(
        f"Submitted to CADTH without HC pediatric approval: {len(submitted_not_hc_ped)}"
    )
    pos_without_hc = df[
        (df["pediatric_hc_status"] != "approved")
        & (df["pediatric_cadth_status"].isin(["positive", "restricted positive"]))
    ]
    if not pos_without_hc.empty:
        print("Positive/restricted CADTH without HC pediatric approval:")
        for _, r in pos_without_hc.iterrows():
            print(f"- {r['drug']}: {r['pediatric_cadth_status']}")

    # Among HC pediatric approvals: CADTH pre/post/unknown, recommendation breakdown
    hc_approved_df = df[df["pediatric_hc_status"] == "approved"].copy()
    reviewed = hc_approved_df[
        hc_approved_df["pediatric_cadth_status"] != "not reviewed"
    ].copy()

    def pre_post(row):
        a = row["pediatric_hc_approval"]
        s = row["pediatric_cadth_submission"]
        if pd.isna(a) or pd.isna(s):
            return "unknown"
        return "pre-NOC" if s <= a else "post-NOC"

    if not reviewed.empty:
        reviewed["pre_post"] = reviewed.apply(pre_post, axis=1)
        print("\nHC-approved pediatric → CADTH review timing:")
        print(reviewed["pre_post"].value_counts().to_string())
    print("\nHC-approved pediatric → CADTH recommendation types:")
    print(hc_approved_df["pediatric_cadth_status"].value_counts().to_string())

    # pCPA status among HC pediatric approvals
    print("\n=== pCPA (pediatric, among HC-approved) ===")
    print(hc_approved_df["pediatric_pcpa_status"].value_counts().to_string())

    # No pCPA LOIs for non-HC-pediatric approvals?
    n_loi_non_hc = df[
        (df["pediatric_hc_status"] != "approved")
        & (df["pediatric_pcpa_status"] == "LOI")
    ].shape[0]
    print(f"No. of LOIs for indications without HC pediatric approval: {n_loi_non_hc}")

    # CCO listing
    print("\n=== Cancer Care Ontario (CCO) listing ===")
    cco = df[df["pediatric_cco_listing"].str.lower() == "yes"]
    print(f"Total CCO pediatric indications: {cco.shape[0]}")
    print(
        f"… of which HC pediatric-approved: {(cco['pediatric_hc_status'] == 'approved').sum()}"
    )
    print("CCO programs (counts):")
    print(cco["pediatric_cco_program"].value_counts().to_string())

    # Median timelines for CADTH and pCPA
    print("\n=== Median timelines (days) ===")
    cadth_review = (
        df["pediatric_cadth_recommendation"] - df["pediatric_cadth_submission"]
    ).dt.days
    print(f"CADTH submission → recommendation: {fmt_days(cadth_review)}")
    pcpa_review = (
        df["pediatric_pcpa_negotiation_completed"] - df["pediatric_pcpa_consideration"]
    ).dt.days
    print(f"pCPA consideration → negotiation completed: {fmt_days(pcpa_review)}")

    # HC submission vs CADTH submission difference; and pre-NOC overlap
    hc_vs_cadth_sub = (
        df["pediatric_cadth_submission"] - df["pediatric_hc_submission"]
    ).dt.days
    print(f"HC submission ↔ CADTH submission difference: {fmt_days(hc_vs_cadth_sub)}")
    pre_noc_overlap = df[
        (df["pediatric_cadth_submission"].notna())
        & (df["pediatric_hc_approval"].notna())
        & (df["pediatric_cadth_submission"] <= df["pediatric_hc_approval"])
    ]
    overlap_days = (
        pre_noc_overlap["pediatric_hc_approval"]
        - pre_noc_overlap["pediatric_cadth_submission"]
    ).dt.days
    print(
        f"Pre-NOC overlap (CADTH submission before HC approval): {fmt_days(overlap_days)}"
    )

    # HC approval → CADTH recommendation; HC approval → pCPA completion; CADTH → pCPA
    hc_to_cadth = (
        df["pediatric_cadth_recommendation"] - df["pediatric_hc_approval"]
    ).dt.days
    hc_to_pcpa = (
        df["pediatric_pcpa_negotiation_completed"] - df["pediatric_hc_approval"]
    ).dt.days
    cadth_to_pcpa = (
        df["pediatric_pcpa_negotiation_completed"]
        - df["pediatric_cadth_recommendation"]
    ).dt.days
    print(f"HC approval → CADTH recommendation: {fmt_days(hc_to_cadth)}")
    print(f"HC approval → pCPA completion:     {fmt_days(hc_to_pcpa)}")
    print(f"CADTH recommendation → pCPA completion: {fmt_days(cadth_to_pcpa)}")

    # Total duration: HC submission → pCPA completion
    hcsub_to_pcpacomp = (
        df["pediatric_pcpa_negotiation_completed"] - df["pediatric_hc_submission"]
    ).dt.days
    print(f"HC submission → pCPA completion: {fmt_days(hcsub_to_pcpacomp)}")

    # Yearly counts for Figure 2 (FDA vs HC pediatric approvals)
    print("\n=== Yearly counts (Figure 2 support) ===")
    fda_years = df["pediatric_fda_approval"].dt.year.value_counts().sort_index()
    hc_years = df["pediatric_hc_approval"].dt.year.value_counts().sort_index()
    print("FDA pediatric approvals per year:")
    print(fda_years.to_string())
    print("HC pediatric approvals per year:")
    print(hc_years.to_string())

    # Canada-side timelines for Table 1 examples (blinatumomab, dinutuximab, tisagenlecleucel)
    print("\n=== Canada-side timelines for Table 1 drugs ===")
    for name in ["Blinatumomab", "Dinutuximab", "Tisagenlecleucel"]:
        sub = df[df["drug"].str.contains(name, case=False, regex=False)].copy()
        if sub.empty:
            continue
        sub["HC→CADTH_sub"] = (
            sub["pediatric_cadth_submission"] - sub["pediatric_hc_approval"]
        ).dt.days
        sub["CADTH_sub→Rec"] = (
            sub["pediatric_cadth_recommendation"] - sub["pediatric_cadth_submission"]
        ).dt.days
        sub["HC→Rec"] = (
            sub["pediatric_cadth_recommendation"] - sub["pediatric_hc_approval"]
        ).dt.days
        keep = sub[
            [
                "drug",
                "fda_indication_pediatric",
                "HC→CADTH_sub",
                "CADTH_sub→Rec",
                "HC→Rec",
            ]
        ]
        print(f"\n{name}:")
        for _, r in keep.iterrows():
            drug = r["drug"]
            ind = r["fda_indication_pediatric"]
            print(
                f"- {drug}: HC→CADTH_sub={r['HC→CADTH_sub']}, CADTH_sub→Rec={r['CADTH_sub→Rec']}, HC→Rec={r['HC→Rec']}"
            )


if __name__ == "__main__":
    main()
