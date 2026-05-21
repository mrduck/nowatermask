# 背景替换 + 图片压缩 设计文档

## 概述

在现有 AI 图像工具集上新增两个独立工具：
- **换背景**：AI 自动抠图，替换为白/蓝/红/自定义背景色
- **图片压缩**：调整质量/格式，实时预览压缩效果和体积变化

## 工具一：换背景

### 用户流程
1. 上传图片（证件照 / 人物照）
2. AI 自动抠图，展示透明背景结果
3. 选择背景颜色：白色(默认) / 蓝色 / 红色 / 自定义颜色
4. 下载 PNG 结果图

### 后端

- **模型**：rembg (u2net, ~176MB)，通过 onnxruntime CPU 推理
- **模型路径**：`backend/models/u2net.onnx`
- **环境变量**：`U2NET_HOME=backend/models`
- **API 端点**：
  - `POST /api/remove-bg`：上传图片 → 返回 RGBA PNG（透明背景）
  - `POST /api/replace-bg`：上传图片 + 背景色 hex → 返回合成 PNG

### 前端

- **路由**：`/bg`
- **组件**：`BackgroundReplace.vue`
- **交互**：ImageUploader 上传 → 自动抠图(loading) → 原图/结果左右对比 → 背景色选择器(4个预设+取色器) → 下载按钮

## 工具二：图片压缩

### 用户流程
1. 上传图片
2. 拖动质量滑块（1-100%）
3. 左右对比：原图 vs 压缩图
4. 显示体积变化：原始大小 → 压缩后大小 → 压缩率
5. 可选切换输出格式：PNG / JPEG / WebP
6. 下载压缩图

### 后端

- **方案**：纯 Pillow 处理，零模型依赖
- **API 端点**：
  - `POST /api/compress`：上传图片 + quality(int) + format(str) → 返回压缩图

### 前端

- **路由**：`/compress`
- **组件**：`ImageCompress.vue`
- **交互**：ImageUploader 上传 → 质量滑块(默认75) → 格式选择器 → 原图/压缩图左右对比 → 体积信息卡片 → 下载按钮

## 文件改动清单

| 文件 | 动作 | 说明 |
|------|------|------|
| `backend/main.py` | 修改 | 新增 3 个 API 端点 |
| `backend/requirements.txt` | 修改 | 新增 rembg 依赖 |
| `backend/models/` | 已有 | u2net 模型已下载 |
| `frontend/src/router/index.ts` | 修改 | 新增 `/bg` 和 `/compress` 路由 |
| `frontend/src/components/Navbar.vue` | 修改 | 新增 2 个导航入口 |
| `frontend/src/pages/BgReplacePage.vue` | 新建 | 换背景页面 |
| `frontend/src/pages/CompressPage.vue` | 新建 | 压缩页面 |
| `frontend/src/utils/api.ts` | 修改 | 新增 3 个 API 函数 |

## 非功能性要求

- 抠图处理时间：普通照片 < 10 秒
- 压缩处理时间：毫秒级
- 复用现有 ImageUploader 组件
- 页面风格与现有工具一致（Tailwind CSS）