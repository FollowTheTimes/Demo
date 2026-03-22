import redis
import time
import uuid

class RedisLock:
    """Redis 分布式锁类"""
    
    def __init__(self, redis_client, key, timeout=10):
        """
        初始化锁
        :param redis_client: Redis 客户端实例
        :param key: 锁的 key
        :param timeout: 锁的超时时间（秒）
        """
        self.redis_client = redis_client
        self.key = key
        self.timeout = timeout
        self.identifier = str(uuid.uuid4())
    
    def acquire(self):
        """
        获取锁
        :return: 是否获取成功
        """
        # 使用 SET NX EX 命令获取锁
        # NX: 仅当 key 不存在时才设置
        # EX: 设置过期时间
        result = self.redis_client.set(self.key, self.identifier, nx=True, ex=self.timeout)
        return result is not None
    
    def release(self):
        """
        释放锁
        使用 Lua 脚本确保原子性操作
        :return: 是否释放成功
        """
        # Lua 脚本：只有当锁的 value 与当前 identifier 匹配时才删除
        lua_script = """
        if redis.call('get', KEYS[1]) == ARGV[1] then
            return redis.call('del', KEYS[1])
        else
            return 0
        end
        """
        result = self.redis_client.eval(lua_script, 1, self.key, self.identifier)
        return result == 1
    
    def __enter__(self):
        """
        上下文管理器进入方法
        """
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        上下文管理器退出方法
        """
        self.release()
