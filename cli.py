from worker import Worker
from shift_scheduler import schedule_shifts
from datetime import datetime

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
