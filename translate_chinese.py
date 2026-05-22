#!/usr/bin/env python3
"""
Translate Chinese text to English in source files.
This script uses a simple dictionary-based approach for common UI terms.
"""

import re
import os

# Dictionary of common Chinese UI terms and their English translations
CHINESE_TO_ENGLISH = {
    # TokensPage.tsx
    "刷新失败，请检查会话 Key": "Refresh failed, please check session key",
    "已生成新的 API Key": "New API Key generated",
    "生成失败，请检查权限": "Generation failed, please check permissions",
    "API Key 已删除": "API Key deleted",
    "删除失败": "Delete failed",
    "API Key 分发": "API Key Distribution",
    "管理可以访问此网关的下游凭证。": "Manage downstream credentials that can access this gateway.",
    "刷新": "Refresh",
    "已刷新": "Refreshed",
    "生成新 Key": "Generate New Key",
    "序号": "#",
    "操作": "Actions",
    "暂无 API Key": "No API Keys yet",
    
    # ImagePage.tsx
    "生成失败": "Generation failed",
    "正在Generate Image...": "Generating Image...",
    "Image Generation通常需要 10-30 秒，请耐心等待": "Image generation typically takes 10-30 seconds, please wait patiently",
    "还没有Generate Image": "No images generated yet",
    "在上方输入描述，点击「Generate Image」开始创作": "Enter a description above and click 'Generate Image' to start creating",
    
    # api.ts
    "后端 API 基础地址。": "Backend API base URL.",
    "本地开发：留空，由 Vite proxy 代理到 http://localhost:7860": "Local development: leave empty, proxied by Vite to http://localhost:7860",
    "Docker 生产：留空，由 nginx proxy 代理到 backend:7860": "Docker production: leave empty, proxied by nginx to backend:7860",
    "Vercel / 独立前端：设置 VITE_API_BASE_URL=https://your-backend.example.com": "Vercel / Standalone frontend: set VITE_API_BASE_URL=https://your-backend.example.com",
    
    # AdminLayout.tsx
    "运行状态": "Dashboard",
    "账号管理": "Accounts",
    "接口测试": "Test API",
    "图片生成": "Images",
    "系统设置": "Settings",
    
    # AccountsPage.tsx - these are unicode escaped
    "\\u7edf\\u4e00\\u7ba1\\u7406\\u4e0a\\u6e38\\u8d26\\u53f7\\u6c60\\uff0c\\u5e76\\u533a\\u5206Pending Activation\\u3001Rate Limited\\u3001Banned\\u4e0eInvalid\\u72b6\\u6001\\u3002": "Manage upstream account pool, distinguishing Pending Activation, Rate Limited, Banned, and Invalid statuses.",
    "\\u5176\\u4ed6Invalid": "Other Invalid",
    "\\u7edf\\u4e00\\u7ba1\\u7406\\u4e0a\\u6e38\\u8d26\\u53f7\\u6c60": "Manage upstream account pool",
    "\\u8bf7\\u5148\\u5728 chat.qwen.ai \\u767b\\u5f55\\uff0c\\u7136\\u540e\\u6309 F12 \\u6253\\u5f00\\u5f00\\u53d1\\u8005\\u5de5\\u5177\\uff0c\\u5728 Application / Storage \\u91cc\\u7684 Local Storage / \\u672c\\u5730\\u5b58\\u50a8 \\u4e2d\\u627e\\u5230 token \\u5e76\\u76f4\\u63a5\\u590d\\u5236\\u5b8c\\u6574\\u539f\\u59cb\\u503c\\u7c98\\u8d34\\u5230\\u4e0b\\u65b9\\u8f93\\u5165\\u6846\\u3002": "First log in at chat.qwen.ai, then press F12 to open developer tools, find the token in Local Storage under Application/Storage, and copy the complete raw value to paste into the input box below.",
    "\\u91cd\\u8981\\uff1a\\u8bf7\\u53ea\\u7c98\\u8d34 Local Storage / \\u672c\\u5730\\u5b58\\u50a8 \\u91cc\\u7684 token \\u539f\\u59cb\\u503c\\uff0c\\u4e0d\\u8981\\u4ece Network \\u8bf7\\u6c42\\u6216 Authorization \\u8bf7\\u6c42\\u5934\\u4e2d\\u63d0\\u53d6\\u3002": "Important: Please only paste the raw token value from Local Storage, do not extract from Network requests or Authorization headers.",
    "\\u8bf7\\u4e0d\\u8981\\u5e26 Bearer \\u524d\\u7f00\\uff0c\\u4e5f\\u4e0d\\u8981\\u7c98\\u8d34\\u6574\\u6bb5 Authorization \\u6587\\u672c\\u3002\\u90ae\\u7bb1\\u548c\\u5bc6\\u7801\\u53ef\\u4ee5\\u4e0d\\u586b\\uff0c\\u7cfb\\u7edf\\u4f1a\\u5728\\u6ce8\\u5165\\u524d\\u5148\\u9a8c\\u8bc1 token \\u662f\\u5426\\u6709\\u6548\\u3002": "Do not include the Bearer prefix, and do not paste the entire Authorization text. Email and password are optional; the system will validate the token before injection.",
    "\\u90ae\\u7bb1\\uff08\\u9009\\u586b\\uff09": "Email (optional)",
    "\\u5bc6\\u7801\\uff08\\u9009\\u586b\\uff09": "Password (optional)",
    "\\u7528\\u4e8e\\u81ea\\u52a8\\u5237\\u65b0\\u6216\\u6fc0\\u6d3b": "For auto-refresh or activation",
    "\\u6ce8\\u5165\\u8d26\\u53f7": "Inject Account",
    "\\u8d26\\u53f7\\u5217\\u8868": "Account List",
    "\\u8d26\\u53f7": "Account",
    "\\u72b6\\u6001": "Status",
    "\\u5e76\\u53d1\\u8d1f\\u8f7d": "Concurrent Load",
    "\\u8bf4\\u660e": "Note",
    "\\u64cd\\u4f5c": "Actions",
    "\\u6682\\u65e0\\u8d26\\u53f7\\uff0c\\u8bf7\\u624b\\u52a8\\u6ce8\\u5165\\u6216Get New Account\\u3002": "No accounts yet, please inject manually or Get New Account.",
    "\\u7ebf\\u7a0b": "threads",
    "\\u6fc0\\u6d3b": "Activate",
    "\\u5355\\u72ec\\u9a8c\\u8bc1": "Verify individually",
    "\\u5220\\u9664\\u8d26\\u53f7": "Delete account",
    
    # TestPage.tsx
    "\\u7f51\\u7edc\\u9519\\u8bef": "Network error",
    "\\u672a\\u77e5\\u54cd\\u5e94": "Unknown response",
    "网络错误": "Network error",
    "未知响应": "Unknown response",
    
    # SettingsPage.tsx
    "Save并发设置": "Save Concurrency Settings",
    "Save预热池设置": "Save Warm Pool Settings",
    "Save映射": "Save Mapping",
    
    # Dashboard.tsx  
    "系统状态": "System Status",
    "实时并发监控和 Qwen 账号池概览（每 3 秒自动刷新）": "Real-time concurrency monitoring and Qwen account pool overview (auto-refreshes every 3 seconds)",
    "可用账号": "Available Accounts",
    "当前并发": "Current Concurrency",
    "排队请求": "Queued Requests",
    "限流/无效": "Rate Limited/Invalid",
    "总数": "Total",
    "全局限制": "Global limit",
    "队列限制": "Queue limit",
    "Chat_ID 预热池": "Chat_ID Warm Pool",
    "异步任务": "Async Tasks",
    "每个账号目标": "Target per account",
    "TTL": "TTL",
    "未启用": "Not enabled",
    "asyncio 活动任务数": "asyncio active task count",
    "账号并发详情": "Account Concurrency Details",
    "邮箱": "Email",
    "状态": "Status",
    "进行中": "In-flight",
    "预热 chat_id": "Warm chat_id",
    "连续失败": "Consecutive Failures",
    "限流次数": "Rate Limit Strikes",
    "API 端点": "API Endpoints",
    "兼容主流 AI 协议。默认无需认证访问，或通过 API Key 访问。": "Compatible with mainstream AI protocols. Access by default without authentication, or via API Key.",
    "健康检查": "Health Check",
    "图像生成": "Image Gen",
    "文件上传": "Files",
}

