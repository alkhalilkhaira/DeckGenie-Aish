import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional

from src.models.presentation import db, Presentation, GenerationLog
from src.services.ai_service import AIService
from src.services.enhanced_data_service import EnhancedDataService
from src.services.presentation_service import PresentationService

class GenerationService:
    """Main service for orchestrating presentation generation."""
    
    def __init__(self):
        self.ai_service = AIService()
        self.data_service = EnhancedDataService()
        self.presentation_service = PresentationService()
        self.active_generations = {}  # Track active generation processes
    
    def start_generation(self, presentation_id: int) -> bool:
        """
        Start the presentation generation process in a background thread.
        
        Args:
            presentation_id: Database ID of the presentation to generate
            
        Returns:
            True if generation started successfully, False otherwise
        """
        try:
            # Check if generation is already running for this presentation
            if presentation_id in self.active_generations:
                return False
            
            # Start generation in background thread
            thread = threading.Thread(
                target=self._generate_presentation_background,
                args=(presentation_id,),
                daemon=True
            )
            thread.start()
            
            self.active_generations[presentation_id] = {
                'thread': thread,
                'started_at': datetime.utcnow()
            }
            
            return True
            
        except Exception as e:
            print(f"Error starting generation: {e}")
            return False
    
    def _generate_presentation_background(self, presentation_id: int) -> None:
        """Background task for generating a presentation."""
        start_time = datetime.utcnow()
        
        try:
            # Get presentation from database
            presentation = Presentation.query.get(presentation_id)
            if not presentation:
                return
            
            # Log generation start
            self._log_step(presentation_id, 'generation_started', 'started')
            
            # Step 1: Research and data gathering
            presentation.status = 'researching'
            presentation.progress = 10
            presentation.current_step = 'Gathering research data'
            db.session.commit()
            
            self._log_step(presentation_id, 'research', 'started')
            
            # Analyze prompt to get research topics
            analysis = self.ai_service.analyze_prompt(presentation.original_prompt)
            
            # Gather research data
            research_data = self.data_service.get_comprehensive_research(
                presentation.original_prompt,
                analysis.get('subtopics', [])
            )
            
            # Flatten research data for easier use
            all_research = []
            for source_type, results in research_data.items():
                all_research.extend(results)
            
            self._log_step(presentation_id, 'research', 'completed', 
                          details={'sources_found': len(all_research)})
            
            # Step 2: Content planning
            presentation.status = 'planning'
            presentation.progress = 30
            presentation.current_step = 'Planning presentation structure'
            db.session.commit()
            
            self._log_step(presentation_id, 'planning', 'started')
            
            # Generate presentation outline
            outline = self.ai_service.generate_presentation_outline(
                presentation.original_prompt,
                presentation.slide_count,
                analysis
            )
            
            # Update presentation title if AI generated a better one
            if outline.get('title') and outline['title'] != presentation.original_prompt:
                presentation.title = outline['title']
                db.session.commit()
            
            self._log_step(presentation_id, 'planning', 'completed',
                          details={'slides_planned': len(outline.get('slides', []))})
            
            # Step 3: Generate presentation
            presentation.status = 'generating'
            presentation.progress = 50
            presentation.current_step = 'Generating presentation content'
            db.session.commit()
            
            self._log_step(presentation_id, 'content_generation', 'started')
            
            # Generate the actual presentation
            success = self.presentation_service.generate_presentation(
                presentation_id,
                all_research
            )
            
            if success:
                self._log_step(presentation_id, 'content_generation', 'completed')
                self._log_step(presentation_id, 'generation_completed', 'completed')
            else:
                self._log_step(presentation_id, 'content_generation', 'failed',
                              error_message='Presentation generation failed')
                
                # Update presentation status
                presentation.status = 'failed'
                presentation.error_message = 'Failed to generate presentation content'
                db.session.commit()
            
        except Exception as e:
            print(f"Error in background generation: {e}")
            
            # Log error
            self._log_step(presentation_id, 'generation_error', 'failed',
                          error_message=str(e))
            
            # Update presentation status
            try:
                presentation = Presentation.query.get(presentation_id)
                if presentation:
                    presentation.status = 'failed'
                    presentation.error_message = str(e)
                    db.session.commit()
            except Exception as db_error:
                print(f"Error updating presentation status: {db_error}")
        
        finally:
            # Calculate total generation time
            end_time = datetime.utcnow()
            generation_time = int((end_time - start_time).total_seconds())
            
            try:
                presentation = Presentation.query.get(presentation_id)
                if presentation:
                    presentation.generation_time = generation_time
                    db.session.commit()
            except Exception as db_error:
                print(f"Error updating generation time: {db_error}")
            
            # Remove from active generations
            if presentation_id in self.active_generations:
                del self.active_generations[presentation_id]
    
    def _log_step(self, presentation_id: int, step_name: str, status: str, 
                  details: Dict[str, Any] = None, error_message: str = None) -> None:
        """Log a generation step."""
        try:
            log_entry = GenerationLog(
                presentation_id=presentation_id,
                step_name=step_name,
                status=status,
                start_time=datetime.utcnow(),
                details=str(details) if details else None,
                error_message=error_message
            )
            
            if status in ['completed', 'failed']:
                log_entry.end_time = datetime.utcnow()
                if log_entry.start_time:
                    duration = (log_entry.end_time - log_entry.start_time).total_seconds() * 1000
                    log_entry.duration = int(duration)
            
            db.session.add(log_entry)
            db.session.commit()
            
        except Exception as e:
            print(f"Error logging step: {e}")
            db.session.rollback()
    
    def get_generation_status(self, presentation_id: int) -> Dict[str, Any]:
        """
        Get detailed generation status for a presentation.
        
        Args:
            presentation_id: Database ID of the presentation
            
        Returns:
            Dictionary with detailed status information
        """
        try:
            presentation = Presentation.query.get(presentation_id)
            if not presentation:
                return {'error': 'Presentation not found'}
            
            # Get recent generation logs
            logs = GenerationLog.query.filter_by(
                presentation_id=presentation_id
            ).order_by(GenerationLog.created_at.desc()).limit(10).all()
            
            status_info = {
                'presentation_id': presentation_id,
                'status': presentation.status,
                'progress': presentation.progress,
                'current_step': presentation.current_step,
                'error_message': presentation.error_message,
                'generation_time': presentation.generation_time,
                'is_active': presentation_id in self.active_generations,
                'logs': [
                    {
                        'step_name': log.step_name,
                        'status': log.status,
                        'start_time': log.start_time.isoformat() if log.start_time else None,
                        'end_time': log.end_time.isoformat() if log.end_time else None,
                        'duration': log.duration,
                        'error_message': log.error_message
                    }
                    for log in logs
                ]
            }
            
            return status_info
            
        except Exception as e:
            print(f"Error getting generation status: {e}")
            return {'error': str(e)}
    
    def cancel_generation(self, presentation_id: int) -> bool:
        """
        Cancel an active generation process.
        
        Args:
            presentation_id: Database ID of the presentation
            
        Returns:
            True if cancellation successful, False otherwise
        """
        try:
            if presentation_id not in self.active_generations:
                return False
            
            # Update presentation status
            presentation = Presentation.query.get(presentation_id)
            if presentation:
                presentation.status = 'failed'
                presentation.error_message = 'Generation cancelled by user'
                db.session.commit()
            
            # Log cancellation
            self._log_step(presentation_id, 'generation_cancelled', 'completed')
            
            # Remove from active generations
            del self.active_generations[presentation_id]
            
            return True
            
        except Exception as e:
            print(f"Error cancelling generation: {e}")
            return False
    
    def cleanup_stale_generations(self, max_age_hours: int = 2) -> int:
        """
        Clean up stale generation processes.
        
        Args:
            max_age_hours: Maximum age in hours before considering a generation stale
            
        Returns:
            Number of stale generations cleaned up
        """
        try:
            current_time = datetime.utcnow()
            stale_generations = []
            
            for presentation_id, info in self.active_generations.items():
                age = current_time - info['started_at']
                if age.total_seconds() > max_age_hours * 3600:
                    stale_generations.append(presentation_id)
            
            # Clean up stale generations
            for presentation_id in stale_generations:
                self.cancel_generation(presentation_id)
            
            return len(stale_generations)
            
        except Exception as e:
            print(f"Error cleaning up stale generations: {e}")
            return 0
    
    def get_active_generations_count(self) -> int:
        """Get the number of currently active generations."""
        return len(self.active_generations)

# Global instance
generation_service = GenerationService()

