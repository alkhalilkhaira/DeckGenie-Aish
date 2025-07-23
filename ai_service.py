import os
import json
from typing import Dict, List, Optional, Any
from openai import OpenAI
from datetime import datetime

class AIService:
    """Service for handling AI-powered content generation using OpenAI GPT-4."""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            base_url=os.getenv('OPENAI_API_BASE')
        )
        self.model = "gpt-4"
    
    def analyze_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Analyze the user prompt to extract key topics and determine presentation structure.
        
        Args:
            prompt: User's presentation topic/prompt
            
        Returns:
            Dictionary containing analysis results including topics, suggested structure, etc.
        """
        system_prompt = """You are an expert presentation analyst. Analyze the given prompt and provide a structured response with:
1. Main topic and subtopics
2. Suggested presentation structure
3. Key areas to research
4. Appropriate presentation style (corporate, academic, creative)
5. Estimated complexity level

Respond in JSON format with the following structure:
{
    "main_topic": "string",
    "subtopics": ["string1", "string2", ...],
    "suggested_structure": ["Introduction", "Main Points", "Conclusion"],
    "research_areas": ["area1", "area2", ...],
    "presentation_style": "corporate|academic|creative",
    "complexity_level": "basic|intermediate|advanced",
    "estimated_slides": number
}"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this presentation prompt: {prompt}"}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            print(f"Error analyzing prompt: {e}")
            return {
                "main_topic": prompt,
                "subtopics": [],
                "suggested_structure": ["Introduction", "Main Content", "Conclusion"],
                "research_areas": [prompt],
                "presentation_style": "corporate",
                "complexity_level": "intermediate",
                "estimated_slides": 10
            }
    
    def generate_presentation_outline(self, prompt: str, slide_count: int, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a detailed presentation outline based on the prompt and analysis.
        
        Args:
            prompt: Original user prompt
            slide_count: Requested number of slides
            analysis: Result from analyze_prompt
            
        Returns:
            Dictionary containing the presentation outline
        """
        system_prompt = f"""You are an expert presentation designer. Create a detailed outline for a {slide_count}-slide presentation.

The outline should include:
1. Title slide
2. Agenda/Overview slide
3. Content slides with specific topics
4. Conclusion slide
5. References slide (if needed)

Each slide should have:
- Title
- Main points (3-5 bullet points max)
- Suggested visual elements (charts, images, etc.)
- Speaker notes outline

Respond in JSON format:
{{
    "title": "Presentation Title",
    "slides": [
        {{
            "slide_number": 1,
            "title": "Slide Title",
            "type": "title|agenda|content|conclusion|references",
            "main_points": ["point1", "point2", ...],
            "visual_elements": ["chart", "image", "diagram"],
            "speaker_notes": "Brief outline of what to say"
        }}
    ]
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Create an outline for: {prompt}\nSlide count: {slide_count}\nStyle: {analysis.get('presentation_style', 'corporate')}"}
                ],
                temperature=0.4,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            print(f"Error generating outline: {e}")
            return self._generate_fallback_outline(prompt, slide_count)
    
    def generate_slide_content(self, slide_info: Dict[str, Any], research_data: List[Dict[str, Any]], presentation_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate detailed content for a specific slide.
        
        Args:
            slide_info: Information about the slide from the outline
            research_data: Relevant research data for this slide
            presentation_context: Overall presentation context
            
        Returns:
            Dictionary containing detailed slide content
        """
        system_prompt = """You are an expert content writer for presentations. Create detailed, professional slide content.

For each slide, provide:
1. Refined title
2. 3-5 concise bullet points
3. Detailed speaker notes
4. Suggested images/visuals with descriptions
5. Any charts or data visualizations needed
6. Citations for factual claims

Keep content professional, engaging, and factually accurate. Use the provided research data to support your points.

Respond in JSON format:
{
    "title": "Refined Slide Title",
    "bullet_points": ["point1", "point2", ...],
    "speaker_notes": "Detailed speaker notes",
    "visual_suggestions": [
        {
            "type": "image|chart|diagram",
            "description": "Description of visual",
            "search_terms": ["term1", "term2"]
        }
    ],
    "citations": [1, 2, 3],
    "additional_notes": "Any additional context"
}"""
        
        research_context = "\n".join([
            f"Source: {data.get('title', 'Unknown')}\nContent: {data.get('content', '')[:500]}..."
            for data in research_data[:3]  # Limit to top 3 sources
        ])
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Create content for slide:\nTitle: {slide_info.get('title')}\nType: {slide_info.get('type')}\nMain points: {slide_info.get('main_points')}\n\nResearch data:\n{research_context}"}
                ],
                temperature=0.5,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            print(f"Error generating slide content: {e}")
            return self._generate_fallback_slide_content(slide_info)
    
    def generate_speaker_notes(self, slide_content: Dict[str, Any], presentation_context: Dict[str, Any]) -> str:
        """
        Generate detailed speaker notes for a slide.
        
        Args:
            slide_content: The slide content
            presentation_context: Overall presentation context
            
        Returns:
            Detailed speaker notes as a string
        """
        system_prompt = """You are an expert public speaker. Create detailed, natural speaker notes for this slide.

The notes should:
1. Be conversational and natural
2. Expand on the bullet points
3. Include smooth transitions
4. Suggest timing and emphasis
5. Be 2-3 minutes of speaking content

Write in a natural, engaging tone that a presenter can easily follow."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Create speaker notes for:\nTitle: {slide_content.get('title')}\nBullet points: {slide_content.get('bullet_points')}\nContext: {presentation_context.get('title', '')}"}
                ],
                temperature=0.6,
                max_tokens=800
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating speaker notes: {e}")
            return f"Speaker notes for {slide_content.get('title', 'this slide')}. Expand on the key points and engage with your audience."
    
    def _generate_fallback_outline(self, prompt: str, slide_count: int) -> Dict[str, Any]:
        """Generate a basic fallback outline when AI generation fails."""
        slides = [
            {
                "slide_number": 1,
                "title": prompt,
                "type": "title",
                "main_points": ["Professional Presentation"],
                "visual_elements": ["title_image"],
                "speaker_notes": "Welcome and introduction"
            },
            {
                "slide_number": 2,
                "title": "Agenda",
                "type": "agenda",
                "main_points": ["Overview", "Main Topics", "Conclusion"],
                "visual_elements": ["agenda_list"],
                "speaker_notes": "Outline of presentation structure"
            }
        ]
        
        # Add content slides
        for i in range(3, slide_count):
            slides.append({
                "slide_number": i,
                "title": f"Topic {i-1}",
                "type": "content",
                "main_points": ["Key Point 1", "Key Point 2", "Key Point 3"],
                "visual_elements": ["relevant_image"],
                "speaker_notes": f"Discuss topic {i-1} in detail"
            })
        
        # Add conclusion
        slides.append({
            "slide_number": slide_count,
            "title": "Conclusion",
            "type": "conclusion",
            "main_points": ["Summary", "Key Takeaways", "Thank You"],
            "visual_elements": ["conclusion_image"],
            "speaker_notes": "Summarize and conclude"
        })
        
        return {
            "title": prompt,
            "slides": slides
        }
    
    def _generate_fallback_slide_content(self, slide_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback slide content when AI generation fails."""
        return {
            "title": slide_info.get('title', 'Slide Title'),
            "bullet_points": slide_info.get('main_points', ['Key Point 1', 'Key Point 2', 'Key Point 3']),
            "speaker_notes": slide_info.get('speaker_notes', 'Detailed speaker notes for this slide.'),
            "visual_suggestions": [
                {
                    "type": "image",
                    "description": "Relevant image for this topic",
                    "search_terms": [slide_info.get('title', 'topic')]
                }
            ],
            "citations": [],
            "additional_notes": "Generated content"
        }

