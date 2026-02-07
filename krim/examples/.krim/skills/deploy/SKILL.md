# Deploy Skill

When deploying, follow these steps:
1. Run the full test suite: `pytest`
2. Check for lint errors: `npm run lint` or `ruff check .`
3. Build the project: `npm run build` or `python -m build`
4. If all checks pass, commit and tag: `git tag v$(python -c "import mypackage; print(mypackage.__version__)")`
