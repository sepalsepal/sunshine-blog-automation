import streamlit as st
import state_manager
import time

class WorkflowManager:
    """
    Central controller for the application workflow.
    Manages state transitions, progress updates, and persistence.
    """
    
    def __init__(self):
        self._init_session_state()
        
    def _init_session_state(self):
        """Initialize session state variables if they don't exist."""
        if 'pipeline' not in st.session_state:
            st.session_state.pipeline = {'step': 0, 'status': 'idle'}
            
        if 'progress' not in st.session_state:
            st.session_state.progress = {
                'search_trends': {'status': 'pending', 'percent': 0},
                'search_youtube': {'status': 'pending', 'percent': 0},
                'search_blog': {'status': 'pending', 'percent': 0},
                'combine_research': {'status': 'pending', 'percent': 0},
                'write_content': {'status': 'pending', 'percent': 0},
                'create_hashtags': {'status': 'pending', 'percent': 0},
                'audit_content': {'status': 'pending', 'percent': 0},
                'create_img_prompt': {'status': 'pending', 'percent': 0},
                'audit_img_prompt': {'status': 'pending', 'percent': 0},
                'generate_images': {'status': 'pending', 'percent': 0},
                'telegram_report': {'status': 'pending', 'percent': 0},
                'approval': {'status': 'pending', 'percent': 0},
                'upload_wordpress': {'status': 'pending', 'percent': 0},
                'archive_sheets': {'status': 'pending', 'percent': 0}
            }
            
        if 'final_data' not in st.session_state:
            st.session_state.final_data = {}

    def load_state(self):
        """Load state from disk and perform auto-recovery if needed."""
        if state_manager.load_state():
            st.toast("💾 이전 작업 상태를 복구했습니다.")
            self._auto_recover()
            return True
        return False

    def _auto_recover(self):
        """Fix inconsistencies between step and progress (e.g. after crash)."""
        step = self.get_current_step()
        progress = st.session_state.progress
        
        # Step 1 Complete -> Move to Step 2
        if step == 1 and progress['combine_research']['status'] == 'complete':
            self.set_step(2)
            
        # Step 2 Complete -> Move to Step 3
        elif step == 2 and progress['write_content']['status'] == 'complete':
            self.set_step(3)

    def get_current_step(self):
        """Return the current step number."""
        return st.session_state.pipeline['step']

    def set_step(self, step_id):
        """Update the current step and save state."""
        st.session_state.pipeline['step'] = step_id
        self.save_state()

    def update_progress(self, task_name, status, percent=None):
        """Update progress for a specific task."""
        if status:
            st.session_state.progress[task_name]['status'] = status
        if percent is not None:
            st.session_state.progress[task_name]['percent'] = percent
        # Note: We don't save state on every progress update to avoid IO thrashing,
        # but critical updates should call save_state() explicitly.

    def save_state(self):
        """Persist current state to disk."""
        state_manager.save_state()

    def rerun(self):
        """Trigger a Streamlit rerun."""
        st.rerun()
