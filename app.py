from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
import threading
import jwt
import datetime
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this in production
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('articles', lazy=True))

# In-memory recently viewed articles per user (not persisted)
recently_viewed = {}
recently_viewed_lock = threading.Lock()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['user_id']).first()
            if not current_user:
                raise Exception('User not found')
        except Exception as e:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    if not username:
        return jsonify({'message': 'Username is required'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists'}), 400
    user = User(username=username)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'message': 'Invalid username'}), 401
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    return jsonify({'token': token})

# Helper: get user from JWT (now passed as current_user)
# CRUD Endpoints
@app.route('/articles', methods=['POST'])
@token_required
def create_article(current_user):
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    if not title or not content:
        abort(400, 'Title and content are required')
    article = Article(title=title, content=content, user_id=current_user.id)
    db.session.add(article)
    db.session.commit()
    return jsonify({'id': article.id, 'title': article.title, 'content': article.content}), 201

@app.route('/articles/batch', methods=['POST'])
@token_required
def create_articles_batch(current_user):
    data = request.get_json()
    if not isinstance(data, list):
        return jsonify({'message': 'Request body must be a list of articles'}), 400
    created = []
    for item in data:
        title = item.get('title')
        content = item.get('content')
        if not title or not content:
            continue  # skip invalid
        article = Article(title=title, content=content, user_id=current_user.id)
        db.session.add(article)
        created.append(article)
    db.session.commit()
    return jsonify([
        {'id': a.id, 'title': a.title, 'content': a.content} for a in created
    ]), 201

@app.route('/articles/<int:article_id>', methods=['GET'])
@token_required
def get_article(current_user, article_id):
    article = Article.query.filter_by(id=article_id, user_id=current_user.id).first()
    if not article:
        abort(404, 'Article not found')
    # Track recently viewed
    with recently_viewed_lock:
        rv = recently_viewed.setdefault(current_user.id, [])
        if article_id in rv:
            rv.remove(article_id)
        rv.insert(0, article_id)
        if len(rv) > 5:
            rv.pop()
    return jsonify({'id': article.id, 'title': article.title, 'content': article.content})

@app.route('/articles/<int:article_id>', methods=['PUT'])
@token_required
def update_article(current_user, article_id):
    article = Article.query.filter_by(id=article_id, user_id=current_user.id).first()
    if not article:
        abort(404, 'Article not found')
    data = request.get_json()
    article.title = data.get('title', article.title)
    article.content = data.get('content', article.content)
    db.session.commit()
    return jsonify({'id': article.id, 'title': article.title, 'content': article.content})

@app.route('/articles/<int:article_id>', methods=['DELETE'])
@token_required
def delete_article(current_user, article_id):
    article = Article.query.filter_by(id=article_id, user_id=current_user.id).first()
    if not article:
        abort(404, 'Article not found')
    db.session.delete(article)
    db.session.commit()
    return '', 204

@app.route('/articles', methods=['GET'])
@token_required
def list_articles(current_user):
    page = request.args.get('page', default=1, type=int)
    limit = request.args.get('limit', default=10, type=int)
    query = Article.query.filter_by(user_id=current_user.id).order_by(desc(Article.id))
    pagination = query.paginate(page=page, per_page=limit, error_out=False)
    articles = pagination.items
    return jsonify({
        'articles': [
            {'id': a.id, 'title': a.title, 'content': a.content} for a in articles
        ],
        'total': pagination.total,
        'page': page,
        'limit': limit
    })

@app.route('/recently_viewed', methods=['GET'])
@token_required
def get_recently_viewed(current_user):
    with recently_viewed_lock:
        rv_ids = recently_viewed.get(current_user.id, [])
    articles = Article.query.filter(Article.id.in_(rv_ids), Article.user_id == current_user.id).all()
    articles_dict = {a.id: a for a in articles}
    result = [
        {'id': articles_dict[aid].id, 'title': articles_dict[aid].title, 'content': articles_dict[aid].content}
        for aid in rv_ids if aid in articles_dict
    ]
    return jsonify(result)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', debug=True) 