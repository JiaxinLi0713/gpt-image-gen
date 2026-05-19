# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# 同步/安装依赖
uv sync

# 启动开发服务器（热重载）
uv run uvicorn main:app --reload --port 8000

# 格式化代码
uvx ruff format .

# Lint 并自动修复
uvx ruff check --fix .
```

> **WSL 注意**：必须在 Linux 文件系统（`/home/jiaxi/projects/gpt-image-gen`）下运行，不能在 `/mnt/c/...` 下——Windows NTFS 不支持 uv 安装包时的 hardlink/symlink 操作。

## 依赖版本约束原因

- `fastapi<0.120`：0.136+ 在 Python 3.14 下安装后 `fastapi` 模块不可导入（dist-info 存在但无实际文件）
- `openai<2.0`：2.x SDK 超出当前知识范围，行为未知
- `requires-python<3.14`：Python 3.14 下 pydantic-core（Rust 扩展）无预编译 wheel，安装后无法 import

## 架构

单文件 FastAPI 后端 + 单文件纯 HTML/JS 前端，无构建步骤。

**请求流程：**
```
浏览器 (static/index.html)
  └─ POST /api/generate  multipart/form-data
       ├─ prompt (str)
       ├─ size (str, 默认 1024x1024)
       ├─ quality (str, 默认 medium)
       └─ image (file, 可选)
            │
            ▼
       main.py — generate_image()
            ├─ 有图片 → Pillow 转 RGBA PNG → client.images.edit()
            └─ 无图片 → client.images.generate()
                         │
                         ▼
                   OpenAI gpt-image-2
                         │
                    {"image": "<b64>"} 或 {"url": "..."}
                         │
                         ▼
               前端渲染图片 + 提供下载
```

**API key** 硬编码在 `main.py` 顶部的 `OPENAI_API_KEY` 常量，前端完全不知道它的存在——前端只与 `/api/generate` 通信。

**静态文件**：FastAPI 通过 `StaticFiles` 挂载 `static/` 目录，`GET /` 直接返回 `static/index.html`。前端逻辑（上传预览、拖拽、loading 状态、下载）全部在 `index.html` 内的 `<script>` 标签中，无外部 JS 框架依赖。
