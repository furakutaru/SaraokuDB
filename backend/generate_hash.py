from passlib.context import CryptContext

# パスワードをハッシュ化
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed_password = pwd_context.hash("uma_5272002")

print(f"Hashed password: {hashed_password}")
print(f"Hash length: {len(hashed_password)}")

# 検証
print(f"Password matches: {pwd_context.verify('uma_5272002', hashed_password)}")
