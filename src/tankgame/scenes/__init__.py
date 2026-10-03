class Scene:
    def __init__(self, game):
        self.game = game

    @property
    def profile(self):
        return self.game.profile

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, surf):
        pass
