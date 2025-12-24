#!/usr/bin/env python3
"""
对比分析两个分支的单元测试运行效率
"""
import subprocess
import json
import re
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

def run_command(cmd: List[str], cwd: str = None) -> Tuple[int, str, str]:
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=3600  # 1小时超时
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def get_current_branch() -> str:
    """获取当前分支名称"""
    returncode, stdout, _ = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if returncode == 0:
        return stdout.strip()
    return "unknown"

def checkout_branch(branch: str) -> bool:
    """切换到指定分支"""
    # 先尝试本地分支
    returncode, _, _ = run_command(["git", "checkout", branch])
    if returncode == 0:
        return True
    
    # 尝试远程分支
    returncode, _, _ = run_command(["git", "checkout", "-b", branch, f"origin/{branch}"])
    if returncode == 0:
        return True
    
    # 尝试直接fetch并checkout
    run_command(["git", "fetch", "origin", f"{branch}:{branch}"])
    returncode, _, _ = run_command(["git", "checkout", branch])
    return returncode == 0

def run_tests() -> Dict[str, float]:
    """运行测试并返回每个测试用例的运行时间"""
    import time
    
    # 直接运行测试，不使用 --list（避免依赖问题）
    cmd = [
        "cargo", "test", 
        "--all-features", 
        "--workspace",
        "--",
        "--test-threads=1",
        "--nocapture"
    ]
    
    print("运行测试中...")
    start_time = time.time()
    returncode, stdout, stderr = run_command(cmd)
    total_elapsed = time.time() - start_time
    
    test_times = {}
    
    # 解析多种可能的时间格式
    patterns = [
        r'test\s+([^\s:]+(?:::[^\s:]+)*)\s+\.\.\.\s+(ok|FAILED|ignored)\s+\(([\d.]+)s\)',  # test name ... ok (0.123s)
        r'test\s+([^\s:]+(?:::[^\s:]+)*)\s+\.\.\.\s+(ok|FAILED|ignored)\s+\[([\d.]+)s\]',  # test name ... ok [0.123s]
        r'test\s+([^\s:]+(?:::[^\s:]+)*)\s+\.\.\.\s+(ok|FAILED|ignored).*?([\d.]+)\s*s',   # 更宽松的匹配
    ]
    
    for pattern in patterns:
        for line in stdout.split('\n'):
            match = re.search(pattern, line)
            if match:
                test_name = match.group(1)
                status = match.group(2)
                time_str = match.group(3)
                try:
                    time_seconds = float(time_str)
                    # 如果同一个测试有多个匹配，取最大值
                    if test_name not in test_times or test_times[test_name] < time_seconds:
                        test_times[test_name] = time_seconds
                except ValueError:
                    continue
    
    # 如果仍然没有找到时间信息，尝试从测试摘要中提取
    if not test_times:
        # 查找测试摘要，例如: "test result: ok. 123 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 1.23s"
        summary_patterns = [
            r'(\d+)\s+passed.*?finished\s+in\s+([\d.]+)s',
            r'(\d+)\s+passed.*?(\d+\.\d+)\s*s',
        ]
        
        for pattern in summary_patterns:
            match = re.search(pattern, stdout, re.IGNORECASE)
            if match:
                passed_count = int(match.group(1))
                total_time = float(match.group(2))
                if passed_count > 0:
                    # 从输出中提取所有测试名称
                    test_names = []
                    for line in stdout.split('\n'):
                        if 'test ' in line and ('... ok' in line or '... FAILED' in line):
                            # 提取测试名称
                            test_match = re.search(r'test\s+([^\s:]+(?:::[^\s:]+)*)', line)
                            if test_match:
                                test_names.append(test_match.group(1))
                    
                    if test_names:
                        # 平均分配时间
                        avg_time = total_time / len(test_names)
                        for test_name in test_names:
                            test_times[test_name] = avg_time
                    break
    
    # 如果还是没有，至少记录总时间
    if not test_times and returncode == 0:
        print(f"警告: 无法解析单个测试时间，总运行时间: {total_elapsed:.3f}s")
    
    return test_times

def analyze_test_differences(branch1_times: Dict[str, float], 
                            branch2_times: Dict[str, float],
                            branch1_name: str,
                            branch2_name: str) -> List[Tuple[str, float, float, float]]:
    """分析两个分支的测试时间差异"""
    differences = []
    
    # 获取所有测试用例名称
    all_tests = set(branch1_times.keys()) | set(branch2_times.keys())
    
    for test_name in all_tests:
        time1 = branch1_times.get(test_name, 0.0)
        time2 = branch2_times.get(test_name, 0.0)
        
        # 计算差异（绝对值）
        diff = abs(time2 - time1)
        differences.append((test_name, time1, time2, diff))
    
    # 按差异大小排序
    differences.sort(key=lambda x: x[3], reverse=True)
    
    return differences

