from src.versioning import (
    compact_version,
    default_contract_paths,
    default_kernel_slug,
    notebook_stem,
)


def test_notebook_stem_and_compact_version_for_scratch_lineage():
    assert notebook_stem("vR.2") == "vR.2_HNDSR"
    assert compact_version("vR.2") == "vr2"


def test_kernel_slug_handles_pretrained_lineage():
    assert default_kernel_slug("vR.P.1") == "vr-p-1-hndsr-sr3-baseline"


def test_default_contract_paths_match_repo_layout():
    paths = default_contract_paths("vR.3")
    assert paths["notebook"].as_posix().endswith("notebooks/versions/vR.3_HNDSR.ipynb")
    assert paths["doc"].as_posix().endswith("docs/notebooks/vR.3_HNDSR.md")
    assert paths["review"].as_posix().endswith("reports/reviews/vR.3_HNDSR.review.md")
    assert paths["full_config"].as_posix().endswith("configs/phase1_sr3_vr3_kaggle.yaml")
