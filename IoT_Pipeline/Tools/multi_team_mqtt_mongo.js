#!/usr/bin/env node
/**
 * Multi-Team MQTT to MongoDB Bridge
 * 
 * Listens to team-specific topics (e.g., "team01", "team02")
 * Parses complete JSON messages with all sensor data
 * Automatically stores to corresponding MongoDB database (workshop_teamXX)
 * 
 * Students send complete JSON objects to their team topic:
 * Topic: "team01"
 * Message: {"temperature": 22.5, "humidity": 45.0, "light": 850}
 */

// ============================================================================
// CONFIGURATION
// ============================================================================

// MQTT Broker Configuration
const MQTT_BROKER = 'mqtt://automaatio:Z0od2PZF65jbtcXu@automaatio.cloud.shiftr.io';
const MQTT_USER = '';  // Leave empty if credentials are in URL
const MQTT_PASSWORD = '';

// MongoDB Atlas Configuration
// Replace with your actual MongoDB Atlas connection string
const MONGODB_URI = "mongodb+srv://thai-test:1928@cluster0.inpz4xy.mongodb.net/?appName=Cluster0"; 

// Team Configuration - Maps MQTT topics to MongoDB databases
const TEAM_CONFIG = {
  'team01': { database: 'workshop_team01', collection: 'sensor_data' },
  'team02': { database: 'workshop_team02', collection: 'sensor_data' },
  'team03': { database: 'workshop_team03', collection: 'sensor_data' },
  'team04': { database: 'workshop_team04', collection: 'sensor_data' },
  'team05': { database: 'workshop_team05', collection: 'sensor_data' },
  'team06': { database: 'workshop_team06', collection: 'sensor_data' },
  'team07': { database: 'workshop_team07', collection: 'sensor_data' },
  'team08': { database: 'workshop_team08', collection: 'sensor_data' },
  'team09': { database: 'workshop_team09', collection: 'sensor_data' },
  'team10': { database: 'workshop_team10', collection: 'sensor_data' }
};

// ============================================================================
// DEPENDENCIES
// ============================================================================

const mqtt = require('mqtt');
const { MongoClient, ServerApiVersion } = require('mongodb');

// ============================================================================
// MONGODB CONNECTION
// ============================================================================

// Create MongoDB client with connection pooling
const mongoClient = new MongoClient(MONGODB_URI, {
  serverApi: {
    version: ServerApiVersion.v1,
    strict: true,
    deprecationErrors: true,
  },
  maxPoolSize: 50,  // Support concurrent writes from multiple teams
  minPoolSize: 10
});

// Connect to MongoDB
async function connectMongoDB() {
  try {
    await mongoClient.connect();
    await mongoClient.db("admin").command({ ping: 1 });
    console.log("✓ Connected to MongoDB Atlas");
    return true;
  } catch (error) {
    console.error("✗ MongoDB connection failed:", error.message);
    process.exit(1);
  }
}

// ============================================================================
// MQTT CONNECTION
// ============================================================================

// Connect to MQTT broker
const mqttClient = mqtt.connect(MQTT_BROKER, {
  username: MQTT_USER,
  password: MQTT_PASSWORD,
  clientId: 'multi-team-bridge-' + Math.random().toString(16).substr(2, 8),
  clean: true,
  reconnectPeriod: 5000
});

// MQTT connection event handlers
mqttClient.on('connect', function() {
  console.log('✓ Connected to MQTT broker');
  
  // Subscribe to each team's main topic (not subtopics)
  Object.keys(TEAM_CONFIG).forEach(team => {
    const topic = team;  // Just the team name: "team01", "team02", etc.
    mqttClient.subscribe(topic, function(err) {
      if (err) {
        console.error(`✗ Failed to subscribe to ${topic}:`, err.message);
      } else {
        console.log(`✓ Subscribed to topic: ${topic}`);
      }
    });
  });
  
  console.log('\n✓ Bridge is running. Waiting for messages...\n');
  console.log('Teams publish complete JSON to their topic:');
  console.log('  Example: team01 → {"temperature": 22.5, "humidity": 45}');
  console.log();
});

mqttClient.on('error', function(error) {
  console.error('✗ MQTT connection error:', error.message);
});

mqttClient.on('reconnect', function() {
  console.log('⚠ Reconnecting to MQTT broker...');
});

mqttClient.on('offline', function() {
  console.log('⚠ MQTT client is offline');
});

// ============================================================================
// MESSAGE PROCESSING
// ============================================================================

/**
 * Extract team name from MQTT topic
 * Since topic IS the team name (e.g., "team01"), just return it directly
 */
function extractTeamFromTopic(topic) {
  // Topic is just "team01", "team02", etc.
  return topic.trim();
}

/**
 * Validate incoming sensor data
 */
function validateSensorData(data) {
  // Basic validation - ensure it's an object
  if (typeof data !== 'object' || data === null) {
    return { valid: false, error: 'Data must be a JSON object' };
  }
  
  // Ensure it's not an empty object
  if (Object.keys(data).length === 0) {
    return { 
      valid: false, 
      error: 'Data object cannot be empty' 
    };
  }
  
  // Accept any JSON object with sensor data
  // Students can include any key-value pairs they want
  return { valid: true };
}

/**
 * Add timestamp to the data
 * 
 * For TimeSeries collections, the timestamp MUST be a BSON Date object,
 * not a string. MongoDB will reject ISO string timestamps.
 */
