import time
import logging
from jobs.janitor import cleanup_stuck_jobs

# Set up logging so we can see the Janitor working in journalctl
logging.basicConfig(level=logging.INFO, format='%(asctime)s - JANITOR - %(message)s')

def main():
    logging.info("Janitor service started. Monitoring for stuck jobs...")
    while True:
        try:
            # Cleans jobs stuck in PROCESSING for > 10 mins
            # Also deletes old temporary files if you added that logic
            cleanup_stuck_jobs(timeout_minutes=10)
            logging.info("Janitor check complete. Sleeping for 5 minutes.")
        except Exception as e:
            logging.error(f"Janitor encountered an error: {e}")
        
        # Wait for 5 minutes (300 seconds)
        time.sleep(300)

if __name__ == "__main__":
    main()