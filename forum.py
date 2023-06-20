from flask import Flask, render_template, request, redirect, url_for, flash ,g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine,DateTime
from datetime import datetime
from flask_paginate import Pagination, get_page_args
import markdown
from markdown import Markdown






app = Flask(__name__, template_folder='templates',static_folder='static')
app.config['SECRET_KEY'] = 'your_secret_key'  # 设置一个密钥以用于会话
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///forum.db'  # 数据库的URI
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
engine = create_engine('sqlite:///forum.db')
# 创建会话工厂
Session = sessionmaker(bind=engine)

# 创建会话实例
session = Session()


# 用户模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    create_on = db.Column(DateTime, default=datetime.now)


# 帖子模型
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    categories = db.Column(db.String(50))
    content = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', backref=db.backref('posts', lazy='dynamic'))
    create_on = db.Column(DateTime, default=datetime.now)


# 评论模型
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', backref=db.backref('comments', lazy='dynamic'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    post = db.relationship('Post', backref=db.backref('comments', lazy='dynamic'))
    create_on = db.Column(DateTime, default=datetime.now)



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/',methods=['GET', 'POST'])
def index():
    page_size = 10
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    posts = Post.query.order_by(Post.create_on.desc()).offset(offset).limit(per_page).all()
    total_posts = Post.query.count()
    pagination = Pagination(page=page, per_page=page_size, total=total_posts)
    if request.method == 'POST':
        # 处理按键点击事件
        button_name = request.form['button_name']
        if button_name == 'search':
            # 执行搜索操作
            keyword = request.form['keyword']

            # 在这里编写实际的搜索逻辑
            # 可以向数据库查询数据，返回搜索结果等
            post_title = Post.query.filter(Post.title.contains(keyword)).all()
            post_content = Post.query.filter(Post.content.contains(keyword)).all()
            posts = set(post_title+post_content)
            # 示例：输出搜索关键字到控制台
            # print('Searching for:', keyword)

    return render_template('index.html', posts=posts, pagination=pagination)

@app.route('/process_pagination', methods=['POST'])
def process_pagination():
    selected_page_size = request.form.get('page_size')
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    posts = Post.query.order_by(Post.create_on.desc()).offset(offset).limit(selected_page_size).all()
    total_posts = Post.query.count()
    pagination = Pagination(page=page, per_page=int(selected_page_size), total=total_posts)

    return render_template('index.html', posts=posts, pagination=pagination,page_size = selected_page_size,page = page)

@app.route('/categories')
def get_categories():
    # categories = Post.categories.distinct()
    # print((Post.categories))
    # categories = set(Post.categories.unique)
    categories = db.session.query(Post.categories).distinct().group_by(Post.categories).all()
    categories =[j for i in categories for j in i if j and j!='None']
    print(categories)

    return render_template('categories.html',categories= categories,)

@app.route('/categories/<categories>',methods = ['POST','GET'])
def get_categories_detail(categories):
    g.category = categories
    category_detail = Post.query.filter_by(categories=categories)

    return render_template('categories_detail.html',category_detail = category_detail)

@app.route('/post/<int:post_id>')
def post_detail(post_id):
    post = Post.query.order_by(Post.create_on.desc()).get(post_id)
    return render_template('post_detail.html', post=post)


@app.route('/post/create', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        categories = request.form['categories']
        content = request.form['content']
        md = Markdown()
        content = md.convert(content)
        post = Post(title=title, categories=categories,content=content, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Post created successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('create_post.html')

def get_current_user_id():
    if current_user.is_authenticated:
        return current_user.id
    else:
        return None
@app.route('/user')
@login_required
def get_user():
    user_id = get_current_user_id()  # 获取当前用户的ID，这里假设有一个函数可以获取当前用户的ID
    user = User.query.get(user_id)  # 根据用户ID从数据库中获取用户对象
    g.username = user.username
    try:
        user_posts = user.posts  # 获取用户已发表的帖子列表


    except:
        user_posts = []
    finally:
        return render_template('user.html', user_posts=user_posts)


@app.route('/post/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get(post_id)
    if post.author != current_user:
        flash('You are not allowed to edit this post!', 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        db.session.commit()
        flash('Post updated successfully!', 'success')
        return redirect(url_for('post_detail', post_id=post.id))
    return render_template('edit_post.html',post=post)
@app.route('/post/delete/<int:post_id>', methods=['POST','GET'])
@login_required
def delete_post(post_id):
    post = Post.query.get(post_id)
    if post.author != current_user:
        flash('You are not allowed to delete this post!', 'danger')
        return redirect(url_for('index'),)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted successfully!', 'success')
    return redirect(url_for('index'))


@app.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def create_comment(post_id):
    post = Post.query.get(post_id)
    content = request.form['content']
    comment = Comment(content=content, author=current_user, post=post)
    db.session.add(comment)
    db.session.commit()
    flash('Comment added successfully!', 'success')
    return redirect(url_for('post_detail', post_id=post.id))


@app.route('/comment/delete/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)
    # comment = session.query(Comment).options(joinedload(Comment.post)).first()
    print(session,comment)
    comment = session.merge(comment)
    post = comment.post

    if comment.author != current_user:
        flash('You are not allowed to delete this comment!', 'danger')
        return redirect(url_for('index'))

    # db.session.delete(comment)
    # db.session.commit()
    post.delete()  # 删除帖子
    flash('Comment deleted successfully!', 'success')
    return redirect(url_for('post_detail', post_id=comment.post.id))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User(username=username, password=password)
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
        except:
            # 回滚事务
            db.session.rollback()

            # 显示错误消息给用户
            flash('你易经注册过了，请直接登录！')
        finally:
            return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        # db.drop_all()
        db.create_all()
    app.run(debug=True)

