MATCHSTICKS_SVG_PATH = "assets/matchstick.svg"

def display_matchsticks_img(n=5, height=140):
    """
    Return HTML for a row of matchstick images.
    """
    html = "<div style='display: flex; align-items: center;'>"
    
    for i in range(n):
        # every 5 matchsticks, add a small gap
        gap = height/7 if (i + 1) > 0 and (i + 1) % 5 == 0 else 0
        html += f"""
        <img src="{MATCHSTICKS_SVG_PATH}"
            style="
                height: {height}px;
                margin-right: {gap}px;
            ">
        """
    
    html += "</div>"
    
    return html

def load_svg(path):
    """
    Load an SVG file from disk and return its contents.
    """
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def display_matchsticks(n=5, height=80):
    """
    Return HTML for a row of inline SVG matchsticks.
    """
    match_svg_inline = load_svg(MATCHSTICKS_SVG_PATH)
    
    html = "<div style='display: flex; align-items: center;'>"

    for i in range(n):
        gap = height / 7 if (i + 1) % 5 == 0 else 0

        html += f"""
        <div style="
            height: {height}px;
            margin-right: {gap}px;
        ">
            {match_svg_inline}
        </div>
        """

    html += "</div>"
    return html
