from gevent import monkey

monkey.patch_all()

from app import app

from db import db, init_db
from db_models import User

# Подготоваливаем контекст и создаём таблицы
init_db(app)
app.app_context().push()
db.create_all()

# Insert-запросы
admin = User(login='admin', password='password')
db.session.add(admin)
db.session.commit()

# Select-запросы
User.query.all()
User.query.filter_by(login='admin').first()
