# Project Structure

```
├── devastator
│   ├── app
│   ├── __init__.py
│   ├── main.py
│   ├── navigation
│   ├── robot
│   ├── sound
│   └── vision
├── docs
├── readme.md
├── requirements.txt
├── scripts
│   └── arduino
└── tests
    ├── app
    ├── robot
    ├── sound
    └── vision
```

# Important Notes

1. Hardware devices are located in `devastator > robot`.
2. With the exception of the Intel RealSense D435i, all hardware devices are run on separate processes and communicate via TCP/IP - their `host` and `port` numbers are located within their respective scripts.
3. External packages and libraries are located within their respective folders (e.g. the Vokaturi library is in the `sound` module).
4. Ensure that import paths are relative to the `devastator` module. To test individual Python scripts, import and execute them from within the `tests`.folder.
4. Add `udev` rules for the ReSpeaker - do not run the program as root or super user (because the Python dependencies are all over the place).

# How To Run

To start the robot:
```
python3 devastator/main.py --robot
```

To start the manual controller:
```
python3 tests/robot/test_xpad.py
```
