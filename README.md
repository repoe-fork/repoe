# RePoE

Repository of Path of Exile resources for tool developers.

Forked from [brather1ng/RePoE](https://github.com/brather1ng/RePoE); not using GitHub fork
functionality due to [a bug](https://github.com/git-lfs/git-lfs/issues/1906).

Contains data about stats, mods, base items, gems and more. See the `data`
folder for those files and the `docs` folder for their documentation.

For the actual GGPK parsing, [PyPoE](https://github.com/lvlvllvlvllvlvl/PyPoE) is used.
This is a fork of the version used by Project PoE Wiki, reverting to the data
[schema](https://github.com/poe-tool-dev/dat-schema) provided by poe-tool-dev.
The code in this repo just converts PyPoE's Python objects to JSON.

Developed to supply [PoESkillTree](https://github.com/PoESkillTree/PoESkillTree) with the
game data information it requires. If you need other files converted, feel free to
open an Issue or Pull Request for that. The source data files can be inspected with [poe-dat-viewer](https://snosme.github.io/poe-dat-viewer/).

## Files

The [RePoE/data](RePoE/data) folder contains the generated data in Json format. Each file has a
formatted and a compact version. The formatted versions complement their descriptions
in the [RePoE/docs](RePoE/docs) folder.

Web apps using provided files should link to files in the
[gh-pages](https://lvlvllvlvllvlvl.github.io/RePoE/), for better performance and caching behavior
than linking to raw files in the repository.

Note that the file formats are not final, they may change at any time, e.g. when the format
of files in the GGPK changes. 

The following data is currently available:

- `stat_translations.json`: Maps stat ids together with their values to human-readable
  text. This is the text that appears on items in-game.
- `stats.json`: Describes stat ids. Defines whether they are local and whether they
  are aliased depending on main-hand or off-hand.
- `mods.json`: Describes mod ids. Defines which items they can appear on and what
  stats with what values they have.
- `crafting_bench_options.json`: Describes master crafting options. Defines which
  masters can craft them at which level on which items.
- `npc_master.json`: Describes the master's signature mods and on which items they
  can appear.
- `gems.json`: Describes skill gems and skill gem effects only provided by mods.
- `gem_tags.json`: Simple object that contains all gem tags with their internal id as
  keys and their translation as value.
- `base_items.json`: Describes base item types. Contains information applicable to
  all item types, e.g. inventory size, item class and tags, as well as attribute
  requirements and properties.
- `tags.json`: Lists all possible item tags. These are the tags used in `base_items.json` and 
  `mods.json`.
- `item_classes.json`: Defines the item class ids and the tags added to items when they are
  Shaper/Elder items.
- `essences.json`: Describes essences. Defines the mods they spawn on items of the different
  item classes and general information like level and tier.
- `default_monster_stats.json`: Describes the stat base values of monsters at specific levels.
- `characters.json`: Describes the stat base values of the different player character classes.
- `flavour.json`: Table containing the flavour text used throughout the game.
- `fossils.json`: Describes fossils. Defines the mods they spawn, the tags they affect, and 
  auxillary effects of the fossils.
- `mod_types.json`: Describes the types of mods with sell price information and the tags
  relevant for fossil crafting.
- `cluster_jewels.json`: Describes how cluster jewels can be generated and how they influence the passive tree. 
- `cluster_jewel_notables.json`: Lists the notable and keystone passive skills that can appear on cluster jewels.
- `cost_types.json`: Defines the resource cost types used in `gems.json`.
- `active_skill_types.json`: List the active skill types used in `gems.json`.
- `uniques.json`: Lists the names and art files of unique items - this is the only information
included in the data files.
  

## Credits

- [Grinding Gear Games](http://www.grindinggear.com/) for 
  [Path of Exile](https://www.pathofexile.com/). The contents of all `data` files
  obviously belong to them.
- [OmegaK2](https://github.com/OmegaK2/) for [PyPoE](https://github.com/OmegaK2/PyPoE).
- [Project PoE Wiki](poewiki.net) for updating PyPoE to handle the latest data format.
- [Path of Exile Tool Devs](https://github.com/poe-tool-dev/) for maintaining a standardised
data schema.
