#!/usr/bin/env node
/**
 * Test Script for Multi-Team MQTT Bridge
 * 
 * Sends test messages to all team topics to verify bridge is working
 */

const mqtt = require('mqtt');

// Configuration
const MQTT_BROKER = 'mqtt://automaatio:Z0od2PZF65jbtcXu@automaatio.cloud.shiftr.io';
const TEAMS = ['team01', 'team02', 'team03', 'team04', 'team05', 
               'team06', 'team07', 'team08', 'team09', 'team10'];

// Sample sensor data templates
const testData = [
  { temperature: 22.5, humidity: 45.2 },
  { temperature: 23.1, humidity: 48.5, light: 850 },
  { temperature: 21.8, humidity: 52.0, pressure: 1013.25 },
  { temperature: 24.3, humidity: 41.8, co2: 420 },
  { temperature: 20.5, humidity: 55.0, voltage: 3.28 }
];

console.log('='.repeat(60));
console.log('MQTT Bridge Test Script');
console.log('='.repeat(60));
console.log(`Testing ${TEAMS.length} teams...`);
console.log();

// Connect to MQTT
const client = mqtt.connect(MQTT_BROKER, {
  clientId: 'test-script-' + Math.random().toString(16).substr(2, 8)
});

client.on('connect', function() {
  console.log('✓ Connected to MQTT broker\n');
  
  // Send test message to each team
  TEAMS.forEach((team, index) => {
    const data = testData[index % testData.length];
    const message = JSON.stringify(data);
    const topic = team;
    
    setTimeout(() => {
      client.publish(topic, message);
      console.log(`✓ Sent to ${team}: ${message}`);
      
      // Disconnect after last message
      if (index === TEAMS.length - 1) {
        setTimeout(() => {
          console.log('\n✓ All test messages sent!');
          console.log('\nCheck bridge logs and MongoDB to verify data was saved.');
          client.end();
          process.exit(0);
        }, 1000);
      }
    }, index * 500);  // Stagger messages by 500ms
  });
});

client.on('error', function(error) {
  console.error('✗ MQTT error:', error.message);
  process.exit(1);
});

// Timeout after 30 seconds
setTimeout(() => {
  console.error('✗ Test timeout - check MQTT connection');
  process.exit(1);
}, 30000);