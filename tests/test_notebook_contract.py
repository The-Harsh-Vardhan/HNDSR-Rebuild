from src.notebook_contract import validate_versioned_notebook


def test_vr1_notebook_contract_passes():
    failures = validate_versioned_notebook(
        notebook_path="notebooks/versions/vR.1_HNDSR.ipynb",
        doc_path="docs/notebooks/vR.1_HNDSR.md",
        review_path="reports/reviews/vR.1_HNDSR.review.md",
        full_config_path="configs/phase1_sr3_vr1_kaggle.yaml",
        smoke_config_path="configs/phase1_sr3_vr1_smoke.yaml",
        control_config_path="configs/phase0_bicubic_vr1_kaggle_control.yaml",
        version="vR.1",
    )
    assert failures == []


def test_vr2_notebook_contract_passes():
    failures = validate_versioned_notebook(
        notebook_path="notebooks/versions/vR.2_HNDSR.ipynb",
        doc_path="docs/notebooks/vR.2_HNDSR.md",
        review_path="reports/reviews/vR.2_HNDSR.review.md",
        full_config_path="configs/phase2_supervised_vr2_kaggle.yaml",
        smoke_config_path="configs/phase2_supervised_vr2_smoke.yaml",
        control_config_path="configs/phase0_bicubic_vr2_kaggle_control.yaml",
        version="vR.2",
    )
    assert failures == []
