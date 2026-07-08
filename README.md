# 京东会场头图 Lottie 动效延展 (jd-campaign-head-img-motion)

> 将 2-4 个静帧 Lottie JSON 合并为带切帧动效的循环 Lottie JSON，自动识别静态图层并生成平滑的入场/退场动画。支持 Figma 插件导出的顶层 `Clip Mask + Content` 画布包装。

## 效果演示

[▶️ 点击观看演示视频](https://github.com/hugohung/jd-campaign-head-img-motion/releases/download/v9.7.2/demo.mp4)

## 功能特性

- 🎯 **自动识别静态图层** — 背景、腰封等不变元素自动保持不动
- 🧩 **支持 2-4 个画面** — 旧的双图输入继续可用，也可输入 3/4 个静态 JSON 生成多段循环
- 🎨 **Figma 导出兼容** — 自动展开顶层 `Clip Mask + Content`，把 `Content` comp 作为真实动效图层来源
- 🫧 **文案透明度编排** — 文案层以中心点到达画布边缘或指定点位触发渐现/渐隐，非文案元素保持源透明度
- ✨ **智能方向分配** — 根据元素在画布中的位置，自动选择入场/退场方向（左/右/下/中）
- 🎬 **专业动效参数** — 弹性缓动曲线 + 过冲回弹效果 + 垂直错帧延迟
- 🔗 **完整属性保留** — parent 父子关系、旋转、锚点、混合模式全部保留
- 📦 **即开即用预览** — 自动生成含播放控制 + 下载按钮的 HTML 预览页
- 🔄 **无缝循环** — 首尾帧状态完全一致，循环播放无跳变

## 快速开始

```bash
# 安装（WorkBuddy 用户）
# 1. 下载 Release zip
# 2. WorkBuddy → 技能管理 → 上传技能

# 使用
python scripts/generate_merged_lottie_pipeline.py <场景A.json> <场景B.json> [场景C.json] [场景D.json] [输出目录]

# 预览
# 本地直接打开 preview_embedded.html；或起服务查看 preview.html
cd 输出目录 && python -m http.server 8770
```

## 输入输出

```
输入：场景A.json + 场景B.json + 可选场景C.json/场景D.json
      ↓ 脚本自动处理
输出：merged_output.json（合并后的动效文件）
     preview.html（预览页面，含播放/暂停/速度/下载功能）
     preview_embedded.html（本地文件预览页面，无需起服务）
```

**输入要求：**
- 2-4 个 Lottie JSON 文件
- 尺寸相同（宽 × 高一致）
- 背景层相同或相近，前景层不同
- Figma 插件导出的顶层 `Clip Mask + Content` 会自动展开

## 工作原理

### 1. 图层分类

脚本自动对比所有输入文件的每个图层，通过 7 维度匹配判断是否为「全场景静态图层」：

| 匹配维度 | 说明 |
|----------|------|
| 图层类型 (ty) | 必须相同 |
| 父级关系 (parent) | 必须相同 |
| 旋转角度 (rotation) | 容差 < 0.01° |
| 位置 (position) | 容差 < 2px |
| 锚点 (anchor) | 容差 < 0.1px |
| 缩放比例 (scale) | 容差 < 0.1% |
| asset 内容 | 图片: base64 对比; 形状: 变换对比 |

### 2. 时间轴

```
0.0s ── 1.0s   场景 A 显示
1.0s ── 1.5s   A 渐隐消失 + B 渐显出现（同步交叉溶解）
1.5s ── 3.5s   场景 B 显示
3.5s ── 4.0s   B 渐隐消失 + A 渐显出现（同步交叉溶解）
4.0s ── 5.0s   场景 A 显示 ← 循环回到开头
```

### 3. 动画参数

- **弹性过冲 (overshoot)**：小元素弹得更夸张 (10%)，大元素柔和 (3%)
- **垂直错帧**：高处元素先入场，产生波浪感
- **缓动曲线**：标准缓入/缓出 + 弹性缓入/缓出组合

## 示例

`examples/` 目录包含完整的示例案例：

```bash
# 运行示例
python scripts/generate_merged_lottie_pipeline.py examples/scene-a.json examples/scene-b.json examples/

# 预览示例输出
cd examples && python -m http.server 8770
# 浏览器打开 http://localhost:8770/preview.html
```

## 支持的 Lottie 元素类型

| 类型代码 | 名称 | 是否支持 |
|----------|------|----------|
| ty=0 | 预合成 (Pre-composition) | ✅ |
| ty=1 | 文本 (Text) | ⚠️ 基础支持 |
| ty=2 | 图片 (Image) | ✅ |
| ty=3 | 空对象 (Null) | ✅ |
| ty=4 | 形状 (Shape) | ✅ |
| ty=5 | 纯色 (Solid) | ✅ |

## 项目结构

```
jd-campaign-head-img-motion/
├── SKILL.md                        # AI 指令文档
├── README.md                       # 本文件
├── LICENSE                         # MIT 协议
├── scripts/
│   └── generate_merged_lottie_pipeline.py # 主脚本（分阶段流水线）
├── references/
│   ├── .gitkeep
│   └── LOTTIE_BUG_CHECKLIST.md    # 排错自查表
└── examples/
    ├── .gitkeep
    ├── scene-a.json                # 示例源文件A
    ├── scene-b.json                # 示例源文件B
    ├── expected-output.json        # 示例预期输出
    └── preview.html                # 示例预览页
```

## 版本历史

查看 [SKILL.md](./SKILL.md) 中的版本历史表格。

## 技术栈

- Python 3.12+ (无第三方依赖)
- lottie-web 5.12.x (CDN 加载)
- FileSaver.js 2.0.x (CDN 加载)
- Lottie JSON 格式 (5.6+)

## License

[MIT](./LICENSE)

## 作者

[honghaoxiang](https://github.com/hugohung) — 京东
