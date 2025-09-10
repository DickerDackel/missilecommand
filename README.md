# Missile Command in pygame and tinyecs

This is just a testbed to figure out how to work with tinyecs.

This project does too much ECS, but I mostly learned that by doing it this
way.

## Installation

At one day, this might get an installer, but this is not that day...

If you have `git-bash`, Windows and Linux installation is pretty much the
same, except for the activate script.

### Linux bash instructions

```console
git clone https://github.com/dickerdackel/missilecommand
cd missilecommand
python3 -m venv --prompt missilecommand .venv
source .venv/bin/activate.sh
pip install .
```

After that, just run `missile` in the activated env.

### Windows

This is untested, since I'm not running a Windows PC.

If you have `git-bash` installed (and know what you're doing), open a command
prompt in the directory of your choice and run

```cmd
git clone https://github.com/dickerdackel/missilecommand
cd missilecommand
py -m venv --prompt missilecommand .venv
.venv/Scripts/activate
py -m pip install .
```

After that, just run `missile` in the activated env.

## Support / Contributing

Issues can be opened on [Github](https://github.com/dickerdackel/missilecommand/issues)

## License

This software is provided under the MIT license.

See LICENSE file for details.
