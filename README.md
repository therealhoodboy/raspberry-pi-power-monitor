# Raspberry Pi Power Monitor

**Raspberry Pi Power Monitor** is a Python script designed to monitor, analyze, and visualize the power consumption of a Raspberry Pi in real-time. The script provides insightful metrics, terminal-based visualizations, and detailed power consumption charts exported as PNG diagrams.

## Features

- **Real-Time Monitoring**: Displays power consumption in the terminal with graphical and numerical outputs.
- **Metrics Calculation**:
  - Minimum, maximum, and average power consumption.
  - Total energy consumption (in Joules).
  - Timestamp of peak power usage.
  - Most power-consuming component.
- **Graphical Terminal Output**: Combines text and bar charts for a comprehensive real-time display.
- **Detailed Exported Charts**:
  - Line chart of total and component-specific power consumption.
  - Metrics annotation in the exported PNG diagram.

## Requirements

- Python 3.6+
- Dependencies:
  - `matplotlib`
  - `curses` (standard Python library)
- Raspberry Pi with the `vcgencmd` command available.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/therealhoodboy/raspberry-pi-power-monitor.git
   cd raspberry-pi-power-monitor
