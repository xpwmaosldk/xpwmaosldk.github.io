import struct
import zlib
import os
import math

def make_png(width, height, rgba_data):
    """
    rgba_data: bytes of length width * height * 4
    """
    raw_data = bytearray()
    for y in range(height):
        raw_data.append(0)  # filter type 0 (None)
        start = y * width * 4
        end = start + width * 4
        raw_data.extend(rgba_data[start:end])
    
    def chunk(tag, data):
        c = tag + data
        crc = zlib.crc32(c) & 0xffffffff
        return struct.pack('>I', len(data)) + c + struct.pack('>I', crc)
    
    png = bytearray(b'\x89PNG\r\n\x1a\n')
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    png.extend(chunk(b'IHDR', ihdr))
    png.extend(chunk(b'IDAT', zlib.compress(bytes(raw_data), level=9)))
    png.extend(chunk(b'IEND', b''))
    return bytes(png)

def make_ico(png_images):
    """
    png_images: list of (width, height, png_bytes)
    """
    count = len(png_images)
    header = struct.pack('<HHH', 0, 1, count)
    entries = bytearray()
    offset = 6 + 16 * count
    data_bytes = bytearray()
    
    for w, h, pdata in png_images:
        b_width = 0 if w >= 256 else w
        b_height = 0 if h >= 256 else h
        size = len(pdata)
        entry = struct.pack('<BBBBHHII', b_width, b_height, 0, 0, 1, 32, size, offset)
        entries.extend(entry)
        data_bytes.extend(pdata)
        offset += size
        
    return bytes(header + entries + data_bytes)

def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    p1x, p1y = poly[0]
    for i in range(1, n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def dist_segment(px, py, ax, ay, bx, by):
    l2 = (bx - ax)**2 + (by - ay)**2
    if l2 == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * (bx - ax) + (py - ay) * (by - ay)) / l2))
    proj_x = ax + t * (bx - ax)
    proj_y = ay + t * (by - ay)
    return math.hypot(px - proj_x, py - proj_y)

def rounded_rect_sdf(px, py, x, y, w, h, r):
    cx = x + w / 2.0
    cy = y + h / 2.0
    dx = abs(px - cx) - (w / 2.0 - r)
    dy = abs(py - cy) - (h / 2.0 - r)
    ox = max(dx, 0.0)
    oy = max(dy, 0.0)
    inside_dist = min(max(dx, dy), 0.0)
    return math.hypot(ox, oy) + inside_dist - r

