import obspython as obs 
import dbus 

interval    = 30
source_name = ""

def spotify():
	global source_name
	source = obs.obs_get_source_by_name(source_name)
	if source is not None:
		try:
			bus = dbus.SessionBus()
			mp = bus.get_object('org.mpris.MediaPlayer2.spotify','/org/mpris/MediaPlayer2')
			t = dbus.Interface(mp,'org.freedesktop.DBus.Properties')
			x = t.Get('org.mpris.MediaPlayer2.Player','Metadata')
			text = '{} - {}'.format(x['xesam:artist'][0],x['xesam:title']) 
			settings = obs.obs_data_create()
			obs.obs_data_set_string(settings, "text", text)
			obs.obs_source_update(source, settings)
			obs.obs_data_release(settings)

		except:
			obs.script_log(obs.LOG_WARNING, "Can't parse Spotify")
			obs.remove_current_callback()

	obs.obs_source_release(source)

def refresh_pressed(props, prop):
    spotify()




def script_description():
    return "Updates a text source to the text retrieved from a spotify at every specified interval.\n\nBy Thomas"

def script_update(settings):
    global interval
    global source_name

    interval    = obs.obs_data_get_int(settings, "interval")
    source_name = obs.obs_data_get_string(settings, "source")

    obs.timer_remove(spotify)

    if source_name != "":
        obs.timer_add(spotify, interval * 1000)

def script_defaults(settings):
    obs.obs_data_set_default_int(settings, "interval", 5)

def script_properties():
    props = obs.obs_properties_create()

    obs.obs_properties_add_int(props, "interval", "Update Interval (seconds)", 5, 3600, 1)
    p = obs.obs_properties_add_list(props, "source", "Text Source", obs.OBS_COMBO_TYPE_EDITABLE, obs.OBS_COMBO_FORMAT_STRING)
    sources = obs.obs_enum_sources()
    if sources is not None:
        for source in sources:
            source_id = obs.obs_source_get_unversioned_id(source)
            if source_id == "text_gdiplus" or source_id == "text_ft2_source":
                name = obs.obs_source_get_name(source)
                obs.obs_property_list_add_string(p, name, name)

        obs.source_list_release(sources)

    obs.obs_properties_add_button(props, "button", "Refresh", refresh_pressed)
    return props

