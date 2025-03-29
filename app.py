import os
import sys
from flask import request, url_for, redirect, flash
import click
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy  # 导入扩展类
from markupsafe import escape

WIN = sys.platform.startswith('win')
if WIN:  # 如果是 Windows 系统，使用三个斜线
    prefix = 'sqlite:///'
else:  # 否则使用四个斜线
    prefix = 'sqlite:////'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
app.config['SECRET_KEY'] = 'dev'  # 等同于 app.secret_key = 'dev'
# 在扩展类实例化前加载配置
db = SQLAlchemy(app)

# 创建数据库模型
class User(db.Model):  # 表名将会是 user（自动生成，小写处理）
    id = db.Column(db.Integer, primary_key=True)  # 主键
    name = db.Column(db.String(20))  # 名字


class Movie(db.Model):  # 表名将会是 movie
    id = db.Column(db.Integer, primary_key=True)  # 主键
    title = db.Column(db.String(60))  # 电影标题
    year = db.Column(db.String(4))  # 电影年份

# 模板上下文处理函数
# 这个函数返回的变量（以字典键值对的形式）将会统一注入到每一个模板的上下文环境中，因此可以直接在模板中使用
@app.context_processor
def inject_user():  # 函数名可以随意修改
    user = User.query.first()
    return dict(user=user)  # 需要返回字典，等同于 return {'user': user}


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':  # 判断是否是 POST 请求
        # 获取表单数据
        title = request.form.get('title')  # 传入表单对应输入字段的 name 值
        year = request.form.get('year')
        # 验证数据
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('Invalid input.')  # 显示错误提示
            return redirect(url_for('index'))  # 重定向回主页
        # 保存表单数据到数据库
        movie = Movie(title=title, year=year)  # 创建记录
        db.session.add(movie)  # 添加到数据库会话
        db.session.commit()  # 提交数据库会话
        flash('Item created.')  # 显示成功创建的提示
        return redirect(url_for('index'))  # 重定向回主页

    movies = Movie.query.all()
    return render_template('index.html', movies=movies)

@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
def edit(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    if request.method == 'POST':  # 处理编辑表单的提交请求
        title = request.form['title']
        year = request.form['year']

        if not title or not year or len(year) != 4 or len(title) > 60:
            flash('Invalid input.')
            return redirect(url_for('edit', movie_id=movie_id))  # 重定向回对应的编辑页面

        movie.title = title  # 更新标题
        movie.year = year  # 更新年份
        db.session.commit()  # 提交数据库会话
        flash('Item updated.')
        return redirect(url_for('index'))  # 重定向回主页

    return render_template('edit.html', movie=movie)  # 传入被编辑的电影记录

@app.route('/movie/delete/<int:movie_id>', methods=['POST'])  # 限定只接受 POST 请求
def delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)  # 获取电影记录
    db.session.delete(movie)  # 删除对应的记录
    db.session.commit()  # 提交数据库会话
    flash('Item deleted.')
    return redirect(url_for('index'))  # 重定向回主页

@app.route('/user/<name>')
def user_page(name):
    return f'User: {escape(name)}'

@app.cli.command()  # 注册为命令，可以传入 name 参数来自定义命令
@click.option('--drop', is_flag=True, help='Create after drop.')  # 设置选项
def initdb(drop):
    """Initialize the database."""
    if drop:  # 判断是否输入了选项
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.')  # 输出提示信息

# 下面是为了测试数据库操作
"""
>>> from app import User, Movie  # 导入模型类
>>> user = User(name='Grey Li')  # 创建一个 User 记录
>>> m1 = Movie(title='Leon', year='1994')  # 创建一个 Movie 记录
>>> m2 = Movie(title='Mahjong', year='1996')  # 再创建一个 Movie 记录
>>> db.session.add(user)  # 把新创建的记录添加到数据库会话
>>> db.session.add(m1)
>>> db.session.add(m2)
>>> db.session.commit()  # 提交数据库会话，只需要在最后调用一次即可
"""

# 通过对模型类的属性进行使用，就可以对数据库进行操作
# 下面是为了测试数据
"""all()	返回包含所有查询记录的列表
first()	返回查询的第一条记录，如果未找到，则返回 None
get(id)	传入主键值作为参数，返回指定主键值的记录，如果未找到，则返回 None
count()	返回查询结果的数量
first_or_404()	返回查询的第一条记录，如果未找到，则返回 404 错误响应
get_or_404(id)	传入主键值作为参数，返回指定主键值的记录，如果未找到，则返回 404 错误响应
paginate()	返回一个 Pagination 对象，可以对记录进行分页处理"""
# 查询操作，通过query
"""
>>> from app import Movie  # 导入模型类
>>> movie = Movie.query.first()  # 获取 Movie 模型的第一个记录（返回模型类实例）
>>> movie.title  # 对返回的模型类实例调用属性即可获取记录的各字段数据
"""
# 更新，使用get
"""
>>> movie = Movie.query.get(2)
>>> movie.title = 'WALL-E'  # 直接对实例属性赋予新的值即可
>>> movie.year = '2008'
>>> db.session.commit()  # 注意仍然需要调用这一行来提交改动
"""
# 删除
"""
>>> movie = Movie.query.get(1)
>>> db.session.delete(movie)  # 使用 db.session.delete() 方法删除记录，传入模型实例
>>> db.session.commit()  # 提交改动
"""

# 自定义命令forge，添加虚拟数据
@app.cli.command()
def forge():
    """Generate fake data."""
    db.create_all()

    # 全局的两个变量移动到这个函数内
    name = 'Grey Li'
    movies = [
        {'title': 'My Neighbor Totoro', 'year': '1988'},
        {'title': 'Dead Poets Society', 'year': '1989'},
        {'title': 'A Perfect World', 'year': '1993'},
        {'title': 'Leon', 'year': '1994'},
        {'title': 'Mahjong', 'year': '1996'},
        {'title': 'Swallowtail Butterfly', 'year': '1996'},
        {'title': 'King of Comedy', 'year': '1999'},
        {'title': 'Devils on the Doorstep', 'year': '1999'},
        {'title': 'WALL-E', 'year': '2008'},
        {'title': 'The Pork of Music', 'year': '2012'},
    ]

    user = User(name=name)
    db.session.add(user)
    for m in movies:
        movie = Movie(title=m['title'], year=m['year'])
        db.session.add(movie)

    db.session.commit()
    click.echo('Done.')

if __name__ == '__main__':
    app.run(debug=True, port=8888)