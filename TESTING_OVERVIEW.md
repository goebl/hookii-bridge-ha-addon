# Hookii Neomow - REST & MQTT Testdateien Übersicht

Alle notwendigen Informationen zum direkten Testen der Hookii Production Cloud REST API und MQTT Telemetrie.

## 📄 Erstellte Dateien

### 1. **TEST_GUIDE.md** ← START HIER
Umfassender Leitfaden für Production Cloud:
- ✓ REST API Endpoints (Production nur)
- ✓ Erforderliche Header für jeden Request
- ✓ Request/Response Beispiele
- ✓ MQTT Cloud-Konfiguration (Direct zu Hookii)
- ✓ MQTT Topics (Live von Mower)
- ✓ Checkliste vor dem Testen
- ✓ Fehlerlösung

**Wie verwenden**: In Texteditor öffnen und durchlesen

---

### 2. **MQTT_EXPLORER_GUIDE.md**
Spezifischer Guide für MQTT Explorer (Cloud Connection):
- ✓ Verbindungseinstellungen zu Hookii Cloud (Copy-Paste ready)
- ✓ Topics zum Abonnieren (hk/server/mower/push/...)
- ✓ Live Telemetrie empfangen
- ✓ Payload-Beispiele
- ✓ Debugging-Tipps
- ✓ Workflow im MQTT Explorer

**Wie verwenden**: 
1. MQTT Explorer öffnen (https://mqtt-explorer.com oder AppStore)
2. Verbindungseinstellungen aus dem Guide kopieren
3. Topics gemäß Guide abonnieren

---

### 3. **hookii-rest-collection.postman_collection.json**
REST Client Collection (Postman/Insomnia/Thunder Client kompatibel):
- ✓ Login (Production nur)
- ✓ Mower Commands (Start, Pause, Return, Stop)
- ✓ Schedule Management
- ✓ Camera & Recovery Operations
- ✓ Alle Headers bereits vorkonfiguriert
- ✓ Variablen für JWT Token

**Wie verwenden**:
1. REST Client öffnen (z.B. Postman: https://www.postman.com/downloads/)
2. Datei importieren: File → Import → diese JSON
3. Variablen anpassen:
   - `{{jwt_token}}` wird durch Login-Response ersetzt
   - `HKX1EB100JD25010115` durch Mower-Serial ersetzen
4. Requests ausführen

---

### 4. **test-api.sh**
Bash-Script für Linux/macOS:
- ✓ Vollständige REST API Testsequenz (Production)
- ✓ Login → JWT Extraktion
- ✓ Command-Ausführung
- ✓ Schedule-Schreiben
- ✓ Image-Capture
- ✓ Ausgabe mit `jq` formatiert

**Wie verwenden**:
```bash
# 1. Script editierbar machen
chmod +x test-api.sh

# 2. Konfiguration am Top des Scripts anpassen
nano test-api.sh

# 3. Ausführen
./test-api.sh
```

Benötigte Tools: `curl`, `jq`
```bash
# Installation (Ubuntu/Debian):
sudo apt-get install curl jq

# Installation (macOS):
brew install curl jq
```

---

### 5. **test-api.ps1**
PowerShell-Script für Windows:
- ✓ Vollständige REST API Testsequenz (Production)
- ✓ Strukturierte Funktionen
- ✓ Fehlerbehandlung
- ✓ Farbige Konsolenausgabe
- ✓ Alle API-Operationen included

**Wie verwenden**:
```powershell
# 1. PowerShell öffnen (als Admin)

# 2. Execution Policy setzen (falls nötig):
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 3. Zum Script-Verzeichnis navigieren:
cd C:\Users\admin\OneDrive\Development\hookii-bridge-ha-addon

# 4. Konfiguration anpassen:
# - $Email setzen
# - $Password setzen
# - $MowerSerial setzen

# 5. Ausführen:
.\test-api.ps1
```

---

## 🔑 Wichtige Informationen (Quick Reference)

### Hookii Production Cloud Endpoint
| Komponente | Host | Port | Zweck |
|-----------|------|------|--------|
| **REST API** | iot.hookii.com | 10443 | Commands & Operations |
| **MQTT** | iot.hookii.com | 8883 | Live Telemetrie |

### MQTT Cloud Broker Credentials
- **Username**: `hookii-iot` (shared)
- **Password**: `CaV4C4qHBQxwWI#GomA2zuI&D#MxyaMF` (shared, Production)
- **Protocol**: MQTT over SSL/TLS

### Wichtige REST Endpoints
| Funktion | Method | Endpoint | 
|----------|--------|----------|
| Login | POST | /api/v1/user/login/email |
| Start/Stop | POST | /api/v1/mower/cmd/start/stop/job |
| Schedule | POST | /api/v1/mower/cmd/calendar/time |
| Parameter | POST | /api/v1/mower/cmd/calendar/param |
| Image | POST | /api/v1/mower/capture/image |
| Alarm | POST | /api/v1/mower/remote/recovery/alarm |

### Wichtige MQTT Topics (Cloud)
```
Empfangen:  hk/server/mower/push/0002/<SERIAL>  (Telemetrie vom Mower)
Heartbeat:  hk/app/mower/hb/0002/<SERIAL>       (Keep-Alive Signals)
```
