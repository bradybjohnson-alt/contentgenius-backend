from src.models.user import db
from datetime import datetime
import json

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)  # blog_post, article, social_media, marketing_copy, video_script
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    requirements = db.Column(db.Text, nullable=True)  # JSON string
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, cancelled
    priority = db.Column(db.String(10), default='medium')  # low, medium, high
    word_count = db.Column(db.Integer, nullable=True)
    price = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    content = db.relationship('Content', backref='order', lazy=True, uselist=False)
    payments = db.relationship('Payment', backref='order', lazy=True)

    def __repr__(self):
        return f'<Order {self.id}: {self.title}>'

    def set_requirements(self, requirements_dict):
        """Set requirements as JSON string"""
        self.requirements = json.dumps(requirements_dict)

    def get_requirements(self):
        """Get requirements as dictionary"""
        if self.requirements:
            try:
                return json.loads(self.requirements)
            except json.JSONDecodeError:
                return {}
        return {}

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'content_type': self.content_type,
            'title': self.title,
            'description': self.description,
            'requirements': self.get_requirements(),
            'status': self.status,
            'priority': self.priority,
            'word_count': self.word_count,
            'price': self.price,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

