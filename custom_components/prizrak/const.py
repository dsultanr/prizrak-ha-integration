"""Constants for the Prizrak Monitoring integration."""
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass

DOMAIN = "prizrak"
CONF_EMAIL = "email"
CONF_PASSWORD = "password"

PLATFORMS = ["sensor", "binary_sensor", "button", "device_tracker"]

# Sensor definitions: (name, unit, device_class, icon, state_key, state_class)
SENSOR_TYPES = {
    "serial_no": ("Serial Number", None, None, "mdi:identifier", "serial_no", None),
    "last_update": ("Last Update", None, SensorDeviceClass.TIMESTAMP, "mdi:clock-outline", "last_update", None),
    "last_device_exchange_time": ("Last Device Exchange", None, SensorDeviceClass.TIMESTAMP, "mdi:swap-horizontal", "last_device_exchange_time", None),

    # GPS
    "latitude": ("Latitude", "°", None, "mdi:map-marker", "geo.lat", SensorStateClass.MEASUREMENT),
    "longitude": ("Longitude", "°", None, "mdi:map-marker", "geo.lon", SensorStateClass.MEASUREMENT),
    "gnss_speed": ("GNSS Speed", "km/h", SensorDeviceClass.SPEED, "mdi:speedometer", "geo_ext.gnss_speed", SensorStateClass.MEASUREMENT),
    "altitude": ("Altitude", "m", SensorDeviceClass.DISTANCE, "mdi:altimeter", "geo_ext.gnss_height", SensorStateClass.MEASUREMENT),
    "satellites": ("Satellites", None, None, "mdi:satellite-variant", "geo_ext.gnss_sat_used", SensorStateClass.MEASUREMENT),
    "azimuth": ("Azimuth", "°", None, "mdi:compass", "geo_ext.gnss_azimuth", SensorStateClass.MEASUREMENT),

    # Telemetry
    "battery_voltage": ("Battery Voltage", "V", SensorDeviceClass.VOLTAGE, "mdi:car-battery", "accum_voltage", SensorStateClass.MEASUREMENT),
    "fuel_level": ("Fuel Level", "L", None, "mdi:gas-station", "fuel_level", SensorStateClass.MEASUREMENT),
    "temperature": ("Inside Temperature", "°C", SensorDeviceClass.TEMPERATURE, "mdi:thermometer", "inside_temp", SensorStateClass.MEASUREMENT),
    "outside_temperature": ("Outside Temperature", "°C", SensorDeviceClass.TEMPERATURE, "mdi:thermometer", "outside_temp", SensorStateClass.MEASUREMENT),
    "engine_temperature": ("Engine Temperature", "°C", SensorDeviceClass.TEMPERATURE, "mdi:engine", "engine_temp", SensorStateClass.MEASUREMENT),
    "speed": ("Speed", "km/h", SensorDeviceClass.SPEED, "mdi:speedometer", "speed", SensorStateClass.MEASUREMENT),
    "rpm": ("Engine RPM", "RPM", None, "mdi:engine", "rpm", SensorStateClass.MEASUREMENT),
    "odometer": ("Odometer", "km", SensorDeviceClass.DISTANCE, "mdi:counter", "route", SensorStateClass.TOTAL_INCREASING),

    # Engine & Systems (ignition and parking_brake moved to binary_sensor)

    # GSM
    "gsm_level": ("GSM Signal", "%", None, "mdi:signal", "gsm_level", SensorStateClass.MEASUREMENT),
    "sim_vendor": ("SIM Operator", None, None, "mdi:sim", "sim_1_vendor", None),
    "sim_balance": ("SIM Balance", None, None, "mdi:cash", "balance.value", None),

    # Heating
    "driver_seat_heating": ("Driver Seat Heating", None, None, "mdi:car-seat-heater", "driver_seat_heating_state", None),
    "front_pass_seat_heating": ("Passenger Seat Heating", None, None, "mdi:car-seat-heater", "front_pass_seat_heating_state", None),
    "rear_left_seat_heating": ("Rear Left Seat Heating", None, None, "mdi:car-seat-heater", "rear_left_seat_heating_state", None),
    "rear_right_seat_heating": ("Rear Right Seat Heating", None, None, "mdi:car-seat-heater", "rear_right_seat_heating_state", None),
    "front_window_heating": ("Front Window Heating", None, None, "mdi:car-defrost-front", "front_window_heating_state", None),
    "rear_window_heating": ("Rear Window Heating", None, None, "mdi:car-defrost-rear", "rear_window_heating_state", None),
    "mirror_heating": ("Mirror Heating", None, None, "mdi:mirror", "mirror_heating_state", None),
    "wheel_heating": ("Wheel Heating", None, None, "mdi:steering", "wheel_heating_state", None),
}

# Binary sensor definitions: (name, device_class, state_key)
BINARY_SENSOR_TYPES = {
    # Doors & Locks
    "driver_door": ("Driver Door", BinarySensorDeviceClass.DOOR, "driver_door"),
    "front_pass_door": ("Passenger Door", BinarySensorDeviceClass.DOOR, "front_pass_door"),
    "rear_left_door": ("Rear Left Door", BinarySensorDeviceClass.DOOR, "rear_left_door"),
    "rear_right_door": ("Rear Right Door", BinarySensorDeviceClass.DOOR, "rear_right_door"),
    "trunk": ("Trunk", BinarySensorDeviceClass.DOOR, "trunk"),
    "hood": ("Hood", BinarySensorDeviceClass.DOOR, "hood"),
    "central_lock": ("Central Lock", BinarySensorDeviceClass.LOCK, "central_lock"),

    # Security & Safety
    "connection": ("Connection", BinarySensorDeviceClass.CONNECTIVITY, "connection_state"),
    "guard": ("Guard", None, "guard"),
    "alarm": ("Alarm", BinarySensorDeviceClass.SAFETY, "alarm"),

    # Engine & Systems
    "ignition": ("Ignition", BinarySensorDeviceClass.RUNNING, "ignition_switch"),
    "parking_brake": ("Parking Brake", BinarySensorDeviceClass.PROBLEM, "parking_brake"),

    # GPS
    "gps": ("GPS", None, "geo.gps_state"),
}

# Button definitions: (name, command, icon)
BUTTON_TYPES = {
    "guard_on": ("Guard On", "GuardOn", "mdi:shield-check"),
    "guard_off": ("Guard Off", "GuardOff", "mdi:shield-off"),
    "autolaunch_on": ("Autolaunch On", "AutolaunchOn", "mdi:engine"),
    "autolaunch_off": ("Autolaunch Off", "AutolaunchOff", "mdi:engine-off"),
}
