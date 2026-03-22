import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 根据环境变量选择配置
ENV = os.getenv('ENV', 'dev')

if ENV == 'prod':
    from .prod import *
else:
    from .dev import *
