# Complete Data Flow - MQTT to MongoDB

## Overview

**Simple concept:** Students send complete JSON sensor data to their team topic. Bridge receives it, adds timestamp, and stores the entire object in MongoDB.

---

## Complete Data Flow

### **Step 1: ESP32 Publishes**

**Student code:**

```cpp
String message = "{\"temperature\":22.5,\"humidity\":45.0,\"light\":850}";
client.publish("team01", message);
```

**What's sent:**

- **Topic:** `team01`
- **Message:** `{"temperature":22.5,"humidity":45.0,"light":850}`

---

### **Step 2: MQTT Broker Routes**

Shiftr.io receives the message and routes to all subscribers of `team01` topic.

The bridge is subscribed to:

- `team01`
- `team02`
- `team03`
- ... up to `team10`

---

### **Step 3: Bridge Receives and Processes**

**Bridge receives:**

```
Topic: team01
Message: {"temperature":22.5,"humidity":45.0,"light":850}
```

**Bridge processing:**

1. Identifies team from topic: `team01`
2. Parses JSON: Extracts all key-value pairs
3. Validates: Ensures it's valid JSON with data
4. Adds timestamp: `"timestamp": "2025-01-15T10:30:45.123Z"`
5. Adds metadata: `"team": "team01"`, `"topic": "team01"`
6. Stores complete object in MongoDB

**Console output:**

```
[team01] Received sensor data from topic: team01
   Data: {
     "temperature": 22.5,
     "humidity": 45.0,
     "light": 850
   }
[team01] Stored sensor data | Sensors: temperature, humidity, light | MongoDB ID: 67abc123...
```

---

### **Step 4: MongoDB Storage**

**Database:** `workshop_team01`  
**Collection:** `sensor_data`

**Stored document:**

```json
{
  "_id": ObjectId("67abc123..."),
  "temperature": 22.5,
  "humidity": 45.0,
  "light": 850,
  "timestamp": "2025-01-15T10:30:45.123Z",
  "timestamp_readable": "15 Jan 2025 10:30:45",
  "topic": "team01",
  "team": "team01"
}
```

**Key points:**

- All sensor data preserved exactly as sent
- Additional metadata added by bridge (timestamp, team, topic)
- Each message = one MongoDB document
- Students' key names are preserved

---

## What Gets Stored

### **Student sends:**

```json
{
  "temperature": 22.5,
  "humidity": 45.0,
  "light": 850
}
```

### **Bridge adds:**

```json
{
  "timestamp": "2025-01-15T10:30:45.123Z",
  "timestamp_readable": "15 Jan 2025 10:30:45",
  "topic": "team01",
  "team": "team01"
}
```

### **Final stored document:**

```json
{
  "temperature": 22.5,
  "humidity": 45.0,
  "light": 850,
  "timestamp": "2025-01-15T10:30:45.123Z",
  "timestamp_readable": "15 Jan 2025 10:30:45",
  "topic": "team01",
  "team": "team01"
}
```

---

## Key Features

### **1. Complete JSON Parsing**

Bridge parses the entire JSON object and stores all key-value pairs exactly as sent.

**Example - Complex sensor data:**

```json
{
  "temp_c": 22.5,
  "temp_f": 72.5,
  "humidity": 45.0,
  "pressure": 1013.25,
  "light_lux": 850,
  "motion": 1,
  "door_open": false,
  "battery_voltage": 3.28,
  "rssi": -45
}
```

All of this gets stored as one document. Students can include as many sensors as they want.

---

### **2. Automatic Timestamps**

Bridge adds ISO 8601 timestamps for:

- Sorting by time
- Filtering by date range
- Time-series analysis

```json
{
  "timestamp": "2025-01-15T10:30:45.123Z", // For queries
  "timestamp_readable": "15 Jan 2025 10:30:45" // For humans
}
```

---

### **3. Team Isolation**

Each team's data goes to their own database:

```
team01 → workshop_team01/sensor_data
team02 → workshop_team02/sensor_data
team03 → workshop_team03/sensor_data
...
team10 → workshop_team10/sensor_data
```

Teams should not see or modify each other's data.

---

### **4. Metadata Tracking**

Bridge adds metadata for troubleshooting:

```json
{
  "topic": "team01", // Which topic message came from
  "team": "team01" // Which team owns this data
}
```

Useful for:

- Debugging which team sent what
- Filtering data by team
- Verifying correct routing

---

## Example: Multiple Sensor Types

### **Scenario: Team has 3 different sensor setups**