def render_resume_icon(size, is_maskable=False):
    """
    Renders Developer Resume (CV) Icon:
    - Folded-corner document (Resume symbol)
    - Code brackets < / > (Developer symbol)
    - Resume content accent lines
    - Neo-Brutalist yellow (#FFE600), bold black strokes, and hard drop shadow
    """
    c_yellow = (255, 230, 0, 255)       # #FFE600
    c_black = (17, 17, 17, 255)          # #111111 Jet Black
    c_white = (255, 255, 255, 255)      # Flap fill
    c_transparent = (0, 0, 0, 0)
    
    s = size
    rgba = bytearray(s * s * 4)
    
    # Scale calculation
    if is_maskable:
        bg_color = c_yellow
        doc_scale = 0.68
    else:
        bg_color = c_transparent
        doc_scale = 0.82
        
    doc_w = s * doc_scale * 0.88   # aspect ratio of resume paper (approx 1:1.15)
    doc_h = s * doc_scale * 1.02
    
    shadow_offset = max(1.5, s * 0.055)
    center_x = s * 0.5 - (0 if is_maskable else shadow_offset * 0.35)
    center_y = s * 0.5 - (0 if is_maskable else shadow_offset * 0.35)
    
    # Document dimensions
    left = center_x - doc_w / 2.0
    right = center_x + doc_w / 2.0
    top = center_y - doc_h / 2.0
    bottom = center_y + doc_h / 2.0
    
    fold_size = doc_w * 0.30  # Corner fold
    
    # Document polygon (5 points: top-left, fold-start, fold-end, bottom-right, bottom-left)
    doc_poly = [
        (left, top),
        (right - fold_size, top),
        (right, top + fold_size),
        (right, bottom),
        (left, bottom)
    ]
    
    # Fold flap triangle
    flap_poly = [
        (right - fold_size, top),
        (right - fold_size, top + fold_size),
        (right, top + fold_size)
    ]
    
    # Shadow polygon
    shadow_poly = [(px + shadow_offset, py + shadow_offset) for px, py in doc_poly]
    
    stroke_w = max(1.2, s * 0.045)
    
    # Code brackets geometry < / >
    bracket_y = center_y - doc_h * 0.04
    bracket_h = doc_h * 0.22
    bracket_w = doc_w * 0.18
    bracket_stroke = max(1.2, s * 0.055)
    
    # Left bracket <
    lb_x1, lb_y1 = center_x - doc_w * 0.26, bracket_y - bracket_h / 2.0
    lb_x2, lb_y2 = center_x - doc_w * 0.38, bracket_y
    lb_x3, lb_y3 = center_x - doc_w * 0.26, bracket_y + bracket_h / 2.0
    
    # Slash /
    sl_x1, sl_y1 = center_x + doc_w * 0.07, bracket_y - bracket_h / 2.0 - doc_h * 0.03
    sl_x2, sl_y2 = center_x - doc_w * 0.07, bracket_y + bracket_h / 2.0 + doc_h * 0.03
    
    # Right bracket >
    rb_x1, rb_y1 = center_x + doc_w * 0.26, bracket_y - bracket_h / 2.0
    rb_x2, rb_y2 = center_x + doc_w * 0.38, bracket_y
    rb_x3, rb_y3 = center_x + doc_w * 0.26, bracket_y + bracket_h / 2.0
    
    # Resume lines (show when size >= 32)
    has_lines = (size >= 32)
    line1_y = center_y + doc_h * 0.24
    line1_w = doc_w * 0.58
    line1_h = max(1.5, doc_h * 0.065)
    
    line2_y = center_y + doc_h * 0.36
    line2_w = doc_w * 0.38
    line2_h = max(1.5, doc_h * 0.065)
    
    # Precompute SSAA offsets (2x2)
    subpixels = [(-0.25, -0.25), (0.25, -0.25), (-0.25, 0.25), (0.25, 0.25)]
    
    for y in range(s):
        for x in range(s):
            acc_r = acc_g = acc_b = acc_a = 0
            
            for sx, sy in subpixels:
                px = x + 0.5 + sx
                py = y + 0.5 + sy
                
                r, g, b, a = bg_color
                
                # 1. Shadow pass (if not maskable)
                if not is_maskable:
                    if point_in_poly(px, py, shadow_poly):
                        r, g, b, a = c_black
                else:
                    # In maskable mode: also draw hard shadow behind paper
                    if point_in_poly(px, py, shadow_poly):
                        r, g, b, a = c_black
                
                # 2. Main Document Body pass
                if point_in_poly(px, py, doc_poly):
                    # Check if near edge for black border
                    min_edge_dist = min(
                        dist_segment(px, py, doc_poly[i][0], doc_poly[i][1], doc_poly[(i+1)%5][0], doc_poly[(i+1)%5][1])
                        for i in range(5)
                    )
                    if min_edge_dist <= stroke_w:
                        r, g, b, a = c_black
                    else:
                        r, g, b, a = c_yellow
                        
                    # 3. Flap pass
                    if point_in_poly(px, py, flap_poly):
                        flap_edge_dist = min(
                            dist_segment(px, py, flap_poly[i][0], flap_poly[i][1], flap_poly[(i+1)%3][0], flap_poly[(i+1)%3][1])
                            for i in range(3)
                        )
                        if flap_edge_dist <= stroke_w * 0.85:
                            r, g, b, a = c_black
                        else:
                            r, g, b, a = c_white
                            
                    # 4. Content elements (Code brackets < / >)
                    # Left bracket
                    d_lb1 = dist_segment(px, py, lb_x1, lb_y1, lb_x2, lb_y2)
                    d_lb2 = dist_segment(px, py, lb_x2, lb_y2, lb_x3, lb_y3)
                    if min(d_lb1, d_lb2) <= bracket_stroke * 0.5:
                        r, g, b, a = c_black
                        
                    # Slash /
                    d_sl = dist_segment(px, py, sl_x1, sl_y1, sl_x2, sl_y2)
                    if d_sl <= bracket_stroke * 0.5:
                        r, g, b, a = c_black
                        
                    # Right bracket >
                    d_rb1 = dist_segment(px, py, rb_x1, rb_y1, rb_x2, rb_y2)
                    d_rb2 = dist_segment(px, py, rb_x2, rb_y2, rb_x3, rb_y3)
                    if min(d_rb1, d_rb2) <= bracket_stroke * 0.5:
                        r, g, b, a = c_black
                        
                    # 5. Resume lines
                    if has_lines:
                        # Line 1
                        d_l1 = rounded_rect_sdf(px, py, center_x - line1_w / 2.0, line1_y - line1_h / 2.0, line1_w, line1_h, line1_h * 0.5)
                        if d_l1 <= 0:
                            r, g, b, a = c_black
                        # Line 2
                        d_l2 = rounded_rect_sdf(px, py, center_x - line1_w / 2.0, line2_y - line2_h / 2.0, line2_w, line2_h, line2_h * 0.5)
                        if d_l2 <= 0:
                            r, g, b, a = c_black
                else:
                    # Antialiasing for outer document edges
                    min_edge_dist = min(
                        dist_segment(px, py, doc_poly[i][0], doc_poly[i][1], doc_poly[(i+1)%5][0], doc_poly[(i+1)%5][1])
                        for i in range(5)
                    )
                    if min_edge_dist <= 0.6 and not (not is_maskable and point_in_poly(px, py, shadow_poly)):
                        r, g, b, a = c_black
                        
                acc_r += r
                acc_g += g
                acc_b += b
                acc_a += a
                
            idx = (y * s + x) * 4
            rgba[idx] = acc_r // 4
            rgba[idx + 1] = acc_g // 4
            rgba[idx + 2] = acc_b // 4
            rgba[idx + 3] = acc_a // 4
            
    return make_png(s, s, bytes(rgba))

