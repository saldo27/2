from datetime import datetime

def input_date(prompt):
    while True:
        try:
            return datetime.strptime(input(prompt), "%d/%m/%y")
        except ValueError:
            print("Invalid date format. Please use DD/MM/YY.")

def input_percentage(prompt):
    while True:
        try:
            percentage = input(prompt)
            if percentage == "":
                return 100.0
            percentage = float(percentage)
            if 0 <= percentage <= 100:
                return percentage
            else:
                print("Percentage must be between 0 and 100.")
        except ValueError:
            print("Invalid percentage. Please enter a number.")
