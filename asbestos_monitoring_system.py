import datetime
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import pandas as pd

class AsbestosMonitoringSystem:
    def __init__(self):
        self.db_connection = sqlite3.connect('asbestos_monitoring.db')
        self.setup_database()
        self.readings = [0]  # Initialize with a zero reading
        self.timestamps = [0]  # Initialize with a zero timestamp
        
        # Setup plot
        plt.style.use('bmh')
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.line, = self.ax.plot(self.timestamps, self.readings, 'b-', linewidth=2, label='Asbestos Concentration')
        
        # Plot settings
        self.ax.set_xlabel('Time (seconds)')
        self.ax.set_ylabel('Concentration (f/cc)')
        self.ax.set_title('Real-time Asbestos Monitoring')
        self.ax.grid(True)
        
        # Add risk level lines
        self.ax.axhline(y=0.01, color='yellow', linestyle='--', linewidth=2, label='Medium Risk Threshold')
        self.ax.axhline(y=0.1, color='red', linestyle='--', linewidth=2, label='High Risk Threshold')
        self.ax.legend()
        
        # Set initial plot limits
        self.ax.set_ylim(0, 0.15)
        self.ax.set_xlim(0, 60)

    def setup_database(self):
        cursor = self.db_connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS asbestos_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                location TEXT,
                concentration FLOAT,
                risk_level TEXT
            )
        ''')
        self.db_connection.commit()

    def calculate_risk_level(self, concentration):
        if concentration < 0.01:
            return "Low"
        elif concentration < 0.1:
            return "Medium"
        else:
            return "High"

    def update_plot(self, frame):
        # Update x-axis limits to show last 60 seconds
        if len(self.timestamps) > 1:
            current_time = (self.timestamps[-1] - self.timestamps[1]).total_seconds()
            self.ax.set_xlim(max(0, current_time - 60), current_time + 5)
            
            # Convert timestamps to seconds from start
            plot_times = [(t - self.timestamps[1]).total_seconds() for t in self.timestamps[1:]]
            self.line.set_data(plot_times, self.readings[1:])
            
            # Update y-axis limit if needed
            current_max = max(self.readings)
            if current_max > self.ax.get_ylim()[1]:
                self.ax.set_ylim(0, current_max * 1.1)
        
        return self.line,

    def export_to_csv(self, location):
        df = pd.DataFrame({
            'Timestamp': self.timestamps[1:],  # Skip the initial zero
            'Location': [location] * (len(self.timestamps) - 1),
            'Concentration': self.readings[1:],  # Skip the initial zero
            'Risk_Level': [self.calculate_risk_level(c) for c in self.readings[1:]]
        })
        filename = f'asbestos_readings_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        df.to_csv(filename, index=False)
        return filename

    def real_time_monitoring(self, location, duration_minutes=60):
        print(f"\nStarting real-time monitoring at {location}")
        print("Press Ctrl+C to stop monitoring\n")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        # Setup animation with a fixed frame count
        frame_count = int(duration_minutes * 60 / 5)  # One frame every 5 seconds
        self.ani = FuncAnimation(
            self.fig, 
            self.update_plot,
            frames=frame_count,
            interval=5000,  # 5000ms = 5s
            blit=True,
            cache_frame_data=False
        )
        
        plt.show(block=False)
        plt.pause(0.1)  # Small pause to let the window open
        
        try:
            while time.time() < end_time:
                # Simulate sensor reading
                concentration = np.random.uniform(0, 0.2)
                risk_level = self.calculate_risk_level(concentration)
                current_time = datetime.datetime.now()
                
                # Store readings for plotting
                self.readings.append(concentration)
                self.timestamps.append(current_time)
                
                # Record in database
                cursor = self.db_connection.cursor()
                cursor.execute('''
                    INSERT INTO asbestos_readings 
                    (timestamp, location, concentration, risk_level)
                    VALUES (?, ?, ?, ?)
                ''', (
                    current_time,
                    location,
                    concentration,
                    risk_level
                ))
                self.db_connection.commit()
                
                # Display current reading
                print(f"Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Location: {location}")
                print(f"Concentration: {concentration:.4f} f/cc")
                print(f"Risk Level: {risk_level}")
                if risk_level == "High":
                    print("⚠ WARNING: High Risk Level Detected!")
                print("-" * 50)
                
                # Update plot
                plt.pause(5)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
        except Exception as e:
            print(f"\nError during monitoring: {str(e)}")
        finally:
            # Export data to CSV
            if len(self.readings) > 1:  # Only export if we have readings
                csv_file = self.export_to_csv(location)
                print(f"\nData exported to {csv_file}")
            
            self.db_connection.close()
            print("\nMonitoring session ended")
            plt.close()

def main():
    # Create system instance
    system = AsbestosMonitoringSystem()
    
    # Get location from user
    location = input("Enter monitoring location: ")
    
    # Get duration from user
    try:
        duration = int(input("Enter monitoring duration in minutes (default 60): ") or "60")
    except ValueError:
        duration = 60
        print("Invalid duration. Using default 60 minutes.")
    
    # Start monitoring
    system.real_time_monitoring(location, duration)

if __name__ == "__main__":
    main() 
