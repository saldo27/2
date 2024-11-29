from worker import Worker
from shift_scheduler import schedule_shifts
from datetime import datetime

if __name__ == "__main__":
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

def run_cli():
    print("Enter work periods (comma-separated, e.g., '01/10/2024-10/10/2024'): ")
    work_periods_input = input().split(',')
    work_periods = [period.strip() for period in work_periods_input]

    print("Enter festivos (comma-separated, e.g., '05/10/2024'): ")
    holidays = input().split(',')

    print("Enter number of jobs per day: ")
    jobs_per_day = int(input())

    print("Enter minimum distance between work shifts (in days): ")
    min_distance = int(input())

    print("Enter maximum shifts that can be assigned per week: ")
    max_shifts_per_week = int(input())

    print("Enter number of workers: ")
    num_workers = int(input())

    workers = []
    for _ in range(num_workers):
        workers.append(Worker.from_user_input())

    schedule = schedule_shifts(work_periods, holidays, workers, min_distance, max_shifts_per_week, jobs_per_day)
    
    print("Shifts scheduled successfully.")
    for job, shifts in schedule.items():
        print(f"Job {job}:")
        for date, worker in shifts.items():
            print(f"  {date}: {worker}")

if __name__ == "__main__":
    run_cli()
