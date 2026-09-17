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

