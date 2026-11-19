def deduplicate_flags(flags, get_flag):
    """Keep the first occurrence of each exact flag, preserving input order.

    Returns a tuple: (unique_items, number_of_duplicates_removed).
    """
    unique_items = []
    seen_flags = set()
    duplicates_removed = 0

    for item in flags:
        flag = get_flag(item)
        if flag in seen_flags:
            duplicates_removed += 1
            continue

        seen_flags.add(flag)
        unique_items.append(item)

    return unique_items, duplicates_removed
