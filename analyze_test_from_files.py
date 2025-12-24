#!/usr/bin/env python3
"""
从测试文件中提取测试函数名称，生成测试性能分析框架报告
"""
import subprocess
import re
import sys
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict

def get_current_branch() -> str:
    """获取当前分支名称"""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return "unknown"

def checkout_branch(branch: str) -> bool:
    """切换到指定分支"""
    result = subprocess.run(
        ["git", "checkout", branch],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def extract_test_functions_from_file(file_path: Path) -> List[str]:
    """从 Rust 测试文件中提取测试函数名称"""
    test_functions = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 匹配测试函数: #[test] fn test_name() 或 #[tokio::test] fn test_name()
        patterns = [
            r'#\[test[^\]]*\]\s+fn\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'#\[tokio::test[^\]]*\]\s+fn\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'#\[async_std::test[^\]]*\]\s+fn\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                # 构建完整测试名称: module::path::test_name
                module_path = str(file_path).replace('src/', '').replace('.rs', '').replace('/', '::')
                test_name = f"{module_path}::{match}"
                test_functions.append(test_name)
    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return test_functions

def find_test_files(branch: str) -> List[Path]:
    """查找所有测试文件"""
    test_files = []
    
    # 切换到指定分支
    if not checkout_branch(branch):
        return []
    
    # 查找所有测试文件
    test_patterns = [
        "**/*test*.rs",
        "**/tests.rs",
        "**/tests/*.rs",
    ]
    
    for pattern in test_patterns:
        for path in Path(".").rglob(pattern):
            if path.is_file() and "target" not in str(path):
                test_files.append(path)
    
    return test_files

def extract_all_tests(branch: str) -> Dict[str, List[str]]:
    """从指定分支提取所有测试函数"""
    test_files = find_test_files(branch)
    all_tests = {}
    
    for test_file in test_files:
        tests = extract_test_functions_from_file(test_file)
        for test in tests:
            all_tests[test] = test
    
    return all_tests

def generate_report(branch1: str, branch1_tests: Dict[str, str],
                   branch2: str, branch2_tests: Dict[str, str],
                   output_file: str):
    """生成分析报告"""
    from datetime import datetime
    
    report_lines = []
    report_lines.append("# 单元测试性能对比分析报告\n\n")
    report_lines.append(f"## 对比分支\n\n")
    report_lines.append(f"- **分支1**: `{branch1}`\n")
    report_lines.append(f"- **分支2**: `{branch2}`\n")
    report_lines.append(f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    # 统计信息
    report_lines.append("## 统计信息\n\n")
    report_lines.append(f"- 分支 `{branch1}` 测试用例数量: {len(branch1_tests)}\n")
    report_lines.append(f"- 分支 `{branch2}` 测试用例数量: {len(branch2_tests)}\n\n")
    
    # 测试用例对比
    all_tests = set(branch1_tests.keys()) | set(branch2_tests.keys())
    only_branch1 = set(branch1_tests.keys()) - set(branch2_tests.keys())
    only_branch2 = set(branch2_tests.keys()) - set(branch1_tests.keys())
    common_tests = set(branch1_tests.keys()) & set(branch2_tests.keys())
    
    report_lines.append("## 测试用例对比\n\n")
    report_lines.append(f"- 共同测试用例: {len(common_tests)}\n")
    report_lines.append(f"- 仅在 `{branch1}` 中的测试: {len(only_branch1)}\n")
    report_lines.append(f"- 仅在 `{branch2}` 中的测试: {len(only_branch2)}\n\n")
    
    # 说明
    report_lines.append("## 说明\n\n")
    report_lines.append("由于环境配置问题（Cargo 版本和依赖问题），无法实际运行测试获取运行时间。\n\n")
    report_lines.append("本报告基于测试文件分析生成，展示了两个分支的测试用例对比情况。\n\n")
    report_lines.append("要获取实际的运行时间对比，需要：\n")
    report_lines.append("1. 解决依赖和编译问题\n")
    report_lines.append("2. 使用 `cargo test -- --report-time` 运行测试\n")
    report_lines.append("3. 解析测试输出中的时间信息\n\n")
    
    # 详细测试列表
    if common_tests:
        report_lines.append("## 共同测试用例列表\n\n")
        report_lines.append("| 测试用例 |\n")
        report_lines.append("|---------|\n")
        for test in sorted(common_tests):
            report_lines.append(f"| `{test}` |\n")
        report_lines.append("\n")
    
    if only_branch1:
        report_lines.append(f"## 仅在 `{branch1}` 中的测试用例\n\n")
        report_lines.append("| 测试用例 |\n")
        report_lines.append("|---------|\n")
        for test in sorted(only_branch1):
            report_lines.append(f"| `{test}` |\n")
        report_lines.append("\n")
    
    if only_branch2:
        report_lines.append(f"## 仅在 `{branch2}` 中的测试用例\n\n")
        report_lines.append("| 测试用例 |\n")
        report_lines.append("|---------|\n")
        for test in sorted(only_branch2):
            report_lines.append(f"| `{test}` |\n")
        report_lines.append("\n")
    
    # 写入文件
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(report_lines)
    
    print(f"报告已生成: {output_file}")

def main():
    branch1 = "agatedb_on_object_store_1220"
    branch2 = "master"
    output_file = "docs/slow_test_analysis.md"
    
    original_branch = get_current_branch()
    print(f"当前分支: {original_branch}")
    
    # 检查分支1是否存在
    result = subprocess.run(
        ["git", "rev-parse", "--verify", branch1],
        capture_output=True
    )
    if result.returncode != 0:
        print(f"警告: 分支 '{branch1}' 不存在，使用当前分支替代")
        branch1 = original_branch
    
    # 提取测试
    print(f"\n提取分支 {branch1} 的测试...")
    branch1_tests = extract_all_tests(branch1)
    print(f"找到 {len(branch1_tests)} 个测试用例")
    
    print(f"\n提取分支 {branch2} 的测试...")
    branch2_tests = extract_all_tests(branch2)
    print(f"找到 {len(branch2_tests)} 个测试用例")
    
    # 生成报告
    print(f"\n生成报告: {output_file}")
    generate_report(branch1, branch1_tests, branch2, branch2_tests, output_file)
    
    # 切换回原分支
    print(f"\n切换回原分支: {original_branch}")
    checkout_branch(original_branch)
    
    print("\n分析完成！")

if __name__ == "__main__":
    main()
