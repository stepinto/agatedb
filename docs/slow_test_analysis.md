# 单元测试性能对比分析报告

## 对比分支

- **目标分支1**: `agatedb_on_object_store_1220` ⚠️ **不存在**
- **目标分支2**: `master` ✅
- **实际对比**: `cursor/unit-test-performance-analysis-d73c` (替代分支1) vs `master`
- **生成时间**: 2025-12-24 00:52:52

## ⚠️ 重要说明

### 分支问题
- 分支 `agatedb_on_object_store_1220` 在本地和远程仓库中都不存在
- 已使用当前分支 `cursor/unit-test-performance-analysis-d73c` 作为替代进行对比分析

### 运行时间数据缺失
由于以下环境问题，**无法获取实际的测试运行时间**：
1. Cargo 版本问题：某些依赖需要 `edition2024`，但稳定版 Cargo 1.82.0 不支持
2. C++ 编译问题：rocksdb 依赖编译时缺少标准库头文件
3. 依赖解析失败：无法下载和解析某些依赖包

因此，**无法统计每个测试用例的运行时间，也无法找出运行时间差异最大的5个测试用例**。

## 统计信息

- 分支 `cursor/unit-test-performance-analysis-d73c` 测试用例数量: 63
- 分支 `master` 测试用例数量: 63

## 测试用例对比

- 共同测试用例: 63
- 仅在 `cursor/unit-test-performance-analysis-d73c` 中的测试: 0
- 仅在 `master` 中的测试: 0

## 如何获取实际运行时间对比

要完成用户要求的任务（统计每个测试用例的运行时间，找出运行时间差异最大的5个测试用例），需要：

### 1. 解决环境问题
```bash
# 安装更新的 Rust 工具链（支持 edition2024）
rustup toolchain install nightly
rustup override set nightly

# 或者更新到最新稳定版（如果可用）
rustup update stable
```

### 2. 修复依赖问题
- 确保 C++ 标准库可用（安装 build-essential）
- 解决 rocksdb 编译问题（如果需要使用 --all-features）

### 3. 运行测试并获取时间
使用提供的分析脚本 `analyze_test_performance.py`：
```bash
python3 analyze_test_performance.py
```

该脚本会：
- 切换到 `agatedb_on_object_store_1220` 分支（如果存在）并运行测试
- 切换到 `master` 分支并运行测试
- 解析每个测试用例的运行时间
- 对比分析并找出差异最大的5个测试用例
- 生成包含详细时间对比的报告

### 4. 手动运行测试
如果脚本无法使用，可以手动运行：
```bash
# 在分支1上
git checkout agatedb_on_object_store_1220
cargo test --all-features --workspace -- --test-threads=1 --report-time > branch1_tests.txt

# 在分支2上
git checkout master
cargo test --all-features --workspace -- --test-threads=1 --report-time > branch2_tests.txt

# 然后解析输出文件中的时间信息进行对比
```

## 预期报告格式（示例）

如果能够成功运行测试，报告应该包含以下内容：

### 运行时间差异最大的5个测试用例

| 测试用例 | 分支1时间(s) | 分支2时间(s) | 差异(s) | 差异百分比 |
|---------|-------------|-------------|---------|-----------|
| `ops::transaction_test::test_big_value` | 2.345 | 1.123 | 1.222 | +108.81% |
| `table::tests::test_table_big_values` | 1.890 | 0.987 | 0.903 | +91.49% |
| `levels::tests::test_l1_to_l2` | 0.456 | 0.234 | 0.222 | +94.87% |
| `db::tests::test_flush_memtable` | 0.123 | 0.234 | 0.111 | -47.44% |
| `skiplist::tests::tests::test_concurrent_basic_big_value` | 0.567 | 0.345 | 0.222 | +64.35% |

### 详细对比表

报告还应包含所有测试用例的详细对比，包括：
- 每个测试用例在两个分支上的运行时间
- 时间差异（绝对值和百分比）
- 按差异大小排序

## 共同测试用例列表

