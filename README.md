# WHR90 Ventilation Unit To MQTT Bridge

This project provides a lightweight Dockerized Python service that connects a **J.E. Storkair / Zehnder / R-Vent / Bergschenhoek WHR90 ventilation unit** via an **Elfin EW11A RS485/TCP gateway** and publishes sensor data to an MQTT broker. It also supports Home Assistant discovery, so your ventilation unit appears automatically in Home Assistant with temperature, fan speed, and binary sensors.

---

## Hardware

### WHR90
I use a J.E. Storkair WHR90R ventilation unit, built in the 29th week of 2001. Unfortunately this unit isn't fitted with a bypass, so my script doesn't collect any bypass-related values or any values from the outdoor and return PTC. My unit uses firmware V1.08 according to the IC on the PCB.

### EW11

I use the Elfin EW11A-0. Make sure to buy the EW11A, not the EW11. Although the PCB in my WHR90 unit tells shows 12V on the RS485 port, it does provide 20V. The EW11A-0 adds an external WiFi antenna, which improves reception compared to the regular EW11A. I bought my Elfin EW11 on Aliexpress.

| Model         | Power input | Antenna  | Recommended                           |
|---------------|-------------|----------|---------------------------------------|
| Elfin EW11    | 5~18VDC     | Internal | No, due to power input                |
| Elfin EW11-0  | 5~18VDC     | External | No, due to power input                |
| Elfin EW11A   | 5~36VDC     | Internal | Yes, if your wifi reception is strong |
| Elfin EW11A-0 | 5~36VDC     | External | Yes                                   |

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
   - I do recommend to change the password of the EW11.
   - Assign a static IP address to the EW11 (e.g. `192.168.1.50`).
   - Ensure the EW11 is reachable from the Docker host.

2. **Serial Port settings**
   - Baud rate: 9600
   - Data bit: 8
   - Stop bit: 1
   - Parity: None
   - Buffer size: 512
   - Gap time: 50
   - Flow control: Half duplex
   - Cli: Always
   - Waiting time: 500
   - Protocol: None

 3. **Communication settings**
   - Protocol: TCP Server
   - Local port: 502
   - Buffer size: 512
   - Keep alive(s): 60
   - Timeout(s): 300
   - Max accept: 3
   - Security: Disable
   - Route: UART

3. **Restart**
   - Restart the EW11 device.

---

## ⚙️ Environment Variables

All configuration is done via environment variables in docker compose. Below is a full list with configuration variables:

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

Make sure your EW11 is configured correctly. Download docker-compose.yaml and deploy with:
```bash
docker compose up -d
```
Or add it as stack to Portainer / Dockge.

