# 秒杀系统项目

## 项目简介

这是一个基于 Django 开发的秒杀系统，支持高并发秒杀场景，具备完整的商品管理、活动管理、订单管理和用户管理功能。系统采用 Redis 进行库存管理和分布式锁，使用 Celery 进行异步任务处理，确保秒杀过程的稳定性和可靠性。

## 技术栈

- **后端框架**：Django 6.0.3
- **数据库**：MySQL
- **缓存**：Redis
- **异步任务**：Celery
- **部署**：uWSGI + Nginx
- **容器化**：Docker + Docker Compose
- **前端**：HTML5 + CSS3 + JavaScript

## 功能特性

### 核心功能
- **秒杀活动管理**：创建、编辑、删除秒杀活动
- **商品管理**：添加、编辑、删除商品信息
- **订单管理**：查看、处理秒杀订单
- **用户管理**：用户注册、登录、权限控制
- **高并发处理**：Redis 分布式锁、Lua 脚本原子操作
- **异步任务**：Celery 异步创建订单
- **限流机制**：用户级、IP级、全局级限流
- **容错机制**：Redis 不可用时回退到数据库事务

### 性能优化
- **Redis 连接池**：优化 Redis 连接管理
- **数据库查询优化**：使用 select_related、only 等减少数据库查询
- **批量处理**：支持批量限流检查
- **重试机制**：网络或锁竞争时的自动重试

### 安全性
- **CSRF 防护**：防止跨站请求伪造
- **XSS 防护**：防止跨站脚本攻击
- **Clickjacking 防护**：防止点击劫持
- **登录尝试限制**：防止暴力破解
- **密码强度验证**：强制密码复杂度

## 安装步骤

### 1. 克隆仓库

```bash
git clone https://github.com/your-username/seckill-project.git
cd seckill-project
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env` 文件并修改配置：

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库和 Redis 连接信息
```

### 4. 数据库迁移

```bash
python manage.py migrate
```

### 5. 生成测试数据

```bash
python manage.py generate_test_data
```

### 6. 加载库存到 Redis

```bash
python manage.py load_stock_to_redis
```

### 7. 启动服务

#### 开发环境

```bash
python manage.py runserver
```

#### 生产环境（Docker）

```bash
docker-compose up -d
```

## 使用方法

### 访问地址
- **前端**：http://localhost
- **管理后台**：http://localhost/admin/
- **默认管理员账号**：admin / admin123

### 测试秒杀功能
1. 访问首页，在 "测试秒杀功能" 部分选择用户和商品
2. 输入秒杀价格（至少比原价优惠300元）
3. 设置开始时间和结束时间
4. 点击 "执行秒杀" 按钮
5. 查看秒杀结果

### 管理功能
1. 登录管理后台
2. 在侧边栏选择相应的功能模块：
   - **商品**：管理商品信息
   - **秒杀活动**：管理秒杀活动
   - **订单**：查看秒杀订单
   - **用户**：管理系统用户

## 项目结构

```
seckill_project/
├── apps/
│   ├── seckill/         # 秒杀核心功能
│   ├── users/           # 用户管理
│   └── monitor/         # 系统监控
├── seckill_project/
│   ├── settings/        # 配置文件
│   └── templates/       # 模板文件
├── templates/           # 自定义模板
├── utils/               # 工具函数
├── docker/              # Docker 配置
├── nginx/               # Nginx 配置
├── logs/                # 日志文件
├── .env                 # 环境变量配置
├── docker-compose.yml   # Docker Compose 配置
├── requirements.txt     # 依赖项
└── manage.py            # Django 管理脚本
```

## API 接口

### 秒杀接口
- **URL**：`/api/seckill/`
- **方法**：POST
- **参数**：`user_id` (用户ID), `activity_id` (活动ID)
- **返回**：JSON 格式的秒杀结果

### 订单状态查询
- **URL**：`/api/order/status/`
- **方法**：GET
- **参数**：`order_id` (订单ID)
- **返回**：JSON 格式的订单状态

### 创建秒杀活动
- **URL**：`/api/create_activity/`
- **方法**：POST
- **参数**：`product_id` (商品ID), `seckill_price` (秒杀价格), `start_time` (开始时间), `end_time` (结束时间)
- **返回**：JSON 格式的活动创建结果

## 压力测试

### 运行压力测试

```bash
python stress_test.py
```

### 测试参数配置

在 `stress_test.py` 文件中可以修改以下参数：
- `USER_COUNT`：并发用户数
- `ACTIVITY_ID`：测试的活动ID
- `REQUEST_INTERVAL`：请求间隔时间

## 注意事项

1. **环境要求**：
   - Python 3.8+
   - MySQL 5.7+
   - Redis 6.0+
   - Docker (可选，用于容器化部署)

2. **生产环境配置**：
   - 确保 `DEBUG=False`
   - 配置 `SECRET_KEY` 为安全的随机字符串
   - 配置正确的数据库和 Redis 连接信息
   - 配置 Nginx 和 uWSGI 以提高性能

3. **性能优化**：
   - 生产环境建议使用 Redis 集群
   - 数据库建议开启查询缓存
   - 考虑使用 CDN 加速静态资源

4. **安全注意**：
   - 定期更新依赖包
   - 监控系统日志，及时发现异常
   - 定期备份数据库

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
