from __future__ import annotations

import unittest

from lpp import cipolla_log5_repacked_seed, r_inverse_seed
from lpp.r_inverse_sensitivity import (
    ANCHOR_DATASET,
    build_anchor_summary,
    build_sensitivity_result_rows,
    cipolla_log5_repacked_seed_with_scales,
    launch_components,
    load_sensitivity_datasets,
    r_inverse_seed_with_scales,
    summarize_family_results,
)


class RInverseSensitivityTests(unittest.TestCase):
    def test_unperturbed_helpers_match_shipped_functions(self) -> None:
        for n_value in (100, 1000, 10**12):
            with self.subTest(n=n_value):
                self.assertEqual(
                    cipolla_log5_repacked_seed_with_scales(n_value),
                    cipolla_log5_repacked_seed(n_value),
                )
                self.assertEqual(
                    r_inverse_seed_with_scales(n_value),
                    r_inverse_seed(n_value),
                )

    def test_term_perturbations_only_change_requested_launch_component(self) -> None:
        n_value = 10**12
        baseline = launch_components(n_value)
        c_shift = launch_components(n_value, c_scale=0.9, kappa_scale=1.0)
        kappa_shift = launch_components(n_value, c_scale=1.0, kappa_scale=1.1)

        self.assertNotEqual(baseline["d_term"], c_shift["d_term"])
        self.assertEqual(baseline["kappa_term"], c_shift["kappa_term"])
        self.assertEqual(baseline["d_term"], kappa_shift["d_term"])
        self.assertNotEqual(baseline["kappa_term"], kappa_shift["kappa_term"])

    def test_loader_uses_declared_exact_and_local_surfaces(self) -> None:
        rows = load_sensitivity_datasets()
        datasets = {str(row["dataset"]) for row in rows}
        self.assertEqual(
            datasets,
            {
                ANCHOR_DATASET,
                "reproducible_exact_stage_a",
                "reproducible_exact_stage_b",
                "local_continuation_stage_c",
            },
        )
        anchor_rows = [row for row in rows if str(row["dataset"]) == ANCHOR_DATASET]
        self.assertEqual(len(anchor_rows), 17)
        self.assertEqual(min(int(row["n"]) for row in anchor_rows), 100)
        self.assertEqual(max(int(row["n"]) for row in anchor_rows), 10**18)

    def test_result_rows_and_anchor_summary_keep_declared_columns(self) -> None:
        dataset_rows = [
            {
                "dataset": ANCHOR_DATASET,
                "source_label": "published exact",
                "exact_labels": True,
                "row_id": "anchor__n1000",
                "family": "published_exact_grid",
                "decade_exponent": 3,
                "n": 1000,
                "p_n": 7919,
            },
            {
                "dataset": "local_continuation_stage_c",
                "source_label": "local continuation",
                "exact_labels": False,
                "row_id": "dense_local_window__k17__middle__offset+0",
                "family": "dense_local_window",
                "decade_exponent": 17,
                "n": 50000000000000000,
                "p_n": 2056949323753784567,
            },
        ]
        result_rows = build_sensitivity_result_rows(dataset_rows)
        self.assertEqual(len(result_rows), 10)
        self.assertEqual(
            set(result_rows[0].keys()),
            {
                "dataset",
                "source_label",
                "exact_labels",
                "row_id",
                "family",
                "decade_exponent",
                "n",
                "p_n",
                "scenario",
                "scenario_label",
                "c_scale",
                "kappa_scale",
                "launch_seed",
                "seed",
                "seed_signed_error",
                "seed_absolute_error",
                "seed_rel_ppm",
                "li_inverse_seed",
                "li_inverse_signed_error",
                "li_inverse_absolute_error",
                "li_inverse_rel_ppm",
                "advantage_vs_li_ppm",
            },
        )

        family_summary = summarize_family_results(result_rows)
        anchor_summary = build_anchor_summary(result_rows)
        self.assertTrue(all("source_label" in row for row in family_summary))
        self.assertTrue(all("exact_labels" in row for row in family_summary))
        self.assertEqual(len(anchor_summary), 5)
        self.assertTrue(all(bool(row["exact_labels"]) for row in anchor_summary))


if __name__ == "__main__":
    unittest.main()
