from models import Worker, Shift
from scheduler import Scheduler
from utils import input_date, input_percentage

def main():
    # Input date range
    start_date = input_date("Enter the start date (DD/MM/YY): ")
    end_date = input_date("Enter the end date (DD/MM/YY): ")
    
    # Input holidays
    holidays = []
    while True:
        holiday = input("Enter a holiday date (DD/MM/YY) or leave blank to finish: ")
        if holiday == "":
            break
        holidays.append(input_date(holiday))
    
    # Input jobs
    jobs = []
    while True:
        job = input("Enter a job (A, B, C, ...) or leave blank to finish: ")
        if job == "":
            break
        jobs.append(job)
    
    # Input workers
    workers = []
    num_workers = int(input("Enter the number of workers: "))
    for _ in range(num_workers):
        id = input("Enter worker ID: ")
        work_dates = input("Enter work dates (DD/MM/YY-DD/MM/YY,...) or leave blank for full period: ")
        percentage = input_percentage("Enter percentage of working day: ")
        group = int(input("Enter worker group: "))
        incompatible_job = input("Enter incompatible job (A, B, C, ...) or leave blank: ")
        group_incompatibility = input("Enter group incompatibility: ")
        obligatory_coverage = input("Enter obligatory coverage date (DD/MM/YY) or leave blank: ")
        day_off = input("Enter day off date (DD/MM/YY) or leave blank: ")
        
        worker = Worker(id, work_dates, percentage, group, incompatible_job, group_incompatibility, obligatory_coverage, day_off)
        workers.append(worker)
    
    # Initialize scheduler and distribute shifts
    scheduler = Scheduler(start_date, end_date, holidays, jobs, workers)
    shifts = scheduler.distribute_shifts()
    
    # Output shifts
    for shift in shifts:
        print(shift)

if __name__ == "__main__":
    main()
