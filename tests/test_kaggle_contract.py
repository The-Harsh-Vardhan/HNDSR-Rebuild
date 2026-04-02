from src.kaggle_contract import (
    CODE_DATASET_ID,
    load_dataset_metadata,
    load_kernel_metadata,
    validate_dataset_metadata,
    validate_kernel_metadata,
)


def test_kernel_metadata_matches_vr1_notebook():
    metadata = load_kernel_metadata()
    failures = validate_kernel_metadata("vR.1", metadata)
    assert failures == []
    assert metadata["code_file"] == "vR.1_HNDSR.ipynb"


def test_dataset_metadata_matches_code_dataset_contract():
    metadata = load_dataset_metadata()
    failures = validate_dataset_metadata(metadata)
    assert failures == []
    assert metadata["id"] == CODE_DATASET_ID
