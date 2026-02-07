#!/usr/bin/env python3
"""
Generate PNG icons for Tauri build using pure Pillow.
Creates gradient circle icons that match the SVG design.
"""

import os
import sys
import math

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Installing pillow...")
    os.system(f"{sys.executable} -m pip install pillow")
    from PIL import Image, ImageDraw


def create_gradient_circle(size: int) -> Image.Image:
    """Create a circular icon with gradient background and WiFi symbol."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Create gradient background circle
    center = size // 2
    radius = int(size * 0.47)  # ~94% of half (240/256)
    
    # Draw gradient circle (diagonal gradient from blue to purple)
    for y in range(size):
        for x in range(size):
            dx = x - center
            dy = y - center
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist <= radius:
                # Calculate gradient position (0-1 based on diagonal)
                t = (x + y) / (2 * size)
                
                # Gradient from #3B82F6 (blue) to #8B5CF6 (purple)
                r = int(59 + (139 - 59) * t)
                g = int(130 + (92 - 130) * t)
                b = int(246 + (246 - 246) * t)
                
                # Anti-aliasing at edges
                if dist > radius - 1:
                    alpha = int(255 * (radius - dist + 1))
                else:
                    alpha = 255
                
                img.putpixel((x, y), (r, g, b, alpha))
    
    # Draw WiFi arcs (white)
    stroke_width = max(1, int(size * 0.047))  # ~24/512
    
    # Arc 1 (outermost) - from point (80, 240) spanning 176 width
    arc1_cy = int(size * 0.47)  # y=240/512
    arc1_width = int(size * 0.69)  # 352/512
    arc1_height = int(size * 0.30)  # 152/512
    arc1_left = center - arc1_width // 2
    arc1_top = arc1_cy - arc1_height // 2
    draw.arc(
        [(arc1_left, arc1_top), (arc1_left + arc1_width, arc1_top + arc1_height)],
        start=200, end=340, fill='white', width=stroke_width
    )
    
    # Arc 2 (middle) - smaller arc
    arc2_cy = int(size * 0.56)
    arc2_width = int(size * 0.50)
    arc2_height = int(size * 0.22)
    arc2_left = center - arc2_width // 2
    arc2_top = arc2_cy - arc2_height // 2
    draw.arc(
        [(arc2_left, arc2_top), (arc2_left + arc2_width, arc2_top + arc2_height)],
        start=200, end=340, fill='white', width=stroke_width
    )
    
    # Arc 3 (innermost) - smallest arc
    arc3_cy = int(size * 0.66)
    arc3_width = int(size * 0.31)
    arc3_height = int(size * 0.13)
    arc3_left = center - arc3_width // 2
    arc3_top = arc3_cy - arc3_height // 2
    draw.arc(
        [(arc3_left, arc3_top), (arc3_left + arc3_width, arc3_top + arc3_height)],
        start=200, end=340, fill='white', width=stroke_width
    )
    
    # Center dot
    dot_radius = max(2, int(size * 0.055))
    dot_cy = int(size * 0.74)
    draw.ellipse(
        [(center - dot_radius, dot_cy - dot_radius),
         (center + dot_radius, dot_cy + dot_radius)],
        fill='white'
    )
    
    # Eye overlay (semi-transparent)
    eye_cy = int(size * 0.66)
    eye_rx = int(size * 0.195)
    eye_ry = int(size * 0.117)
    
    # Draw semi-transparent eye ellipse outline
    for angle in range(360):
        rad = math.radians(angle)
        x = int(center + eye_rx * math.cos(rad))
        y = int(eye_cy + eye_ry * math.sin(rad))
        if 0 <= x < size and 0 <= y < size:
            img.putpixel((x, y), (255, 255, 255, 100))
    
    # Eye center dot (semi-transparent)
    eye_dot_r = max(1, int(size * 0.049))
    for dy in range(-eye_dot_r, eye_dot_r + 1):
        for dx in range(-eye_dot_r, eye_dot_r + 1):
            if dx*dx + dy*dy <= eye_dot_r*eye_dot_r:
                px, py = center + dx, eye_cy + dy
                if 0 <= px < size and 0 <= py < size:
                    current = img.getpixel((px, py))
                    # Blend with existing pixel
                    img.putpixel((px, py), (255, 255, 255, min(255, current[3] + 100)))
    
    return img


def create_ico(images: list, output_path: str) -> None:
    """Create ICO file from list of PIL images."""
    # ICO format needs specific sizes
    ico_sizes = [(16, 16), (32, 32), (48, 48), (256, 256)]
    ico_images = []
    
    for target_size in ico_sizes:
        # Find closest size or resize
        best = None
        for img in images:
            if img.size[0] >= target_size[0]:
                if best is None or img.size[0] < best.size[0]:
                    best = img
        
        if best is None:
            best = images[-1]  # Use largest
        
        resized = best.resize(target_size, Image.Resampling.LANCZOS)
        ico_images.append(resized)
    
    # Save as ICO
    ico_images[0].save(
        output_path,
        format='ICO',
        sizes=ico_sizes,
        append_images=ico_images[1:]
    )


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    icons_dir = os.path.join(project_dir, 'src-tauri', 'icons')
    
    os.makedirs(icons_dir, exist_ok=True)
    
    # Required sizes for Tauri
    sizes = {
        '32x32.png': 32,
        '128x128.png': 128,
        '128x128@2x.png': 256,
        'icon.png': 512,
    }
    
    generated_images = []
    
    print("Generating icons...")
    for filename, size in sizes.items():
        output_path = os.path.join(icons_dir, filename)
        img = create_gradient_circle(size)
        img.save(output_path, 'PNG')
        generated_images.append(img)
        print(f"  Created: {filename} ({size}x{size})")
    
    # Generate ICO for Windows
    ico_path = os.path.join(icons_dir, 'icon.ico')
    create_ico(generated_images, ico_path)
    print(f"  Created: icon.ico")
    
    print(f"\n All icons generated successfully!")
    print(f"   Location: {icons_dir}")


if __name__ == '__main__':
    main()
