

def get_traffic_light(value, ideal, yellow_threshold=15, green_threshold=5):
    """Return a (status, icon) tuple based on deviation from the ideal value.

    Args:
        value: Observed value.
        ideal: Target / ideal value.
        yellow_threshold: Max % deviation still considered Yellow.
        green_threshold: Max % deviation considered Green.

    Returns:
        Tuple of (status_string, emoji_icon).
    """
    deviation = abs(value - ideal) / ideal * 100
    if deviation <= green_threshold:
        return "Green", "✅"
    elif deviation <= yellow_threshold:
        return "Yellow", "⚠️"
    else:
        return "Red", "🚨"
