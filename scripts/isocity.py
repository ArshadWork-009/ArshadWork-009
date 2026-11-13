"""Isometric 3D contribution city shared by the themes.

Blocks rise from the floor in a wave (CSS animation, skipped for reduced motion) and busy days get their own colour.
"""
import math

# put this inside the svg's <style>
CSS = (".b{transform-box:fill-box;transform-origin:50% 100%;animation:rise .7s cubic-bezier(.2,.8,.2,1) both}"
       "@keyframes rise{from{transform:scaleY(0);opacity:0}}"
       "@media (prefers-reduced-motion:reduce){.b{animation:none}}")


# flat heatmaps (terminal, soc): cells pop in as a sweep, left to right
HEATMAP_CSS = (".h{transform-box:fill-box;transform-origin:center;animation:pop .45s cubic-bezier(.2,.8,.2,1) both}"
               "@keyframes pop{from{transform:scale(0);opacity:0}}@media (prefers-reduced-motion:reduce){.h{animation:none}}")


def sweep(c, r):  # style attribute that staggers a cell by its column and row
    return f'style="animation-delay:{c * 15 + r * 6}ms"'


def iso_city(days, maxc, pal, high, high_min):
    """days: [row, col, date, level, count]; pal: level -> (top, left, right) colours; high: colours for days with at least high_min commits.

    Returns (shapes, W, H, ox, oy): a list of svg strings to put inside <g transform="translate(ox,oy)"> and the canvas size.
    """
    scale, pad = 15.0, 44
    c30 = math.cos(math.radians(30))
    P = lambda x, y, z: ((x + y) * c30 * scale, (y - x) * 0.5 * scale - z)
    poly = lambda pts, fill: '<polygon points="%s" fill="%s"/>' % (" ".join("%.1f,%.1f" % p for p in pts), fill)
    shapes, xs, ys = [], [], []
    for r, c, d, lvl, n in sorted(days, key=lambda t: (-t[1], t[0])):  # far blocks first
        h = 1.5 if n == 0 else 3 + 80 * (n / maxc) ** 0.7
        top, left, right = high if n >= high_min else pal[lvl]
        t = [P(c, r, h), P(c + 1, r, h), P(c + 1, r + 1, h), P(c, r + 1, h)]
        lf = [P(c, r, 0), P(c, r + 1, 0), P(c, r + 1, h), P(c, r, h)]
        rt = [P(c, r + 1, 0), P(c + 1, r + 1, 0), P(c + 1, r + 1, h), P(c, r + 1, h)]
        faces = poly(lf, left) + poly(rt, right) + poly(t, top)
        # empty days stay flat; the rest rise, left to right
        shapes.append(f'<g class="b" style="animation-delay:{c * 14 + r * 5}ms">{faces}</g>' if n else faces)
        for p in t + lf + rt:
            xs.append(p[0]); ys.append(p[1])
    W, H = max(xs) - min(xs) + pad * 2, max(ys) - min(ys) + pad * 2
    return shapes, W, H, pad - min(xs), pad - min(ys)
