import os
from flask_jwt_extended import JWTManager, create_access_token, verify_jwt_in_request, get_jwt
from datetime import timedelta
from functools import wraps
from flask import jsonify

def init_jwt(app):
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'default-dev-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    return JWTManager(app)

def create_token(user):
    additional_claims = {
        "user_id": user['id'],
        "name": user['name'],
        "email": user['email'],
        "role": user['role']
    }
    # Using user_id as identity
    return create_access_token(identity=str(user['id']), additional_claims=additional_claims)

def admin_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") != "admin":
                return jsonify(msg="Admins only!"), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper
