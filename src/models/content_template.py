from src.models.user import db
from datetime import datetime

class ContentTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)
    template_prompt = db.Column(db.Text, nullable=False)
    default_word_count = db.Column(db.Integer, default=500)
    base_price = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ContentTemplate {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'content_type': self.content_type,
            'template_prompt': self.template_prompt,
            'default_word_count': self.default_word_count,
            'base_price': self.base_price,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

