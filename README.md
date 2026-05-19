# GPT Image Generator

基于 OpenAI **gpt-image-2** 模型的浏览器端多模态图像生成工具。支持纯文本生图，以及上传参考图片配合文字描述进行图像再创作。API Key 仅存在于服务端，不会暴露给浏览器。

## 功能

- **文本生图**：输入提示词，直接生成图像
- **多模态生图**：上传参考图片 + 提示词，对图片进行二次创作
- 支持拖拽上传图片
- 可选尺寸（1:1 / 竖版 / 横版）和质量档位
- 生成结果一键下载为 PNG

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python · FastAPI · Uvicorn |
| 图像处理 | Pillow（上传图片统一转为 RGBA PNG） |
| AI 接口 | OpenAI Python SDK（`client.images.generate` / `.edit`） |
| 前端 | 纯 HTML + CSS + 原生 JS，无框架 |
| 包管理 | uv + pyproject.toml |
| 代码风格 | ruff（格式化 + lint） |

## 前置要求

- [uv](https://docs.astral.sh/uv/) 已安装
- 可访问 OpenAI API 且有 gpt-image-2 权限的 API Key
- **WSL 用户**：项目须放在 Linux 文件系统下（如 `/home/<user>/...`），不能在 `/mnt/c/...` 下运行——Windows NTFS 不支持 uv 安装依赖所需的 hardlink 操作

## 安装

```bash
# 1. 进入项目目录
cd /home/jiaxi/projects/gpt-image-gen

# 2. 安装依赖（uv 自动创建 .venv）
uv sync
```

## 配置

在 `main.py` 第 9 行将占位符替换为真实的 API Key：

```python
OPENAI_API_KEY = "sk-your-api-key-here"  # ← 替换这里
```

> API Key 只写在后端，前端页面无法读取到它。

## 运行

```bash
uv run uvicorn main:app --reload --port 8000
```

浏览器打开 [http://localhost:8000](http://localhost:8000)

## 使用方法

1. 在左侧面板填写**提示词**，描述想生成的图像
2. （可选）点击或拖拽上传一张**参考图片**——有图片时调用图像编辑接口，无图片时调用纯生成接口
3. 选择**尺寸**和**质量**档位
4. 点击**生成图像**，等待结果出现在右侧
5. 点击**下载图片**保存为 PNG

## 代码格式化

```bash
uvx ruff format .        # 格式化
uvx ruff check --fix .   # lint 并自动修复
```

## 项目结构

```
gpt-image-gen/
├── main.py              # FastAPI 应用，唯一的后端入口
├── pyproject.toml       # 依赖声明 + ruff 配置
├── uv.lock              # 锁定的依赖版本（不要手动编辑）
├── .python-version      # 固定 Python 3.12（3.14 下部分 Rust 扩展无 wheel）
├── CLAUDE.md            # Claude Code 使用说明
└── static/
    └── index.html       # 前端页面（HTML + CSS + JS 合一）
```

## API

### `POST /api/generate`

接收 `multipart/form-data`：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `prompt` | string | ✓ | 图像描述 |
| `size` | string | — | `1024x1024`（默认）/ `1024x1536` / `1536x1024` |
| `quality` | string | — | `medium`（默认）/ `low` / `high` |
| `image` | file | — | 参考图片；有此字段时走 edit 接口 |

**响应（200）**

```json
{ "image": "<base64 PNG>" }
// 或（极少数情况下模型返回 URL）
{ "url": "https://..." }
```

**响应（500）**

```json
{ "detail": "错误信息" }
```
