# -*- coding: utf-8 -*-
"""ROUND16 · 七主题对比度审计（WCAG 2.1 相对亮度）
数据源：styles.css 各主题令牌（与源码一致，人工核对过）。
输出：关键色对对比度 + WCAG 等级表。
"""


def lin(c):
    c /= 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def lum(rgb):
    return 0.2126 * lin(rgb[0]) + 0.7152 * lin(rgb[1]) + 0.0722 * lin(rgb[2])


def cr(a, b):
    x, y = lum(a), lum(b)
    return (max(x, y) + 0.05) / (min(x, y) + 0.05)


def lv(v):
    if v >= 7:
        return "AAA"
    if v >= 4.5:
        return "AA"
    if v >= 3:
        return "AA大字"
    return "FAIL"


def hx(s):
    s = s.lstrip("#")
    return tuple(int(s[i : i + 2], 16) for i in (0, 2, 4))


# theme: (bg-deep, bg-panel, ink-hi, ink-mid, ink-low, gold(CTA底), btn-ink字)
T = {
    "A 柔雾青绿": ("E8EFF3", "DDE9F0", "1F3A4D", "4A6577", "6B8296", "5B9E84", "17222B"),
    "B 黑白瑞士": ("FFFFFF", "FFFFFF", "000000", "333333", "6B6B6B", "000000", "FFFFFF"),
    "C 暗墨夜山": ("0A1424", "161A20", "E8E2C8", "A99F80", "7A7362", "C9A227", "17222B"),
    "D 青绿金碧": ("C9B58A", "BFA87E", "2C2418", "4E4335", "6E604C", "B89048", "17222B"),
    "E 雨过天青": ("E3E9E5", "DAE2DC", "22302A", "46564E", "68776E", "589384", "17222B"),
    "F 玄墨赭金": ("171512", "1E1B17", "E9E2D4", "B3AA96", "877E6B", "C2955A", "17222B"),
    "G 秋香宣纸": ("EFE8D9", "E6DECB", "322C20", "5C5442", "7D745E", "A0824A", "17222B"),
}

print(f"{'主题':<10} {'正文/主底':>10} {'次级/面板':>10} {'辅助/主底':>10} {'CTA字/CTA底':>12}")
for name, (bg, panel, hi, mid, low, gold, onink) in T.items():
    a = cr(hx(hi), hx(bg))
    b = cr(hx(mid), hx(panel))
    c = cr(hx(low), hx(bg))
    d = cr(hx(onink), hx(gold))
    print(
        f"{name:<10} {a:>6.2f} {lv(a):<4} {b:>6.2f} {lv(b):<4} {c:>6.2f} {lv(c):<4} {d:>6.2f} {lv(d):<4}"
    )

print()
print("门槛：正文 AA>=4.5（小字辅助文字同门槛）/ 大字 AA>=3.0 / AAA>=7.0")
