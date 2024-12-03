import curses
import subprocess
import re
import time
import matplotlib.pyplot as plt

CURRENT_REGEX = re.compile(r"([A-Za-z0-9_]+)_A current\(\d+\)=([\d.]+)A")
VOLT_REGEX = re.compile(r"([A-Za-z0-9_]+)_V volt\(\d+\)=([\d.]+)V")

def parse_pmic_output(output):
    currents = {}
    volts = {}
    output = re.sub(r"\s+", " ", output)  

    current_matches = CURRENT_REGEX.findall(output)
    volt_matches = VOLT_REGEX.findall(output)

    for name, value in current_matches:
        currents[name] = float(value)
    for name, value in volt_matches:
        volts[name] = float(value)

    return currents, volts

def calculate_power(currents, volts):
    return {
        component: current * volts[component]
        for component, current in currents.items() if component in volts
    }

def calculate_metrics(data):
    if not data:
        return {}

    total_power = [sum(entry[1].values()) for entry in data]
    timestamps = [entry[0] for entry in data]

    metrics = {
        "min_power": min(total_power),
        "max_power": max(total_power),
        "avg_power": sum(total_power) / len(total_power),
        "total_energy": sum(total_power[i] * (timestamps[i] - timestamps[i - 1])
                            for i in range(1, len(timestamps))),
        "peak_timestamp": timestamps[total_power.index(max(total_power))],
        "most_consuming_component": max(data[-1][1], key=data[-1][1].get),
        "component_power": data[-1][1],
    }

    return metrics

def measure_consumption(duration, interval=1):
    data = []
    start_time = time.time()
    while time.time() - start_time < duration:
        output = subprocess.getoutput("vcgencmd pmic_read_adc")
        currents, volts = parse_pmic_output(output)
        power = calculate_power(currents, volts)
        data.append((time.time() - start_time, power))
        time.sleep(interval) 
    return data

def display_terminal_interface(data):
    metrics = calculate_metrics(data)

    def draw(screen):
     
        curses.start_color()
        curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Highlight
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Bar
        curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)  # Title
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)  # Warning

        max_height, max_width = screen.getmaxyx()

        while True:
            screen.clear()
            if not data:
                screen.addstr(0, 0, "No data available.", curses.color_pair(4))
                screen.refresh()
                time.sleep(1)
                continue

            title = "Power Consumption Metrics and Graph"
            screen.addstr(0, (max_width - len(title)) // 2, title, curses.color_pair(3))

            row = 2
            screen.addstr(row, 2, f"Minimum Power: {metrics['min_power']:.6f} W", curses.color_pair(1))
            screen.addstr(row + 1, 2, f"Maximum Power: {metrics['max_power']:.6f} W", curses.color_pair(1))
            screen.addstr(row + 2, 2, f"Average Power: {metrics['avg_power']:.6f} W", curses.color_pair(1))
            screen.addstr(row + 3, 2, f"Total Energy: {metrics['total_energy']:.6f} J", curses.color_pair(1))
            screen.addstr(row + 4, 2, f"Peak Power at: {metrics['peak_timestamp']:.2f} s", curses.color_pair(1))
            screen.addstr(row + 5, 2, f"Most Consuming Component: {metrics['most_consuming_component']}", curses.color_pair(1))

            row += 7
            for component, value in metrics["component_power"].items():
                screen.addstr(row, 2, f"{component}:", curses.color_pair(1))
                screen.addstr(row, 20, f"{value:.6f} W", curses.color_pair(2))
                row += 1

            chart_start = row + 2
            total_power = [sum(entry[1].values()) for entry in data]
            max_power = max(total_power) if total_power else 1
            bar_width = max(1, max_width // len(total_power))

            for idx, power in enumerate(total_power):
                bar_height = int((power / max_power) * (max_height - chart_start - 2))
                x_start = idx * bar_width
                for y in range(max_height - 2, max_height - 2 - bar_height, -1):
                    try:
                        screen.addstr(y, x_start, "█" * bar_width, curses.color_pair(2))
                    except curses.error:
                        pass

            screen.addstr(max_height - 3, 0, f"Max Power: {max_power:.2f} W", curses.color_pair(3))
            instruction = "Press 'q' to return to the menu."
            screen.addstr(max_height - 1, (max_width - len(instruction)) // 2, instruction, curses.color_pair(3))
            screen.refresh()

            key = screen.getch()
            if key == ord('q'):
                break

    curses.wrapper(draw)
def export_plot(data, filename="power_consumption.png"):
    if not data:
        print("No data available to export.")
        return

    metrics = calculate_metrics(data)
    timestamps = [entry[0] for entry in data]
    total_power = [sum(entry[1].values()) for entry in data]
    components = data[-1][1].keys()

    plt.figure(figsize=(12, 8))

    plt.plot(timestamps, total_power, label="Total Power", color="blue", linewidth=2)

    for component in components:
        component_power = [entry[1].get(component, 0) for entry in data]
        plt.plot(timestamps, component_power, label=f"{component} Power", linestyle="--", alpha=0.7)

    plt.xlabel("Time (s)", fontsize=12)
    plt.ylabel("Power Consumption (W)", fontsize=12)
    plt.title("Power Consumption Over Time", fontsize=16)
    plt.legend()

    metrics_text = (
        f"Minimum Power: {metrics['min_power']:.2f} W\n"
        f"Maximum Power: {metrics['max_power']:.2f} W\n"
        f"Average Power: {metrics['avg_power']:.2f} W\n"
        f"Total Energy: {metrics['total_energy']:.2f} J\n"
        f"Peak Power at: {metrics['peak_timestamp']:.2f} s\n"
        f"Most Consuming Component: {metrics['most_consuming_component']}"
    )
    plt.gcf().text(0.7, 0.5, metrics_text, fontsize=10, bbox=dict(facecolor="white", alpha=0.8))

    plt.tight_layout()
    plt.savefig(filename)
    print(f"Plot exported to {filename}")


def main():
    duration = float(input("Enter measurement duration in seconds: "))
    sampling_interval = float(input("Enter sampling interval in seconds (default: 1): ") or 1)
    data = measure_consumption(duration, sampling_interval)

    while True:
        print("Options:")
        print("1. Show power consumption in terminal")
        print("2. Export power consumption plot")
        print("3. Exit")
        choice = input("Enter your choice: ")
        if choice == "1":
            display_terminal_interface(data)
        elif choice == "2":
            filename = input("Enter filename for export (default: power_consumption.png): ")
            filename = filename.strip() or "power_consumption.png"
            export_plot(data, filename)
        elif choice == "3":
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
