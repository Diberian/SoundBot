#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试搜索查询扩展"""

import sys
sys.path.insert(0, '/Users/huyang/Downloads/SoundMind/backend')

from core.ucs_keywords import expand_query_with_ucs

# 测试查询扩展
test_queries = ['石头', '岩石', '石头撞击', '石头掉落']
print('查询扩展测试:')
for query in test_queries:
    expanded = expand_query_with_ucs(query)
    print(f"  '{query}' -> {expanded}")
