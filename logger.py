import obspython as obs
import time, sys, os, math
import numpy as np
from pynput.mouse import Button, Controller, Listener
from pynput.keyboard import KeyCode
from pynput.keyboard import Listener as KBListner
import os.path

# Export
enabled = True
file_name = 'obs_cursor_recorder' # Write your folder in OBS Script window
folder_path = 'C:/Users/iml/Documents' # Write your folder in OBS Script window


# Global State
is_being_recorded = False
start_time_record = None
log = np.array([])
my_setting = None

trigger = 'keyboard'
button_listener = None
button_clicked = 0
button_prev_pressed = False
key_listener = None
key_pressed = 0
key_released = True
keys_pressed = set([])

count = 0 #debugging

###############################################################################
# UTILS
###############################################################################

def on_click(x, y, button, pressed):
	global button_clicked, button_prev_pressed
	if pressed and not button_prev_pressed:
		button_clicked = int(math.log(button.value[0], 4))
		# if button == Button.left:
		# 	button_clicked = 0
		# elif button == Button.middle:
		# 	button_clicked = 1
		# elif button == Button.middle:
		# 	button_clicked = 2
		# else:
		# 	print(button)
		# 	raise ValueError
		
	button_prev_pressed = pressed


def unpack_key(_key, pressed=True):
    raw = format(_key)
    keys = set([])
	
    # special keys
    if raw.startswith("Key."):
        keys.add(raw[4:])
    # the pressed number and special characters with ctrl
    elif raw.startswith("<") and raw.endswith(">"):
        # number
        keys.add(chr(int(raw[1:-1])))

        # special character
    
    # character
    else:
        # case 1 : alphabet
        if _key.char.isalpha():
            if _key.char.isupper():
                if pressed:
                    keys.add('shift')
            keys.add(_key.char.lower())

        # case 2 :other character & the pressed with ctrl_l
        elif (ord(_key.char) <= 26):
            k = chr(ord(_key.char) + 96)
            keys.add(k)
            if pressed:
                keys.add('ctrl_l')

        # case 3 : number
        elif _key.char.isdigit():
            keys.add(_key.char)

        # case 4 : number & shift
        elif _key.char in "!@#$%^&*()":  
            # print("case 4")
            upper, lower = "!@#$%^&*()", "1234567890"
            k = lower[upper.find(_key.char)]
            keys.add(k)
            if pressed:
                keys.add('shift')

        # case 5 : others
        elif _key.char in "-=\\`[];',./":
            keys.add(_key.char)

        # case 6 : others & shift
        elif _key.char in '_+|~{}:"<>?':
            # print("case 5")
            upper, lower = '_+|~{}:"<>?', "-=\\`[];',./"
            k = lower[upper.find(_key.char)]
            keys.add(k)
            if pressed:
                keys.add('shift')
        
        # exception!!!!
        else:
            # print(raw)
            print("not expected values")
            raise ValueError
    
    return keys

def on_press(key):
	global keys_pressed

	# processing an input
	keys_pressed = keys_pressed | unpack_key(key)
	
def on_release(key):
	global keys_pressed

	keys_pressed = keys_pressed - unpack_key(key, pressed=False) # difference(set)
	# print("{} will be removed.".format(format(key)))
	# keys_pressed.remove(format(key))


def save_to_file():
	global log, folder_path, file_name
	global my_setting

	folder_path = obs.obs_data_get_string(my_setting, "path")
	file_name = obs.obs_data_get_string(my_setting, "name")

	full_path = os.path.join(folder_path, file_name+".csv")
	if os.path.isfile(full_path):
		full_path = os.path.join(folder_path, file_name + "_" + str(time.time()).split('.')[0] +".csv")
	
	with open(full_path, "w") as f:
		log = log.reshape((-1,6))
		np.savetxt(f, log, delimiter=',', fmt=["%s", "%s", "%s", "%s", "%s", "%s"], comments='')
		print("Saved successfully at {}".format(full_path))

	output = obs.obs_frontend_get_recording_output()
	output_settings = obs.obs_output_get_settings(output)
	print(obs.obs_data_get_string(output_settings, "path"))
	print("Saved successfully.")


###############################################################################
# HOOK HANDLER
###############################################################################

