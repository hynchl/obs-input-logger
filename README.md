# obs-input-logger
A python script for synchronized input logging on OBS recordings.
This scripts are tested on Windows 10, OBS 27

### Configuration
1. Make conda virtual environment and install libraries with `requirements.txt`
2. Tool > Script > Python Configuration, Input the python 3.6 path you installed
3. Tool > Script > Script, Press `+` button and import `logger.py`.
4. Set your input type, folder path, and name.

### Output(csv)
Each row has following shape.

[cursor x, cursor y, pressed button(single), pressed key(multiple), time, fps]
- current x, cursor y : current cursor location
- pressed button : 0 = None, 1 = Left, 2 = Right, 3 = Mid
- pressed key : keys joined with `/` ex) 'a/b/c/left/space'
- time: current time `time.time()`
- fps: 1/(frame interval), for stability check