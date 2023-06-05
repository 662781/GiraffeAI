from shared.model import CVGame

class WarmingUpMenu(CVGame):
    def __init__(self):
        super().__init__()

    def setup(self, options):
        return super().setup(options)

    def update(self, frame):
        return super().update(frame)
    
    def cleanup(self):
        return super().cleanup()
