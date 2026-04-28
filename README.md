# musicDownload

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Web_UI-000000?logo=flask&logoColor=white)
![musicdl](https://img.shields.io/badge/musicdl-powered-6f42c1)
![ffmpeg](https://img.shields.io/badge/ffmpeg-optional-007808?logo=ffmpeg&logoColor=white)
![Single File](https://img.shields.io/badge/Architecture-single--file-orange)
![UI](https://img.shields.io/badge/UI-local_web-2563eb)

一个基于 <a href="https://github.com/CharlesPikachu/musicdl">musicdl</a> 的本地 Web 音乐下载器。<br>
已去掉 <code>PyQt5</code> 桌面界面，改为浏览器可访问的单文件 Flask 应用。

</div>

---

<a id="intro"></a>

## ✨ 项目简介

`musicDownload` 是一个面向本地使用的音乐搜索与下载工具，核心基于 `musicdl`，并在此基础上完成了：

- 桌面版 → Web 版迁移
- 实时下载进度展示
- 下载后自动转 MP3
- 下载目录网页浏览
- 扁平化输出目录整理
- 单文件部署（后端 + 模板 + 样式全部在 `musicdownload.py`）

如果你想要的是一个：

- 不依赖 `PyQt5`
- 打开浏览器就能用
- 支持多来源搜索
- 下载后可直接在网页点链接取文件

的轻量本地工具，那么这个项目就是为这个场景准备的。

---

## 📚 目录

- [✨ 项目简介](#intro)
- [🚀 功能亮点](#features)
- [🖼️ 当前形态](#shape)
- [📦 项目结构](#structure)
- [🛠️ 环境要求](#requirements)
- [⚡ 快速开始](#quickstart)
- [⚙️ 环境变量](#env)
- [🎵 使用流程](#usage)
- [📁 下载目录规则](#save-dir)
- [🌐 支持的音乐来源](#sources)
- [🔌 主要页面与接口](#routes)
- [❓ 常见问题](#faq)
- [🆚 与旧版的区别](#compare)
- [📝 提交到 GitHub 的建议](#github)
- [🙏 致谢](#thanks)

---

<a id="features"></a>

## 🚀 功能亮点

### 1. 本地 Web 界面

- 不再依赖 `PyQt5`
- 启动后直接用浏览器访问
- 适合本机或局域网轻量使用

### 2. 多来源搜索 / 歌单解析

- 支持歌曲搜索
- 支持歌单链接解析
- 可同时勾选多个音乐来源搜索
- 可配置每个来源的搜索结果数量

### 3. 下载任务后台执行

- 支持下载单首
- 支持下载勾选结果
- 支持一键下载全部搜索结果
- 支持搜索完成后自动下载全部结果

### 4. 实时下载进度

页面会自动刷新并展示：

- 总体任务进度
- 当前正在处理的歌曲
- 每首歌曲的状态
- 每个来源的目标数量 / 完成数量

### 5. 自动转 MP3

- 下载完成后可自动转成 MP3
- 支持选择“保留原始格式”
- 支持“转 MP3 后保留原始音频”
- 依赖系统 `ffmpeg`

### 6. 网页浏览下载目录

- 首页可直接进入“浏览下载目录”
- 歌曲名本身就是下载链接
- 右侧保留“下载文件”按钮
- 使用 token 下载，不暴露真实绝对路径

### 7. 扁平化输出目录

下载完成后会整理目录：

- 尽量移除来源生成的多级子目录
- 只保留音频文件
- 非音频文件会清理掉
- 同名文件自动重命名，避免覆盖

---

<a id="shape"></a>

## 🖼️ 当前形态

> 当前版本是 **单文件 Web 版**，不是桌面 GUI 版。

- 主程序：`musicdownload.py`
- Web 框架：`Flask`
- 页面模板：内嵌字符串模板
- 样式文件：内嵌 CSS
- 下载核心：`musicdl`
- 转码工具：`ffmpeg`（可选）

这意味着项目现在非常适合：

- 本地直接运行
- 快速打包上传 GitHub
- 二次修改 UI / 逻辑
- 继续往 API 化或 Docker 化扩展

---

<a id="structure"></a>

## 📦 项目结构

```text
musicDownload/
├── musicdownload.py      # 主程序：Flask + HTML + CSS + 下载逻辑
├── requirements.txt      # Python 依赖
├── README.md             # 项目说明
└── .gitignore            # Git 忽略规则
```

运行时会自动生成以下目录，但**不建议提交到 GitHub**：

```text
.venv/                    # 虚拟环境
.musicdownload_runtime/   # 搜索与运行时临时目录
已下载音乐/               # 下载输出目录
__pycache__/              # Python 缓存
```

---

<a id="requirements"></a>

## 🛠️ 环境要求

- Python `3.10+`
- 操作系统：Linux / macOS / Windows
- `ffmpeg`：仅在“自动转 MP3”时需要

### 安装 ffmpeg（示例）

```bash
# Debian / Ubuntu
sudo apt-get update
sudo apt-get install -y ffmpeg
```

如果未安装 `ffmpeg`：

- 程序仍可运行
- 仍可搜索和下载
- 但“自动转 MP3”不会真正转码，而是保留原始音频格式

---

<a id="quickstart"></a>

## ⚡ 快速开始

### 1）克隆项目

```bash
git clone <your-repo-url>
cd musicDownload
```

### 2）创建虚拟环境（推荐）

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3）安装依赖

```bash
uv pip install -r requirements.txt
```

### 4）启动服务

```bash
uv run musicdownload.py
```

默认启动参数：

- Host：`0.0.0.0`
- Port：`8005`

浏览器打开：

```text
http://127.0.0.1:8005
```

---

<a id="env"></a>

## ⚙️ 环境变量

可通过环境变量覆盖默认配置：

| 变量名 | 默认值 | 说明 |
|---|---:|---|
| `MUSIC_WEB_HOST` | `0.0.0.0` | Web 服务监听地址 |
| `MUSIC_WEB_PORT` | `8005` | Web 服务监听端口 |
| `MUSIC_WEB_DEBUG` | `0` | 是否启用 Flask Debug |
| `MUSIC_WEB_SECRET` | `musicdownload-web-secret` | Flask Session Secret |

示例：仅本机访问

```bash
export MUSIC_WEB_HOST=127.0.0.1
export MUSIC_WEB_PORT=8005
python3 musicdownload.py
```

---

<a id="usage"></a>

## 🎵 使用流程

### 搜索与下载

1. 打开首页
2. 勾选音乐来源
3. 选择：
   - `搜索歌曲`
   - `解析歌单链接`
4. 输入关键词或歌单链接
5. 设置：
   - 结果数量
   - 保存目录
   - 输出格式
6. 点击 **开始搜索**
7. 在结果区执行：
   - `下载这首`
   - `下载勾选项`
   - `下载全部结果`

### 查看进度

下载开始后，页面会自动显示：

- 任务总进度
- 当前处理状态
- 每首歌曲进度
- 下载完成后的文件链接

### 浏览下载目录

你可以通过两种方式进入目录浏览页面：

- 首页按钮：**浏览下载目录**
- 下载任务卡片中的：**浏览下载目录**

在目录浏览页面中：

- 歌曲名本身可点击下载
- 右侧还有单独的“下载文件”按钮
- 不会在 URL 中暴露真实绝对路径

---

<a id="save-dir"></a>

## 📁 下载目录规则

当前版本会在后处理阶段自动整理下载结果：

### 规则

- 所有音频尽量整理到**同一层目录**
- 来源自动创建的子目录会尽量清理
- 非音频文件会删除
- 空目录会删除
- 同名文件自动追加 ` (1)`、` (2)` 等后缀

### 效果

这让下载目录更适合：

- 本地直接播放
- 批量拷贝到播放器
- 网页里快速浏览和下载

---

<a id="sources"></a>

## 🌐 支持的音乐来源

当前 Web 界面可选来源来自 `musicdl`，包括但不限于：

- 苹果音乐
- Deezer
- 5sing
- Jamendo
- Joox
- 酷我音乐
- 酷狗音乐
- 咪咕音乐
- 网易云音乐
- QQ 音乐
- 千千音乐
- Qobuz
- SoundCloud
- StreetVoice
- 汽水音乐
- Spotify

> 说明：Web 界面中已隐藏 `TIDAL` 搜索按钮。
>
> 实际搜索/下载可用性取决于 `musicdl` 当前支持情况、目标站点返回结果以及网络环境。

---

<a id="routes"></a>

## 🔌 主要页面与接口

### 页面路由

| 路径 | 说明 |
|---|---|
| `/` | 首页：搜索、结果展示、下载任务进度 |
| `/browse-save-dir` | 浏览当前配置的下载目录 |
| `/browse/<job_id>` | 浏览某个下载任务目录 |
| `/browse-song/<job_id>/<song_key>` | 聚焦到某首歌所在目录 |

### 下载相关接口

| 路径 | 说明 |
|---|---|
| `/downloads/<job_id>/<song_key>` | 下载任务中的单首文件 |
| `/browse-save-download` | 下载当前保存目录中的文件（token 模式） |
| `/browse-download/<job_id>` | 下载任务目录中的文件（token 模式） |
| `/api/download-jobs/<job_id>` | 轮询下载任务实时状态 |

---

<a id="faq"></a>

## ❓ 常见问题

<details>
<summary><strong>1. 为什么下载后不是 MP3？</strong></summary>
<br>
通常有以下几种情况：

- 你选择的是“保留原始格式”
- 系统没有安装 `ffmpeg`
- 某些文件转码失败，程序保留了原始音频

建议先检查：

```bash
ffmpeg -version
```

</details>

<details>
<summary><strong>2. 为什么有些歌搜不到，比如某些关键词没有结果？</strong></summary>
<br>
常见原因：

- 当前勾选的来源没有该资源
- 关键词过细，包含太多版本描述
- 不同平台对同一首歌命名不同
- `musicdl` 当前对某个来源返回不稳定

建议：

- 同时勾选多个来源
- 先用更短关键词搜索
- 再尝试加歌手名
- 去掉括号版本信息后再试

</details>

<details>
<summary><strong>3. 为什么目录下载链接不显示真实文件路径？</strong></summary>
<br>
这是刻意保留的设计：

- 前端只拿到 token
- 服务端再把 token 映射成相对路径
- 避免在 URL 中直接泄露服务端绝对路径

</details>

<details>
<summary><strong>4. 这个项目适合直接部署到公网吗？</strong></summary>
<br>
当前更适合本地或受控网络环境使用，因为：

- 任务状态保存在内存中
- 默认没有登录鉴权
- 更偏向个人工具 / 局域网工具形态

如果你后续要公网部署，建议增加：

- 认证
- 任务持久化
- 反向代理
- 访问控制

</details>

---

<a id="compare"></a>

## 🆚 与旧版的区别

相对于旧的 PyQt5 桌面版，当前 Web 版主要变化如下：

| 旧版 | 当前版本 |
|---|---|
| `PyQt5` 桌面 GUI | 本地 Web UI |
| 多文件前端资源 | 单文件内嵌模板与样式 |
| 无网页目录浏览 | 支持网页浏览下载目录 |
| 无实时 Web 进度 | 支持实时下载进度轮询 |
| 原始格式为主 | 可自动转 MP3 |
| 目录可能分散 | 自动整理为扁平音频目录 |

---

<a id="github"></a>

## 📝 提交到 GitHub 的建议

建议保留这些核心文件：

- `musicdownload.py`
- `requirements.txt`
- `README.md`
- `.gitignore`

建议不要提交这些运行产物：

- `.venv/`
- `.musicdownload_runtime/`
- `已下载音乐/`
- `__pycache__/`

如果你准备把这个仓库正式作为 **Web 版** 发布，建议提交信息可参考：

```bash
git add README.md .gitignore musicdownload.py requirements.txt
git commit -m "refactor: migrate music downloader to single-file web UI"
```

---

<a id="thanks"></a>

## 🙏 致谢

- 上游项目：[`CharlesPikachu/musicdl`](https://github.com/CharlesPikachu/musicdl)
- 本项目在其基础上完成了本地 Web 化、下载进度展示、目录浏览与 MP3 转码整理

---

<div align="center">

如果这个项目对你有帮助，欢迎自行继续扩展：认证、Docker 化、任务持久化、批量管理、封面展示优化等。  
当前版本已经非常适合作为一个 **可直接运行、可直接上传 GitHub 的单文件 Web 工具**。

</div>
