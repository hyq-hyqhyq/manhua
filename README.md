# Interactive Comic Generator

这是一个基于 Entity Pool 的交互式多格漫画生成系统。

当前项目采用：

- `frontend/`: Next.js / React 前端
- `backend/`: FastAPI 后端
- `sam3_service/`: 独立 SAM3 分割服务
- GPT / OpenAI-compatible text provider: 分镜规划、引用选择、修改规划、ref note
- GPT Image: anchor 图和 panel 图生成
- SAM3: 从 anchor / panel 图中分割实体，持续更新 Entity Pool
- Mock providers: 在 `USE_MOCK_PROVIDERS=true` 时完整跑通，不依赖真实模型

## 快速运行

推荐开 4 个终端：SAM3、后端、前端、进度监控。

### 1. 准备环境

```bash
cd ~/code/manhua
conda env update -f environment.yml --prune
conda activate manhua
```

如果是第一次安装前端依赖：

```bash
cd ~/code/manhua/frontend
npm install
```

### 2. 配置 `.env`

复制示例文件：

```bash
cd ~/code/manhua
cp .env.example .env
```

真实模式至少需要配置：

```env
USE_MOCK_PROVIDERS=false

OPENAI_TEXT_API_KEY=...
OPENAI_TEXT_BASE_URL=...
OPENAI_TEXT_MODEL=...

OPENAI_IMAGE_API_KEY=...
OPENAI_IMAGE_BASE_URL=...
OPENAI_IMAGE_MODEL=...
OPENAI_IMAGE_TIMEOUT_SECONDS=300
OPENAI_IMAGE_EDITS_ENDPOINT=/v1/images/edits
OPENAI_IMAGE_GENERATIONS_ENDPOINT=/v1/images/generations

SAM3_ENDPOINT=http://127.0.0.1:8100/segment

OUTPUT_DIR=outputs
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

如果只想先跑 mock：

```env
USE_MOCK_PROVIDERS=true
```

不要把 `.env` 提交到 GitHub。

### 3. 启动 SAM3 服务

```bash
cd ~/code/manhua/sam3_service
conda activate manhua
CUDA_VISIBLE_DEVICES=6 uvicorn app:app --host 0.0.0.0 --port 8100
```

检查：

```bash
curl http://127.0.0.1:8100/health
```

### 4. 启动后端

```bash
cd ~/code/manhua/backend
conda activate manhua
uvicorn main:app --host 0.0.0.0 --port 8000
```

检查：

```bash
curl http://127.0.0.1:8000/health
```

### 5. 启动前端

```bash
cd ~/code/manhua/frontend
conda activate manhua
npm run dev -- -H 0.0.0.0 -p 3000
```

如果在服务器上跑，推荐本地电脑开 SSH 转发：

```bash
ssh -L 3000:127.0.0.1:3000 -L 8000:127.0.0.1:8000 -L 8100:127.0.0.1:8100 tflab4090
```

然后本地浏览器打开：

```text
http://localhost:3000
```

### 6. 不走前端直接生成

```bash
cd ~/code/manhua
conda activate manhua

curl -sS -X POST http://127.0.0.1:8000/api/comics \
  -H "Content-Type: application/json" \
  -d '{"user_prompt":"一个穿蓝色雨衣的少年在雨夜遇到一只会说话的灰猫。","layout":"3x3","style":"black_white_manga"}'
```

实时看进度：

```bash
cd ~/code/manhua

watch -n 1 'latest=$(ls -td backend/outputs/comic_* 2>/dev/null | head -1); echo $latest; [ -n "$latest" ] && cat "$latest/status.json"'
```

生成完成后查看：

```text
http://localhost:8000/outputs/{comic_id}/final_comic.png
```

下载结果到本地：

```bash
scp -r tflab4090:~/code/manhua/backend/outputs/{comic_id} .
```

## 常用 API

创建漫画：

```bash
curl -X POST http://localhost:8000/api/comics \
  -H "Content-Type: application/json" \
  -d '{"user_prompt":"A boy in a blue raincoat meets a talking gray cat on a rainy night.","layout":"2x2","style":"black_white_manga"}'
