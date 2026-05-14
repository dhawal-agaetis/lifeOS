# Skill: Git Release

Use this when the user wants to mark a stable checkpoint and release to main.

## Steps
1. Ensure all changes on dev are committed and pushed
2. Run any tests, confirm nothing is broken
3. Merge dev into main: git checkout main && git merge dev
4. Push main: git push origin main
5. Create annotated tag: git tag -a v<version> -m "<description>"
6. Push tag: git push origin v<version>
7. Switch back to dev: git checkout dev
8. Update CLAUDE.md Current Versions section with new tag
9. Report back with what was released and the tag created
