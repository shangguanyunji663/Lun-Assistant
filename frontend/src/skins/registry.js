/* ============================================================
   v18 · 皮肤注册表（单一真源）
   —— 取代 v16 的「6 主题 + 柔化开关」体系。

   一套「皮肤」= 一种完整的设计语言（配色 / 字体 / 排版 / 材质 / 动效性格），
     · 工作台：<html data-skin="..."> 切换，样式见 src/skins/*.css
     · 落地页：每套皮肤一个独立 HTML（六种结构差异过大，无法靠 CSS 换肤），
       见 landing 字段；两侧共用同一份 localStorage.lj_skin 保持同步。
   ============================================================ */

export const SKINS = [
  {
    id: 'a',
    label: '铅字印刷',
    en: 'Letterpress',
    chip: '#C0332A',
    desc: '新闻纸灰白 + 墨黑 + 朱砂红，编辑网格与朱印',
    landing: './index.html',
    themeColor: '#E8E3D8',
  },
  {
    id: 'b',
    label: '夜航仪表',
    en: 'Instrument Console',
    chip: '#3FE0C4',
    desc: '近黑仪器台 + 荧光青，网格底纹与遥测读数',
    landing: './landing-b.html',
    themeColor: '#07080A',
  },
  {
    id: 'c',
    label: '学术海报',
    en: 'Poster',
    chip: '#CCFF00',
    desc: '纯白 + 纯黑 + 荧光酸绿，巨型排版与满幅摄影',
    landing: './landing-c.html',
    themeColor: '#F2F2EF',
  },
  {
    id: 'd',
    label: '木牍竖排',
    en: 'Bamboo Slips',
    chip: '#A8402C',
    desc: '竹青灰 + 墨绿 + 朱色，竖排标题与书签式切换',
    landing: './landing-d.html',
    themeColor: '#D5DCCD',
  },
  {
    id: 'e',
    label: '孔版双色',
    en: 'Riso Collage',
    chip: '#FF4D9D',
    desc: '荧光粉 + 荧光青 + 零模糊硬阴影，拼贴错位套印',
    landing: './landing-e.html',
    themeColor: '#F1F1EC',
  },
  {
    id: 'f',
    label: '索引档案',
    en: 'Archive Index',
    chip: '#A33B2A',
    desc: '档案纸灰绿 + 打字机字 + 图章红，索引卡与连续打印纸',
    landing: './landing-f.html',
    themeColor: '#E1E2DD',
  },
]

export const SKIN_IDS = SKINS.map(s => s.id)

/** 默认皮肤：落地页 index.html 即 A 的页面，工作台回退到 A */
export const DEFAULT_SKIN = 'a'

export const findSkin = (id) => SKINS.find(s => s.id === id) || SKINS[0]

const LS_SKIN = 'lj_skin'

export const loadSkin = () => {
  try {
    const v = localStorage.getItem(LS_SKIN)
    return SKIN_IDS.includes(v) ? v : DEFAULT_SKIN
  } catch {
    return DEFAULT_SKIN
  }
}

export const saveSkin = (id) => {
  try { localStorage.setItem(LS_SKIN, id) } catch { /* 隐私模式忽略 */ }
}

export { LS_SKIN }