```

查询状态：

```bash
curl http://localhost:8000/api/comics/{comic_id}/status
```

获取结果：

```bash
curl http://localhost:8000/api/comics/{comic_id}
```

整体修改：

```bash
curl -X POST http://localhost:8000/api/comics/{comic_id}/revise-global \
  -H "Content-Type: application/json" \
  -d '{"feedback":"让后半部分更紧张，男主更害怕。"}'
```

单格修改：

```bash
curl -X POST http://localhost:8000/api/comics/{comic_id}/revise-panel \
  -H "Content-Type: application/json" \
  -d '{"panel_id":3,"feedback":"让男主更靠近镜头，猫坐在他肩膀上。"}'
```

单格直接编辑 summary 和 text：

```bash
curl -X POST http://localhost:8000/api/comics/{comic_id}/revise-panel \
  -H "Content-Type: application/json" \
  -d '{
    "panel_id": 3,
    "feedback": "manual edit",
    "summary": "The boy leans close to the camera while the gray cat sits on his shoulder.",
    "text": [
      {
        "type": "speech",
        "speaker": "cat",
        "content": "你终于来了。",
        "position": "top_right"
      }
    ]
  }'
```

## 目录结构

```text
comic_project/
  frontend/              Next.js / React 前端
  backend/               FastAPI 后端
    api/                 API 路由
    pipeline/            主生成流水线、prompt、验证、revision
    providers/           LLM / image / segment provider 抽象和实现
    pool/                Entity Pool 与 reference sheet
    image/               mock 图像生成工具
    segmentation/        分割辅助工具
    render/              final comic 拼接
    storage/             文件存储和 public path 映射
    outputs/             生成产物
  sam3_service/          独立 SAM3 HTTP 服务
```

## 代码思路

项目核心是“先规划，再逐格生成，再持续维护角色外观历史”。

用户输入：

- `user_prompt`: 故事描述
- `layout`: 漫画格数布局，例如 `2x2`、`3x3`
- `style`: 漫画风格，例如 `black_white_manga`

系统输出：

- `storyboard.json`
- `entity_pool.json`
- 每格 panel 图
- 每格 reference sheet
- 每个实体的 appearance refs
- `final_comic.png`

### 1. Storyboard

后端先调用文本 provider 生成极简 storyboard：

```json
{
  "style": "black_white_manga",
  "layout": "3x3",
  "entities": [
    {
      "entity_id": "boy",
      "description": "teenage boy, slim, blue raincoat"
    }
  ],
  "panels": [
    {
      "panel_id": 1,
      "summary": "The boy walks through heavy rain near an abandoned station.",
      "entities_used": ["boy"],
      "text": [
        {
          "type": "caption",
          "speaker": null,
          "content": "雨夜。",
          "position": "top_left"
        }
      ]
    }
  ]
}
```

`summary` 用于描述画面内容。  
`text` 用于让 GPT Image 直接在图里生成气泡、旁白、拟声词。项目不会再用 PIL 单独排字。

`backend/pipeline/validators.py` 会修复模型输出：

- panel 数量必须等于 layout 对应数量
- `panel_id` 必须从 1 递增
- `entities_used` 必须引用已有 entity
- 缺失 `text` 时补 `[]`
- 非法 text item 会被丢弃

### 2. Entity Pool

Entity Pool 是角色一致性的核心。它不是每个实体只保留一张图，而是保存 appearance history：

```json
{
  "boy": {
    "description": "teenage boy, slim, blue raincoat",
    "refs": [
      {
        "ref_id": "boy_ref_000",
        "rgba_path": "/outputs/comic_xxx/entity_pool/boy/boy_ref_000.png",
        "source": "anchor",
        "note": "anchor appearance"
      },
      {
        "ref_id": "boy_ref_001",
        "rgba_path": "/outputs/comic_xxx/entity_pool/boy/boy_ref_001.png",
        "source": "panel_1",
        "note": "front half-body, nervous expression"
      }
    ]
  }
}
```

初始化时：

1. 对 storyboard 中每个 entity 生成 anchor image。
2. 调用 SAM3 分割 anchor，得到透明 RGBA cutout。
3. 把 cutout 作为该实体的第一个 ref。

每生成一格后：

1. 用 SAM3 从 panel 图中分割当前出现的实体。
2. 追加新的 appearance ref。
3. Entity Pool 持续积累这个角色在不同角度、表情、动作下的外观。

### 3. Reference Selection

生成某一格时，不会把整个 Entity Pool 都塞给图像模型。

流程是：

1. 文本 provider 只看当前 panel summary、entities_used、Entity Pool 中的 `ref_id` 和 `note`。
2. 每个 entity 选 1 到 3 个 refs。
3. 优先保留 anchor ref。
4. 再选最近或最相关的 appearance refs。

如果文本 provider 失败，会回退到规则选择：

- anchor ref 优先
- 最近 refs 补齐
- 每个 entity 最多 3 张

### 4. Reference Sheet

`backend/pool/reference_sheet.py` 会把选中的 refs 拼成一张 reference sheet。

当前 reference sheet 是纯图拼贴：

- 无标题
- 无左侧标签
- 无 `ref_id/source` 文字
- 白色背景
- 尽量方正
- 每个 ref 使用较大的 cell

这张 reference sheet 会作为 GPT Image edits 的图像输入，提示词中称为 `Image A`。

### 5. Panel Image

`backend/pipeline/prompt_builder.py` 的 `panel_image_prompt(...)` 会生成每格图像 prompt。

它包含：

- style prompt
- 当前 panel summary
- 当前 panel 使用的实体描述
- 当前 panel 的 text 数组
- reference sheet 说明

GPT Image 负责直接生成带文字的 panel：

- speech -> speech balloon
- thought -> thought balloon
- caption -> caption box
- sfx -> stylized sound effect

项目不额外做独立文字渲染层。

### 6. SAM3 Update

每格 panel 生成后，后端会对 `entities_used` 中的每个实体调用 SAM3：

```text
panel image + entity_id + entity description
    -> rgba cutout
    -> append to Entity Pool
