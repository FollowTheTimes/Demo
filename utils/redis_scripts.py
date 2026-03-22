# 限流脚本：使用 Redis 的 ZSET 实现真正的滑动窗口
RATE_LIMIT_SCRIPT = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

# 移除窗口外的记录
redis.call('ZREMRANGEBYSCORE', key, 0, now - window)

# 统计当前窗口内的请求数
local current = redis.call('ZCARD', key)

if current >= limit then
    return 0
end

# 添加当前请求记录
redis.call('ZADD', key, now, now)

# 设置过期时间，避免内存泄漏
redis.call('EXPIRE', key, window)

return 1
"""

# 批量限流脚本：同时检查多个限流规则
BATCH_RATE_LIMIT_SCRIPT = """
local keys = KEYS
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

for i, key in ipairs(keys) do
    # 移除窗口外的记录
    redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
    
    # 统计当前窗口内的请求数
    local current = redis.call('ZCARD', key)
    
    if current >= limit then
        return 0
    end
end

# 所有限流规则都通过，添加当前请求记录
for i, key in ipairs(keys) do
    redis.call('ZADD', key, now, now)
    redis.call('EXPIRE', key, window)
end

return 1
"""

# 扣减库存脚本：原子性检查库存并扣减
SECKILL_STOCK_SCRIPT = """
local stock_key = KEYS[1]
local stock_field = KEYS[2]
local decrement = tonumber(ARGV[1])

local current_stock = tonumber(redis.call('HGET', stock_key, stock_field) or '0')

if current_stock < decrement then
    return -1
end

local new_stock = redis.call('HINCRBY', stock_key, stock_field, -decrement)
return new_stock
"""
