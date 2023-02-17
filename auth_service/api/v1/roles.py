from http import HTTPStatus

from database.service import create_role, delete_role, change_role
from database.models import Roles
from roles.administrator import admin_or_manager_required
from flask import jsonify, request, make_response


@admin_or_manager_required()
def create_role():
    role = request.values.get('role', None)
    if not role:
        return make_response('New role is empty', HTTPStatus.BAD_REQUEST)

    new_role = create_role(role)
    return jsonify(msg=f'Role {role} was successfully created')


@admin_or_manager_required()
def delete_role():
    role = request.values.get("role", None)
    if not role:
        return make_response('Role is empty', HTTPStatus.BAD_REQUEST)
    db_role = Roles.query.filter_by(name=role).first()
    if not db_role:
        return make_response('Role does not exist', HTTPStatus.NOT_FOUND)
    delete_role(db_role)
    return jsonify(msg=f'Role {role} was successfully deleted')


@admin_or_manager_required()
def change_role():
    role = request.values.get("role", None)
    new_role = request.values.get("new_name", None)
    if not role or not new_role:
        return make_response('Role or new name is empty', HTTPStatus.BAD_REQUEST)

    change_role(role, new_role)
    return jsonify(msg=f'Role {role} was successfully changed')


@admin_or_manager_required()
def roles_list():
    roles = Roles.query.all()
    output = [role.name for role in roles]
    return jsonify(roles=output)
