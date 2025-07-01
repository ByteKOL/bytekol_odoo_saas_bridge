def read_lines_backwards(file_path, chunk_size=8192):
    with open(file_path, 'r', encoding='utf-8') as f:
        f.seek(0, 2)  # Move the cursor to the end of the file
        size = f.tell()
        buffer = ''
        while size > 0:
            if size < chunk_size:
                chunk_size = size
            f.seek(size - chunk_size)
            chunk = f.read(chunk_size)
            lines = (chunk + buffer).splitlines(True)
            buffer = lines.pop(0) if lines and not lines[0].endswith('\n') else ''
            for line in reversed(lines):
                yield line
            size -= chunk_size
        if buffer:
            yield buffer


def extract_log_block(log_path, head_log_code, tail_log_code, max_lines=5000):
    lines = []
    found_end = False
    line_count = 0

    # Iterate through lines from the end of the file upwards
    for line in read_lines_backwards(log_path):
        line_count += 1
        if not found_end:
            # Find the end line containing tail_log_code
            if line.strip().endswith(tail_log_code):
                found_end = True
                lines.append(line)
            # If max_lines is exceeded without finding the end line, stop
            elif line_count > max_lines:
                return None
        else:
            # After finding the end line, continue collecting lines until the start line is found
            lines.append(line)
            if line.strip().endswith(head_log_code):
                break
    else:
        # If the start line is not found after iterating through the file
        return None

    # Reverse the list of lines to restore correct order (from start to end)
    lines.reverse()
    # Join the lines into a single string and return
    return ''.join(lines)
