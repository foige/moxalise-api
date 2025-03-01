#!/usr/bin/env python3
"""
Job runner script for Moxalise API Cloud Run jobs.

This script is designed to run different jobs based on the job name provided
as a command-line argument. It serves as a central entry point for all scheduled
jobs, making it easier to add new jobs in the future without creating new Docker
images for each job.
"""
import importlib
import logging
import sys
from typing import Dict, Callable, List, Optional

import click

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Define job registry - add new jobs here
JOB_REGISTRY: Dict[str, Dict[str, str]] = {
    "transfer_data": {
        "module": "moxalise.scripts.transfer_data",
        "function": "process_spreadsheet_data",
        "description": "Transfer data from 'დაზარალებულთა შევსებული ინფორმაცია' to 'დაზარალებულთა სია'"
    },
    # Add more jobs here as needed
    # "another_job": {
    #     "module": "moxalise.scripts.another_job",
    #     "function": "main_function",
    #     "description": "Description of another job"
    # },
}

def list_available_jobs() -> None:
    """
    List all available jobs with their descriptions.
    """
    logger.info("Available jobs:")
    for job_name, job_info in JOB_REGISTRY.items():
        logger.info(f"  - {job_name}: {job_info['description']}")

def run_job(job_name: str) -> bool:
    """
    Run the specified job.
    
    Args:
        job_name: The name of the job to run.
        
    Returns:
        True if the job ran successfully, False otherwise.
    """
    if job_name not in JOB_REGISTRY:
        logger.error(f"Unknown job: {job_name}")
        list_available_jobs()
        return False
    
    job_info = JOB_REGISTRY[job_name]
    logger.info(f"Running job: {job_name} - {job_info['description']}")
    
    try:
        # Import the module dynamically
        module = importlib.import_module(job_info["module"])
        
        # Get the specified function
        job_function = getattr(module, job_info["function"])
        
        # Run the job
        job_function()
        
        logger.info(f"Job '{job_name}' completed successfully")
        return True
    except ImportError as e:
        logger.error(f"Failed to import module '{job_info['module']}': {str(e)}")
    except AttributeError as e:
        logger.error(f"Function '{job_info['function']}' not found in module '{job_info['module']}': {str(e)}")
    except Exception as e:
        logger.error(f"Error running job '{job_name}': {str(e)}")
    
    return False

@click.group()
def cli():
    """
    Job runner for Moxalise API Cloud Run jobs.
    """
    pass

@cli.command("list")
def list_jobs():
    """
    List all available jobs.
    """
    list_available_jobs()

@cli.command("run")
@click.argument("job_name")
def execute_job(job_name: str):
    """
    Run a specific job by name.
    """
    success = run_job(job_name)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    cli()