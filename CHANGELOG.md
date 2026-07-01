# Changelog

## 版本历史

| 版本 | 日期 | 主要变更 |
|------|------|----------|
| V9.6.1 | 2026-07-01 | **修复预览模板速度按钮高亮丢失**：`ss()` 函数生成的 `btnId` 与按钮实际 `id` 不匹配（`0.5`→`s005` vs `s05`），导致点击任何速度按钮后 active 类被移除但无法重新添加。统一按钮 id 为 `s0.5`/`s1`/`s2`，`ss()` 改为 `btnId = 's' + s` |
| V9.6 | 2026-07-01 | **文字图层关键词自动识别装饰/突出元素**：Stage 0 新增 `_extract_text_content()` 扫描 ty=5 文字图层获取实际文本内容；Stage 1 新增 `_auto_detect_deco_highlight()` 将匹配关键词（`装饰`/`核心利益点`/`主推`/`爆品` 等）的文字图层空间映射到最近图片图层，自动应用展示动效；无文字图层或无匹配时跳过 Stage 4 并输出引导提示（可截图指定图层编号后用 `--deco`/`--highlight` 重跑）；图层名语义匹配不再直接触发展示动效，仅用于分组方向判断 |
| V9.4 | 2026-06-30 | **展示阶段动效定稿**：参数化指定 `--deco` 装饰元素和 `--highlight` 突出元素；装饰元素匀速环形晃动+持续旋转（线性缓动，参考0610.json画画/植物）；突出元素缩放两下 100%-120%（以图片中心为缩放中心）；删除自动识别（避免空名误伤），改为提问确认+参数指定；embedded预览改本地依赖（自动下载 lottie.min.js/FileSaver.min.js，无需联网）；修复 `_build_pos/rot_kfs_style` 中 `in_start == windup_dur_f` 导致 t=0 重复关键帧的 bug；移除预览容器 `#lc` 的 `border-radius` 避免满宽元素（如腰带）被裁切 |
| V9.3 | 2026-06-30 | **全面fps自适应**：退场蓄力下限max(2帧)改T_WINDUP_MIN秒定义；淡入淡出0.07/0.10硬编码改T_FADE常量；最小展示0.6硬编码改T_MIN_HOLD常量；废弃_calc_stagger_ref改秒定义；30fps+100fps交叉验证节奏一致 |
| V9.2 | 2026-06-30 | **fps自适应+静态识别修复**：所有时长改秒定义按fps换算（修复100fps下节奏太快/蓄力不可见）；静态识别改用asset尺寸(aw/ah)代替base64比对（修复lottielab重导出导致的漏判）；分组bug修复（空名nm做dict key互相覆盖导致所有元素同方向） |
| V9.1 | 2026-06-30 | 分阶段流水线架构（6阶段解耦+中间产物+自检+局部重跑）；参考动效风格（两段式交叉+首尾空帧+蓄力+overshoot+bounce+退场蓄力）；L1纯代码分组（语义匹配+空间聚类）+L2人工微调；预览模板固化（单一函数+自检+JSON大小显示） |
| V8.1 | 2026-06-30 | 预览模板固化：fetch/embedded 合并 build_preview_html()，生成后自检 |
| V8.0 | 2026-06-29 | 预览优化：toggle按钮、FileSaver.js、回归V6时间轴 |
| V9实验 | 2026-06-29 | 参考动效分析尝试，因元素不可见回滚（教训：A组opacity别设0首帧） |
| V7.x | 2026-06-24~26 | 7维度静态识别、center交叉溶解、CDN修复 |
| V6 | 2026-06-18 | position/scale 3分量、视觉边界飞行距离、弹性缓动 |
| V1-V5 | 2026-06-17~18 | 基础功能、parent保留、anchor/rotation/cl修复 |

## 备份与回滚

早期版本备份文件曾保存在 `scripts/` 目录下。现已移除——如需回滚，通过 Git 历史：
```bash
git log --oneline scripts/generate_merged_lottie_pipeline.py
git checkout <commit> -- scripts/generate_merged_lottie_pipeline.py
```
