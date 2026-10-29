# Sound skills

两个用于音效素材检索与程序化音频生成的 skill。

| Skill | 用途 |
| --- | --- |
| [sfx-sources](sfx-sources/SKILL.md) | 从 Pixabay、Freesound、Mixkit 和 Kenney 查找并下载音效。 |
| [procedural-audio](procedural-audio/SKILL.md) | 使用 Python、Surge XT、sfizz 等本地工具离线生成音乐和音效。 |

## 安装

将需要的 skill 目录复制到项目的 `.claude/skills/` 中。例如，在仓库根目录执行：

```sh
mkdir -p /path/to/project/.claude/skills
cp -R sfx-sources procedural-audio /path/to/project/.claude/skills/
```

每个目录中的 `SKILL.md` 包含使用说明，`scripts/` 包含配套脚本。

## 环境要求

- `sfx-sources` 需要 Python 和网络访问；部分来源还依赖本地代理或额外依赖，详见其说明与 `references/local-setup.md`。
- `procedural-audio` 依赖 `local_music`、Surge XT、sfizz、本地采样库及相关 Python 包。本仓库不包含这些依赖或音源，原说明中的本机路径需要按实际环境配置。

两个 skill 目录保留原始文件内容。
