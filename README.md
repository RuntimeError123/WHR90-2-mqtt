# WHR90 Ventilation Unit to MQTT Bridge

This project provides a lightweight Dockerized Python service that connects a **J.E. Storkair / Zehnder / R-Vent / Bergschenhoek WHR90 ventilation unit** via an **Elfin EW11A RS485/TCP gateway** and publishes sensor data to an MQTT broker. It also supports Home Assistant discovery, so your ventilation unit appears automatically in Home Assistant, exposing temperature, fan speed, and binary sensors.

---

## Home Assistant Integration

This container publishes **MQTT discovery topics** automatically, so Home Assistant will detect the WHR90 unit without any manual configuration. Once the service is running and connected to your MQTT broker, entities will appear under the device defined by the `NAME` and `MANUFACTURER` environment variables.

### Entities created
The following sensors and binary sensors are exposed:

- **Temperature**
  - `sensor.<prefix>_exhaust_c` → Exhaust air temperature (°C)

- **Fan status**
  - `sensor.<prefix>_supply_pct` → Supply fan percentage (%)
  - `sensor.<prefix>_extract_pct` → Extract fan percentage (%)
  - `sensor.<prefix>_supply_rpm` → Supply fan RPM
  - `sensor.<prefix>_extract_rpm` → Extract fan RPM

- **Binary sensors**
  - `binary_sensor.<prefix>_supply_active` → Supply fan active (ON/OFF)
  - `binary_sensor.<prefix>_exhaust_active` → Extract fan active (ON/OFF)

### Notes
- The `<prefix>` is defined by the `MQTT_PREFIX` environment variable (default: `whr90`).
- All entities are retained in MQTT, so Home Assistant will restore their state after restart.
- If you change `NAME` or `MANUFACTURER`, Home Assistant will show the device under that name in the UI.
- No additional YAML configuration is required; everything is handled via MQTT discovery.

## Hardware

### WHR90
I use a J.E. Storkair WHR90R ventilation unit, built in the 29th week of 2001. Unfortunately this unit isn't fitted with a bypass, so my script doesn't collect any bypass-related values or any values from the outdoor and return PTC. My unit uses firmware V1.08 according to the IC on the PCB.

### EW11

I use the Elfin EW11A-0. Make sure to buy the EW11A, not the EW11. Although the PCB in my WHR90 unit shows 12V on the RS485 port, it does provide 20V. The EW11A-0 adds an external WiFi antenna, which improves reception compared to the regular EW11A. I bought my Elfin EW11 on AliExpress.

| Model         | Power input | Antenna  | Recommended                           |
|---------------|-------------|----------|---------------------------------------|
| Elfin EW11    | 5~18VDC     | Internal | No, due to power input                |
| Elfin EW11-0  | 5~18VDC     | External | No, due to power input                |
| Elfin EW11A   | 5~36VDC     | Internal | Yes, if your WiFi reception is strong |
| Elfin EW11A-0 | 5~36VDC     | External | Yes                                   |

Other devices that convert RS485 to TCP might also work, but I haven't tested that.

### Wiring

I used a CAT5e cable to connect the WHR90 to the EW11. 
On the EW11 side:

| Pin RJ45 | Purpose EW11  | Color
|----------|---------------|--------------|
| 1        | Not connected | None         |
| 2        | Not connected | None         |
| 3        | Not connected | None         |
| 4        | Reload        | None         |
| 5        | A+            | Orange-white |
| 6        | B-            | Orange       |
| 7        | VCC           | Blue         |
| 8        | Ground        | Brown        |

On the WHR90 side I use a male DE9 connector to plug into the ventilation unit female DE9 port. The connector I use is a solderless DE9 connector (sold as DB9 connector) bought on AliExpress.

| Pin DE9 | Purpose WHR90 | Color        |
|---------|---------------|--------------|
| 1       | Ground        | Brown        |
| 5       | VCC           | Blue         |
| 6       | A             | Orange-white | 
| 7       | B             | Orange       | 

