import re
import secrets
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer
from flask import current_app


class PasswordValidator:
    def __init__(self, policy=None):
        self.policy = policy or self._get_default_policy()
    
    def _get_default_policy(self):
        return {
            'min_length': 8,
            'require_uppercase': True,
            'require_lowercase': True,
            'require_digit': True,
            'require_special': True,
            'special_chars': '!@#$%^&*()_+-=[]{}|;:,.<>?'
        }
    
    def validate(self, password):
        errors = []
        score = 0
        
        if len(password) < self.policy['min_length']:
            errors.append(f'密码长度至少为 {self.policy["min_length"]} 个字符')
        else:
            score += 1
        
        if self.policy['require_uppercase'] and not re.search(r'[A-Z]', password):
            errors.append('密码需要包含大写字母')
        else:
            score += 1
        
        if self.policy['require_lowercase'] and not re.search(r'[a-z]', password):
            errors.append('密码需要包含小写字母')
        else:
            score += 1
        
        if self.policy['require_digit'] and not re.search(r'\d', password):
            errors.append('密码需要包含数字')
        else:
            score += 1
        
        if self.policy['require_special']:
            special_pattern = f'[{re.escape(self.policy["special_chars"])}]'
            if not re.search(special_pattern, password):
                errors.append(f'密码需要包含特殊字符 ({self.policy["special_chars"]})')
            else:
                score += 1
        
        if len(password) >= 12:
            score += 1
        
        level = self._get_strength_level(score)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'score': score,
            'max_score': 6,
            'level': level
        }
    
    def _get_strength_level(self, score):
        if score <= 2:
            return 'weak'
        elif score <= 4:
            return 'medium'
        else:
            return 'strong'


def generate_verification_token(user_id, token_type, expiration_hours=24):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    token = serializer.dumps({'user_id': user_id, 'type': token_type}, salt=token_type)
    return token


def verify_token(token, token_type, expiration_hours=24):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        data = serializer.loads(token, salt=token_type, max_age=expiration_hours * 3600)
        return data
    except:
        return None


def generate_random_password(length=12):
    import string
    alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password
