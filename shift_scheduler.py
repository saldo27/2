import logging
logging.basicConfig(level=logging.DEBUG)
from datetime import timedelta, datetime
from collections import defaultdict
import csv

class Worker:
    def __init__(self, identification, work_dates=None, percentage=100.0, group='1', group_incompatibility=None, obligatory_coverage=None, unavailable_dates=None):
        self.identification = identification
        self.work_dates = work_dates if work_dates else []
        self.percentage_shifts = float(percentage) if percentage else 100.0
        self.group = group if group else '1'
        self.group_incompatibility = group_incompatibility if group_incompatibility else []
        self.obligatory_coverage = obligatory_coverage if obligatory_coverage else []
        self.unavailable_dates = unavailable_dates if unavailable_dates else []
def calculate_shift_quota(workers, total_days, jobs_per_day):
    total_percentage = sum(worker.percentage_shifts for worker in workers)
    total_shifts = total_days * jobs_per_day
    for worker in workers:
        worker.shift_quota = (worker.percentage_shifts / 100) * (total_days * jobs_per_day) / (total_percentage / 100)
        worker.weekly_shift_quota = worker.shift_quota / ((total_days // 7) + 1)

def generate_date_range(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def is_weekend(date):
    return date.weekday() >= 4

def is_holiday(date_str, holidays_set):
    if isinstance(date_str, str) and date_str:
        return date_str in holidays_set
    else:
        return False

def can_work_on_date(worker, date, last_shift_dates, weekend_tracker, holidays_set, weekly_tracker, job, job_count, min_distance, max_shifts_per_week, jobs, override=False, schedule=None, workers=None):
    if isinstance(date, str) and date:
        date = datetime.strptime(date.strip(), "%d/%m/%Y")

    if schedule and workers:
        for job_schedule in schedule.values():
            if date.strftime("%d/%m/%Y") in job_schedule:
                assigned_worker_id = job_schedule[date.strftime("%d/%m/%Y")]
                assigned_worker = next((w for w in workers if w.identification == assigned_worker_id), None)
                if assigned_worker:
                    logging.debug(f"Assigned worker {assigned_worker.identification} found for job on {date}")
                    if any(group == assigned_worker.group for group in worker.group_incompatibility):
                        logging.debug(f"Worker {worker.identification} cannot work on {date} due to group incompatibility with worker {assigned_worker.identification}.")
                        return False
  
    if date in [datetime.strptime(day.strip(), "%d/%m/%Y") for day in worker.unavailable_dates if day]:
        logging.debug(f"Worker {worker.identification} cannot work on {date} due to unavailability.")
        return False

    for start_date, end_date in worker.work_dates:
        if start_date <= date <= end_date:
            break
    else:
        logging.debug(f"Worker {worker.identification} cannot work on {date} because it is outside their working dates.")
        return False

    if not override:
        adjusted_min_distance = min_distance * worker.percentage_shifts / 100.0

        if last_shift_dates[worker.identification]:
            last_date = last_shift_dates[worker.identification][-1]
            days_diff = (date - last_date).days
            logging.debug(f"Worker {worker.identification} last worked on {last_date}, {days_diff} days ago.")
            if days_diff < adjusted_min_distance:
                logging.debug(f"Worker {worker.identification} cannot work on {date} due to adjusted minimum distance from previous shift.")
                return False
            if days_diff in {7, 14, 21, 28}:
                logging.debug(f"Worker {worker.identification} cannot work on {date} due to 7, 14, 21 or 28 days constraint.")
                return False
            if last_date.date() == date.date():
                logging.debug(f"Worker {worker.identification} cannot work on {date} because they already have a shift on this day.")

        for next_shift_date in last_shift_dates[worker.identification]:
            next_days_diff = (next_shift_date - date).days
            if next_days_diff > 0 and next_days_diff < adjusted_min_distance:
                logging.debug(f"Worker {worker.identification} cannot work on {date} due to adjusted minimum distance to next shift on {next_shift_date}.")
                return False
            if next_days_diff in {7, 14, 21, 28}:
                logging.debug(f"Worker {worker.identification} cannot work on {date} due to 7, 14, 21 or 28 days constraint with next shift on {next_shift_date}.")
                return False

        if is_weekend(date) or is_holiday(date.strftime("%d/%m/%Y"), holidays_set):
            consecutive_weekends = 0
            for past_date in reversed(last_shift_dates[worker.identification]):
                if is_weekend(past_date) or is_holiday(past_date.strftime("%d/%m/%Y"), holidays_set):
                    consecutive_weekends += 1
                else:
                    break
            if consecutive_weekends >= 3:
                logging.debug(f"Worker {worker.identification} cannot work on {date} due to exceeding 3 consecutive weekend/holiday shifts.")
                return False

        week_number = date.isocalendar()[1]
        if weekly_tracker[worker.identification][week_number] >= max_shifts_per_week:
            logging.debug(f"Worker {worker.identification} cannot work on {date} due to weekly quota limit.")
            return False

    return True
    
def assign_worker_to_shift(worker, date, job, schedule, last_shift_dates, weekend_tracker, weekly_tracker, job_count, holidays_set, min_distance, max_shifts_per_week, total_days, jobs_per_day):
    logging.debug(f"Assigning worker {worker.identification} to job {job} on {date.strftime('%d/%m/%Y')}")
    last_shift_dates[worker.identification].append(date)
    schedule[job][date.strftime("%d/%m/%Y")] = worker.identification
    job_count[worker.identification][job] += 1
    weekly_tracker[worker.identification][date.isocalendar()[1]] += 1
    if is_weekend(date) or is_holiday(date.strftime("%d/%m/%Y"), holidays_set):
        weekend_tracker[worker.identification] += 1
    worker.shift_quota -= 1
    worker.percentage_shifts -= (1 / (total_days * jobs_per_day)) * 100  # Ensure jobs_per_day is an integer
    logging.debug(f"Worker {worker.identification} assigned to job {job} on {date.strftime('%d/%m/%Y')}. Updated schedule: {schedule[job][date.strftime('%d/%m/%Y')]}")

def schedule_shifts(work_periods, holidays, workers, min_distance, max_shifts_per_week, jobs_per_day):
    logging.debug(f"Workers: {workers}")
    logging.debug(f"Work Periods: {work_periods}")
    logging.debug(f"Holidays: {holidays}")

    jobs = [f"Job{i+1}" for i in range(jobs_per_day)]  
    
    schedule = defaultdict(dict)
    holidays_set = set(holidays)
    weekend_tracker = {worker.identification: 0 for worker in workers}
    last_shift_dates = {worker.identification: [] for worker in workers}
    weekly_tracker = defaultdict(lambda: defaultdict(int))
    last_assigned_day = {worker.identification: None for worker in workers}
    day_rotation_tracker = {worker.identification: {i: False for i in range(7)} for worker in workers}

    valid_work_periods = []
    for period in work_periods:
        try:
            start_date_str, end_date_str = period.split('-')
            start_date = datetime.strptime(start_date_str.strip(), "%d/%m/%Y")
            end_date = datetime.strptime(end_date_str.strip(), "%d/%m/%Y")
            valid_work_periods.append((start_date, end_date))
        except ValueError as e:
            logging.error(f"Invalid period '{period}': {e}")

    total_days = sum((end_date - start_date).days + 1 for start_date, end_date in valid_work_periods)
    calculate_shift_quota(workers, total_days, jobs_per_day)

    # Step 1: Assign obligatory coverage shifts
    for worker in workers:
        if not worker.work_dates:
            worker.work_dates = valid_work_periods

        for date_str in worker.obligatory_coverage:
            cleaned_date_str = date_str.strip().replace('.', '').replace(' ', '')
            if cleaned_date_str:
                date = datetime.strptime(cleaned_date_str, "%d/%m/%Y")
                logging.debug(f"Trying to assign obligatory coverage shift for Worker {worker.identification} on {date} for jobs {jobs}")
                for job in jobs:
                    assign_worker_to_shift(worker, date, job, schedule, last_shift_dates, weekend_tracker, weekly_tracker, job_count, holidays_set, min_distance, max_shifts_per_week, total_days, jobs)
                    last_assigned_job[worker.identification] = job
                    last_assigned_day[worker.identification] = date.weekday()
                    day_rotation_tracker[worker.identification][date.weekday()] = True
                    logging.debug(f"Assigned obligatory coverage shift for Worker {worker.identification} on {date} for job {job}")
                    break
                else:
                    logging.debug(f"Worker {worker.identification} cannot be assigned for obligatory coverage on {date} for any job.")
                    continue

    # Step 2: Assign remaining shifts respecting all premises
    for start_date, end_date in valid_work_periods:
        for date in generate_date_range(start_date, end_date):
            date_str = date.strftime("%d/%m/%Y")
            for job in jobs:
                # Skip if the job is already assigned on this date
                if date_str in schedule[job]:
                    continue

                logging.debug(f"Processing job '{job}' on date {date_str}")

                assigned = False
                iteration_count = 0
                max_iterations = len(workers) * 2

                while not assigned and iteration_count < max_iterations:
                    available_workers = [worker for worker in workers if worker.shift_quota > 0 and date_str not in [datetime.strptime(day.strip(), "%d/%m/%Y").strftime("%d/%m/%Y") for day in worker.unavailable_dates if day] and can_work_on_date(worker, date_str, last_shift_dates, weekend_tracker, holidays_set, weekly_tracker, job, job_count, min_distance, max_shifts_per_week, jobs)]
                    if not available_workers:
                        logging.error(f"No available workers for job {job} on {date_str}. Stopping assignment.")
                        return schedule

                    worker = max(available_workers, key=lambda w: (
                        (date - last_shift_dates[w.identification][-1]).days if last_shift_dates[w.identification] else float('inf'),
                        w.shift_quota,
                        w.percentage_shifts,
                        last_assigned_job[w.identification] != job,
                        last_assigned_day[w.identification] != date.weekday(),
                        not day_rotation_tracker[w.identification][date.weekday()]
                    ))
                    assign_worker_to_shift(worker, date, job, schedule, last_shift_dates, weekend_tracker, weekly_tracker, job_count, holidays_set, min_distance, max_shifts_per_week, total_days, jobs)
                    last_assigned_job[worker.identification] = job
                    last_assigned_day[worker.identification] = date.weekday()
                    day_rotation_tracker[worker.identification][date.weekday()] = True
                    logging.debug(f"Assigned shift for Worker {worker.identification} on {date} for job {job}")
                    assigned = True

                    iteration_count += 1
                    if iteration_count >= max_iterations:
                        logging.error(f"Exceeded maximum iterations for job {job} on {date_str}. Exiting to prevent infinite loop.")
                        return schedule

    return schedule

def export_schedule_to_csv(schedule, file_path):
    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Job', 'Date', 'Worker'])
        for job, shifts in schedule.items():
            for date, worker in shifts.items():
                writer.writerow([job, date, worker])

def prepare_breakdown(schedule):
    breakdown = defaultdict(list)
    for job, shifts in schedule.items():
        for date, worker_id in shifts.items():
            breakdown[worker_id].append((date, job))
    return breakdown

def export_breakdown(breakdown):
    output = ""
    for worker_id, shifts in breakdown.items():
        output += f"Worker {worker_id}:\n"
        for date, job in shifts:
            output += f"  {date}: {job}\n"
    return output

if __name__ == "__main__":
    work_periods = input("Enter work periods (e.g., 01/10/2024-31/10/2024, separated by commas): ").split(',')
    holidays = input("Enter holidays (e.g., 09/10/2024, separated by commas): ").split(',')
    jobs_per_day = input("Enter jobs per day: ").split(',')
    min_distance = int(input("Enter minimum distance between work shifts (in days): "))
    max_shifts_per_week = int(input("Enter maximum shifts that can be assigned per week: "))
    num_workers = int(input("Enter number of available workers: "))

    workers = [Worker(f"W{i+1}") for i in range(num_workers)]

    schedule = schedule_shifts(work_periods, holidays, jobs, workers, min_distance, max_shifts_per_week)
    breakdown = prepare_breakdown(schedule)
    print(export_breakdown(breakdown))
