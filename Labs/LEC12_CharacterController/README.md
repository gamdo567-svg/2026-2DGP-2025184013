# Character controller

## Run

From this folder:

```powershell
python -m pip install -r requirements.txt
python main.py
```

## Controls

| Input | Behavior |
| --- | --- |
| Left / Right | Run in the selected direction; wake from SLEEP or cancel AutoRun into Run |
| Space | Jump from Idle/Run; wake from SLEEP into Idle |
| A | Start AutoRun from Idle only |
| Escape | Close the game |

Idle enters SLEEP after five seconds. AutoRun uses the current facing direction,
moves at 500 pixels/second (normal: 250), draws a 200 x 200 sprite (normal: 100 x 100),
and reverses direction at the left and right boundaries without keyboard input.
It ends after five seconds and returns to Idle. Arrows cancel it immediately into
normal Run; releasing the arrow returns to Idle. Space and A are ignored during
AutoRun. Holding A does not restart the timer or automatically restart the mode.

`AutoRun` is a dedicated `transitions.State` subclass in `main.py`. Its activation,
movement, boundary reflection, deadline, rendering, and cleanup belong to that class.
`boy.invincible` is true only in AutoRun. The scene currently has no enemies or damage
system; future damage handling can use this flag.

The complete submission diagram is in [state_diagram.md](state_diagram.md).
The source requirements are in [pre-prd.md](pre-prd.md).

## Verification

```powershell
python -m unittest -v test_controller
```

Eleven headless tests cover activation restrictions, automatic speed, enlargement,
both wall reflections, deadline boundaries and long frames, direction cancellation,
invincibility cleanup, held-key behavior, and the existing sleep/jump controls.
