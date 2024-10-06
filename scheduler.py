from models import Shift
from datetime import timedelta, datetime

class Scheduler:
    def __init__(self, start_date, end_date, holidays, jobs, workers):
        self.start_date = start_date
        self.end_date = end_date
        self.holidays = holidays
        self.jobs = jobs
        self.workers = workers
        self.shifts = []

    def distribute_shifts(self):
        current_date = self.start_date
        while current_date <= self.end_date:
            if current_date not in self.holidays:
                for job in self.jobs:
                    worker = self.assign_worker(current_date, job)
                    if worker:
                        shift = Shift(current_date, job, worker.id)
                        self.shifts.append(shift)
                        print(f"Assigned Shift: {shift}")
                    else:
                        print(f"No available worker for job {job} on {current_date}")
            current_date += timedelta(days=1)
        return self.shifts

    def assign_worker(self, date, job):
        available_workers = self.get_available_workers(date, job)
        if not available_workers:
            return None
        
        for worker in available_workers:
            if self.can_assign_shift(worker, date, job):
                return worker
        
        return None

    def get_available_workers(self, date, job):
        available_workers = []
        date_str = date.strftime("%d/%m/%y")
        for worker in self.workers:
            if job != worker.incompatible_job and date_str not in worker.day_off:
                if worker.work_dates:
                    for period in worker.work_dates.split(","):
                        start, end = map(lambda x: datetime.strptime(x.strip(), "%d/%m/%y"), period.split("-"))
                        if start <= date <= end:
                            available_workers.append(worker)
                else:
                    available_workers.append(worker)
        return available_workers

    def can_assign_shift(self, worker, date, job):
        if worker.obligatory_coverage and date in worker.obligatory_coverage:
            return True

        if self.has_consecutive_shifts(worker, date) or self.has_consecutive_weekends(worker, date):
            return False
        
        return True

    def has_consecutive_shifts(self, worker, date):
        for i in range(1, 5):
            check_date = date - timedelta(days=i)
            for shift in self.shifts:
                if shift.date == check_date and shift.worker_id == worker.id:
                    return True
        return False

    def has_consecutive_weekends(self, worker, date):
        weekend_count = 0
        for i in range(1, 22, 7):  # Check last 3 weekends (21 days)
            check_date = date - timedelta(days=i)
            if check_date.weekday() in [4, 5, 6]:  # Friday, Saturday, Sunday
                for shift in self.shifts:
                    if shift.date == check_date and shift.worker_id == worker.id:
                        weekend_count += 1
                        break
        return weekend_count >= 3