def generate_report(branch1_name: str, branch1_times: Dict[str, float],
                   branch2_name: str, branch2_times: Dict[str, float],
                   differences: List[Tuple[str, float, float, float]],
                   output_file: str):
    """生成分析报告"""
    report_lines = []
    report_lines.append("# 单元测试性能对比分析报告\n")
    report_lines.append(f"## 对比分支\n")
    report_lines.append(f"- **分支1**: `{branch1_name}`\n")
    report_lines.append(f"- **分支2**: `{branch2_name}`\n")
    report_lines.append(f"- **生成时间**: {subprocess.check_output(['date']).decode().strip()}\n\n")
    
    # 统计信息
    report_lines.append("## 统计信息\n\n")
    report_lines.append(f"- 分支 `{branch1_name}` 测试用例数量: {len(branch1_times)}\n")
    report_lines.append(f"- 分支 `{branch2_name}` 测试用例数量: {len(branch2_times)}\n")
    
    total_time1 = sum(branch1_times.values())
    total_time2 = sum(branch2_times.values())
    report_lines.append(f"- 分支 `{branch1_name}` 总运行时间: {total_time1:.3f}s\n")
    report_lines.append(f"- 分支 `{branch2_name}` 总运行时间: {total_time2:.3f}s\n")
    report_lines.append(f"- 总时间差异: {abs(total_time2 - total_time1):.3f}s ({((total_time2 - total_time1) / total_time1 * 100) if total_time1 > 0 else 0:.2f}%)\n\n")
    
    # 运行时间差异最大的5个测试用例
    report_lines.append("## 运行时间差异最大的5个测试用例\n\n")
    report_lines.append("| 测试用例 | 分支1时间(s) | 分支2时间(s) | 差异(s) | 差异百分比 |\n")
    report_lines.append("|---------|-------------|-------------|---------|-----------|\n")
    
    top5 = differences[:5]
    for test_name, time1, time2, diff in top5:
        if time1 > 0:
            percent_diff = ((time2 - time1) / time1) * 100
        elif time2 > 0:
            percent_diff = 100.0
        else:
            percent_diff = 0.0
        
        report_lines.append(f"| `{test_name}` | {time1:.3f} | {time2:.3f} | {diff:.3f} | {percent_diff:+.2f}% |\n")
    
    report_lines.append("\n")
    
    # 详细对比表（所有测试用例）
    report_lines.append("## 详细对比表\n\n")
    report_lines.append("| 测试用例 | 分支1时间(s) | 分支2时间(s) | 差异(s) | 差异百分比 |\n")
    report_lines.append("|---------|-------------|-------------|---------|-----------|\n")
    
    for test_name, time1, time2, diff in differences:
        if time1 > 0:
            percent_diff = ((time2 - time1) / time1) * 100
        elif time2 > 0:
            percent_diff = 100.0
        else:
            percent_diff = 0.0
        
        report_lines.append(f"| `{test_name}` | {time1:.3f} | {time2:.3f} | {diff:.3f} | {percent_diff:+.2f}% |\n")
    
    # 写入文件
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(report_lines)
    
    print(f"报告已生成: {output_file}")

def check_branch_exists(branch: str) -> bool:
    """检查分支是否存在（本地或远程）"""
    # 检查本地分支
    returncode, _, _ = run_command(["git", "rev-parse", "--verify", branch])
    if returncode == 0:
        return True
    
    # 检查远程分支
    returncode, _, _ = run_command(["git", "rev-parse", "--verify", f"origin/{branch}"])
    if returncode == 0:
        return True
    
    # 尝试fetch
    run_command(["git", "fetch", "origin", branch])
    returncode, _, _ = run_command(["git", "rev-parse", "--verify", branch])
    return returncode == 0

def main():
    branch1 = "agatedb_on_object_store_1220"
    branch2 = "master"
    output_file = "docs/slow_test_analysis.md"
    
    original_branch = get_current_branch()
    print(f"当前分支: {original_branch}")
    
    # 检查分支是否存在
    if not check_branch_exists(branch1):
        print(f"\n警告: 分支 '{branch1}' 不存在！")
        print(f"将使用当前分支 '{original_branch}' 替代 '{branch1}' 进行对比分析。")
        branch1 = original_branch
    
    # 切换到分支1并运行测试
    print(f"\n切换到分支: {branch1}")
    if not checkout_branch(branch1):
        print(f"错误: 无法切换到分支 '{branch1}'")
        sys.exit(1)
    
    print(f"运行测试: {branch1}")
    try:
        branch1_times = run_tests()
        print(f"完成，共 {len(branch1_times)} 个测试用例")
    except Exception as e:
        print(f"运行测试时出错: {e}")
        branch1_times = {}
    
    # 切换到分支2并运行测试
    print(f"\n切换到分支: {branch2}")
    if not checkout_branch(branch2):
        print(f"错误: 无法切换到分支 '{branch2}'")
        sys.exit(1)
    
    print(f"运行测试: {branch2}")
    try:
        branch2_times = run_tests()
        print(f"完成，共 {len(branch2_times)} 个测试用例")
    except Exception as e:
        print(f"运行测试时出错: {e}")
        branch2_times = {}
    
    # 检查是否有测试数据
    if not branch1_times and not branch2_times:
        print("\n警告: 两个分支都没有获取到测试数据")
        print("生成说明报告...")
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# 单元测试性能对比分析报告\n\n")
            f.write(f"## 对比分支\n\n")
            f.write(f"- **分支1**: `{branch1}`\n")
            f.write(f"- **分支2**: `{branch2}`\n\n")
            f.write(f"## 问题说明\n\n")
            f.write(f"由于依赖问题（Cargo 版本过旧，无法处理某些依赖），无法运行测试。\n\n")
            f.write(f"建议：\n")
            f.write(f"1. 更新 Rust 和 Cargo 到最新版本\n")
            f.write(f"2. 或者使用支持 `edition2024` 的 nightly 版本\n")
            f.write(f"3. 或者修复依赖问题后重新运行分析脚本\n\n")
        print(f"说明报告已生成: {output_file}")
        return
    
    # 分析差异
    print("\n分析测试差异...")
    differences = analyze_test_differences(branch1_times, branch2_times, branch1, branch2)
    
    # 生成报告
    print(f"\n生成报告: {output_file}")
    generate_report(branch1, branch1_times, branch2, branch2_times, differences, output_file)
    
    # 切换回原分支
    print(f"\n切换回原分支: {original_branch}")
    checkout_branch(original_branch)
    
    print("\n分析完成！")

if __name__ == "__main__":
    main()
