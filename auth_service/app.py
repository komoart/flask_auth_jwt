import os
import click
import logger

from datetime import timedelta
from flask import Flask
from flask_redoc import Redoc
from flask import request, send_from_directory
from flask.cli import with_appcontext
from flask_jwt_extended import JWTManager
from flask_swagger_ui import get_swaggerui_blueprint

from database.service import create_user, assign_role_to_user, get_users_roles
from database.models import Roles
from api.v1.blueprint import blueprint
from database.cache_redis import redis_app
from database.postgresql import init_db

ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
REFRESH_TOKEN_EXPIRES = timedelta(days=7)

app = Flask(__name__)

app.config['REDOC'] = {
    'spec_route': '/docs',
    'title': 'Flask Auth Service', }

redoc = Redoc(app, 'service.yml')

SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger_config.yml'
swagger_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': 'Auth service API documentation',
    },
)


@click.command(name='create-superuser')
@with_appcontext
def create_superuser():
    superuser = create_user(
        username=os.environ.get('ADMIN_USERNAME'),
        password=os.environ.get('ADMIN_PASSWORD'))
    role = Roles.query.filter_by(name='admin').first()
    if superuser and role:
        assign_role_to_user(superuser, role)
        logger.save_log.info(msg='Superuser was created')
    else:
        logger.save_log.error(msg='Error while creating superuser')


def create_app():
    app.config["JWT_SECRET_KEY"] = os.environ.get('JWT_SECRET_KEY')
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = ACCESS_TOKEN_EXPIRES
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = REFRESH_TOKEN_EXPIRES
    
    app.cli.add_command(create_superuser)
    
    app.register_blueprint(swagger_blueprint)
    app.register_blueprint(blueprint, url_prefix='/api/v1')
    
    JWTManager(app)
    
    @app.route('/static/<path:path>')
    def send_static(path):
        return send_from_directory('static', path)
    
    return app
    
    @jwt.token_in_blocklist_loader
    def check_if_token_is_revoked(jwt_header, jwt_payload: dict):
        user_agent = request.headers['user_agent']
        jti = jwt_payload["jti"]
        key = ':'.join((jti, user_agent))
        token_in_redis = redis_app.get(key)
        return token_in_redis is not None
    
    @jwt.additional_claims_loader
    def add_role_to_token(identity):
        roles = get_users_roles(identity)
        is_administrator = False
        is_manager = False
        for role in roles:
            if role.name == 'admin':
                is_administrator = True
            if role.name == 'manager':
                is_manager = True
        
        return {'is_administrator': is_administrator,
                'is_manager': is_manager}


def app_run():
    app = create_app()
    init_db(app)
    app.app_context().push()
    return app


if __name__ == "__main__":
    app_run()
