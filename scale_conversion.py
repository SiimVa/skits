DEFAULT_MAP_SCALE = 50000
DEFAULT_SKETCH_SCALE = 50000

MAP_SCALE_OPTIONS = [50000, 10000, 5000, 2500, 2000, 1000]
SKETCH_SCALE_OPTIONS = [50000, 10000, 5000, 2500, 2000, 1000]


def format_scale_label(scale):
    if isinstance(scale, int):
        return f"1 : {scale:,}".replace(",", " ")
    return scale


def resolve_scale(selected_scale, custom_scale):
    if selected_scale == "Kohandatud...":
        return int(custom_scale)
    return int(selected_scale)


def convert_mm_to_sketch(measured_mm: float, source_scale: int, target_scale: int) -> float:
    if source_scale <= 0 or target_scale <= 0:
        raise ValueError("Mõõtkavad peavad olema positiivsed.")
    return measured_mm * source_scale / target_scale
