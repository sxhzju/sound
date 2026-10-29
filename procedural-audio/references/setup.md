# 自行下载与配置

本 skill 不要求作者电脑上的软件、路径或 `local_music` 模块。Python 渲染辅助功能已包含在 `scripts/audio_backend.py` 中；插件和大型采样库由使用者从官方渠道自行下载安装。

## 1. Python 依赖

安装 [Python](https://www.python.org/downloads/)，使用所选 Python 创建虚拟环境。以下命令在安装了 skill 的项目根目录执行：

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r .claude/skills/procedural-audio/requirements.txt
```

Windows PowerShell 使用 `py -m venv .venv`，然后运行 `.venv\Scripts\Activate.ps1`。后续始终使用该虚拟环境的 Python；无需安装系统级 Python 包。若 Python 版本没有对应的二进制包，可换用 Python 3.11 或 3.12 后重新创建环境。

## 2. 按用途下载

| 需要的能力 | 官方来源 | 安装内容 |
| --- | --- | --- |
| 合成器预设、鼓、电子音色 | [Surge XT 官方下载](https://surge-synthesizer.github.io/downloads/) | 选择自己系统和处理器架构的 **VST3** 插件及 factory patches。渲染适配器针对 1.3.4。 |
| 播放 SFZ 乐器 | [sfizz 官方下载](https://sfz.tools/sfizz/downloads/) | 安装 **VST3** 插件；适配器针对 1.2.3 的状态格式。 |
| 管弦乐采样 | [VSCO 2 CE 官方页面](https://versilian-studios.com/vsco-community/) | 选择 **Vanilla SFZ Version / Direct Download**。 |
| 键盘、世界乐器和打击乐采样 | [VCSL 官方页面](https://versilian-studios.com/vcsl/) | 下载 SFZ 与完整样本文件。 |

纯 Python 噪声扫频、低频下坠、混音和分析只需要第 1 步。Surge 音色只需要 Surge XT；SFZ 乐器需要 sfizz 加至少一个 SFZ 采样库。无需一次下载所有资源。

下载采样库后完整解压，保留 `.sfz`、WAV 样本及其相对目录关系。只复制 `.sfz` 文件不能发声。VSCO 2 CE 与 VCSL 的官方下载链接见各自页面；本仓库不镜像插件或大型采样文件。

## 3. 指向自己的安装目录

路径通过环境变量配置，在启动 Python **之前**设置。示例中的 `/path/to/...` 必须换成使用者自己的实际路径：

```sh
export SOUND_SURGE_PLUGIN="/path/to/Surge XT.vst3"
export SOUND_SURGE_DATA="/path/to/Surge XT factory data"
export SOUND_SFIZZ_PLUGIN="/path/to/sfizz.vst3"
export SOUND_SAMPLE_DIR="/path/to/audio-assets"
```

PowerShell 的等价语法是 `$env:SOUND_SAMPLE_DIR = "D:\Audio\Libraries"`，其他变量同理。

- `SOUND_SURGE_PLUGIN` / `SOUND_SFIZZ_PLUGIN`：具体 `.vst3` 文件或插件包目录，不能只填插件父目录。Python 与插件的 CPU 架构须匹配。仅安装 standalone、AU 或 CLAP 不能用于此 VST3 适配器。
- `SOUND_SURGE_DATA`：包含 `.fxp` factory presets 的目录或上层目录；递归搜索。无需依赖固定预设数量或个人安装位置。
- `SOUND_SAMPLE_DIR`：完整解压的采样库所在目录；递归搜索其中所有 `.sfz`，子目录名称可自定。默认使用当前项目下的 `audio-assets/`。

插件和 Surge 数据未显式配置时，辅助模块会尝试常见的 macOS、Windows、Linux 安装位置。若诊断显示未找到，请设置上面的变量；不同发行包的路径可能不同。只配置本次任务需要的资源即可。可在自己的 shell 配置或项目启动脚本中保存变量。

## 4. 检查与试渲染

```sh
K=.claude/skills/procedural-audio/scripts/audio_kit.py
python "$K" doctor
python "$K" find "kick" --kind surge
python "$K" find "harp" --kind sfz
```

`doctor` 仅检查路径和预设文件是否存在，未安装的可选资源会显示 `MISSING`。从 `find` 的真实输出中选择音色，再验证所需引擎：

```sh
python "$K" probe "Category/Actual Preset Name" 60
python "$K" sfzmap "/absolute/path/to/Actual Instrument.sfz"
python "$K" probe "/absolute/path/to/Actual Instrument.sfz" 60
```

请将示例名称替换为本机实际结果。探测成功后，按 `SKILL.md` 创建渲染脚本。安装与下载需要网络；安装完成后的渲染无需网络、音频设备或插件 GUI。

状态适配器已使用 Surge XT 1.3.4、sfizz 1.2.3 与 Pedalboard 0.9.26 验证。其他版本或操作系统需先运行 `probe`；如果报告不支持的状态格式，请改用上述版本或适配辅助模块，不要忽略报错。
