import openai
import os
from src.models.content_template import ContentTemplate
from src.models.content import Content
from src.models.order import Order
from src.models.user import db

class ContentGenerator:
    def __init__(self):
        # OpenAI API key is already set in environment variables
        self.client = openai.OpenAI()
    
    def generate_content(self, order_id):
        """Generate content for a given order"""
        try:
            # Get the order
            order = Order.query.get(order_id)
            if not order:
                raise ValueError("Order not found")
            
            # Get the content template
            template = ContentTemplate.query.filter_by(
                content_type=order.content_type,
                is_active=True
            ).first()
            
            if not template:
                raise ValueError("Content template not found")
            
            # Build the prompt
            prompt = self._build_prompt(order, template)
            
            # Generate content using OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional content writer. Create high-quality, engaging content based on the user's requirements."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=min(order.word_count * 2, 4000),  # Rough estimate for token limit
                temperature=0.7
            )
            
            generated_text = response.choices[0].message.content
            
            # Calculate quality score (simple heuristic)
            quality_score = self._calculate_quality_score(generated_text, order.word_count)
            
            # Save the generated content
            content = Content(
                order_id=order.id,
                generated_content=generated_text,
                content_format='markdown',
                quality_score=quality_score,
                is_approved=quality_score > 0.7  # Auto-approve if quality is good
            )
            
            db.session.add(content)
            
            # Update order status
            order.status = 'completed'
            order.updated_at = db.func.now()
            
            db.session.commit()
            
            return {
                'success': True,
                'content': content.to_dict(),
                'order': order.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _build_prompt(self, order, template):
        """Build the prompt for content generation"""
        prompt_parts = []
        
        # Start with the template prompt
        base_prompt = template.template_prompt.format(topic=order.title)
        prompt_parts.append(base_prompt)
        
        # Add order description if available
        if order.description:
            prompt_parts.append(f"\nAdditional context: {order.description}")
        
        # Add requirements
        requirements = order.get_requirements()
        if requirements:
            prompt_parts.append("\nSpecific requirements:")
            
            if requirements.get('tone'):
                prompt_parts.append(f"- Tone: {requirements['tone']}")
            
            if requirements.get('target_audience'):
                prompt_parts.append(f"- Target audience: {requirements['target_audience']}")
            
            if requirements.get('keywords'):
                prompt_parts.append(f"- Include these keywords: {requirements['keywords']}")
            
            if requirements.get('additional_notes'):
                prompt_parts.append(f"- Additional notes: {requirements['additional_notes']}")
        
        # Add word count requirement
        prompt_parts.append(f"\nTarget word count: approximately {order.word_count} words")
        
        # Add content type specific instructions
        content_instructions = {
            'blog_post': "Structure the content with a compelling headline, introduction, main body with subheadings, and conclusion.",
            'article': "Write in a professional, informative style with proper citations and references where appropriate.",
            'social_media': "Keep it engaging, shareable, and include relevant hashtags. Make it platform-appropriate.",
            'marketing_copy': "Focus on benefits, create urgency, and include a strong call-to-action.",
            'video_script': "Include scene descriptions, dialogue, and timing notes. Make it engaging for video format."
        }
        
        if order.content_type in content_instructions:
            prompt_parts.append(f"\nContent format: {content_instructions[order.content_type]}")
        
        return "\n".join(prompt_parts)
    
    def _calculate_quality_score(self, content, target_word_count):
        """Calculate a simple quality score for the generated content"""
        if not content:
            return 0.0
        
        # Basic quality metrics
        word_count = len(content.split())
        
        # Word count accuracy (closer to target = better)
        word_count_ratio = min(word_count / target_word_count, target_word_count / word_count)
        
        # Content length (not too short)
        length_score = min(len(content) / 500, 1.0)  # Normalize to 500 chars
        
        # Sentence variety (simple check for different sentence lengths)
        sentences = content.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        sentence_score = min(avg_sentence_length / 15, 1.0)  # Normalize to 15 words per sentence
        
        # Combine scores
        quality_score = (word_count_ratio * 0.4 + length_score * 0.3 + sentence_score * 0.3)
        
        return min(quality_score, 1.0)
    
    def preview_content(self, content_type, title, description, requirements):
        """Generate a preview of content without saving to database"""
        try:
            # Get the content template
            template = ContentTemplate.query.filter_by(
                content_type=content_type,
                is_active=True
            ).first()
            
            if not template:
                raise ValueError("Content template not found")
            
            # Build a simple prompt for preview
            prompt = f"{template.template_prompt.format(topic=title)}\n"
            if description:
                prompt += f"Context: {description}\n"
            
            prompt += "Generate a brief preview (100-150 words) of what the full content would look like."
            
            # Generate preview using OpenAI
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Use cheaper model for previews
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional content writer. Create a brief preview of content based on the user's requirements."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            return {
                'success': True,
                'preview': response.choices[0].message.content
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

