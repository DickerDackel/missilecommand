# Missile Command in pygame and tinyecs

This is just a testbed to figure out how to work with tinyecs.

This project does too much ECS, but I mostly learned that by doing it this
way.

## Installation

You can try the [latest release](https://github.com/DickerDackel/missilecommand/releases)
but I'm not sure the linux AppImage will run on every linux distro.  The
Windows exe was built in a Windows 10 VM, and pyinstaller is known for triggering
virus alerts.

So if you don't want to download an executable, you're probably only be able
to play it if you're a software developer and have a working python
environment.

Follow these steps then:

_If you have `git-bash`, Windows and Linux installation is pretty much the
same, except for the activate script._

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

### If you don't care to look at the source...

...you can also just install without cloning the repo.  Create a virtual
environment in a directory (probably `missilecommand`) and activate it as
described above.

Then just run

```cmd
pip install git+https://github.com/dickerdackel/missilecommand
```

Same as above, this will add the `missile` command inside your venv.

## Support / Contributing

Issues can be opened on [Github](https://github.com/dickerdackel/missilecommand/issues)

## License

This software is provided under the MIT license.

See LICENSE file for details.
