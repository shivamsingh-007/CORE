"""Generate an animated workflow GIF showing the loop states in sequence."""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r"C:\Users\shiva\AppData\Local\Programs\Python\Python311\Lib\site-packages")

from pathlib import Path
from PIL import Image

ASSETS = Path(__file__).parent

# The 10 workflow states (0=DISCOVERY through 9=READY)
STATES = [
    "DISCOVERY", "PLANNING", "SCAFFOLDING", "INITIALIZING", "IMPLEMENTING",
    "SELF_CHECK", "VERIFYING", "BUG_HUNT", "REWORK", "READY"
]

# CSS class assignments for each frame:
# past: already processed states
# active: currently processing
# next: next to process
# (READY has special 'done' class, FAILED has 'error' class)
CSS = """
#n%d { border-color: %s !important; box-shadow: %s !important; }
#n%d .s { color: %s !important; }
#n%d .n { color: %s !important; font-size: 13px !important; }
#n%d .a { color: %s !important; }
"""

COLORS = {
    "past":     ("rgba(52,211,153,0.4)",  "0 0 15px rgba(52,211,153,0.1)",   "#34d399", "#6ee7b7"),
    "active":   ("rgba(99,102,241,0.6)",  "0 0 20px rgba(99,102,241,0.15)",  "#818cf8", "#a5b4fc"),
    "next":     ("rgba(251,191,36,0.3)",  "0 0 10px rgba(251,191,36,0.05)",  "#fbbf24", "#fcd34d"),
    "done":     ("rgba(34,197,94,0.4)",   "0 0 20px rgba(34,197,94,0.15)",   "#22c55e", "#86efac"),
}

ARROW_CSS = """
#a%d { color: %s !important; }
"""

def build_css(frame_idx):
    css = []
    for i in range(10):
        if i < frame_idx:
            state = "past"
        elif i == frame_idx:
            state = "active"
        elif i == frame_idx + 1 and i < 10:
            state = "next"
        else:
            continue
        border, shadow, text, sub = COLORS[state]
        css.append(CSS % (i, border, shadow, i, text, i, text, i, sub))
    # Arrow styling
    for i in range(9):  # arrows 0-8
        if i < frame_idx:
            css.append(ARROW_CSS % (i, "#34d399"))
        elif i == frame_idx:
            css.append(ARROW_CSS % (i, "#818cf8"))
        else:
            css.append(ARROW_CSS % (i, "#fbbf24"))
    return "\n".join(css)


def capture_frames():
    from playwright.sync_api import sync_playwright
    frames = []
    frame_dir = ASSETS / "frames"
    frame_dir.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1000, "height": 500})

        for i in range(10):
            html_path = (ASSETS / "frame.html").resolve().as_posix()
            page.goto(f"file:///{html_path}")
            page.wait_for_load_state("networkidle")

            # Inject CSS for this frame
            css = build_css(i)
            page.evaluate(f"const s=document.createElement('style');s.textContent=`{css}`;document.head.appendChild(s)")

            # Small delay for render
            page.wait_for_timeout(100)

            out_path = str(frame_dir / f"frame_{i:02d}.png")
            page.screenshot(path=out_path)
            frames.append(Image.open(out_path))
            print(f"  Frame {i}: {STATES[i]}")

        browser.close()

    return frames


def make_gif(frames, out_path, duration=800):
    # Make all frames same size (they should be, but ensure)
    sizes = [f.size for f in frames]
    w = max(s[0] for s in sizes)
    h = max(s[1] for s in sizes)

    rgb_frames = []
    for f in frames:
        if f.mode != "RGB":
            f = f.convert("RGB")
        # Pad if needed
        if f.size != (w, h):
            padded = Image.new("RGB", (w, h), (15, 23, 42))
            padded.paste(f, (0, 0))
            f = padded
        rgb_frames.append(f)

    rgb_frames[0].save(
        out_path,
        save_all=True,
        append_images=rgb_frames[1:],
        duration=duration,
        loop=0,
        optimize=True,
    )
    print(f"\nSaved GIF: {out_path} ({Path(out_path).stat().st_size} bytes)")


if __name__ == "__main__":
    print("Capturing workflow frames...")
    frames = capture_frames()
    print(f"\nCombining {len(frames)} frames into GIF...")
    make_gif(frames, str(ASSETS / "workflow.gif"), duration=800)
    print("Done.")
