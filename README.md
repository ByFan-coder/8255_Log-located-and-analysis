# 8255 日志定位与分析 Skill

面向 T18D（8255）及类似 QNX / Android 平台的离线日志分析技能，技能名为 **`t18d-8255-debug`**。

从当前日志目录开始，先确认故障时间和日志覆盖，再查 QNX、屏端以及其他相关软件层，输出可复核的分析、日志位置与下一步建议。

当前版本：**v1.1.0**。下载：[GitHub Releases](https://github.com/ByFan-coder/8255_Log-located-and-analysis/releases)。

## 主要能力

- **先确认时间和覆盖**：检查故障前、中、后是否有记录，区分 boot、校时、休眠、缺分片、截断、未解码及未对齐。
- **QNX 优先**：联查 `qnxlog` 中的 `slog2`、`systeminfo`，检查 `QNXRunInfo.tar.gz`，按现象选择 `kgsl / smmu / openwfd / display / i2c / disp_svc / ads_service`。
- **屏端按需解析**：先询问是否解析 `display_log`；线束、供电、复位等现场推断需要询问视频或照片，必要时建议测量。
- **信息对应故障屏**：仪表问题给仪表信息，吸顶屏问题给吸顶屏信息，多屏分组；保留零件号及 `hw_ver / sw_ver / tp_ver / supplier_code` 四项和定位，查不到明确标记失败。
- **继续跨层排查**：QNX 和屏端未定位时，继续检查应用、fwk、安卓内核、合成/HAL、业务通信、启动服务、开机动画及适用构建的 Host/PVM。
- **简洁流转**：非驱动、非屏端问题用易懂语言简析，只给关键几处日志，输出 `建议流转模块/层级：xxxx`。
- **编辑器行号**：对外引用先按 CRLF、独立 CR/LF 的编辑器规则重定位，不对混合换行文件套用固定偏移；附只读工具。
- **项目源码与协议核对**：检查当前分析目录的 `code/` 和 `protocol/`，查找当前项目源码、头文件、配置和通信协议，核对版本及适用屏型。缺失、为空或缺少相关资料时询问是否添加，等待期间继续独立日志分析。
- **简短 Bug 表单与去重**：维护当前分析目录的 `bug_table.md`，记录项目/版本、故障对象、时间/启动实例、关键证据、简要结论及关联ID。同一事件复用原ID，相似问题只标记疑似重复，不自动合并、删除或关闭Bug。

分析区分日志事实、可能原因和待验证项。“未检出”受覆盖和解码能力限制，不代表该层已被排除；建议流转不代表责任已确认。

## 安装

### Release 安装

下载 `t18d-8255-debug-v1.1.0.zip` 和 `SHA256SUMS`。解压后复制**整个 `t18d-8255-debug` 文件夹**到目标 agent 的技能目录，保留内部相对结构。`references` 是参考资料，不能单独作为完整技能安装。

Codex 本地技能目录通常为 `$CODEX_HOME/skills`；未设置 `CODEX_HOME` 时使用用户目录的 `.codex/skills`。Windows PowerShell 示例，在已解压目录运行：

```powershell
$skillRoot = if ($env:CODEX_HOME) {
    Join-Path $env:CODEX_HOME 'skills'
} else {
    Join-Path $env:USERPROFILE '.codex/skills'
}
$skillTarget = Join-Path $skillRoot 't18d-8255-debug'
if (Test-Path -LiteralPath $skillTarget) {
    throw '已存在同名技能，请先比较和备份，避免覆盖自定义修改。'
}
New-Item -ItemType Directory -Force -Path $skillRoot | Out-Null
Copy-Item -LiteralPath './t18d-8255-debug' -Destination $skillTarget -Recurse
```

### 从 Git 安装

```powershell
git clone https://github.com/ByFan-coder/8255_Log-located-and-analysis.git
```

进入克隆后的仓库，按上面的步骤复制 `t18d-8255-debug/`。支持 `SKILL.md` 的其他 agent 可按自己的目录规则安装；不支持技能发现时，可显式让 agent 先读 `SKILL.md`，再按需读取引用资料。`agents/openai.yaml` 是界面元数据，不支持它的 agent 可以忽略。

## 使用

将 agent 工作目录设置为待分析日志目录，描述现象、故障屏、时间段、操作前提和恢复方式，不依赖固定盘符或工程路径。

```text
使用 $t18d-8255-debug 分析当前目录日志。
问题：仪表黑屏，约在当天 14:05 发生，重启恢复。
先确认时间与覆盖，给出可能原因和关键日志定位。
```

```text
使用 $t18d-8255-debug 分析当前目录的吸顶屏触摸无响应问题。
给出对应吸顶屏的零件号、四项版本信息及日志定位。
如果需要解析 display_log，请先询问。
```

时间不清楚时先核对材料并询问，不任选一段异常定责。专用封装、屏端二进制协议及 dump 仍需匹配解码工具；无法解析时记录限制，并继续可独立进行的排查。

### 源码、协议与 Bug 简表

在待分析目录可准备如下材料，技能只读核对源码与协议，不会自动编译、运行工程或修改源码：

```text
待分析目录/
  qnxlog/
  code/          当前项目参考源码、头文件、配置
  protocol/      通信协议及版本、屏型适用说明
  bug_table.md   本地 Bug 索引（首次分析时从空白模板建立）
```

Bug表单简记：ID、项目/版本、故障对象与现象、发生时间/启动实例、关键特征与证据、简要结论/建议模块、去重结果/关联ID。材料不全时标记未知，不要求填齐才能分析。

去重范围限当前索引和用户明确提供的历史材料，结果分为“重复（同一事件）”“疑似重复”“未发现重复（限当前索引）”“无法判断”。仅有“黑屏”“无ACK”等通用关键词相同不足以判重。不同时间的独立复现保留自己的记录，并关联候选ID；本功能不会自动操作 Jira 或 GitHub issue。

空白模板在 `t18d-8255-debug/assets/bug_table.md`。真实 Bug 表、项目源码、协议和现场日志保存在各自分析目录，不收进技能安装目录或发布包。

## 输出约定

首先说明“时间与覆盖”。驱动或屏端问题给必要的时间线、证据、可能原因和验证建议。仍考虑屏端时，按实际故障屏输出：

```text
屏幕：仪表屏 / 吸顶屏 / 其他实际故障屏
零件号：实际值 日志定位链接
软件/固件版本：hw_ver:实际值，sw_ver:实际值，tp_ver:实际值，supplier_code:实际值 日志定位链接
```

实际结果后附日志文件与编辑器行号链接，找不到显示“屏幕信息查找失败”。非驱动、非屏端问题不提供屏幕信息，简析后给出：

```text
建议流转模块/层级：fwk / 安卓内核 / 仪表应用 / 开机动画等实际建议
```

## 编辑器行号工具

需要 Python 3.10+，仅用标准库，只读处理文本和普通 gzip，不解析 DSV_PKMS。

```powershell
python ./t18d-8255-debug/scripts/editor_line_locator.py ./qnxlog/slog2_1.log --text '命中的唯一日志原文'
python ./t18d-8255-debug/scripts/editor_line_locator.py ./qnxlog/slog2_1.log --line 12345
python ./t18d-8255-debug/scripts/editor_line_locator.py ./qnxlog/slog2_1.log --text '唯一片段' --encoding gb18030
```

默认 UTF-8（含 BOM），其他编码需明确指定。CRLF 计一次换行，独立 CR/LF 各计一次，空行保留，自动折行不增加物理行号；重复匹配按时间、进程与载荷区分，并复核相邻原文。gzip 行号指解压后文本；若目标编辑器规则不同，以实际编辑器为准。

## 仓库结构

```text
README.md
VERSION
docs/releases/v1.1.0.md
scripts/build_release.py
tests/test_editor_line_locator.py
t18d-8255-debug/
  SKILL.md
  agents/openai.yaml
  references/
    bug-form-dedup.md
  assets/bug_table.md
  scripts/editor_line_locator.py
```

仓库包含技能指令、抽象案例经验和定位工具，不附现场原始日志、core、聊天记录或项目源码。

## 验证与打包

在仓库根目录执行：

```powershell
python -B -m unittest discover -s tests -v
python -B scripts/build_release.py --output-dir ./dist
```

打包脚本检查技能名称、内部引用及元数据结构，生成带顶层技能文件夹的 ZIP 和 SHA-256 清单，并逐文件校验压缩包。结构校验不等于现场分析已经自动验证。

发布说明：[v1.1.0](docs/releases/v1.1.0.md)；历史版本：[v1.0.0](docs/releases/v1.0.0.md)。