function addTimestamp(data) {
  // CRITICAL: TimeSeries requires a Date object, not a string!
  data.timestamp = new Date();  // BSON Date object
  
  // Also add human-readable format for convenience (as string)
  data.timestamp_readable = timeConverter(Date.now());
  
  return data;
}

/**
 * Convert Unix timestamp to human-readable format
 */
function timeConverter(unixTimestamp) {
  const date = new Date(unixTimestamp);
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  
  const year = date.getFullYear();
  const month = months[date.getMonth()];
  const day = date.getDate();
  const hour = String(date.getHours()).padStart(2, '0');
  const min = String(date.getMinutes()).padStart(2, '0');
  const sec = String(date.getSeconds()).padStart(2, '0');
  
  return `${day} ${month} ${year} ${hour}:${min}:${sec}`;
}

/**
 * Save sensor data to MongoDB
 */
async function saveSensorData(teamName, topic, data) {
  try {
    // Get team configuration
    const teamConfig = TEAM_CONFIG[teamName];
    
    if (!teamConfig) {
      console.error(`✗ Unknown team: ${teamName}`);
      return false;
    }
    
    // Get database and collection references
    const database = mongoClient.db(teamConfig.database);
    const collection = database.collection(teamConfig.collection);
    
    // Add metadata to the sensor data
    data.topic = topic;        // Store which topic this came from
    data.team = teamName;      // Store team identifier
    
    // The complete JSON object (with all sensor readings) is now stored
    // Students' sensor data keys are preserved exactly as sent
    const result = await collection.insertOne(data);
    
    // Extract sensor names for logging (exclude metadata fields)
    const sensorKeys = Object.keys(data).filter(k => 
      !['timestamp', 'timestamp_readable', 'topic', 'team'].includes(k)
    );
    
    // Log success with sensor information
    console.log(
      `✓ [${teamName}] Stored sensor data`,
      `| Sensors: ${sensorKeys.join(', ')}`,
      `| MongoDB ID: ${result.insertedId}`
    );
    
    return true;
    
  } catch (error) {
    console.error(`✗ [${teamName}] MongoDB error:`, error.message);
    return false;
  }
}

// ============================================================================
// MQTT MESSAGE HANDLER
// ============================================================================

mqttClient.on('message', async function(topic, message) {
  try {
    // Topic IS the team name (e.g., "team01")
    const teamName = extractTeamFromTopic(topic);
    
    // Verify this is a configured team
    if (!TEAM_CONFIG[teamName]) {
      console.error(`✗ Received message for unknown team: ${teamName}`);
      return;
    }
    
    // Parse the complete JSON message
    let sensorData;
    try {
      const messageStr = message.toString('utf8');
      sensorData = JSON.parse(messageStr);
    } catch (parseError) {
      console.error(`✗ [${teamName}] JSON parse error:`, parseError.message);
      console.error(`   Raw message: ${message.toString('utf8')}`);
      return;
    }
    
    // Validate the parsed JSON
    const validation = validateSensorData(sensorData);
    if (!validation.valid) {
      console.error(`✗ [${teamName}] Invalid data:`, validation.error);
      console.error(`   Data received:`, sensorData);
      return;
    }
    
    // Add timestamp to the complete sensor data object
    sensorData = addTimestamp(sensorData);
    
    // Log received data
    console.log(`\n📨 [${teamName}] Received sensor data from topic: ${topic}`);
    console.log('   Data:', JSON.stringify(sensorData, null, 2));
    
    // Store the complete JSON object in MongoDB
    await saveSensorData(teamName, topic, sensorData);
    
  } catch (error) {
    console.error('✗ Unexpected error processing message:', error.message);
    console.error('   Topic:', topic);
    console.error('   Message:', message.toString('utf8'));
  }
});

// ============================================================================
// GRACEFUL SHUTDOWN
// ============================================================================

function gracefulShutdown(signal) {
  console.log(`\n⚠ Received ${signal}, shutting down gracefully...`);
  
  // Unsubscribe from all topics
  mqttClient.unsubscribe('#', function() {
    // Disconnect MQTT
    mqttClient.end(false, function() {
      console.log('✓ MQTT connection closed');
      
      // Close MongoDB connection
      mongoClient.close().then(() => {
        console.log('✓ MongoDB connection closed');
        console.log('✓ Shutdown complete');
        process.exit(0);
      });
    });
  });
  
  // Force exit after 5 seconds if graceful shutdown fails
  setTimeout(() => {
    console.error('⚠ Forced shutdown after timeout');
    process.exit(1);
  }, 5000);
}

// Handle shutdown signals
process.on('SIGINT', () => gracefulShutdown('SIGINT'));
process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('✗ Uncaught Exception:', error);
  gracefulShutdown('uncaughtException');
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('✗ Unhandled Rejection at:', promise, 'reason:', reason);
});

// ============================================================================
// START THE BRIDGE
// ============================================================================

async function startBridge() {
  console.log('='.repeat(60));
  console.log('Multi-Team MQTT to MongoDB Bridge');
  console.log('='.repeat(60));
  console.log(`Teams configured: ${Object.keys(TEAM_CONFIG).length}`);
  console.log(`Teams: ${Object.keys(TEAM_CONFIG).join(', ')}`);
  console.log('='.repeat(60));
  console.log();
  
  // Connect to MongoDB first
  await connectMongoDB();
  
  // MQTT connection is handled by the mqtt.connect() call above
  // Event handlers will manage the connection lifecycle
}

// Start the bridge
startBridge().catch(error => {
  console.error('✗ Failed to start bridge:', error);
  process.exit(1);
});