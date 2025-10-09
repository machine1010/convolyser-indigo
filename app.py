import base64
from pathlib import Path
from streamlit.components.v1 import html

def _img_mime(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in [".jpg", ".jpeg"]:
        return "image/jpeg"
    if ext == ".png":
        return "image/png"
    if ext == ".gif":
        return "image/gif"
    return "image/png"

def _b64_image(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def _render_carousel(image_paths, height: int = 260):
    imgs = []
    for p in image_paths:
        pth = Path(p)
        if pth.exists():
            imgs.append(f"data:{_img_mime(pth)};base64,{_b64_image(pth)}")
    if not imgs:
        return

    dots = "".join([f'<div class="dot" data-i="{i}"></div>' for i in range(len(imgs))])
    tags = "".join([f'<img src="{src}" />' for src in imgs])

    html(
        f"""
        <div class="cw">
          <div class="frame" style="height:{height}px">
            {tags}
            <div class="dots">{dots}</div>
          </div>
        </div>
        <script>
          (function(){{
            // Scope strictly to this component instance
            const scope = document.currentScript.previousElementSibling;
            if(!scope) return;
            const imgs = scope.querySelectorAll('.frame img');
            const dots = scope.querySelectorAll('.dot');
            let i = 0, timer = null;

            function show(n){{
              imgs.forEach((im,ix)=> im.style.opacity = (ix===n?1:0));
              dots.forEach((d,ix)=> d.classList.toggle('active', ix===n));
            }}
            function start(){{
              stop();
              timer = setInterval(()=>{{ i = (i+1) % imgs.length; show(i); }}, 2800);
            }}
            function stop(){{
              if(timer) clearInterval(timer), timer = null;
            }}

            show(0);
            start();

            dots.forEach((d,ix)=> d.addEventListener('click', ()=>{{ i = ix; show(i); start(); }}));
            scope.addEventListener('mouseenter', stop);
            scope.addEventListener('mouseleave', start);
          }})();
        </script>
        """,
        height=height + 16,
    )
