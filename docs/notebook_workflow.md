# HNDSR Notebook Workflow

## Version Rules

- Scratch lineage notebooks use `vR.x_HNDSR.ipynb`.
- External pretrained lineage notebooks use `vR.P.x_HNDSR.ipynb`.
- The title markdown cell keeps the human-readable form, for example `# vR.1 HNDSR`.
- A new notebook version is created only when the model, optimizer, loss, dataset/protocol, checkpoint source, or evaluation contract changes.
- Runtime-only Kaggle fixes stay in the same version until the review is closed.

## Immutable Lifecycle

1. Scaffold the next notebook version and its paired markdown doc.
2. Run the local readiness validator before Kaggle handoff.
3. Commit and push the scaffold checkpoint to `origin`.
4. Run the notebook on Kaggle and return the executed notebook.
5. Sync the returned notebook into the same version and commit that state before further fixes.
6. Write the paired review and roast doc, then commit and push again.
7. Fork the next version only after the current version is frozen.

## Paired Files

- Notebook: `notebooks/versions/<stem>.ipynb`
- External doc: `docs/notebooks/<stem>.md`
- Review doc: `reports/reviews/<stem>.review.md`

## Git Discipline

- Preserve broken Kaggle states with a dedicated commit before corrective edits.
- Use commit prefixes tied to the notebook stem:
  - `research(vR.1): scaffold kaggle notebook and docs`
  - `research(vR.1): sync kaggle runtime fixes`
  - `review(vR.1): audit returned run`
- Push every major lifecycle checkpoint to `origin` so failures remain recoverable.
