from .api import app

# Vercel が app 変数を探すため、明示的に公開
__all__ = ['app']
