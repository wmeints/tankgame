"""Game scenes and the `Scene` base class they all share."""


class Scene:
    """Base class for a screen the game loop drives.

    `Game` calls `handle_event`, `update` and `draw` on the current scene
    every frame. Subclasses override the ones they need; the defaults do
    nothing.
    """

    def __init__(self, game):
        self.game = game

    @property
    def profile(self):
        """The player's persistent profile dict."""
        return self.game.profile

    def handle_event(self, event, /):
        """React to one pygame input event.

        Parameters
        ----------
        event : pygame.event.Event
            An event the game loop didn't handle itself (quit and the
            fullscreen toggle are handled before the scene sees them).
        """

    def update(self, dt):
        """Advance the scene by one fixed timestep of `dt` seconds."""

    def draw(self, surf):
        """Draw the whole scene onto the screen surface `surf`."""
