from secrets import token_urlsafe

from app import db
from app.eval_module.models import create_user
from config import BASE_DIR


def default_users():
    pwd = token_urlsafe(32)
    email = 'linkpics@lalic.com'
    create_user(name='LinkPICS', email=email, password=pwd)
    try:
        db.session.commit()
        with open(f'{BASE_DIR}/default_user.txt', 'w') as f:
            f.write(f'{email}\n{pwd}')

    except Exception as exc:
        print(f'[{__file__}] Error while committing user creation: {exc}')


if __name__ == '__main__':
    default_users()