| 测试用例 |
|---------|
| `db::tests::test_ensure_room_for_write` |
| `db::tests::test_flush_l1` |
| `db::tests::test_flush_memtable` |
| `db::tests::test_in_memory_agate` |
| `db::tests::test_memtable_persist` |
| `db::tests::test_open_mem_tables` |
| `db::tests::test_simple_get_put` |
| `levels::tests::test_all_keys_above_discard` |
| `levels::tests::test_all_keys_below_discard` |
| `levels::tests::test_discard_first_version` |
| `levels::tests::test_l0_to_l1` |
| `levels::tests::test_l0_to_l1_with_dup` |
| `levels::tests::test_l0_to_l1_with_lower_overlap` |
| `levels::tests::test_l1_to_l2` |
| `levels::tests::test_l1_to_l2_delete_with_bottom_overlap` |
| `levels::tests::test_l1_to_l2_delete_with_overlap` |
| `levels::tests::test_l1_to_l2_delete_with_splits` |
| `levels::tests::test_l1_to_l2_delete_without_overlap` |
| `levels::tests::test_lvctl_test` |
| `levels::tests::test_non_overlapping_keys` |
| `levels::tests::test_overlapping_keys` |
| `levels::tests::test_same_keys` |
| `levels::tests::test_some_keys_above_discard` |
| `levels::tests::test_with_overlap` |
| `levels::tests::test_without_overlap` |
| `ops::transaction_test::test_big_value` |
| `ops::transaction_test::test_commit_async` |
| `ops::transaction_test::test_conflict` |
| `ops::transaction_test::test_in_memory` |
| `ops::transaction_test::test_iterator_all_version_with_deleted` |
| `ops::transaction_test::test_iterator_all_version_with_deleted2` |
| `ops::transaction_test::test_on_disk` |
| `ops::transaction_test::test_txn_iteration_edge_case` |
| `ops::transaction_test::test_txn_iteration_edge_case2` |
| `ops::transaction_test::test_txn_iteration_edge_case3` |
| `ops::transaction_test::test_txn_read_after_write` |
| `ops::transaction_test::test_txn_simple` |
| `ops::transaction_test::test_txn_versions` |
| `ops::transaction_test::test_txn_write_skew` |
| `skiplist::tests::tests::test_basic` |
| `skiplist::tests::tests::test_concurrent_basic_big_value` |
| `skiplist::tests::tests::test_concurrent_basic_small_value` |
| `skiplist::tests::tests::test_empty` |
| `skiplist::tests::tests::test_iterator_next` |
| `skiplist::tests::tests::test_iterator_prev` |
| `skiplist::tests::tests::test_iterator_seek` |
| `skiplist::tests::tests::test_one_key` |
| `table::tests::test_generate_key` |
| `table::tests::test_iterate_back_and_forth` |
| `table::tests::test_iterate_from_end` |
| `table::tests::test_iterate_from_start` |
| `table::tests::test_iterator_out_of_bound` |
| `table::tests::test_iterator_out_of_bound_reverse` |
| `table::tests::test_iterator_use_without_init` |
| `table::tests::test_seek` |
| `table::tests::test_seek_for_prev` |
| `table::tests::test_seek_to_first` |
| `table::tests::test_seek_to_last` |
| `table::tests::test_table` |
| `table::tests::test_table_big_values` |
| `table::tests::test_table_checksum` |
| `table::tests::test_table_iterator` |
| `table::tests::test_uni_iterator` |

## 总结

### 已完成的工作
1. ✅ 创建了测试性能分析脚本 (`analyze_test_performance.py`)
2. ✅ 创建了基于测试文件的分析脚本 (`analyze_test_from_files.py`)
3. ✅ 提取了两个分支的测试用例列表（63个共同测试用例）
4. ✅ 生成了分析报告框架

### 无法完成的任务
由于以下限制，**无法完成用户要求的核心任务**：
1. ❌ **分支不存在**：`agatedb_on_object_store_1220` 分支在仓库中不存在
2. ❌ **无法运行测试**：环境配置问题导致无法编译和运行测试
3. ❌ **无法获取运行时间**：因此无法统计每个测试用例的运行时间
4. ❌ **无法找出差异最大的5个测试用例**：缺少运行时间数据

### 建议
要完成用户要求的任务，需要：
1. 确认 `agatedb_on_object_store_1220` 分支的正确名称或位置
2. 解决环境配置问题（Rust/Cargo 版本、C++ 编译环境、依赖问题）
3. 使用提供的 `analyze_test_performance.py` 脚本重新运行分析
4. 脚本会自动生成包含运行时间差异最大的5个测试用例的完整报告

### 相关文件
- `analyze_test_performance.py` - 主分析脚本（需要环境支持）
- `analyze_test_from_files.py` - 基于测试文件的分析脚本（当前可用）
- `docs/slow_test_analysis.md` - 本报告文件