> [!NOTE] 
> According to the [manual](https://cdn.webshopapp.com/shops/42891/files/382461178/fairair-manual-bergschenhoek-r-vent-whr90-91.pdf) the DE9 port should be wired differently:
> - 1 VCC
> - 5 Ground
> - 8 B
> - 9 A
> Check how this is wired on your unit.
> Alternatively you can also open the ventilation unit and screw the brown, blue, orange-white and orange cable under the corresponding screw terminals on the WHR90 PCB.


> [!WARNING]
> Make sure your cable is connected correctly before continuing

## EW11 Gateway Setup

The EW11 Modbus/TCP gateway must be configured correctly before running this container:

1. **System settings**
   - I recommend changing the password of the EW11.
   - Assign a static IP address to the EW11 (e.g. `192.168.1.50`).
   - Ensure the EW11 is reachable from the Docker host.

2. **Serial Port settings**
   - Baud rate: `9600`
   - Data bit: `8`
   - Stop bit: `1`
   - Parity: `None`
   - Buffer size: `512`
   - Gap time: `50`
   - Flow control: `Half duplex`
   - Cli: `Always`
   - Waiting time: `500`
   - Protocol: `None`

 3. **Communication settings**
   - Protocol: `TCP Server`
   - Local port: `502`
   - Buffer size: `512`
   - Keep alive(s): `60`
   - Timeout(s): `300`
   - Max accept: `3`
   - Security: `Disable`
   - Route: `UART`

3. **Restart**
   - Restart the EW11 device.

---

## Environment Variables

All configuration is done via environment variables in Docker Compose. Below is a full list with configuration options:

### EW11 Connection
- `EW11_IP` – IP address of the EW11 gateway (**mandatory**).
- `EW11_PORT` – TCP port (default: `502`).
- `SOCKET_TIMEOUT` – Socket timeout in seconds (default: `2.0`).
- `POLL_INTERVAL_SEC` – Polling interval in seconds (default: `5`).

### MQTT Broker
- `MQTT_BROKER` – Hostname/IP of the MQTT broker (default: `localhost`).
- `MQTT_PORT` – Port number (default: `1883` without TLS, `8883` with TLS).
- `MQTT_KEEPALIVE` – Keepalive interval in seconds (default: `60`).
- `MQTT_USERNAME` – Username (optional).
- `MQTT_PASSWORD` – Password (optional).
- `MQTT_USE_TLS` – Enable TLS (`true`/`false`, default: `true`).
- `CA_CERT` – Path to CA certificate (optional).
- `CLIENT_CERT` – Path to client certificate (optional, for mutual TLS).
- `CLIENT_KEY` – Path to client private key (optional, for mutual TLS).
- `MQTT_TLS_INSECURE` – Allow insecure TLS (self-signed/mismatched hostname) (`true`/`false`, default: `false`).
- `MQTT_TLS_VERSION` – TLS version (`TLSv1.2`, `TLSv1.3`, or empty for default negotiation).

### Metadata
- `MQTT_PREFIX` – Topic prefix (default: `whr90`).
- `NAME` – Friendly device name (default: `WHR90 Ventilation Unit`).
- `MANUFACTURER` – Manufacturer name (default: `J.E. Storkair`).

## Installation

Make sure your EW11 is configured correctly. Download the `docker-compose.yaml` file, update environment variables accordingly and deploy with:
```bash
docker compose up -d
```
Or add it as stack in Portainer or Dockge.

## Notes
- Docker and Docker Compose must be installed for the script to work
- The script assumes that an MQTT broker is available. I use Eclipse Mosquitto.
- The script supports three MQTT communication scenarios:
  - Unencrypted plain text traffic
  - Encrypted, authenticated with client certificate and private key
  - Encrypted, authenticated with username and password
  When using encrypted traffic, you can configure the script to allow self‑signed certificates or certificates with a mismatched hostname using the `MQTT_TLS_INSECURE` variable. If you have a self-signed certificate with your own CA (and your MQTT broker hostname) matches the certificate, you can trust your own CA by mapping your CA's public key in the Docker container as a volume and using the `CA_CERT` variable. 
- Currently I haven't been able to use the RS485 port to write data to the ventilation unit. At the moment, only temperatures, fan speed percentages, and RPMs can be read. If someone knows what we can send to change the fan speed, please let me know.
- I noticed some odd quirks while working on this project (20V on a 12V header, RS485 port wired differently than written in the manual), so using this script and connecting anything to your unit is entirely your own responsibility. Please verify your connections and use a multimeter to verify voltages before powering on.

    