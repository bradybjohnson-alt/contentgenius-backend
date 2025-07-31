from src.models.user import db
from src.models.content_template import ContentTemplate

def initialize_content_templates():
    """Initialize default content templates if they don't exist"""
    
    templates = [
        {
            'name': 'Blog Post',
            'content_type': 'blog_post',
            'template_prompt': 'Write a comprehensive blog post about {topic}. Include an engaging introduction, well-structured body paragraphs with subheadings, and a compelling conclusion. Make it informative and engaging for the target audience.',
            'default_word_count': 800,
            'base_price': 25.0
        },
        {
            'name': 'Article',
            'content_type': 'article',
            'template_prompt': 'Create a detailed article about {topic}. Ensure it is well-researched, factual, and provides valuable insights. Include proper structure with introduction, main content sections, and conclusion.',
            'default_word_count': 1000,
            'base_price': 35.0
        },
        {
            'name': 'Social Media Post',
            'content_type': 'social_media',
            'template_prompt': 'Create engaging social media content about {topic}. Make it catchy, shareable, and appropriate for the specified platform. Include relevant hashtags and call-to-action.',
            'default_word_count': 150,
            'base_price': 10.0
        },
        {
            'name': 'Marketing Copy',
            'content_type': 'marketing_copy',
            'template_prompt': 'Write persuasive marketing copy for {topic}. Focus on benefits, create urgency, and include a strong call-to-action. Make it compelling and conversion-focused.',
            'default_word_count': 300,
            'base_price': 20.0
        },
        {
            'name': 'Video Script',
            'content_type': 'video_script',
            'template_prompt': 'Create a video script for {topic}. Include scene descriptions, dialogue, and timing notes. Make it engaging and suitable for the specified video length and style.',
            'default_word_count': 500,
            'base_price': 30.0
        }
    ]
    
    for template_data in templates:
        # Check if template already exists
        existing = ContentTemplate.query.filter_by(
            content_type=template_data['content_type']
        ).first()
        
        if not existing:
            template = ContentTemplate(**template_data)
            db.session.add(template)
    
    try:
        db.session.commit()
        print("Content templates initialized successfully")
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing content templates: {e}")

def create_admin_user():
    """Create default admin user if it doesn't exist"""
    from src.models.user import User
    
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@contentgenius.com',
            first_name='Admin',
            last_name='User',
            is_admin=True
        )
        admin.set_password('admin123')  # Change this in production
        
        db.session.add(admin)
        try:
            db.session.commit()
            print("Admin user created successfully")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin user: {e}")

