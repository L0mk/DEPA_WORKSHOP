#include <Arduino.h>
#include <ArduinoJson.h>
#include <PubSubClient.h>
#include <WiFi.h>
#include <string.h>

// Include sensor libraries that you need! A temperature sensor works as an example, remove it if you don’t use it
#include <DHT.h>

// WiFi credentials
const char *ssid = "";
const char *password = "";

// --- MQTT Broker ---
const char *mqtt_server = ""; // Address of broker
const int mqtt_port = 1883;   // Broker port
const char *mqtt_user = "";
const char *mqtt_pass = "";
const char *topic = ""; // You will be given a topic name. This must match the given name!

// --- Clients ---
WiFiClient espClient;
PubSubClient mqttClient(espClient);

// --- Sensor, pin, etc. definitions ---
#define DHTPIN 5          // Physical pin on the ESP32, needs to match your setup
#define DHTTYPE DHT11     // We are using DHT in this course
DHT dht(DHTPIN, DHTTYPE); // Initiate class

// --- Sensor Functions ---

// Example function for DHT, add more sensors if you need. Check void loop() for how to use!
String ReadSensor1()
{
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  // Set both values to zero if the sensor is faulty
  if (isnan(h) || isnan(t))
  {
    h = 0;
    t = 0;
  }
  // Output contains both humidity and temperature values in JSON-compatible format
  String sensor1 = "H:" + String(h) + "," + "T:" + String(t);

  return sensor1;
}

// Other example functions, make sure you have the correct data type for the value you get back! int = whole number, float = decimals, etc.
// Make sure the functions in void loop() match this
// int ReadSensor2()
// {

// }

// float ReadSensor3()
// {

// }

// --- CONNECTION FUNCTIONS ---
void setup_wifi()
{
  WiFi.mode(WIFI_STA);
  Serial.println();
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  // Wait for connection with feedback
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(1000);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnect()
{
  // Loop until we're reconnected
  while (!mqttClient.connected())
  {
    Serial.print("Attempting MQTT connection...");

    // Attempt to connect
    if (mqttClient.connect("ESP32Client", mqtt_user, mqtt_pass))
    {
      Serial.println("connected!");
    }
    else
    {
      Serial.print("failed, reason=");
      Serial.print(mqttClient.state());
      Serial.println(", trying again in 3 seconds");
      delay(3000);
    }
  }
}

// --- Publish Data ---
template <typename T> // Advanced template function that accepts any datatype
void publishData(const char *sensor_name, T sensor_value)
{
  // Create JSON document
  JsonDocument doc;

  // Add the sensor state to the JSON document
  doc["sensor_name"] = sensor_name;
  doc["sensor_value"] = sensor_value;

  // Create a buffer to hold the serialized JSON string
  char jsonBuffer[128];

  // Convert the JSON document to a string
  serializeJson(doc, jsonBuffer);

  // Publish the JSON string to the MQTT topic
  boolean success = mqttClient.publish(topic, jsonBuffer);

  // Print to Serial Monitor for debugging
  if (success)
  {
    Serial.print("Published JSON: ");
    Serial.println(jsonBuffer);
  }
  else
  {
    Serial.println("✗ Failed to publish message!");
    Serial.print("Client state: ");
    Serial.println(mqttClient.state());
  }
}

// --- MAIN PROGRAM ---

void setup()
{
  // Start Serial FIRST before anything else
  Serial.begin(19200); // Check that your terminal monitor matches this rate
  delay(1000);         // Give Serial time to initialize
  // Connect to WiFi
  setup_wifi();
  // Configure MQTT
  mqttClient.setServer(mqtt_server, mqtt_port);
  // Set a larger buffer size for PubSubClient if needed
  // Default is 256 bytes, increase if you have larger messages (More sensors)
  mqttClient.setBufferSize(512);
  Serial.println("Setup complete!");
}
void loop()
{
  // Ensure MQTT connection is maintained
  if (!mqttClient.connected())
  {
    Serial.println("MQTT disconnected! Reconnecting...");
    reconnect();
  }
  // Process incoming MQTT messages and maintain connection
  // This MUST be called regularly to keep the connection alive
  mqttClient.loop();
  String sensor_value = ReadSensor1();
  // Publish the sensor data via MQTT, you need to add a new one for each sensor! Remember to change the name of the sensor!
  publishData("dht_sensor", sensor_value);
  // Delay to avoid flooding the MQTT broker
  // DO NOT set this under 0.5 seconds
  delay(500);
}
