# Sound skills

三个用于音效素材检索、程序化音频生成与混音的 skill。

| Skill | 用途 |
| --- | --- |
| [sfx-sources](sfx-sources/SKILL.md) | 从 Pixabay、Freesound、Mixkit 和 Kenney 查找并下载音效。 |
| [procedural-audio](procedural-audio/SKILL.md) | 使用 Python、Surge XT、sfizz 等本地工具离线生成音乐和音效。 |
| [audio-mixing](audio-mixing/SKILL.md) | Mix tracks with EQ, dynamics, stereo placement, and loudness control using FFmpeg. |

## 安装

将需要的 skill 目录复制到项目的 `.claude/skills/` 中。例如，在仓库根目录执行：

```sh
mkdir -p /path/to/project/.claude/skills
cp -R sfx-sources procedural-audio audio-mixing /path/to/project/.claude/skills/
```

每个目录中的 `SKILL.md` 包含使用说明，`scripts/` 包含配套脚本。

## 环境要求

- `sfx-sources` 需要 Python 和网络访问；部分来源还依赖本地代理或额外依赖，详见其说明与 `references/local-setup.md`。
- `procedural-audio` 已包含渲染辅助模块，不需要作者本机的 `local_music`。请按[下载与配置指南](procedural-audio/references/setup.md)自行安装 Python 依赖，并按需从官网下载 Surge XT、sfizz、VSCO 2 CE 或 VCSL，配置自己的插件和音源路径。
- `audio-mixing` requires FFmpeg/ffprobe; optional Python uses only the standard library.

`sfx-sources` 保留原始文件；`procedural-audio` 已调整为使用者可自行下载和配置的版本。
