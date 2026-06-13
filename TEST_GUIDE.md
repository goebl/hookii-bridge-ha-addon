# Hookii Neomow - REST & MQTT Testguide

## 🌐 REST API Endpunkte (Hookii Cloud - Production)

### Basis-Konfiguration
- **Production Cloud**: `https://iot.hookii.com:10443`

### Erforderliche Header für ALLE Requests:
```
hookii-token: "Hookii <JWT>" (nach Login) oder "Hookii " (vor Login)
hookii-agent: "Android/Xiaomi 25010PN30G 16/V1.1.0/189"
user-agent: "Dart/3.9 (dart:io)"
accept-encoding: "gzip"
app-time-zone-offset: <minutes_offset_to_utc>
content-type: "application/json"
app-language: "en"
app-name: "Hookii App"
```

### 1. Login (Authentifizierung)
**Endpoint**: `POST /api/v1/user/login/email`

**Request Body**:
```json
{
  "email": "your-hookii-account@example.com",
  "password": "MD5_UPPERCASE_HASH_OR_CLEARTEXT",
  "appVersion": "1.1.0",
  "appName": "Hookii App",
  "phoneModel": "Android",
  "osVersion": "16"
}
```

**Response** (wichtige Felder):
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "token": "<JWT_TOKEN>",
    "appUserId": "<USER_ID>",
    "deviceList": [
      {
        "serialNumber": "HKX1EB100JD25010115",
        "deviceName": "Neomow",
        "modelCode": "0002",
        ...
      }
    ]
  }
}
```

⚠️ **Password-Hinweis**: 
- Entweder Klartext eingeben (MD5-hash wird lokal berechnet)
- Oder manuell MD5-hashen: `printf 'password' | md5sum | awk '{print toupper($1)}'`

---

### 2. Mower-Befehle (Start/Pause/Return)
**Endpoint**: `POST /api/v1/mower/cmd/start/stop/job`

**Request Body**:
```json
{
  "serialNumber": "HKX1EB100JD25010115",
  "modelCode": "0002",
  "command": "start|pause|stop|return",
  "taskId": "optional_task_id"
}
```

**Mögliche Commands**:
- `"start"` - Start mowing
- `"pause"` - Pause current job
- `"stop"` - Stop and clear progress
- `"return"` - Return to dock

---

### 3. Schedule-Verwaltung (Zeitplan)
**Endpoint**: `POST /api/v1/mower/cmd/calendar/time`

**Request Body** (Schedule schreiben):
```json
{
  "serialNumber": "HKX1EB100JD25010115",
  "modelCode": "0002",
  "schedule": {
    "enabled": true,
    "startTime": "09:00",
    "endTime": "17:00",
    "daysOfWeek": [1, 2, 3, 4, 5],
    "timeZoneId": "Europe/Berlin"
  }
}
```

---

### 4. Parameter-Verwaltung
**Endpoint**: `POST /api/v1/mower/cmd/calendar/param`

**Request Body**:
```json
{
  "serialNumber": "HKX1EB100JD25010115",
  "modelCode": "0002",
  "parameters": {
    "rainSensor": true,
    "returnOnRain": true,
    "cuttingHeight": 30,
    ...
  }
}
```

---

### 5. Kamera-Snapshot
**Endpoint**: `POST /api/v1/mower/capture/image`

**Request Body**:
```json
{
  "serialNumber": "HKX1EB100JD25010115",
  "modelCode": "0002"
}
```

**Response**: URL zum Snapshot oder Fehler

---

### 6. Alarm-Recovery
**Endpoint**: `POST /api/v1/mower/remote/recovery/alarm`

**Request Body**:
```json
{
  "serialNumber": "HKX1EB100JD25010115",
  "modelCode": "0002",
  "actionCode": 515
}
```

---

## 📡 MQTT Broker-Konfiguration

### Cloud MQTT Broker (Hookii Production Cloud)
- **Host**: `iot.hookii.com`
- **Port**: `8883` (SSL/TLS erforderlich)
- **Username**: `hookii-iot` (shared credential)
- **Password**: `CaV4C4qHBQxwWI#GomA2zuI&D#MxyaMF` (shared credential)
- **Protocol**: MQTT over SSL/TLS

---

## 📊 MQTT Topics zum Abonnieren

### Von Bridge zu lokalem Broker publiziert:

#### 1. Telemetrie-Status
**Topic**: `hookiivon Hookii Cloud

### Eingehende Telemetrie vom Mower

**Topic**: `hk/server/mower/push/<MODEL>/<SERIAL>`

**Payload** (regelmäßig):
```json
{
  "cmd": 0,
  "data": {
    "STATUS": {
      "serialNumber": "HKX1EB100JD25010115",
      "robotX": 150,
      "robotY": 200,
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
      "taskInfo": {...},
      "timestamp": 1718284800000
    }
  }
}
```

### Heartbeat
**Topic**: `hk/app/mower/hb/<MODEL>/<SERIAL>`

**Payload** (keep-alive Signal, alle 15 Sekunden):
```json
{
  "cmd": 1,
  "data": {
    "hb": 1
  }
}
```
### Test 1: Login und JWT erhalten
```bash
curl -X POST https://iot.beta.hookii.com:10443/api/v1/user/login/email \
  -H "hookii-token: Hookii " \
  -H "hookii-agent: Android/Xiaomi 25010PN30G 16/V1.1.0/189" \
  -H "user-agent: Dart/3.9 (dart:io)" \
  -H "content-type: application/json" \
  -d '{
    "email": "bridge@example.com",
    "password": "5F4DCC3B5AA765D61D8327DEB882CF99",
    "appVersion": "1.1.0"
  }'
