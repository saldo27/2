from cli import run_cli
import sys
from PySide6.QtWidgets import QApplication
from gui import MainWindow
from worker import Worker
from shift_scheduler import schedule_shifts, prepare_breakdown, export_breakdown

if __name__ == "__main__":
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    else:
        print("QApplication instance already exists.")

    # User input for the required parameters
    work_periods = input("Enter work periods (e.g., 01/10/2024-31/10/2024, separated by commas): ").split(',')
    holidays = input("Enter holidays (e.g., 09/10/2024, separated by commas): ").split(',')
    jobs_per_day = int(input("Enter number of jobs per day: "))
    min_distance = int(input("Enter minimum distance between work shifts (in days): "))
    max_shifts_per_week = int(input("Enter maximum shifts that can be assigned per week: "))
    num_workers = int(input("Enter number of available workers: "))

    # Create workers list from user input
    workers = [
        Worker(
            identification=f"W{i+1}",
            work_dates=["01/10/2024-10/10/2024", "20/10/2024-31/10/2024"],  # Example dates
            percentage=100.0,
            group='1',
            group_incompatibility=[],
            obligatory_coverage=[],
            unavailable_dates=[]
        )
        for i in range(num_workers)
    ]
schedule = schedule_shifts(work_periods, holidays, workers, min_distance, max_shifts_per_week, jobs_per_day)

app = QApplication(sys.argv)
window = MainWindow(work_periods, holidays, workers, min_distance, max_shifts_per_week, jobs_per_day)
window.show()
sys.exit(app.exec())
