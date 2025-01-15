#include <WebServer.h>
#include <WiFi.h>
#include <esp32cam.h>

const char* WIFI_SSID = "Sasthamkunnel";
const char* WIFI_PASS = "0NNUP0D@";

// const char* WIFI_SSID = "Sasthamkunnel";
// const char* WIFI_PASS = "0NNUP0D@";

// Pins for the ultrasonic sensor and buzzer
const int trigPin = 4;  // Trigger pin of ultrasonic sensor
const int echoPin = 2;  // Echo pin of ultrasonic sensor
const int buzzerPin = 15; // Pin for the buzzer

// Flash pin
const int flashPin = 4; // GPIO for the flash LED

// Initialize the web server on port 80
WebServer server(80);

// Define resolutions
static auto loRes = esp32cam::Resolution::find(320, 240);  // Low resolution
static auto midRes = esp32cam::Resolution::find(640, 480); // Medium resolution
static auto hiRes = esp32cam::Resolution::find(1024, 768); // High resolution

// Function to capture and serve a JPEG image
void serveJpg() {
  // Turn on the flash
  digitalWrite(flashPin, HIGH);
  delay(100); // Allow the flash to stabilize before capturing

  auto frame = esp32cam::capture();

  // Turn off the flash
  digitalWrite(flashPin, LOW);

  if (frame == nullptr) {
    Serial.println("CAPTURE FAIL");
    server.send(503, "text/plain", "Failed to capture image");
    return;
  }

  Serial.printf("Captured image: %dx%d (%d bytes)\n", frame->getWidth(), frame->getHeight(), frame->size());
  server.setContentLength(frame->size());
  server.send(200, "image/jpeg");

  WiFiClient client = server.client();
  frame->writeTo(client);
}

// Handler for different resolutions
void handleJpg(String resType) {
  if (resType == "lo" && !esp32cam::Camera.changeResolution(loRes)) {
    Serial.println("SET-LO-RES FAIL");
  } else if (resType == "mid" && !esp32cam::Camera.changeResolution(midRes)) {
    Serial.println("SET-MID-RES FAIL");
  } else if (resType == "hi" && !esp32cam::Camera.changeResolution(hiRes)) {
    Serial.println("SET-HI-RES FAIL");
  }
  serveJpg();
}

// Function to read distance from the ultrasonic sensor
float getDistance() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH);
  float distance = duration * 0.034 / 2; // Convert to cm
  return distance;
}

// Function to monitor distance and activate buzzer
void monitorDistance() {
  float distance = getDistance();
  if (distance > 0 && distance < 10) { // If object is closer than 10 cm
    digitalWrite(buzzerPin, HIGH);
  } else {
    digitalWrite(buzzerPin, LOW);
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println();

  // Camera configuration
  using namespace esp32cam;
  Config cfg;
  cfg.setPins(pins::AiThinker);
  cfg.setResolution(midRes);
  cfg.setBufferCount(2);
  cfg.setJpeg(80); // JPEG quality: 80%

  if (!Camera.begin(cfg)) {
    Serial.println("CAMERA FAIL");
    while (true); // Halt execution if camera initialization fails
  }
  Serial.println("CAMERA OK");

  // Connect to Wi-Fi
  WiFi.persistent(false);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("Connected to Wi-Fi. IP: ");
  Serial.println(WiFi.localIP());

  // Define server routes
  server.on("/cam-lo.jpg", []() { handleJpg("lo"); });
  server.on("/cam-mid.jpg", []() { handleJpg("mid"); });
  server.on("/cam-hi.jpg", []() { handleJpg("hi"); });

  // Start the server
  server.begin();
  Serial.println("Server started. Access URLs:");
  Serial.println("  /cam-lo.jpg");
  Serial.println("  /cam-mid.jpg");
  Serial.println("  /cam-hi.jpg");

  // Initialize pins for ultrasonic sensor, buzzer, and flash
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(buzzerPin, OUTPUT);
  pinMode(flashPin, OUTPUT);
  digitalWrite(buzzerPin, LOW);
  digitalWrite(flashPin, LOW);
}

void loop() {
  // Handle web server requests
  server.handleClient();

  // Monitor distance and trigger buzzer
  monitorDistance();
}


// #include <WebServer.h>
// #include <WiFi.h>
// #include <esp32cam.h>
 
// const char* WIFI_SSID = "Sasthamkunnel";
// const char* WIFI_PASS = "0NNUP0D@";
 
// // Initialize the web server on port 80
// WebServer server(80);

// // Define resolutions
// static auto loRes = esp32cam::Resolution::find(320, 240);  // Low resolution
// static auto midRes = esp32cam::Resolution::find(640, 480); // Medium resolution
// static auto hiRes = esp32cam::Resolution::find(1024, 768); // High resolution

// // Function to capture and serve a JPEG image
// void serveJpg() {
//   auto frame = esp32cam::capture();
//   if (frame == nullptr) {
//     Serial.println("CAPTURE FAIL");
//     server.send(503, "text/plain", "Failed to capture image");
//     return;
//   }

//   Serial.printf("Captured image: %dx%d (%d bytes)\n", frame->getWidth(), frame->getHeight(), frame->size());
//   server.setContentLength(frame->size());
//   server.send(200, "image/jpeg");

//   WiFiClient client = server.client();
//   frame->writeTo(client);
// }

// // Handler for different resolutions
// void handleJpg(String resType) {
//   if (resType == "lo" && !esp32cam::Camera.changeResolution(loRes)) {
//     Serial.println("SET-LO-RES FAIL");
//   } else if (resType == "mid" && !esp32cam::Camera.changeResolution(midRes)) {
//     Serial.println("SET-MID-RES FAIL");
//   } else if (resType == "hi" && !esp32cam::Camera.changeResolution(hiRes)) {
//     Serial.println("SET-HI-RES FAIL");
//   }
//   serveJpg();
// }

// void setup() {
//   Serial.begin(115200);
//   Serial.println();

//   // Camera configuration
//   using namespace esp32cam;
//   Config cfg;
//   cfg.setPins(pins::AiThinker);
//   cfg.setResolution(midRes);
//   cfg.setBufferCount(2);
//   cfg.setJpeg(80); // JPEG quality: 80%

//   if (!Camera.begin(cfg)) {
//     Serial.println("CAMERA FAIL");
//     while (true); // Halt execution if camera initialization fails
//   }
//   Serial.println("CAMERA OK");

//   // Connect to Wi-Fi
//   WiFi.persistent(false);
//   WiFi.mode(WIFI_STA);
//   WiFi.begin(WIFI_SSID, WIFI_PASS);
//   while (WiFi.status() != WL_CONNECTED) {
//     delay(500);
//     Serial.print(".");
//   }
//   Serial.println();
//   Serial.print("Connected to Wi-Fi. IP: ");
//   Serial.println(WiFi.localIP());

//   // Define server routes
//   server.on("/cam-lo.jpg", []() { handleJpg("lo"); });
//   server.on("/cam-mid.jpg", []() { handleJpg("mid"); });
//   server.on("/cam-hi.jpg", []() { handleJpg("hi"); });

//   // Start the server
//   server.begin();
//   Serial.println("Server started. Access URLs:");
//   Serial.println("  /cam-lo.jpg");
//   Serial.println("  /cam-mid.jpg");
//   Serial.println("  /cam-hi.jpg");
// }

// void loop() {
//   server.handleClient();
// }
