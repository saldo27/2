import sys
from datetime import datetime
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QLineEdit, QPushButton, QTextEdit, QFileDialog, QGridLayout, QScrollArea
)

from PySide6.QtGui import QAction
from worker import Worker
from shift_scheduler import schedule_shifts, prepare_breakdown, export_breakdown, export_schedule_to_csv
from icalendar import Calendar, Event
from pdf_exporter import export_schedule_to_pdf
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

class MainWindow(QMainWindow):
    def __init__(self, work_periods, holidays, workers, min_distance, max_shifts_per_week, jobs_per_day):
        super().__init__()
        self.work_periods = work_periods
        self.holidays = holidays
        self.workers = workers
        self.min_distance = min_distance
        self.max_shifts_per_week = max_shifts_per_week
        self.jobs_per_day = jobs_per_day
        self.worker_inputs = []

        # Create input widgets
        self.work_periods_input = QLineEdit(','.join(work_periods))
        self.holidays_input = QLineEdit(','.join(holidays))
        self.jobs_input = QLineEdit(str(jobs_per_day))  # Initialize jobs_input
        self.min_distance_input = QLineEdit(str(min_distance))
        self.max_shifts_per_week_input = QLineEdit(str(max_shifts_per_week))
        self.num_workers_input = QLineEdit(str(len(workers)))

        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        self.schedule_button = QPushButton("Reparte las guardias")
        self.export_ical_button = QPushButton("Exportar a iCalendar")
        self.export_pdf_button = QPushButton("Exportar a PDF")
        self.export_csv_button = QPushButton("Exportar a CSV")
        self.breakdown_button = QPushButton("Desglose por médico")

        # Connect buttons to functions
        self.schedule_button.clicked.connect(self.schedule_shifts)
        self.export_ical_button.clicked.connect(self.export_to_ical)
        self.export_pdf_button.clicked.connect(self.export_to_pdf)
        self.export_csv_button.clicked.connect(self.export_to_csv)
        self.breakdown_button.clicked.connect(self.display_breakdown)

        # Setup layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Periodos de trabajo (separados por comas, e.g., '01/10/2024-10/10/2024'):"))
        layout.addWidget(self.work_periods_input)
        layout.addWidget(QLabel("Festivos (separados por comas, e.g., '05/10/2024'):"))
        layout.addWidget(self.holidays_input)
        layout.addWidget(QLabel("Puestos de guardia:"))
        layout.addWidget(self.jobs_input)  # Add jobs_input to the layout
        layout.addWidget(QLabel("Distancia mínima entre guardias:"))
        layout.addWidget(self.min_distance_input)
        layout.addWidget(QLabel("Número máximo de guardias/semana:"))
        layout.addWidget(self.max_shifts_per_week_input)
        layout.addWidget(QLabel("Número de médicos:"))
        layout.addWidget(self.num_workers_input)
        layout.addWidget(self.breakdown_button)
                
        # Worker inputs layout
        self.worker_layout = QGridLayout()

        # Scroll area for worker inputs
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_widget = QWidget()
        self.scroll_area_widget.setLayout(self.worker_layout)
        self.scroll_area.setWidget(self.scroll_area_widget)

        layout.addWidget(self.scroll_area)
        
        self.num_workers_input.textChanged.connect(self.update_worker_inputs)
        
        layout.addWidget(self.schedule_button)
        layout.addWidget(self.export_ical_button)
        layout.addWidget(self.export_pdf_button)
        layout.addWidget(self.export_csv_button)
        layout.addWidget(QLabel("Reparto:"))
        layout.addWidget(self.output_display)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
    def update_worker_inputs(self):
        num_workers = int(self.num_workers_input.text()) if self.num_workers_input.text().isdigit() else 0
        # Clear existing inputs
        for i in reversed(range(self.worker_layout.count())):
            self.worker_layout.itemAt(i).widget().setParent(None)
        self.worker_inputs = []
        for i in range(num_workers):
            identification_input = QLineEdit()
            identification_input.setFixedWidth(150)
            working_dates_input = QLineEdit()
            working_dates_input.setFixedWidth(150)
            percentage_shifts_input = QLineEdit()
            percentage_shifts_input.setFixedWidth(150)
            group_input = QLineEdit()
            group_input.setFixedWidth(150)
            group_incompatibility_input = QLineEdit()
            group_incompatibility_input.setFixedWidth(150)
            obligatory_coverage_input = QLineEdit()
            obligatory_coverage_input.setFixedWidth(150)
            unavailable_dates_input = QLineEdit()
            unavailable_dates_input.setFixedWidth(150)

            self.worker_layout.addWidget(QLabel(f"Guardian {i+1}:"), i, 0)
            self.worker_layout.addWidget(identification_input, i, 1)
            self.worker_layout.addWidget(QLabel("Fechas en que trabaja (comma-separated periods):"), i, 2)
            self.worker_layout.addWidget(working_dates_input, i, 3)
            self.worker_layout.addWidget(QLabel("Porcentaje de jornada:"), i, 4)
            self.worker_layout.addWidget(percentage_shifts_input, i, 5)
            self.worker_layout.addWidget(QLabel("Grupo:"), i, 6)
            self.worker_layout.addWidget(group_input, i, 7)
            self.worker_layout.addWidget(QLabel("Incompatibilidad con grupo:"), i, 8)
            self.worker_layout.addWidget(group_incompatibility_input, i, 9)
            self.worker_layout.addWidget(QLabel("Guardias obligatorias (comma-separated dates):"), i, 10)
            self.worker_layout.addWidget(obligatory_coverage_input, i, 11)
            self.worker_layout.addWidget(QLabel("No disponible (comma-separated dates):"), i, 12)
            self.worker_layout.addWidget(unavailable_dates_input, i, 13)

            self.worker_inputs.append({
                'identification': identification_input,
                'working_dates': working_dates_input,
                'percentage_shifts': percentage_shifts_input,
                'group': group_input,
                'group_incompatibility': group_incompatibility_input,
                'obligatory_coverage': obligatory_coverage_input,
                'unavailable_dates': unavailable_dates_input
            })

    def schedule_shifts(self):
        # Get inputs
        work_periods = self.work_periods_input.text().split(',')
        holidays = self.holidays_input.text().split(',')
        jobs_per_day = int(self.jobs_input.text())  # Use the numeric input to define the number of jobs per day
        num_workers = int(self.num_workers_input.text())
        min_distance = int(self.min_distance_input.text())
        max_shifts_per_week = int(self.max_shifts_per_week_input.text())
        # Create workers list from user input
        workers = [
            Worker(
                input['identification'].text(),
                [period.strip() for period in input['working_dates'].text().split(',')] if input['working_dates'].text() else [],
                float(input['percentage_shifts'].text() or 100),  # Default to 100 if blank
                input['group'].text() or '1',
                input['group_incompatibility'].text().split(',') if input['group_incompatibility'].text() else [],
                [date.strip() for date in input['obligatory_coverage'].text().split(',')] if input['obligatory_coverage'].text() else [],
                [date.strip() for date in input['unavailable_dates'].text().split(',')] if input['unavailable_dates'].text() else []
            )
            for input in self.worker_inputs
        ]
        # Schedule shifts
        schedule = schedule_shifts(self.work_periods, self.holidays, self.workers, self.min_distance, self.max_shifts_per_week, self.jobs_per_day)
        # Display the schedule
        output = ""
        self.schedule = schedule  # Save the schedule for exporting
        for date, jobs in schedule.items():
            output += f"Date {date}:\n"
            for job, worker in jobs.items():
                output += f"  Job {job}: {worker}\n"
        self.output_display.setText(output)
        
    def export_to_ical(self):
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getSaveFileName(self, "Save Schedule as iCalendar", "", "iCalendar Files (*.ics);;All Files (*)", options=options)
        if filePath:
            self.export_icalendar(filePath)

    def export_to_pdf(self):
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getSaveFileName(self, "Save Schedule as PDF", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if filePath:
            export_schedule_to_pdf(self.schedule, filePath)

    def export_to_csv(self):
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getSaveFileName(self, "Save Schedule as CSV", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if filePath:
            export_schedule_to_csv(self.schedule, filePath)

    def export_icalendar(self, filePath):
        cal = Calendar()
        for job, shifts in self.schedule.items():
            for date_str, worker_id in shifts.items():
                date = datetime.strptime(date_str, "%d/%m/%Y")
                event = Event()
                event.add('summary', f'Shift for Job {job}')
                event.add('dtstart', date)
                event.add('dtend', date)
                event.add('description', f'Worker: {worker_id}')
                cal.add_component(event)
        with open(filePath, 'wb') as f:
            f.write(cal.to_ical())
            
    def display_breakdown(self):
        breakdown = prepare_breakdown(self.schedule)
        
        # Create a table widget
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Worker", "Shifts Assigned"])
        
        # Populate the table with data from the breakdown
        table.setRowCount(len(breakdown))
        for row, (worker_id, shifts) in enumerate(breakdown.items()):
            worker_item = QTableWidgetItem(worker_id)
            shifts_item = QTableWidgetItem(", ".join([f"{date}: {job}" for date, job in shifts]))
            table.setItem(row, 0, worker_item)
            table.setItem(row, 1, shifts_item)
        
        # Replace the output display with the table
        self.output_display.setParent(None)
        self.output_display = table
        layout = self.centralWidget().layout()
        layout.addWidget(self.output_display)
        
app = QApplication(sys.argv)

# Provide the required arguments here
work_periods = ['01/10/2024-10/10/2024']
holidays = ['05/10/2024']
workers = []  # Populate with actual Worker instances if needed
min_distance = 2
max_shifts_per_week = 5
jobs_per_day = 3

window = MainWindow(work_periods, holidays, workers, min_distance, max_shifts_per_week, jobs_per_day)
window.show()
sys.exit(app.exec())
