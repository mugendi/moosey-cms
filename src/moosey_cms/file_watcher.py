from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback
        self.ts = 0

    def on_any_event(self, event):
        if event.is_directory:
            return

        if event.event_type in ["modified", "created", "deleted"]:
            # Trigger the callback
            self.callback(event.src_path, event.event_type)


def start_watching(path, callback):
    """
    Starts the watcher in a background thread and returns immediately.
    """
    event_handler = FileChangeHandler(callback)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)

    # This spawns a new thread, so it won't block your main code
    observer.start()

    # Return the observer so you can stop it nicely on server shutdown
    return observer
