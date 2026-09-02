# 论匠前端 · 版本线文档索引（frontend-versions）

> 文档域：frontend-versions
> 文档类型：操作手册 / 指南
> 主题版本：v8 → v12
> 轮次：—
> 日期：2026-09-02
> 状态：已落地

> ⚠️ **变更标注（2026-09-02 · 文档治理轮）**：本目录于文档治理轮新建，将原先散落于 `docs/`、`docs/design-concepts/`、`design-concepts/`、`frontend/` 四处的**前端版本演进文档**统一归口。原路径保留 stub 指针，不计入正文。格式规范见 [`../FORMAT_STANDARD.md`](../FORMAT_STANDARD.md)。

---

## 一、本目录作用

1. **前端版本线单一真源**：v8 → v12 每个版本的提案 / 设计规范 / 变更档案 / 工程落档全部收敛于此，形成完整版本时间线。
2. **后续版本扩展锚点**：新增版本（如 v13）时，复制 [`TEMPLATE.md`](./TEMPLATE.md) 起步，按 `CHANGELOG-v{N}.md` 命名，并在「三、版本索引」追加一行。

---

## 二、主题演进线（一图）

```
ROUND5 文墨浅黛（源头，见 docs/OPTIMIZATION_ROUND5.md §5）
   │
   ▼
v8   水墨留白 · 三方向提案        → VISUAL_DIRECTIONS.md（提案）
   │
   ▼
v9   青绿长卷 · 放松版            → DESIGN_SPEC.md（规范）+ OPTIMIZATION_ROUND7.md（落档）
   │
   ▼
v10  三主题切换系统（A/B/C）       → OPTIMIZATION_ROUND8.md（落档）+ ROUND9.md（WebP）+ ROUND10.md（遗留项 L-2~L-8）
   │
   ▼
v11  四主题（A/B/C/D，4 张参考图） → CHANGELOG-v11-design.md（设计稿侧）+ CHANGELOG-v11-frontend.md（生产侧）
   │
   ▼
v12  B 主题黑白瑞士（ROUND11）     → CHANGELOG-v12.md（设计稿侧）+ OPTIMIZATION_ROUND11.md（生产侧落档）
```

---

## 三、版本索引（文件 → 版本 → 角色）

| 版本 | 文件 | 文档类型 | 角色 |
|---|---|---|---|
| —（v8 前奏） | [`OPTIMIZATION_ROUND5.md`](../../docs/OPTIMIZATION_ROUND5.md) *原位保留* | 轮次记录 | 文墨浅黛主题源头（混合轮次，非本目录） |
| v8 | [`VISUAL_DIRECTIONS.md`](./VISUAL_DIRECTIONS.md) | 提案 | 视觉重构三方向提案（青绿 / 水墨改良 / 暗墨金线） |
| v9 | [`DESIGN_SPEC.md`](./DESIGN_SPEC.md) | 设计规范 | 青绿长卷·放松版设计令牌与规范 |
| v9 | [`OPTIMIZATION_ROUND7.md`](./OPTIMIZATION_ROUND7.md) | 轮次记录 | v9 前端视觉重构落地（后端零改动） |
| v10 | [`OPTIMIZATION_ROUND8.md`](./OPTIMIZATION_ROUND8.md) | 轮次记录 | v10 三主题切换 + 功能同步 |
| v10 | [`OPTIMIZATION_ROUND9.md`](./OPTIMIZATION_ROUND9.md) | 轮次记录 | 主题图 WebP 压缩（5.32→0.26MB）+ GitHub Pages 部署 |
| v10 | [`OPTIMIZATION_ROUND10.md`](./OPTIMIZATION_ROUND10.md) | 轮次记录 | v10 遗留项 L-2~L-8 全落地 |
| v11 | [`CHANGELOG-v11-design.md`](./CHANGELOG-v11-design.md) | 版本变更 | v11 四主题 · 设计稿侧（preview/tuner.html） |
| v11 | [`CHANGELOG-v11-frontend.md`](./CHANGELOG-v11-frontend.md) | 版本变更 | v11 四主题 · 生产侧（frontend/ 端到端改造） |
| v12 | [`CHANGELOG-v12.md`](./CHANGELOG-v12.md) | 版本变更 | v12 B 黑白瑞士 · 设计稿侧 |
| v12 | [`OPTIMIZATION_ROUND11.md`](./OPTIMIZATION_ROUND11.md) | 轮次记录 | v12 B 黑白瑞士 · 生产侧落档 |

---

## 四、配套文档（非本目录）

| 类型 | 位置 |
|---|---|
| 设计稿资源（HTML/PNG） | `design-concepts/`（preview.html / tuner.html / 参考图） |
| 生产代码 | `frontend/src/styles.css`（token）`frontend/src/App.jsx`（主题切换） |
| 后端 / 通用轮次 | `docs/OPTIMIZATION_ROUND{1-6}.md` 等 |

---

## 五、新增版本操作指引

新增前端版本（如 v13）时按以下步骤：

1. 复制 [`TEMPLATE.md`](./TEMPLATE.md) → 重命名 `CHANGELOG-v13.md`（设计稿侧）与/或按需 `OPTIMIZATION_ROUND{N}.md`（生产侧落档）。
2. 在「二、主题演进线」追加一行 v13。
3. 在「三、版本索引」追加一行（版本 / 文件 / 文档类型 / 角色）。
4. 若改动既涉及设计稿又涉及生产代码，保留**双档案模式**（design 侧 + frontend 侧各一份）。
5. 按 [`../FORMAT_STANDARD.md`](../FORMAT_STANDARD.md) §二 填写 front-matter，正文用「## 一、总览（结论先行）」骨架。
6. 同步更新根 [`../README.md`](../README.md) 文档导航表。

---

## 六、本目录文件清单（10 份正文 + 1 模板）

```
docs/frontend-versions/
├── README.md                    ← 本索引
├── TEMPLATE.md                  ← 新增版本模板
├── VISUAL_DIRECTIONS.md         ← v8 提案
├── DESIGN_SPEC.md               ← v9 规范
├── OPTIMIZATION_ROUND7.md       ← v9 落档
├── OPTIMIZATION_ROUND8.md       ← v10 落档
├── OPTIMIZATION_ROUND9.md       ← v10 WebP + 部署
├── OPTIMIZATION_ROUND10.md      ← v10 遗留项
├── CHANGELOG-v11-design.md      ← v11 设计稿侧
├── CHANGELOG-v11-frontend.md    ← v11 生产侧
├── CHANGELOG-v12.md             ← v12 设计稿侧
└── OPTIMIZATION_ROUND11.md      ← v12 生产侧落档
```
