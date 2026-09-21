# CS61A Learning Repo

This repository initializes a local CS61A study workspace around the public course materials from the official Berkeley CS 61A website.

## What is included

- `docs/learning-roadmap.zh-CN.md`: a Chinese study roadmap organized around the course topics.
- `docs/study-guide.zh-CN.md`: a practice-oriented study guide with checkpoints and review questions.
- `private/answers/study-guide.answers.zh-CN.md`: complete reference answers for the local study guide. This directory is ignored by git.
- `scripts/sync_cs61a.py`: a sync script that pulls public starter code, assignment metadata, and study guides from `https://cs61a.org/`.

## Quick start

### Pytea · 本地 Python 导师

在终端输入 `pytea`，自动打开本地浏览器界面。支持简体中文 / English、逐步回放、调用帧、对象引用箭头、输出和 `input()`。

首次安装命令（只创建本地启动脚本，无第三方依赖）：

```bash
python scripts/install_pytea.py
pytea
```

也可以不安装，直接在仓库根目录运行：

```bash
python -m pytea
```

使用方法与限制见 [Pytea 使用指南](docs/pytea.zh-CN.md)。

### 同步课程资料

在任意终端目录输入：

```powershell
cs update
```

命令检查 **2026 秋季**官网新发布的 Lab、HW、Reading，更新 PDF 和目录，并下载起始代码。已有练习代码保持原样，官网不同版本另存 `private/upstream/`；答案始终放在忽略目录 `private/answers/`。旧 PDF、缓存和索引自动备份至 `private/update-backups/`。失败项目会显示错误并记录在索引，命令返回非零退出码，重新运行即可重试。它不会提交或推送 Git，也不会自动切换学期。

本机已安装 `cs` 启动器，使用已有的 Codex Python 运行环境，无新增依赖。换电脑时可运行 `python scripts/install_cs.py --python "具备 lxml、reportlab、pypdf 的 python.exe 完整路径"` 安装；安装位置须已在 PATH 中。更新实现见 `scripts/cs.py`。

已下载的官方课程资料见 [2026 秋季目录](materials/fa26/README.md)：Lab、HW 的题目 PDF 与解压代码，以及课表 Reading 的 PDF。答案和本地下载缓存位于 Git 忽略的 `private/`。来源、时间及 SHA-256 见 `materials/fa26/manifest.json`。

本次下载脚本为 `scripts/download_course.py`（需要 `lxml`、`reportlab`、`pypdf` 和 Windows Arial/Consolas 字体）；它只收集官网已发布的链接，保留已有文件，遇到不同内容拒绝覆盖。PDF 是官方网页的静态阅读版，交互演示仍需访问原页面。

下面是旧版同步器，会生成忽略目录下的 ZIP/网页镜像，并可能重建旧解压目录；不用于更新上述按学期整理的练习代码。

```bash
python scripts/sync_cs61a.py
```

After running the sync script, the repo will contain:

- `materials/starter_code/`: downloaded starter-code zip archives
- `materials/starter_code_extracted/`: extracted starter-code folders
- `materials/guides/`: mirrored public study-guide pages and PDFs
- `materials/catalog.json`: a generated index of assignments and study resources

## Notes

- Official English materials remain the source of truth.
- The Chinese notes in `docs/` are study aids, not official course text.
- Reference answers are intentionally stored in `private/` so you can keep your public repo clean.

## Primary official sources

- `https://cs61a.org/`
- `https://cs61a.org/resources/`
- `https://www.composingprograms.com/`

