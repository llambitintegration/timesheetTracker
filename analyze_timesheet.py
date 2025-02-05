from utils.csv_analyzer import analyze_timesheet_csv, get_time_entries
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    csv_path = "attached_assets/Hours Tracker.csv"

    try:
        # Analyze the CSV
        logger.info("Analyzing timesheet data...")
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

        # Get and validate time entries
        logger.info("Validating time entries...")
        entries = get_time_entries(csv_path)
        print(f"\nValidated {len(entries)} time entries")

    except Exception as e:
        logger.error(f"Error analyzing CSV: {str(e)}")
        raise

if __name__ == "__main__":
    main()