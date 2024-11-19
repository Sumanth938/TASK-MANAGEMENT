import os
from urllib.parse import quote

JWT_ENCODING_ALGORITHM = 'HS256'
JWT_EXPIRY_WINDOW_IN_HOURS = 24
JWT_SECRET_KEY = "MhvR7A0r9MObSekgMqvDH84rr1wAQtD/w5tZNYF2t98="

POSTGRES_DB_USERNAME = 'maang'
POSTGRES_DB_PSWD = 'maang@123'
encoded_password = quote(POSTGRES_DB_PSWD, safe='')
POSTGRES_DB_URL = '178.16.139.18:5432'
POSTGRES_DB_NAME = 'dealmerge-dev'

POSTGRES_DATABASE_URL = 'sqlite:///./spp.db'
# POSTGRES_DATABASE_URL = f'postgresql://{POSTGRES_DB_USERNAME}:{encoded_password}@{POSTGRES_DB_URL}/{POSTGRES_DB_NAME}'
