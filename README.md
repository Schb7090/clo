# Historic building reconstruction

A Claude Code skill that goes from an address and postal code to a sourced
dossier, reconstructed blueprints and an interactive 3D model of a building.

- Plan and status: [PLAN.md](PLAN.md)
- Skill: [.claude/skills/building-reconstruction/SKILL.md](.claude/skills/building-reconstruction/SKILL.md)

## Use
In Claude Code, opened in this repository:

> Reconstruct the building at Andrássy út 22, 1061 Budapest.

The scripts also run on their own (Python 3.9+, standard library only):

```bash
S=.claude/skills/building-reconstruction/scripts
P=$(python3 $S/new_project.py "Andrássy út 22, Budapest" 1061 --country HU)
python3 $S/fetch_open_data.py "$P"
# ... research, then fill $P/04_model/building.json ...
python3 $S/make_blueprints.py "$P"
python3 $S/build_viewer.py "$P"     # open $P/06_3d/viewer.html
```

The viewer loads Three.js from jsDelivr, so it needs an internet connection.
