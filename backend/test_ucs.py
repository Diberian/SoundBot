#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 UCS 关键词加载"""

import sys
import time

# 清除缓存
if 'core.ucs_keywords' in sys.modules:
    del sys.modules['core.ucs_keywords']

from core.ucs_keywords import load_ucs_keywords, expand_query_with_ucs

# 测试加载时间
start = time.time()
keywords = load_ucs_keywords()
load_time = time.time() - start

print(f'✅ UCS 关键词加载完成: {len(keywords)} 个映射')
print(f'⏱️ 加载时间: {load_time:.3f}秒')
print()

# 显示一些样本
print('样本关键词映射:')
for i, (cn, en_list) in enumerate(list(keywords.items())[:10]):
    print(f'  {cn} -> {en_list[:3]}...')
print()

# 测试查询扩展
test_queries = ['石头', '岩石', '风声', '爆炸', '门铃', '汽车', '气体']
print('查询扩展测试:')
for query in test_queries:
    start = time.time()
    expanded = expand_query_with_ucs(query)
    expand_time = (time.time() - start) * 1000
    print(f"  '{query}' -> {expanded[:5]}... ({expand_time:.2f}ms)")
