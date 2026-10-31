# Budapest building reconstruction

A Claude Code skill that goes from a Budapest address and postal code to a
sourced dossier, reconstructed blueprints, an interactive 3D model and statue
dossiers.

- Plan and status: [PLAN.md](PLAN.md)
- Skill: [.claude/skills/building-reconstruction/SKILL.md](.claude/skills/building-reconstruction/SKILL.md)

## Use
In Claude Code, opened in this repository:

> Reconstruct the building at Andrássy út 22, 1061 Budapest, as built and as in 1950.

The scripts also run on their own (Python 3.9+; numpy and Pillow for the
photo and statue tools):

```bash
S=.claude/skills/building-reconstruction/scripts
P=$(python3 $S/new_project.py "Andrássy út 22" 1061)
python3 $S/fetch_open_data.py "$P"          # + 01_sources/search_plan.md
python3 $S/seed_model.py "$P" --floors 4 --storey 4.4
# research, rectify photos, refine $P/04_model/building.json
python3 $S/rectify_photo.py photo.jpg out.png --points "..." --width 24 --height 12.6
python3 $S/make_blueprints.py "$P" --year 1900
python3 $S/build_viewer.py "$P"            # open $P/06_3d/viewer.html
python3 $S/compare_original.py "$P" scan.jpg "$P/05_blueprints/plan_F0_1900.svg"
python3 $S/sculpture_sheet.py "$P" OR1
python3 $S/statue_relief_glb.py cutout.png "$P/07_sculpture/OR1/mesh.glb" --height 2.2
```

The viewer loads Three.js from jsDelivr (needs internet). Statue GLB files
load only over http: `cd "$P" && python3 -m http.server`, then open
`http://localhost:8000/06_3d/viewer.html`.

Try the fictional example: copy
`.claude/skills/building-reconstruction/assets/example_building.json` to
`<project>/04_model/building.json` and run the generators.
