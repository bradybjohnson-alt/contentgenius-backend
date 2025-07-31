from src.models.user import db
from datetime import datetime

class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    generated_content = db.Column(db.Text, nullable=False)
    content_format = db.Column(db.String(20), default='markdown')  # markdown, html, plain_text
    quality_score = db.Column(db.Float, nullable=True)
    revision_count = db.Column(db.Integer, default=0)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Content {self.id} for Order {self.order_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'generated_content': self.generated_content,
            'content_format': self.content_format,
            'quality_score': self.quality_score,
            'revision_count': self.revision_count,
            'is_approved': self.is_approved,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

