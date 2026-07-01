def _sparkline_svg(values, width=80, height=24, color="#3B82F6"):
    """
    純 Python 產生 <svg viewBox="0 0 80 24"><polyline points="..."/></svg>
    支援正常化（min/max 縮放到 height）
    values 只有 0-1 筆時回傳空字串（graceful degradation）
    values 全相同時繪水平線，不死圖
    """
    if not values:
        return ""

    clean_vals = []
    for v in values:
        if v is None:
            continue
        if isinstance(v, (int, float)):
            clean_vals.append(float(v))
        elif isinstance(v, str):
            if "資料缺失" in v or "—" in v:
                continue
            if "無逾期" in v:
                clean_vals.append(0.0)
                continue
            try:
                # 移除非數字和小數點、負號的字元
                cleaned_str = "".join(c for c in v if c.isdigit() or c in ".-")
                if cleaned_str:
                    val = float(cleaned_str)
                    if "%" in v:
                        val /= 100.0
                    clean_vals.append(val)
            except ValueError:
                pass

    if len(clean_vals) < 2:
        return ""

    min_val = min(clean_vals)
    max_val = max(clean_vals)
    n = len(clean_vals)

    padding = 2.0
    points = []

    if abs(max_val - min_val) < 1e-9:
        # values 全相同時繪水平線
        y = height / 2.0
        for i in range(n):
            x = i * (width / (n - 1))
            points.append(f"{x:.1f},{y:.1f}")
    else:
        for i, val in enumerate(clean_vals):
            x = i * (width / (n - 1))
            y = height - padding - ((val - min_val) / (max_val - min_val) * (height - 2 * padding))
            points.append(f"{x:.1f},{y:.1f}")

    points_str = " ".join(points)
    return (
        f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'xmlns="http://www.w3.org/2000/svg" style="display: inline-block; vertical-align: middle;">'
        f'<polyline points="{points_str}" fill="none" stroke="{color}" stroke-width="1.5" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
        f'</svg>'
    )
