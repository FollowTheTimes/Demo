import requests
import time
import threading

# 测试配置
BASE_URL = 'http://localhost:8000'
SECKILL_ENDPOINT = '/api/seckill/'
ACTIVITY_ID = 101  # 使用一个正在进行中的活动 ID
USER_COUNT = 10  # 模拟用户数量

# 结果统计
success_count = 0
fail_count = 0
response_times = []
lock = threading.Lock()

def test_seckill(user_id):
    """测试秒杀接口"""
    global success_count, fail_count, response_times
    
    # 构造请求数据
    data = {
        'user_id': user_id,
        'activity_id': ACTIVITY_ID
    }
    
    try:
        # 记录请求开始时间
        request_start = time.time()
        
        # 发送 POST 请求
        response = requests.post(f'{BASE_URL}{SECKILL_ENDPOINT}', data=data, timeout=10)
        
        # 记录响应时间
        response_time = time.time() - request_start
        
        # 解析响应
        result = response.json()
        
        with lock:
            response_times.append(response_time)
            if result.get('code') == 200:
                success_count += 1
                print(f'用户 {user_id} 秒杀成功: {result.get("message")}')
            else:
                fail_count += 1
                print(f'用户 {user_id} 秒杀失败: {result.get("message")}')
                
    except Exception as e:
        with lock:
            fail_count += 1
            print(f'用户 {user_id} 请求异常: {e}')

def run_stress_test():
    """运行压力测试"""
    start_time = time.time()
    
    print(f'开始模拟 {USER_COUNT} 个用户并发秒杀...')
    
    # 创建并启动线程
    threads = []
    for i in range(1, USER_COUNT + 1):
        thread = threading.Thread(target=test_seckill, args=(i,))
        threads.append(thread)
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    # 计算统计信息
    total_time = time.time() - start_time
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    max_response_time = max(response_times) if response_times else 0
    min_response_time = min(response_times) if response_times else 0
    
    # 输出结果
    print('\n=== 压力测试结果 ===')
    print(f'总用户数: {USER_COUNT}')
    print(f'成功数: {success_count}')
    print(f'失败数: {fail_count}')
    print(f'总耗时: {total_time:.2f} 秒')
    print(f'平均响应时间: {avg_response_time:.4f} 秒')
    print(f'最大响应时间: {max_response_time:.4f} 秒')
    print(f'最小响应时间: {min_response_time:.4f} 秒')
    print(f'QPS: {USER_COUNT / total_time:.2f}')

if __name__ == '__main__':
    run_stress_test()