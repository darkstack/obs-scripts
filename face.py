import obspython as obs
from types import SimpleNamespace
from ctypes import *
from ctypes.util import find_library


image = ''
face_idle = ''
face_speaking = ''
face_shooting = ''
shooting_v = 1.0
speaking_v = 5.0
idle_th = 0.0
audio_source =  ''
current_image = ''
current = 0
release = 0

release_timer = 10
grayed = -30

#Main handler for face (it's dumb)
def listen(volume):
	global face_idle 
	global face_speaking
	global face_shooting
	global idle_th
	global speaking_v 
	global shooting_v 
	global current_image
	global audio_source 
	global release 
	global release_timer 
	global grayed

	if volume < speaking_v:
		if release > grayed:
			release -= 1
		
		if release == grayed:
			set_image(face_idle,0.20)
		elif release > 0:
			return 
		else:
			set_image(face_idle)
		return

	else:
		if volume<shooting_v:
			release = release_timer
			set_image(face_speaking)
			return
		else: 
			release = release_timer
			set_image(face_shooting)



##FFI from https://github.com/upgradeQ/OBS-Studio-Python-Scripting-Cheatsheet-obspython-Examples-of-API
obsffi = CDLL(find_library("obs"))
G = SimpleNamespace()


def wrap(funcname, restype, argtypes):
	"""Simplify wrapping ctypes functions in obsffi"""
	func = getattr(obsffi, funcname)
	func.restype = restype
	func.argtypes = argtypes
	globals()["g_" + funcname] = func


class Source(Structure):
	pass


class Volmeter(Structure):
	pass


volmeter_callback_t = CFUNCTYPE(
		None, c_void_p, POINTER(c_float), POINTER(c_float), POINTER(c_float)
		)
wrap("obs_get_source_by_name", POINTER(Source), argtypes=[c_char_p])
wrap("obs_source_release", None, argtypes=[POINTER(Source)])
wrap("obs_volmeter_create", POINTER(Volmeter), argtypes=[c_int])
wrap("obs_volmeter_destroy", None, argtypes=[POINTER(Volmeter)])
wrap(
		"obs_volmeter_add_callback",
		None,
		argtypes=[POINTER(Volmeter), volmeter_callback_t, c_void_p],
		)
wrap(
		"obs_volmeter_remove_callback",
		None,
		argtypes=[POINTER(Volmeter), volmeter_callback_t, c_void_p],
		)
wrap(
		"obs_volmeter_attach_source",
		c_bool,
		argtypes=[POINTER(Volmeter), POINTER(Source)],
		)


@volmeter_callback_t
def volmeter_callback(data, mag, peak, input):
	G.noise = float(peak[0])


OBS_FADER_LOG = 2
G.lock = False
G.start_delay = 5
G.duration = 0
G.noise = 999
G.tick = 16
G.tick_mili = G.tick * 0.001
G.interval_sec = 0.1
G.tick_acc = 0
G.source_name = "Media Source"
G.volmeter = "not yet initialized volmeter instance"
G.callback = listen 



def event_loop():
	"""wait n seconds, then execute callback with db volume level within interval"""
	if G.duration > G.start_delay:
		if not G.lock:
			source = g_obs_get_source_by_name(G.source_name.encode("utf-8"))
			G.volmeter = g_obs_volmeter_create(OBS_FADER_LOG)
			g_obs_volmeter_add_callback(G.volmeter, volmeter_callback, None)
			if g_obs_volmeter_attach_source(G.volmeter, source):
				g_obs_source_release(source)
				G.lock = True
				return
	G.tick_acc += G.tick_mili
	if G.tick_acc > G.interval_sec:
		G.callback(G.noise)
		G.tick_acc = 0
	else:
		G.duration += G.tick_mili
##END FFI

def script_unload():
	g_obs_volmeter_remove_callback(G.volmeter, volmeter_callback, None)
	g_obs_volmeter_destroy(G.volmeter)


def set_image(img, opacity=1):
	global current_image	
	source = obs.obs_get_source_by_name(current_image)
	if source is not None:
		settings = obs.obs_data_create()
		obs.obs_data_set_string(settings, "file", img)
		obs.obs_source_update(source, settings)
		obs.obs_data_release(settings)
	#Filter

	filters = obs.obs_source_backup_filters(source)
	filter_count = obs.obs_source_filter_count(source)
	for i in range(filter_count):
		current_filter = obs.obs_data_array_item(filters, i)
		filter_name = obs.obs_data_get_string(current_filter, "name")
		if 'Color' in filter_name:
			#should check for color_filter v1/v2 since v1 got int opacity
			image_color_filter = obs.obs_source_get_filter_by_name(source,filter_name)
			settings_opacity = obs.obs_data_create()
			obs.obs_data_set_double(settings_opacity, "opacity",opacity)
			obs.obs_source_update(image_color_filter, settings_opacity)
			obs.obs_data_release(settings_opacity)
			obs.obs_source_release(image_color_filter)
		obs.obs_data_release(settings)
	obs.obs_data_array_release(filters)
	obs.obs_source_release(source)