def recording_start_handler(_):
	global is_being_recorded, start_time_record, log, button_listener, key_listener, count
	global folder_path, file_name

	if enabled:
		is_being_recorded = True
		start_time_record = time.time()
		log = np.array([])

		if (trigger == 'mouse') | (trigger == 'both'):
			print("Start Logging Mouse")
			if(button_listener == None):
				button_listener = (Listener(on_click=on_click))
				button_listener.start()
			# count = 0
		if (trigger == 'keyboard') | (trigger == 'both'):
			print("Start Logging Keyboard")
			if(key_listener == None):
				key_listener = KBListner(on_press=on_press, on_release=on_release)
				key_listener.start()

		print("Start Recording at {start_time}".format(start_time=start_time_record))

def recording_stopped_handler(_):
	global is_being_recorded, button_listener, key_listener
	is_being_recorded = False

	if(button_listener != None):
		button_listener.stop()
		button_listener.join()
		button_listener = None
	
	if(key_listener != None):
		key_listener.stop()
		key_listener.join()
		key_listener = None

	if enabled:
		save_to_file()
		print("Stopped Recording")
		

###############################################################################
# OBS API
###############################################################################

def script_update(settings):
	global file_name, folder_path, enabled, trigger
	global my_setting
	enabled = obs.obs_data_get_bool(settings, "enabled")
	trigger = obs.obs_data_get_string(settings, "trigger")
	
	if(is_being_recorded):
		# Don't change `enabled`
		obs.obs_data_set_bool(settings, "enabled", enabled)
	my_setting = settings

	## it fails to change an output path
	# folder_path = obs.obs_data_get_string(my_setting, "path")
	# file_name = obs.obs_data_get_string(my_setting, "name")
	# full_path = "/".join((folder_path, '.'.join((file_name, "mp4"))))

	# output = obs.obs_frontend_get_recording_output()
	# output_settings = obs.obs_output_get_settings(output)
	# obs.obs_data_set_string(output_settings, "path", full_path)


def script_tick(seconds):
	global is_being_recorded, start_time_record, log, button_clicked, key_pressed, count, keys_pressed
	if (is_being_recorded == False) or (enabled == False):
		return


	if keys_pressed:
		kp = keys_pressed.copy()
		if ',' in keys_pressed:
			kp.remove(',')
			kp.add('comma')
		
		if '/' in keys_pressed:
			kp.remove('/')
			kp.add('slash')
		
		k = '/'.join(kp)
		# print("<Loggy> keys pressed : {}".format(k))
		# keys_pressed = set([])
	else:
		k = ''

	x, y = Controller().position
	c = button_clicked
	# print(button_clicked)

	t = time.time() - start_time_record
	log = np.concatenate((log, np.array([x, y, c, k, t, 1/seconds])), axis=0)

	count += 1
	button_clicked = 0


def script_description():
	return '''
		<b>OBS Cursor Logger</b>
		<hr>
		Record Cursor Position on each frame, and
		<br/>
		Save the log as a csv format which an user defined.
		<br/>
		Made by Hyunchul Kim, © 2020
		<hr>
		'''


def script_properties():
    	
	props = obs.obs_properties_create()

	trigger = obs.obs_properties_add_list(props, "trigger", "Trigger", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
	obs.obs_property_list_add_string(trigger, "mouse", "mouse")
	obs.obs_property_list_add_string(trigger, "keyboard", "keyboard")
	obs.obs_property_list_add_string(trigger, "both", "both")

	enabled = obs.obs_properties_add_bool(props, "enabled", "Enabled")
	obs.obs_property_set_long_description(enabled, "Whether to save the file when recording or not.")

	path = obs.obs_properties_add_path(props, "path", "Path", obs.OBS_PATH_DIRECTORY, '*.*', None)

	name = obs.obs_properties_add_text(props, "name", "File Name", obs.OBS_TEXT_DEFAULT)
	obs.obs_property_set_long_description(name, "This name will be log's and video's")

	return props


def script_save(settings):
	script_update(settings)


def script_defaults(settings):
    	
	output = obs.obs_frontend_get_recording_output()

	signal_handler = obs.obs_output_get_signal_handler(output)
	obs.signal_handler_connect(signal_handler, 'start', recording_start_handler)
	obs.signal_handler_connect(signal_handler, 'stop', recording_stopped_handler)

	obs.obs_data_set_default_bool(settings, "enabled", True)
	obs.obs_data_set_default_string(settings, "name", "Set Your Name")
	obs.obs_data_set_default_string(settings, "path", "Set Your Path")
