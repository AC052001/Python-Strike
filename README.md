# Python Strike
![Python](https://img.shields.io/badge/Python-3.6+-blue?logo=python&logoColor=yellow&style=plastic)
![Pygame](https://img.shields.io/badge/Pygame-2.0+-yellow?logo=pygame&logoColor=yellow&style=plastic)

A top-down first-person shooter (FPS) game built with Python and Pygame. Experience intense combat against waves of enemies with different behaviors and abilities.

## Game Features

- **Dynamic Enemy Types**: Fight against 4 unique enemy types:
  - Normal soldiers
  - Fast scouts
  - Tanky brutes
  - Stealth snipers
- **Power-up System**: Collect health packs, ammo, speed boosts, and damage multipliers
- **Particle Effects**: Stunning visual effects for shooting, explosions, and hits
- **Screen Shake**: Visual feedback for impacts and explosions
- **Wave-based Progression**: Increasing difficulty with each wave
- **Combo System**: Earn bonus points for consecutive kills
- **Sound Effects**: Generated programmatically without external files


### Prerequisites

- Python 3.6+
- Pygame 2.0+

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Game

```bash
python python_strike.py
```

## How to Play

- **Movement**: WASD keys
- **Aiming**: Mouse cursor
- **Shooting**: Left mouse button
- **Reload**: R key
- **Menu**: Press ENTER to start, ESC to quit

### Enemy Types
- **Normal Soldier** (Red): Balanced stats, basic behavior
- **Fast Scout** (Orange): High speed, quick attacks
- **Tank** (Gray): High health, slow but powerful
- **Sniper** (Purple): Long-range attacks, stealthy

### Power-ups
- **Health** (Green): Restore health
- **Ammo** (Yellow): Full ammo refill
- **Speed** (Cyan): Temporary speed boost
- **Damage** (Purple): Temporary damage multiplier

## Project Structure

```
Python-Strike/
├── python_strike.py     # Main game implementation
├── requirements.txt     # Python dependencies
├── README.md            # This file
└── .gitignore           # Git ignore rules
```

## Development

### Code Structure
The game is organized into several key components:
- **Player Class**: Handles player movement, shooting, and stats
- **Enemy Classes**: Multiple enemy types with unique behaviors
- **Bullet System**: Player and enemy bullets with collision detection
- **Power-ups**: Collectible items that enhance player abilities
- **Particle System**: Visual effects for explosions, hits, and muzzle flashes
- **Sound System**: Programmatically generated sound effects
- **UI System**: User interface elements and HUD

### Adding New Features
1. Create new enemy types by extending the Enemy class
2. Add new power-up types by extending the PowerUp class
3. Implement new visual effects in the ParticleSystem
4. Add new sound effects using the generate_sound function


## Game Progression

- **Wave System**: Enemies spawn in waves with increasing difficulty
- **Score System**: Points based on enemy kills with combo multipliers
- **Health System**: Player health decreases with enemy hits
- **Ammo System**: Limited ammunition requiring reloads

## Sound System

All sound effects are generated programmatically:
- Shooting sounds
- Enemy hit sounds
- Explosion sounds
- Player hit sounds
- Reload sounds
- Power-up sounds
- Wave start sounds

## Dependencies

- [Pygame](https://www.pygame.org/) - Game development library


## Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

### Code Style
- Follow PEP 8 guidelines
- Use descriptive variable and function names
- Add docstrings for all functions and classes
- Keep functions focused and small

### Testing
- Write unit tests for new features
- Ensure all existing tests pass
- Test on multiple platforms if possible

## Issues

For bug reports and feature requests, please use the GitHub issue tracker.

## Future Improvements

- Multiplayer support
- More enemy types and power-ups
- Better graphics and animations
- Sound file support
- High score system
- Level progression
- Weapon upgrades

## Testing

The game has been tested on Windows and Linux systems with Python 3.6+ and Pygame 2.0+.

## Contact

For questions or feedback, please open an issue on GitHub.
