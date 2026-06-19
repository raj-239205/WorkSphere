from database.db_manager import db
from datetime import datetime

class ActivityLog(db.Model):
    """Audit Logging System entity."""
    __tablename__ = 'activity_logs'
    
    log_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True)
    action_type = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    old_value = db.Column(db.Text, nullable=True)  # Store JSON state before change
    new_value = db.Column(db.Text, nullable=True)  # Store JSON state after change
    
    # Optional relationship mapping back to User who triggered the action
    user = db.relationship('User', backref=db.backref('activity_logs', lazy=True))

    def __init__(self, user_id: int = None, action_type: str = None, 
                 ip_address: str = None, old_value: str = None, new_value: str = None, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.action_type = action_type
        self.ip_address = ip_address
        self.old_value = old_value
        self.new_value = new_value

    def to_dict(self) -> dict:
        return {
            'log_id': self.log_id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else 'System',
            'action_type': self.action_type,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'ip_address': self.ip_address,
            'old_value': self.old_value,
            'new_value': self.new_value
        }