def main():
    out_dir = r"c:\Users\xpwma\Documents\project\xpwmaosldk.github.io"
    print("Generating Developer Resume Icons...")
    
    # 1. Favicon (16, 32, 48)
    png_16 = render_resume_icon(16)
    png_32 = render_resume_icon(32)
    png_48 = render_resume_icon(48)
    
    ico_data = make_ico([(16, 16, png_16), (32, 32, png_32), (48, 48, png_48)])
    with open(os.path.join(out_dir, "favicon.ico"), "wb") as f:
        f.write(ico_data)
    print("Saved favicon.ico")
    
    # 2. Apple Touch Icon (180x180)
    png_180 = render_resume_icon(180)
    with open(os.path.join(out_dir, "apple-touch-icon.png"), "wb") as f:
        f.write(png_180)
    print("Saved apple-touch-icon.png")
    
    # 3. PWA Icons (192, 512)
    png_192 = render_resume_icon(192)
    with open(os.path.join(out_dir, "icon-192.png"), "wb") as f:
        f.write(png_192)
    print("Saved icon-192.png")
    
    png_512 = render_resume_icon(512)
    with open(os.path.join(out_dir, "icon-512.png"), "wb") as f:
        f.write(png_512)
    print("Saved icon-512.png")
    
    # 4. Maskable Icons (192, 512)
    png_mask_192 = render_resume_icon(192, is_maskable=True)
    with open(os.path.join(out_dir, "icon-maskable-192.png"), "wb") as f:
        f.write(png_mask_192)
    print("Saved icon-maskable-192.png")
    
    png_mask_512 = render_resume_icon(512, is_maskable=True)
    with open(os.path.join(out_dir, "icon-maskable-512.png"), "wb") as f:
        f.write(png_mask_512)
    print("Saved icon-maskable-512.png")
    
    print("All resume icons generated successfully!")

if __name__ == "__main__":
    main()
