def detect_input(message):
    """
    تشخیص نوع ورودی:
    - text
    - document
    - photo
    """

    if message.content_type == "text":
        return "text"

    if message.content_type == "document":
        return "document"

    if message.content_type == "photo":
        return "photo"

    return "unknown"
