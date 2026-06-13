# MQTT Explorer Quick Reference

## Verbindungseinstellungen für MQTT Explorer

### Hookii Cloud Production (Direct)

```
Name: Hookii Cloud Production
Protocol: mqtt (MQTT Explorer verschlüsselt automatisch zu mqtts)
Hostname: iot.hookii.com
Port: 8883
Username: hookii-iot
Password: CaV4C4qHBQxwWI#GomA2zuI&D#MxyaMF
Client ID: mqtt-explorer-cloud
Clean session: true
```

---

## Subscribe Topics

Kopiere diese Topics in MQTT Explorer um sie zu abonnieren:

### 1. Alle Mower Telemetrie (alle Modelle/Serien)
```
hk/server/mower/push/+/+
```
Zeigt STATUS-Payloads von allen Mowern die online sind.

### 2. Spezifischer Mower
```
hk/server/mower/push/0002/HKX1EB100JD25010115
```
Nur STATUS-Updates für einen bestimmten Mower (Model 0002, deine Seriennummer).

### 3. Heartbeats (Keep-Alive Signale)
```
hk/app/mower/hb/+/+
```
Alle Heartbeat-Messages (sollten alle ~15 Sekunden kommen).

### 4. Nur Model 0002 Mower
```
hk/server/mower/push/0002/+
```

---

## Live-Daten beobachten

Nach dem Verbinden mit Hookii Cloud solltest du automatisch folgendes sehen:

1. **Neue Topics expandieren**
   - `hk/`
     - `server/`
       - `mower/`
         - `push/`
           - `0002/` (oder andere Model-Nummer)
             - `HKXxxxxxxxxxx` (deine Mower-Serial)

2. **STATUS-Messages**
   - Alle 5-15 Sekunden neue Daten bei `hk/server/mower/push/0002/<SERIAL>`
   - Enthalten: Position (robotX, robotY), Battery (electricity), Status, Temperatur, GPS, etc.

3. **Heartbeat-Messages**
   - Alle ~15 Sekunden bei `hk/app/mower/hb/0002/<SERIAL>`
   - Einfach `{"cmd": 1, "data": {"hb": 1}}`

---

## Payload-Beispiele

### Telemetrie (STATUS) - von Bridge empfangen

```json
{
  "data": {
    "STATUS": {
      "serialNumber": "HKX1EB100JD25010115",
      "robotX": 1234,Hookii Cloud empfangen

```json
{
  "cmd": 0,
  "data": {
    "STATUS": {
      "serialNumber": "HKX1EB100JD25010115",
      "robotX": 1234,
      "robotY": 5678,
      "robotNav": 45,
      "electricity": 85,
      "voltage": 24.5,
      "chargeCurrent": 0.5,
      "workingMode": 2,
      "robotStatus": 1,
      "knifeDiscMotorSpeed": 1200,
      "batteryTemperature": 28,
      "bladeTemperature": 45,
      "leftWheelTemperature": 32,
      "rightWheelTemperature": 31,
      "wifiSignal": -45,
      "gpsStatus": 5,
      "latitude": 52.123456,
      "longitude": 13.654321,
      "timestamp": 1718284800000,
      "taskInfo": {
        "taskId": "task123",
        "progress": 45
      }
    }
  }
}
```

### Heartbeat - Periodisches Keep-Alive Signal

```json
{
  "cmd": 1,
  "data": {
    "hb": 1

### 1. Verbindung checken
- Topics: `$SYS/broker/clients/+` (zeigt verbundene Clients)
- Topics: `$SYS/broker/subscriptions/+` (zeigt Subscriptions)

### 2. Bridge-Status überprüfen
Wenn im Log "cloud-mqtt connected" steht, sollte der Bridge mit dem Cloud MQTT verbunden sein.
Die Bridge sollte regelmäßig STATUS-Payloads auf `hookii/details/device/<SERIAL>` publizieren.

### 3. Command-Ausführung prüfen
- Publish auf `hookii/cmd/<SERIAL>/<ACTION>`
- Prüfe `hookii/result/<SERIAL>/+` auf Antwort
- Prüfe Bridge-Logs auf Fehler

### 4. Telemetrie-Verzögerung
Die Bridge aktualisiert alle 15 Sekunden (standard `heartbeat_seconds`).
STATUS-Updates vom Mower kommen etwa alle 5-15 Sekunden.

---

## Häufige Topic-Fehldiagnosen

| Symptom | Ursache | Lösung |
|---------|--------|--------|
| Keine Topics sichtbar | Bridge läuft nicht | Bridge Add-on starten |
| Topics bleiben leer | Mower offline / nicht konfiguriert | Mower-Seriennummer überprüfen |
| Commands funktionieren nicht | JWT abgelaufen / Bridge nicht mit Cloud verbunden | Bridge-Logs checken, neu starten |
| Falsche Seriennummer in Topics | Konfiguration falsch | Mower-Serial korrekt in Bridge-Config? |

---

## Beispiel-Workflow in MQTT Explorer

1. **Verbindung hiüberprüfen
- Hostname korrekt: `iot.hookii.com`
- Port korrekt: `8883`
- Credentials: `hookii-iot` / `CaV4C4qHBQxwWI#GomA2zuI&D#MxyaMF`
- MQTT Explorer sollte "Connected" anzeigen

### 2. Topics nicht sichtbar?
- Mower muss in Hookii App **online** sein
- Warten Sie 10-15 Sekunden nach Verbindung (erste Daten brauchen Zeit)
- Expandieren Sie den Baum: `hk/` → `server/` → `mower/` → `push/`

### 3. Payload leeren
Manche Payloads sind sehr groß. In MQTT Explorer:
- Rechtsklick auf Topic
- "Pretty print" für Lesbarkeit
- oder JSON-Viewer in externe App kopieren

### 4. Zu viele Messages?
- Abonnieren Sie nur den spezifischen Mower statt `+/+`
- Beispiel: `hk/server/mower/push/0002/HKX1EB100JD25010115`

---

## Häufige Probleme & Lösungen

| Problem | Ursache | Lösung |
|---------|--------|--------|
| "Connection refused" | Falscher Host/Port | `iot.hookii.com:8883` verwenden |
| "Auth failed" | Falsche Credentials | `hookii-iot` / `CaV4C4qHBQxwWI#GomA2zuI&D#MxyaMF` überprüfen |
| Keine Topics | Mower offline | In Hookii App überprüfen, ob Mower online ist |
| Nur `$SYS` Topics | Warscheinlich falscher Broker | Production Cloud `iot.hookii.com` verwenden |

---

## Workflow in MQTT Explorer

1. **Verbindung hinzufügen**
   - "+" Button → Neue Verbindung
   - Settings aus dem Guide kopieren
   - "Save" → "Connect"

2. **Warten**
   - Connection wird hergestellt
   - Status sollte "Connected" zeigen

3. **Daten beobachten**
   - Baumstruktur expandieren: `hk/server/mower/push/...`
   - Neue STATUS-Messages alle 5-15 Sekunden
   - Heartbeats alle ~15 Sekun