```

如果 SAM3 失败：

- `ALLOW_MOCK_SEGMENT_FALLBACK=true` 时回退 mock cutout，并记录 warning
- `ALLOW_MOCK_SEGMENT_FALLBACK=false` 时直接报错

### 7. Stitch

所有 panel 生成完后，`backend/render/stitcher.py` 根据 layout 拼成：

```text
backend/outputs/{comic_id}/final_comic.png
```

FastAPI 会把 `backend/outputs` 挂载为：

```text
/outputs
```

所以前端可以直接展示：

```text
http://localhost:8000/outputs/{comic_id}/final_comic.png
```

### 8. Revision

整体修改：

```text
feedback
  -> revision planner
  -> affected panels
  -> regenerate affected panels
  -> update Entity Pool
  -> stitch final comic
```

单格修改：

```text
panel_id + feedback / summary / text
  -> only regenerate selected panel
  -> update Entity Pool
  -> stitch final comic
```

前端现在可以直接编辑单格：

- summary
- text type
- speaker
- content
- position

保存后只重生成该 panel。

## Provider 与 fallback

真实模式：

```text
OpenAI-compatible text provider
GPT Image provider
SAM3 provider
```

Mock 模式：

```env
USE_MOCK_PROVIDERS=true
```

Fallback 行为：

- OpenAI text 失败：如果 `ALLOW_MOCK_TEXT_FALLBACK=true`，回退 mock text
- GPT Image 失败：如果 `ALLOW_MOCK_IMAGE_FALLBACK=true`，回退 mock image
- SAM3 失败：如果 `ALLOW_MOCK_SEGMENT_FALLBACK=true`，回退 mock segment

warnings 会写入：

```text
backend/outputs/{comic_id}/status.json
```

并通过前端显示。

## 输出文件

每次生成会保存到：

```text
backend/outputs/{comic_id}/
  storyboard.json
  entity_pool.json
  status.json
  final_comic.png

  anchors/
    boy_anchor.png

  panels/
    panel_1.png
    panel_2.png

  reference_sheets/
    panel_1_refsheet.png

  entity_pool/
    boy/
      boy_ref_000.png
      boy_ref_001.png
```

## 注意事项

- `.env` 不要提交。
- `3x3` 会生成 9 格，真实 GPT Image 会明显更慢。
- 如果图片 API 很快返回 404/401，通常是 base URL、endpoint、key 或 model 配错，不是超时时间问题。
- 如果只看到前端 `GET / 200`，不代表后端收到生成请求；后端窗口应出现 `POST /api/comics`。
- 如果要调试进度，优先看最新 `backend/outputs/{comic_id}/status.json`。
