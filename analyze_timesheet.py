from utils.csv_analyzer import analyze_timesheet_csv, get_time_entries
import json

def main():
    csv_path = "attached_assets/Hours Tracker.csv"
    
    # Analyze the CSV
    print("Analyzing timesheet data...")
    analysis = analyze_timesheet_csv(csv_path)
    
    # Print results
    print("\nAnalysis Results:")
    print(f"Total number of time entries: {analysis['total_time_entries']}")
    print("\nUnique Customers:")
    for customer in analysis['unique_customers']:
        print(f"- {customer}")
        if customer in analysis['customer_projects']:
            for project in analysis['customer_projects'][customer]:
                print(f"  - Project: {project}")

if __name__ == "__main__":
    main()
