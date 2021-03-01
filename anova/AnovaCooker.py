import requests
import random
import string
import datetime


class AnovaCooker(object):
	"""Anova cooker object"""
	def __init__(self, device_id):
		"""Initialize all state variables and call update_state() to get current values from the API."""
		self.device_id = device_id
		self._jwt = None

		#---------------------------------------------
		# States that can be changed via the API
		#---------------------------------------------
		self.cook_time_seconds = None # Int (seconds)
		self.cook = None # Boolean
		self.target_temp = None # Float
		self.temp_display_unit = None # String ('C' for Celcius or 'F' for Farenheit)
		
		#---------------------------------------------
		# States that are read only via the API
		#---------------------------------------------
		# Job
		self.job_status = None # String
		self.job_time_remaining = None # Int

		# Duty cycle
		self.heater_duty_cycle = None # Float
		self.motor_duty_cycle = None # Float

		# WiFi
		self.wifi_connected = None # Boolean
		self.wifi_ssid = None # String
		
		# Safety
		self.device_safe = None # Boolean
		self.water_leak = None # Boolean
		self.water_level_critical = None # Boolean
		self.water_level_low = None # Boolean
		
		# Temperature
		self.heater_temp = None # Float
		self.triac_temp = None # Float
		self.water_temp = None # Float

		# Get initial state from Anova API
		self.update_state()


	def update_state(self):
		"""Get the device state and update local variables."""
		self._raw_device_state_json = self.__get_raw_state()
		self.raw_device_state = self._raw_device_state_json[0].get('body')
		_timestamp = datetime.datetime.strptime( self._raw_device_state_json[0].get('header').get('created-at'),  '%Y-%m-%dT%H:%M:%S.%fZ')
		self.updated_at = _timestamp.strftime("%Y-%m-%d %H:%M:%S")
  
		self.cook_time_seconds = int(self.raw_device_state.get('job').get('cook-time-seconds'))
		_cook_time_delta = datetime.timedelta(seconds=self.cook_time_seconds )
		self.cook_time = str( _cook_time_delta )
		self.cook = False if self.raw_device_state.get('job').get('mode') == 'IDLE' else True
		self.target_temp = float(self.raw_device_state.get('job').get('target-temperature'))
		self.temp_display_unit = str(self.raw_device_state.get('job').get('temperature-unit'))

		self.job_status = str(self.raw_device_state.get('job-status').get('state'))
		self.job_seconds_remaining = int(self.raw_device_state.get('job-status').get('cook-time-remaining')) 	# original ammarzuberi way
		_job_time_remaining_delta = datetime.timedelta(seconds=self.job_seconds_remaining)  				# fabriba human readable way
		self.job_time_remaining = str(_job_time_remaining_delta )				
		self.job_end_time = ( _timestamp + _job_time_remaining_delta ).strftime("%Y-%m-%d %H:%M:%S")
		self.job_start_time = ( _timestamp + _job_time_remaining_delta  - _cook_time_delta ).strftime("%Y-%m-%d %H:%M:%S")

		self.heater_duty_cycle = float(self.raw_device_state.get('heater-control').get('duty-cycle')) if self.raw_device_state.get('heater-control') else None
		self.motor_duty_cycle = float(self.raw_device_state.get('motor-control').get('duty-cycle')) if self.raw_device_state.get('motor-control') else None

		self.wifi_connected = True if self.raw_device_state.get('network-info').get('connection-status') == 'connected-station' else False
		self.wifi_ssid = str(self.raw_device_state.get('network-info').get('ssid'))

		self.device_safe = bool(self.raw_device_state.get('pin-info').get('device-safe'))
		self.water_leak = bool(self.raw_device_state.get('pin-info').get('water-leak'))
		self.water_level_critical = bool(self.raw_device_state.get('pin-info').get('water-level-critical'))
		self.water_level_low = bool(self.raw_device_state.get('pin-info').get('water-level-low'))

		self.heater_temp = float(self.raw_device_state.get('temperature-info').get('heater-temperature'))
		self.triac_temp = float(self.raw_device_state.get('temperature-info').get('triac-temperature'))
		self.water_temp = float(self.raw_device_state.get('temperature-info').get('water-temperature'))

		self.device_state = {	'job': {		'cooking-time-hhmmss': self.cook_time ,
												'mode': self.raw_device_state['job']['mode'],
												'target-temperature': self.target_temp ,
												'cook-start-time': self.job_start_time ,
												'cook-end-time': self.job_end_time },
								'job-status': {	'cook-time-remaining': self.job_time_remaining ,
												'status-updated-at': self.updated_at,
												'state': self.raw_device_state.get('job-status').get('state'),
												'heater-temperature': self.heater_temp,
												'water-temperature': self.water_temp ,
												'device-safe': self.device_safe,
												'water-leak': self.water_leak,
												'water-level-critical': self.water_level_critical,
												'water-temp-too-high': bool(self.raw_device_state.get('pin-info').get('water-temp-too-high')) },
								'system-info': {'connection-status':  self.raw_device_state.get('network-info').get('connected-station') ,
												'ssid': self.raw_device_state.get('network-info').get('ssid'),
												'firmware-version': self.raw_device_state.get('system-info-3220').get('firmware-version'),
												'firmware-version-raw': self.raw_device_state.get('system-info-3220').get('firmware-version-raw'),
												'triac-temperature':self.triac_temp }
							}


	def __get_raw_state(self):
		"""Get raw device state from the Anova API. This does not require authentication."""
		device_state_request = requests.get('https://anovaculinary.io/devices/{}/states/?limit=1&max-age=10s'.format(self.device_id))
		if device_state_request.status_code != 200:
			raise Exception('Error connecting to Anova')

		device_state_body = device_state_request.json()
		if len(device_state_body) == 0:
			raise Exception('Invalid device ID')

		return device_state_body
		

	def authenticate(self, email, password):
		"""Authenticate with Anova via Google Firebase."""
		ANOVA_FIREBASE_KEY = 'AIzaSyDQiOP2fTR9zvFcag2kSbcmG9zPh6gZhHw'

		# First authenticate with Firebase and get the ID token
		firebase_req_data = {
			'email': email,
			'password': password,
			'returnSecureToken': True
		}

		firebase_req = requests.post('https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={}'.format(ANOVA_FIREBASE_KEY), json = firebase_req_data)
		firebase_id_token = firebase_req.json().get('idToken')

		if not firebase_id_token:
			raise Exception('Could not log in with Google Firebase')

		# Now authenticate with Anova using the Firebase ID token to get the JWT
		anova_auth_req = requests.post('https://anovaculinary.io/authenticate', json = {}, headers = { 'firebase-token': firebase_id_token })
		jwt = anova_auth_req.json().get('jwt') # Looks like this JWT is valid for an entire year...

		if not jwt:
			raise Exception('Could not authenticate with Anova')

		# Set JWT local variable
		self._jwt = jwt

		return True


	def save(self):
		"""Push local state to the cooker via the API."""
		if not self._jwt:
			raise Exception('No JWT set - before calling save(), you must call authenticate(email, password)')

		# Convert boolean mode to COOK or IDLE for API
		cook_converted = 'COOK' if self.cook else 'IDLE'

		# Validate temperature unit
		if self.temp_display_unit not in ['F', 'C']:
			raise Exception('Invalid temperature unit - only F or C are supported')

		# Validate cook time and target temperature
		if type(self.cook_time_seconds) != int or type(self.target_temp) != float:
			raise Exception('Invalid cook time or target temperature')

		# Now prepare and send the request
		anova_req_headers = {
			'authorization': 'Bearer ' + self._jwt
		}

		anova_req_data = {
			'cook-time-seconds': self.cook_time_seconds,
			'id': ''.join(random.choices(string.ascii_lowercase + string.digits, k = 22)), # 22 digit random job ID for a new job at every save
			'mode': cook_converted,
			'ota-url': '',
			'target-temperature': self.target_temp,
			'temperature-unit': self.temp_display_unit
		}

		anova_req = requests.put('https://anovaculinary.io/devices/{}/current-job'.format(self.device_id), json = anova_req_data, headers = anova_req_headers)
		if anova_req.status_code != 200:
			raise Exception('An unexpected error occurred')

		if anova_req.json() != anova_req_data:
			raise Exception('An unexpected error occurred')

		return True



