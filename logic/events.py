class EventQueue:
    def __init__(self):
        self._queue = []
    
    def emit(self, event_type, **data):
        self._queue.append({"type": event_type, **data})
    
    def flush(self):
        events = self._queue[:]
        self._queue.clear()
        return events