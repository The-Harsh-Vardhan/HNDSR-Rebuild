# Versioned Kaggle Notebooks

- `vR.x_HNDSR.ipynb` is reserved for scratch-trained notebook versions.
- `vR.P.x_HNDSR.ipynb` is reserved for externally pretrained notebook versions.
- Do not overwrite a reviewed notebook version.
- Pair every notebook with:
  - `docs/notebooks/<stem>.md`
  - `reports/reviews/<stem>.review.md`
- Run `scripts/validate_notebook_version.py` before handing a notebook to Kaggle.
- Use `scripts/scaffold_version.py` to create the next immutable version after review.
