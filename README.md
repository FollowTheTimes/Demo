# 主机管理系统

## 项目介绍

主机管理系统是一个用于管理企业内部主机的系统，包含主机、城市、机房等模型，提供对应模型的增删改查接口，以及主机 ping 可达性探测接口。系统还会定期修改主机密码并加密记录，每天按城市和机房维度统计主机数量。

## 技术栈

- Python
- Django
- Celery
- Redis
- Django REST Framework
- Cryptography

## 功能特性

1. **模型管理**：
   - 城市管理：增删改查城市信息
   - 机房管理：增删改查机房信息，关联到城市
   - 主机管理：增删改查主机信息，关联到机房，包含加密的 root 密码

2. **API 接口**：
   - 城市增删改查接口
   - 机房增删改查接口
   - 主机增删改查接口
   - 主机 ping 可达性探测接口

3. **任务调度**：
   - 每隔 8 小时随机修改每台主机的密码并加密记录
   - 每天 00:00 按城市和机房维度统计主机数量，并把统计数据写入数据库

4. **中间件**：
   - 统计每个请求的请求耗时，并将耗时添加到响应头

## 安装步骤

1. **克隆仓库**：
   ```bash
   git clone https://github.com/FollowTheTimes/Demo.git
   cd Demo
   ```

2. **安装依赖**：
   ```bash
   pip install django celery redis cryptography djangorestframework
   ```

3. **启动 Redis 服务**：
   ```bash
   # Linux
   service redis-server start
   
   # Windows
   # 下载并安装 Redis，然后启动服务
   ```

4. **数据库迁移**：
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **启动 Celery worker 和 Celery beat**：
   ```bash
   celery -A host_management worker --beat --loglevel=info
   ```

6. **启动 Django 开发服务器**：
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

## API 接口

### 城市接口
- `GET /api/cities/` - 获取所有城市
- `POST /api/cities/` - 创建城市
- `GET /api/cities/{id}/` - 获取城市详情
- `PUT /api/cities/{id}/` - 更新城市
- `DELETE /api/cities/{id}/` - 删除城市

### 机房接口
- `GET /api/datacenters/` - 获取所有机房
- `POST /api/datacenters/` - 创建机房
- `GET /api/datacenters/{id}/` - 获取机房详情
- `PUT /api/datacenters/{id}/` - 更新机房
- `DELETE /api/datacenters/{id}/` - 删除机房

### 主机接口
- `GET /api/hosts/` - 获取所有主机
- `POST /api/hosts/` - 创建主机
- `GET /api/hosts/{id}/` - 获取主机详情
- `PUT /api/hosts/{id}/` - 更新主机
- `DELETE /api/hosts/{id}/` - 删除主机
- `GET /api/hosts/{id}/ping/` - 探测主机是否 ping 可达

## 任务调度

- **修改主机密码**：每隔 8 小时执行一次，随机生成新密码并加密存储
- **统计主机数量**：每天 00:00 执行，按城市和机房维度统计主机数量

## 中间件

- **请求耗时统计**：统计每个请求的处理时间，将耗时添加到响应头 `X-Request-Time`

## 项目结构

```
host_management/
├── host_management/       # 项目配置
│   ├── __init__.py
│   ├── asgi.py
│   ├── celery.py          # Celery 配置
│   ├── settings.py        # 项目设置
│   ├── urls.py            # 项目路由
│   └── wsgi.py
├── hosts/                 # 主机管理应用
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── middleware.py      # 请求耗时统计中间件
│   ├── migrations/        # 数据库迁移
│   ├── models.py          # 数据模型
│   ├── serializers.py     # 序列化器
│   ├── tasks.py           # Celery 任务
│   ├── tests.py
│   ├── urls.py            # 应用路由
│   └── views.py           # API 视图
├── .gitignore             # Git 忽略文件
├── manage.py              # Django 管理脚本
└── README.md              # 项目说明
```

## 注意事项

1. **密码加密**：主机的 root 密码使用 Fernet 加密存储，加密密钥存储在 `encryption_key.key` 文件中
2. **Redis 依赖**：系统依赖 Redis 作为 Celery 的 broker，请确保 Redis 服务正常运行
3. **任务调度**：Celery beat 负责定期执行任务，请确保 Celery 服务正常运行
4. **API 安全**：本系统为演示系统，未添加认证和授权，生产环境中请添加适当的安全措施

## 许可证

MIT