def stop(props, prop):
	obs.timer_remove(event_loop)

def start(props, prop):
	obs.timer_add(event_loop, G.tick)

def test(props, prop):
	print('called test')
	set_image(face_idle,0.10)


# -------------------- OBS -------------------------


def script_load(settings):
	print('Load')
	obs.timer_add(event_loop, G.tick)

def script_description():
	return "PNG avatar\n\nBy Thomas"

def script_update(settings):
	global face_idle 
	global face_speaking
	global face_shooting
	global idle_th
	global speaking_v 
	global shooting_v 
	global current_image
	global audio_source
	global release_timer 
	global grayed

	release_timer = obs.obs_data_get_int(settings, "release_timer")
	release_timer = obs.obs_data_get_int(settings, "grayed_timer")
	shooting_v =  obs.obs_data_get_double(settings, "shooting_v")
	speaking_v =  obs.obs_data_get_double(settings, "speaking_v")
	idle_th = obs.obs_data_get_double(settings, "idle_th")

	face_idle = obs.obs_data_get_string(settings, "face_idle")
	face_speaking =obs.obs_data_get_string(settings, "face_speaking")
	face_shooting = obs.obs_data_get_string(settings, "face_shooting")

	current_image = obs.obs_data_get_string(settings,"current_image")
	audio_source = obs.obs_data_get_string(settings,"audio_source")
	G.source_name = audio_source


def script_defaults(settings):
	obs.obs_data_set_default_double(settings, "idle_th", 0.0)

def script_properties():
	props = obs.obs_properties_create()

	#obs.obs_properties_add_text(props, "url", "URL", obs.OBS_TEXT_DEFAULT)

	obs.obs_properties_add_int(props, "release_time", "Release speaking tick", 0,1000,1)
	obs.obs_properties_add_int(props, "grayed_timer", "Grayed speaking tick", 0,1000,1)
	obs.obs_properties_add_float(props, "idle_th", "Idle Threshold", -100.0, 0.0, 0.1)
	obs.obs_properties_add_float(props, "speaking_v", "Speaking Threshold", -100.0, 0.0, 0.1)
	obs.obs_properties_add_float(props, "shooting_v", "Shooting Threshold", -100.0, 0.0, 0.1)
	obs.obs_properties_add_path(props, "face_idle", "Face Idle",obs.OBS_PATH_FILE,"Image (*.jpg *.png);;All file (*.*)",None)
	obs.obs_properties_add_path(props, "face_speaking", "Face Speaking",obs.OBS_PATH_FILE,"Image (*.jpg *.png);;All file (*.*)",None)
	obs.obs_properties_add_path(props, "face_shooting", "Face Shooting",obs.OBS_PATH_FILE,"Image (*.jpg *.png);;All file (*.*)",None)
	#Image source 
	p = obs.obs_properties_add_list(props, "current_image", "image source", obs.OBS_COMBO_TYPE_EDITABLE, obs.OBS_COMBO_FORMAT_STRING)
	sources = obs.obs_enum_sources()
	if sources is not None:
		for source in sources:
			source_id = obs.obs_source_get_unversioned_id(source)
			if source_id == "image_source":
				name = obs.obs_source_get_name(source)
				obs.obs_property_list_add_string(p, name, name)

		obs.source_list_release(sources)
	#Audio 
	audio_pulse_source_combo = obs.obs_properties_add_list(props, "audio_source", "Audio", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
	audio_inputs_sources = obs.obs_enum_sources()
	if audio_inputs_sources is not None : 
		for source in audio_inputs_sources:
			source_id = obs.obs_source_get_unversioned_id(source)
			if 'input_capture' in source_id: 
				name = obs.obs_source_get_name(source)
				obs.obs_property_list_add_string(audio_pulse_source_combo,name,name)

		obs.source_list_release(audio_inputs_sources)

	obs.obs_properties_add_button(props, "button", "start", start)
	obs.obs_properties_add_button(props, "button2", "stop", stop)
	obs.obs_properties_add_button(props, "button3", "test", test)

	return props

