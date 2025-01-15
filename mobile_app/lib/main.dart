import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:audioplayers/audioplayers.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  runApp(IPCameraDescriberApp());
}

class IPCameraDescriberApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: IPDescribeScreen(),
    );
  }
}

class IPDescribeScreen extends StatefulWidget {
  @override
  _IPDescribeScreenState createState() => _IPDescribeScreenState();
}

class _IPDescribeScreenState extends State<IPDescribeScreen> {
  String description = '';
  String audioUrl = '';
  bool isLoading = false;
  bool isMonitoring = false;
  final AudioPlayer audioPlayer = AudioPlayer();
  String baseUrl = '';

  @override
  void initState() {
    super.initState();
    _loadBaseUrl();
  }

  Future<void> _loadBaseUrl() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    setState(() {
      baseUrl = prefs.getString('baseUrl') ?? '';
    });
  }

  Future<void> fetchDescriptionAndPlayAudio() async {
    if (baseUrl.isEmpty) {
      setState(() {
        description = "Base URL is not set. Please set it in the settings.";
      });
      return;
    }

    setState(() {
      isLoading = true;
      description = '';
      audioUrl = '';
    });

    try {
      final response = await http.get(Uri.parse("$baseUrl/describe-ip-camera/"));

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);

        await audioPlayer.stop();

        setState(() {
          description = data['description'];
          audioUrl = "$baseUrl${data['audio_url']}";
        });

        await audioPlayer.play(UrlSource(audioUrl));
      } else {
        setState(() {
          description = "Error: ${response.reasonPhrase}";
        });
      }
    } catch (e) {
      setState(() {
        description = "Error: $e";
      });
    } finally {
      setState(() {
        isLoading = false;
      });
    }
  }

  void startMonitoring() {
    setState(() {
      isMonitoring = true;
    });
    _monitorSurroundings();
  }

  void stopMonitoring() {
    setState(() {
      isMonitoring = false;
    });
    audioPlayer.stop();
  }

  Future<void> _monitorSurroundings() async {
    while (isMonitoring) {
      await fetchDescriptionAndPlayAudio();
      await audioPlayer.onPlayerComplete.first;
    }
  }

  void stopAudio() {
    audioPlayer.stop();
  }

  @override
  void dispose() {
    audioPlayer.dispose();
    super.dispose();
  }

  void _navigateToSettings() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => SettingsPage()),
    ).then((_) => _loadBaseUrl());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text("IP Camera Describer", style: TextStyle(fontSize: 24)),
            IconButton(
              icon: Icon(Icons.settings),
              onPressed: _navigateToSettings,
            ),
          ],
        ),
      ),
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              ElevatedButton(
                onPressed: isLoading ? null : fetchDescriptionAndPlayAudio,
                style: ElevatedButton.styleFrom(
                  padding: EdgeInsets.symmetric(horizontal: 70, vertical: 70),
                  backgroundColor: Colors.red,
                  foregroundColor: Colors.white,
                  shape: CircleBorder(),
                ),
                child: Icon(
                  Icons.mic,
                  size: 60,
                ),
              ),
              SizedBox(height: 40),
              ElevatedButton(
                onPressed: isMonitoring ? null : startMonitoring,
                style: ElevatedButton.styleFrom(
                  padding: EdgeInsets.symmetric(horizontal: 50, vertical: 30),
                  backgroundColor: Colors.green,
                ),
                child: Text(
                  "Start Monitoring",
                  style: TextStyle(fontSize: 22),
                ),
              ),
              SizedBox(height: 20),
              ElevatedButton(
                onPressed: isMonitoring ? stopMonitoring : null,
                style: ElevatedButton.styleFrom(
                  padding: EdgeInsets.symmetric(horizontal: 50, vertical: 30),
                  backgroundColor: Colors.grey,
                ),
                child: Text(
                  "Stop Monitoring",
                  style: TextStyle(fontSize: 22),
                ),
              ),
              SizedBox(height: 20),
              ElevatedButton(
                onPressed: stopAudio,
                style: ElevatedButton.styleFrom(
                  padding: EdgeInsets.symmetric(horizontal: 50, vertical: 30),
                  backgroundColor: Colors.blue,
                ),
                child: Text(
                  "Stop Audio",
                  style: TextStyle(fontSize: 22),
                ),
              ),
              SizedBox(height: 40),
              isLoading
                  ? CircularProgressIndicator()
                  : Text(
                      description.isNotEmpty
                          ? description
                          : "Press the button to describe the IP camera feed.",
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 20),
                    ),
            ],
          ),
        ),
      ),
    );
  }
}

class SettingsPage extends StatefulWidget {
  @override
  _SettingsPageState createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  TextEditingController baseUrlController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadBaseUrl();
  }

  Future<void> _loadBaseUrl() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    baseUrlController.text = prefs.getString('baseUrl') ?? '';
  }

  Future<void> _saveBaseUrl() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    await prefs.setString('baseUrl', baseUrlController.text.trim());
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text("Base URL saved successfully!")),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("Settings"),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            TextField(
              controller: baseUrlController,
              decoration: InputDecoration(
                labelText: "Base URL",
                hintText: "Enter the base URL of the server",
                border: OutlineInputBorder(),
              ),
            ),
            SizedBox(height: 20),
            ElevatedButton(
              onPressed: _saveBaseUrl,
              child: Text("Save Base URL"),
            ),
          ],
        ),
      ),
    );
  }
}
