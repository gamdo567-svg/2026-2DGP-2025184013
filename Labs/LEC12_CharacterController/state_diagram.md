# Character controller state diagram

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Run : LEFT / RIGHT
    Run --> Idle : movement input released
    Idle --> Jump : SPACE
    Run --> Jump : SPACE
    Jump --> Run : land with movement input
    Jump --> Idle : land without movement input
    Idle --> SLEEP : idle for 5 seconds
    SLEEP --> Idle : SPACE
    SLEEP --> Run : LEFT / RIGHT
    Idle --> AutoRun : A
    AutoRun --> Idle : 5 seconds elapsed
    AutoRun --> Run : LEFT / RIGHT (cancel)
    AutoRun : automatic movement at 2x speed
    AutoRun : 2x sprite size and animation speed
    AutoRun : invincible while active
    AutoRun : reverse direction at either wall
```

Wall reflection updates direction inside AutoRun; it does not re-enter the state,
so hitting a wall never resets the five-second deadline. Timeout and cancellation
both remove invincibility and restore the normal drawing size.
