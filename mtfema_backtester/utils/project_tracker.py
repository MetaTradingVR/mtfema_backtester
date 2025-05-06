"""
Project Tracker Utility

This module provides utilities for tracking project progress and updating
the project plan markdown file.
"""

import os
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ProjectTracker:
    """
    Track project progress and update the project plan markdown file.
    """
    
    def __init__(self, project_plan_path):
        """
        Initialize the ProjectTracker
        
        Parameters:
        -----------
        project_plan_path : str
            Path to the project plan markdown file
        """
        self.project_plan_path = project_plan_path
        self.content = None
        self.load_project_plan()
    
    def load_project_plan(self):
        """Load the project plan markdown file"""
        try:
            with open(self.project_plan_path, 'r') as f:
                self.content = f.read()
            logger.info(f"Loaded project plan from {self.project_plan_path}")
        except Exception as e:
            logger.error(f"Error loading project plan: {str(e)}")
            self.content = None
    
    def save_project_plan(self):
        """Save the project plan markdown file"""
        try:
            with open(self.project_plan_path, 'w') as f:
                f.write(self.content)
            logger.info(f"Saved project plan to {self.project_plan_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving project plan: {str(e)}")
            return False
    
    def update_task_status(self, task_text, completed=True):
        """
        Update the status of a task in the project plan
        
        Parameters:
        -----------
        task_text : str
            Text of the task to update
        completed : bool
            Whether the task is completed
            
        Returns:
        --------
        bool
            Whether the update was successful
        """
        if not self.content:
            logger.error("Project plan not loaded")
            return False
        
        # Escape special regex characters in task_text
        escaped_task = re.escape(task_text)
        
        # Create pattern to match task line with either checkbox state
        pattern = rf'- \[([ x])\] {escaped_task}'
        
        # Create replacement with appropriate checkbox state
        replacement = f'- [{"x" if completed else " "}] {task_text}'
        
        # Check if task exists in content
        if not re.search(pattern, self.content):
            logger.warning(f"Task not found: {task_text}")
            return False
        
        # Update task status
        self.content = re.sub(pattern, replacement, self.content)
        
        return self.save_project_plan()
    
    def get_tasks_by_status(self, completed=None):
        """
        Get tasks filtered by status
        
        Parameters:
        -----------
        completed : bool or None
            If True, get completed tasks
            If False, get incomplete tasks
            If None, get all tasks
            
        Returns:
        --------
        list
            List of task texts
        """
        if not self.content:
            logger.error("Project plan not loaded")
            return []
        
        # Define pattern based on status
        if completed is None:
            pattern = r'- \[([ x])\] (.+)'
        else:
            check = 'x' if completed else ' '
            pattern = rf'- \[{check}\] (.+)'
        
        # Find all matching tasks
        if completed is None:
            matches = re.findall(pattern, self.content)
            # If pattern includes status, return both status and text
            return [(m[0] == 'x', m[1]) for m in matches]
        else:
            matches = re.findall(pattern, self.content)
            # If pattern does not include status, return just text
            return matches
    
    def get_task_status(self, task_text):
        """
        Get the status of a specific task
        
        Parameters:
        -----------
        task_text : str
            Text of the task to check
            
        Returns:
        --------
        bool or None
            True if task is completed, False if not, None if task not found
        """
        if not self.content:
            logger.error("Project plan not loaded")
            return None
        
        # Escape special regex characters in task_text
        escaped_task = re.escape(task_text)
        
        # Create pattern to match task line
        pattern = rf'- \[([ x])\] {escaped_task}'
        
        match = re.search(pattern, self.content)
        if match:
            return match.group(1) == 'x'
        
        return None
    
    def update_progress_section(self):
        """
        Update the progress section in the project plan
        
        Returns:
        --------
        bool
            Whether the update was successful
        """
        if not self.content:
            logger.error("Project plan not loaded")
            return False
        
        # Get all tasks
        all_tasks = self.get_tasks_by_status()
        
        # Calculate completion percentage
        if all_tasks:
            completed_count = sum(1 for status, _ in all_tasks if status)
            total_count = len(all_tasks)
            completion_percentage = completed_count / total_count * 100
        else:
            completion_percentage = 0
        
        # Get completed tasks
        completed_tasks = [task for status, task in all_tasks if status]
        
        # Get in-progress tasks
        in_progress_phases = self._identify_in_progress_phases()
        
        # Get next steps (incomplete tasks from current phase)
        next_steps = self._identify_next_steps()
        
        # Create progress section content
        progress_section = "## Current Progress (Updated)\n\n"
        progress_section += f"✅ **Completed** ({completion_percentage:.1f}%):\n"
        for task in completed_tasks:
            progress_section += f"- {task}\n"
        
        progress_section += "\n🔄 **In Progress**:\n"
        for phase in in_progress_phases:
            progress_section += f"- {phase}\n"
        
        progress_section += "\n⏱️ **Next Steps**:\n"
        for step in next_steps:
            progress_section += f"- {step}\n"
        
        # Replace existing progress section or append if not found
        progress_pattern = r"## Current Progress \(Updated\)[\s\S]+?(?=##|\Z)"
        if re.search(progress_pattern, self.content):
            self.content = re.sub(progress_pattern, progress_section, self.content)
        else:
            self.content += f"\n\n{progress_section}"
        
        return self.save_project_plan()
    
    def _identify_in_progress_phases(self):
        """
        Identify phases that are in progress (have both complete and incomplete tasks)
        
        Returns:
        --------
        list
            List of phase names that are in progress
        """
        # Define pattern to match phase headers
        phase_pattern = r"#### (\d+\.\d+) ([^\n]+)"
        
        in_progress_phases = []
        
        # Find all phases
        for match in re.finditer(phase_pattern, self.content):
            phase_number = match.group(1)
            phase_name = match.group(2)
            
            # Find position of this phase in content
            phase_start = match.start()
            
            # Find next phase or end of content
            next_phase_match = re.search(rf"#### {phase_number[0]}\.\d+ ", self.content[phase_start+1:])
            if next_phase_match:
                phase_end = phase_start + 1 + next_phase_match.start()
            else:
                # If no next phase, look for next major section
                next_section_match = re.search(r"### ", self.content[phase_start+1:])
                if next_section_match:
                    phase_end = phase_start + 1 + next_section_match.start()
                else:
                    phase_end = len(self.content)
            
            # Extract phase content
            phase_content = self.content[phase_start:phase_end]
            
            # Check if phase has both complete and incomplete tasks
            has_complete = "- [x]" in phase_content
            has_incomplete = "- [ ]" in phase_content
            
            if has_complete and has_incomplete:
                in_progress_phases.append(f"{phase_name}")
        
        return in_progress_phases
    
    def _identify_next_steps(self):
        """
        Identify next steps (incomplete tasks from current phase)
        
        Returns:
        --------
        list
            List of next steps
        """
        # Get in-progress phases
        in_progress_phases = self._identify_in_progress_phases()
        
        next_steps = []
        
        # For each in-progress phase, find incomplete tasks
        for phase_name in in_progress_phases:
            # Find phase header
            phase_pattern = rf"#### \d+\.\d+ {re.escape(phase_name)}"
            phase_match = re.search(phase_pattern, self.content)
            
            if phase_match:
                # Find position of this phase in content
                phase_start = phase_match.start()
                
                # Find next phase or end of content
                next_phase_match = re.search(r"#### \d+\.\d+ ", self.content[phase_start+1:])
                if next_phase_match:
                    phase_end = phase_start + 1 + next_phase_match.start()
                else:
                    # If no next phase, look for next major section
                    next_section_match = re.search(r"### ", self.content[phase_start+1:])
                    if next_section_match:
                        phase_end = phase_start + 1 + next_section_match.start()
                    else:
                        phase_end = len(self.content)
                
                # Extract phase content
                phase_content = self.content[phase_start:phase_end]
                
                # Find incomplete tasks
                task_pattern = r"- \[ \] (.+)"
                for task_match in re.finditer(task_pattern, phase_content):
                    next_steps.append(task_match.group(1))
        
        return next_steps

def update_project_status(project_plan_path, task_text=None, completed=True):
    """
    Update the status of a task and refresh the progress section
    
    Parameters:
    -----------
    project_plan_path : str
        Path to the project plan markdown file
    task_text : str, optional
        Text of the task to update
    completed : bool
        Whether the task is completed
        
    Returns:
    --------
    bool
        Whether the update was successful
    """
    tracker = ProjectTracker(project_plan_path)
    
    # Update specific task if provided
    if task_text:
        tracker.update_task_status(task_text, completed)
    
    # Update progress section
    return tracker.update_progress_section() 