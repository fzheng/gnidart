# GNIDART

The trading algorithm is contained in the Algorithm class.

## Run
Enter `python3 backtester.py` for a default run. Output is logged to `run.log`.

## Virtualenv Usage
To install `virtualenv` run
```shell script
pip3 install virtualenv
```

If you have a project in a directory called `gnidart` you can set up `virtualenv` for that project by running
```shell script
cd library/
python3 -m virtualenv venv
```

These commands create a `venv/` directory in your project where all dependencies are installed. You need to **activate** it first though (in every terminal instance where you are working on your project):
```shell script
source venv/bin/activate
```

You should see a `(venv)` appear at the beginning of your terminal prompt indicating that you are working inside the `virtualenv`. Now when you install dependencies:
```shell script
pip3 install -r requirements.txt
```

It will get installed in the `venv/` folder, and not conflict with other projects.

To leave the virtual environment run:
```shell script
deactivate
```

**Important**: Remember to add `venv` to your project's `.gitignore` file so you don't include all of that in your source code.

It is preferable to install big packages (like `Numpy`), or packages you always use (like IPython) globally. All the rest can be installed in a `virtualenv`.