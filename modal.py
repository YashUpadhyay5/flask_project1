from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

# Article model
class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationship: one user can have many articles
    user = db.relationship('User', backref=db.backref('articles', lazy=True))

    def __repr__(self):
        return f'<Article {self.title}>'