**ESP32 #1 (Weather station):**

```json
{
  "temperature": 22.5,
  "humidity": 45.0,
  "pressure": 1013.25
}
```

**ESP32 #2 (Light sensor):**

```json
{
  "light_level": 850,
  "uv_index": 3.2
}
```

**ESP32 #3 (Motion detector):**

```json
{
  "motion_detected": true,
  "last_motion": "2025-01-15T10:28:30Z"
}
```

**All three stored in same database (`workshop_team01`):**

The bridge doesn't care what sensors you have - it stores whatever JSON you send.

**MongoDB collection:**

```
Document 1: {temperature: 22.5, humidity: 45.0, pressure: 1013.25, timestamp: ...}
Document 2: {light_level: 850, uv_index: 3.2, timestamp: ...}
Document 3: {motion_detected: true, last_motion: "...", timestamp: ...}
```

Each document can have different fields.

---

## Querying the Data

### **Get latest reading:**

```javascript
db.sensor_data.find().sort({ timestamp: -1 }).limit(1);
```

### **Get all readings from last hour:**

```javascript
db.sensor_data.find({
  timestamp: { $gte: "2025-01-15T09:30:00Z" },
});
```

### **Get readings with specific sensor:**

```javascript
db.sensor_data.find({
  temperature: { $exists: true },
});
```

### **Average temperature:**

```javascript
db.sensor_data.aggregate([
  { $match: { temperature: { $exists: true } } },
  { $group: { _id: null, avgTemp: { $avg: "$temperature" } } },
]);
```

---

## Troubleshooting the Data Flow

### **Problem: Message sent but not in database**

**Check each step:**

**1. Did ESP32 publish successfully?**

```
Check Serial Monitor for:
✓ Published successfully!
```

**2. Did MQTT broker receive it?**

```
Check Shiftr.io web dashboard
Should see message in real-time
```

**3. Did bridge receive it?**

```
Check bridge logs for:
📨 [teamXX] Received sensor data from topic: teamXX
```

**4. Did bridge parse it?**

```
If JSON is malformed, you'll see:
✗ [teamXX] JSON parse error
```

**5. Did bridge store it?**

```
Check for:
✓ [teamXX] Stored sensor data | Sensors: ... | MongoDB ID: ...
```

**6. Is it in MongoDB?**

```
Query MongoDB:
db.sensor_data.find().sort({timestamp: -1}).limit(1)
```

---

### **Problem: Data is malformed in MongoDB**

**Cause:** Student sent malformed JSON

**Example wrong:**

```cpp
String msg = "{temp:22,hum:45}";  // Missing quotes on keys!
```

**Example correct:**

```cpp
String msg = "{\"temp\":22,\"hum\":45}";  // Proper JSON
```

**How to fix:**

1. Check bridge logs for parse errors
2. Look at the raw message in logs
3. Help student fix JSON formatting

---

### **Problem: Timestamp is wrong**

**Likely cause:** Server timezone issue

**Solution:** Bridge uses UTC (ISO 8601):

- All timestamps are in UTC
- Convert to local time when displaying
- This is correct behavior!

```javascript
// In queries, use UTC times
timestamp: {
  $gte: "2025-01-15T00:00:00Z";
} // Midnight UTC
```

---

## Best Practices

### **For Students:**

1. **Keep sensor names short and clear**

   ```json
   // ✅ Good
   {"temp":22.5, "hum":45, "light":850}

   // ❌ Too verbose
   {"temperature_in_celsius":22.5, "relative_humidity_percent":45}
   ```

2. **Use consistent naming**

   ```json
   // ✅ Consistent
   {"temp_c":22.5}  // Always use same key

   // ❌ Inconsistent
   {"temp":22.5}    // Sometimes "temp"
   {"temperature":22.5}  // Sometimes "temperature"
   ```

3. **Include units in key names if ambiguous**
   ```json
   { "temp_c": 22.5, "temp_f": 72.5, "distance_cm": 42.5 }
   ```

### **For Instructors:**

1. **Monitor bridge logs during workshop**

   - Catch JSON errors immediately
   - See which teams are active
   - Identify struggling teams quickly

2. **Set up MongoDB indexes**

   ```javascript
   // Index on timestamp for fast queries
   db.sensor_data.createIndex({ timestamp: -1 });

   // Index on team for filtering
   db.sensor_data.createIndex({ team: 1 });
   ```

3. **Regular data backups**
   ```bash
   # Backup all team data
   mongodump --uri="..." --out=./backup_$(date +%Y%m%d)
   ```




