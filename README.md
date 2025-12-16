EW11 Connection
EW11_IP – IP address of the EW11 Modbus/TCP gateway (required).

EW11_PORT – TCP port of the EW11 (default: 502).

SOCKET_TIMEOUT – Timeout in seconds for socket communication (default: 2.0).

POLL_INTERVAL_SEC – Interval in seconds between polling cycles (default: 5).

MQTT Broker
MQTT_BROKER – Hostname or IP address of the MQTT broker (default: localhost).

MQTT_PORT – Port number for MQTT connection. Used for both plain and TLS connections (default: 1883 if TLS disabled, 8883 if TLS enabled).

MQTT_KEEPALIVE – Keepalive interval in seconds (default: 60).

MQTT_USERNAME – Username for broker authentication (optional).

MQTT_PASSWORD – Password for broker authentication (optional).

TLS Security
MQTT_USE_TLS – Enable TLS (true/false, default: true).

CA_CERT – Path to CA certificate file (optional).

CLIENT_CERT – Path to client certificate file (optional, for mutual TLS).

CLIENT_KEY – Path to client private key file (optional, for mutual TLS).

MQTT_TLS_INSECURE – Allow insecure TLS (self-signed or hostname mismatch) (true/false, default: false).

MQTT_TLS_VERSION – TLS version to enforce (TLSv1.2, TLSv1.3, or empty for default negotiation).

Device Metadata
MQTT_PREFIX – Prefix for MQTT topics (default: whr90).

NAME – Friendly name of the ventilation unit (default: WHR90 Ventilation Unit).

MANUFACTURER – Manufacturer name (default: R-Vent).