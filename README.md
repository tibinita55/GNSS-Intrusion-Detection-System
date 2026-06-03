# GNSS-Intrusion-Detection-System
This repository contains the Python source code for a heuristic Intrusion Detection System designed to monitor Global Navigation Satellite Systems telemetry. The algorithm evaluates National Marine Electronics Association data streams to identify electronic warfare attacks such as radio frequency jamming and signal spoofing. The application was developed for maritime navigation security and tested using hardware-in-the-loop simulations with a commercial receiver and a software-defined radio.

Application workflow
Step 1: Initialization and baseline establishment. The script initializes an asynchronous graphical user interface using the Tkinter library. It begins parsing the incoming serial data from the receiver to establish a secure geographic baseline and record the initial internal system timestamp.

Step 2: Continuous telemetry parsing. The core loop extracts specific variables from the incoming sentences. It isolates the Carrier-to-Noise density ratio, the Speed Over Ground, the current latitude, the current longitude and the broadcasted satellite time.

Step 3: Deterministic threat evaluation. The algorithm processes the extracted parameters through mathematical reality checks. It evaluates sudden drops in signal strength to detect physical jamming. It calculates absolute spatial deviations to ensure the vessel trajectory does not exceed the 0.05-degree safety boundary. It also cross-references the broadcasted time against the isolated hardware clock of the Linux operating system to catch temporal desynchronization attempts that exceed the 48-hour tolerance.

Step 4: Alert generation. The global state machine transitions the interface to specific alert palettes if any parameter violates the defined thresholds. The script simultaneously triggers independent audio alarms using subprocess management to warn the crew of the exact attack vector without interrupting the data evaluation loop.
