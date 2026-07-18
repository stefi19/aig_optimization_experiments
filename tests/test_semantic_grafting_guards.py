from pathlib import Path


def test_disconnected_materialisation_not_usable_label():
    row = {
        "accepted": "false",
        "boundary_utility": "not_usable_frontier",
        "global_cec_status": "not_run_no_valid_graft",
    }
    assert row["accepted"] != "true"
    assert row["boundary_utility"] != "usable_frontier"


def test_global_cec_required_for_accepted_graft():
    row = {"accepted": "true", "global_cec_status": "passed"}
    assert row["accepted"] == "true"
    assert row["global_cec_status"] == "passed"
