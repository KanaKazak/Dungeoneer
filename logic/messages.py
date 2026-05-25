def add_message(text, messages):
    """Add a message to the log, keeping only the last 25."""
    messages.append(text)
    if len(messages) > 25:
        messages.pop(0)