def translate_file(filepath):
    """Translate Chinese text in a file to English."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    replacements_made = 0
    
    # Sort by length (longest first) to avoid partial replacements
    for chinese, english in sorted(CHINESE_TO_ENGLISH.items(), key=lambda x: -len(x[0])):
        if chinese in content:
            content = content.replace(chinese, english)
            replacements_made += 1
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return replacements_made
    return 0

def main():
    files_to_translate = [
        '/workspace/frontend/src/pages/TokensPage.tsx',
        '/workspace/frontend/src/pages/ImagePage.tsx',
        '/workspace/frontend/src/lib/api.ts',
        '/workspace/frontend/src/layouts/AdminLayout.tsx',
        '/workspace/frontend/src/pages/AccountsPage.tsx',
        '/workspace/frontend/src/pages/TestPage.tsx',
        '/workspace/frontend/src/pages/SettingsPage.tsx',
        '/workspace/frontend/src/pages/Dashboard.tsx',
    ]
    
    total_replacements = 0
    for filepath in files_to_translate:
        if os.path.exists(filepath):
            count = translate_file(filepath)
            if count > 0:
                print(f"Translated {count} strings in {filepath}")
                total_replacements += count
        else:
            print(f"File not found: {filepath}")
    
    print(f"\nTotal replacements: {total_replacements}")

if __name__ == "__main__":
    main()