```hookii.com:10443/api/v1/user/login/email \
  -H "hookii-token: Hookii " \
  -H "hookii-agent: Android/Xiaomi 25010PN30G 16/V1.1.0/189" \
  -H "user-agent: Dart/3.9 (dart:io)" \
  -H "content-type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "password": "5F4DCC3B5AA765D61D8327DEB882CF99",
    "appVersion": "1.1.0"
  }'
```

### Test 2: Mower starten
```bash
curl -X POST https://iot

---

## 📱 MQTT Explorer - Testschritte

### 1. Verbindung konfigurieren
- **Server**: `127.0.0.1` oder `core-mosquitto`
- **Port**: `1883`
- **Username**: `mqtt` (oder Ihr MQTT-User)
- **Password**: `<your-password>`

### 2. Topics abonnieren (Subscribe)
```
hookii/details/device/Verbindung zur Hookii Cloud

### 1. Verbindung konfigurieren
- **Server**: `iot.hookii.com`
- **Port**: `8883`
- **Username**: `hookii-iot`
- **Password**: `hookii@iot888`
- **Protocol**: mqtt (MQTT Explorer verschlüsselt automatisch)
- **Clean session**: true

### 2. Topics abonnieren (Subscribe)
```
hk/server/mower/push/+/+    # Alle Mower Telemetrie
hk/server/mower/push/0002/+ # Nur Model 0002 Mower
hk/app/mower/hb/+/+         # Alle Heartbeats
```

### 3. Live-Daten beobachten
- Verbindung herstellen
- Topics expandieren
- STATUS-Payloads sollten alle 5-15 Sekunden auftauchen
- Heartbeat-Messages sollten regelmäßig kommenc...` | JWT-Token aus Login-Response |
| `<USER_ID>` | `12345` | App-User-ID aus Login-Response |
| `<MQTT_HOST>` | `core-mosquitto` | Lokaler MQTT Broker-Hostname |
| `<MQTT_USER>` | `mqtt` | Lokaler MQTT-Benutzer |
| `<MQTT_PASS>` | `password123` | Lokales MQTT-Passwort |
EMAIL>` | `your-email@example.com` | Dein Hookii Account E-Mail |
| `<PASSWORD>` | `my-password` | Dein Hookii Account Passwort (oder MD5-Hash)
## 🔄 Typischer Ablauf

1. **Login via REST** → JWT erhalten
2. **Mit JWT als Header** → Commands senden oder Daten abrufen
3. **MQTT abonnieren** → Telemetrie in Echtzeit empfangen
4. **MQTT publishen** → Commands via Local Broker senden
5. **Ergebnisse prüfen** → Topic `hookii/result/...` auf Feedback

---vom Mower direkt von der Cloud empfangen
4. **Daten beobachten** → Live Positionen, Battery, Status in MQTT Explorer

| Fehler | Ursache | Lösung |
|--------|--------|--------|
| `code: 2, msg: hookii-agent参数错误` | Falscher/fehlender `hookii-agent` Header | Exakten Agent-String verwenden |
| `code: 5, msg: 该用户未注册` | Email nicht im System registriert | Korrekte Bridge-Account-Email prüfen |
| JWT ungültig | JWT abgelaufen | Neu einloggen (Token hat Expiration) |
| MQTT verbindung refused | Falscher Host/Port/Credentials | Mosquitto lEmail prüfen (muss in Hookii App funktionieren) |
| JWT ungültig | JWT abgelaufen | Neu einloggen (Token hat Expiration) |
| MQTT verbindung refused | Falsches Host/Port/Credentials | `iot.hookii.com:8883` mit `hookii-iot / CaV4C4qHBQxwWI#GomA2zuI&D#MxyaMF` |
| Kein STATUS empfangen | Mower offline / falsche Topics | Mower in Hookii App online? Topics korrekt?

## 📋 Checkliste vor dem Testen

- [ ] Separate Bridge-Account erstellt (nicht Haupt-Account!)
- [ ] Mower zum Bridge-Account freigegeben (Device Sharing)
- [ ] Hookii Account funktioniert (Mower sichtbar in Hookii App)
- [ ] Mower-Seriennummer bekannt (16 Zeichen, startet mit HKX)
- [ ] REST Client installiert (Postman, Insomnia, Thunder Client, etc.)
- [ ] MQTT Explorer installiert (https://mqtt-explorer.com)
- [ ] Internet-Verbindung stabil
- [ ] Password griffbereit oder als MD5-Hash vorbereitet

---

## 📚 Weiterführendes

- **REST API**: Alle Endpunkte in diesem Guide dokumentiert
- **MQTT Topics**: Cloud-direkter Zugriff auf Live-Telemetrie
- **Mower Serial**: In Hookii App unter Device Info oder auf dem Mower (Unterseite)