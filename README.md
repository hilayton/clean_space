# Clean space
Explore and clean up your sector of space. 

Hired to work out of the local space station, you'll travel and clean up all the garbage left behind by pesky litter bugs. You get paid out for all the garbage you bring back to the station, and you can use your funds to upgrade your ship, or even buy a different one. 

Watch out for asteroids though, as damaging your ship too much will strand you. The local towing service will bring you back to the station, though you'll have to dump all your cargo and pay a nominal fee for the service. 


## Controls
A: Turn left

D: Turn right

W: Accelerate

R: Reset

ESC: Close game

## Work Outline
### Completed
- Seperate screen and world dimension
- world-coordinate positions for the ship and objects
- Camera that follows the player
- Drawing tied to screen/ camera postions
    - Objects spawn around camera
- Collision logic
- Collectibles stay alive outside camera area temporarily
- World boundries
- Star field
- Station at center of world
- Station drop-off radus

### To-do
- Convert score to cargo storage
- Cargo delivered when in station cargo radius
- Convert delivered cargo into credits
- Create upgrade menu
    - Create ship upgrade values
- Add ship fuel and refueling
- Add ore and salvage sub-classes
- Add minimap

### Stretch Goals
- Add multiple ship classes with different stats
    - Speed, cargo, turning rate


# Old README


## Clean Space
The game will be similar to “Asteroids.” The player will control a spaceship using the W, A, S, and D keys and will be able to fly around the screen. Asteroids and garbage bags will enter from outside the screen and travel across the play area. The player will need to avoid the asteroids while collecting as many garbage bags as possible.

Each garbage bag collected will increase the player’s score. There will be no time limit or traditional win condition. Instead, the objective of the game will be to survive for as long as possible and earn the highest score. As the game continues, the asteroids and garbage bags will move faster and appear more frequently. This will make it harder for the player to avoid collisions while continuing to collect garbage.

The player will begin the game with three lives. If the spaceship collides with an asteroid, the ship will explode and the player will lose one life. An explosion animation, particle effects, and a sound effect will play when this happens. After losing a life, the spaceship will return to the center of the screen so the player can continue. The game will end once all three lives have been spent.

The player’s score and remaining lives will be displayed on the screen throughout the game. Collecting a garbage bag will play a sound and create a small visual effect so the player knows that it was collected successfully. When the player runs out of lives, a game-over screen will appear and display the player’s final score. The game-over screen will also allow the player to restart the game and try to earn a higher score.

### Goals
To be implemented in order, possibly. IDK. I've never made a game or a real program before. 

- [x] Be able to move a ship around the screen 
    - Should have inertial movement
- [x] Basic asteroids and garbage shapes appear and fly in from off screen, from all directions
- [x] Implement collision logic between asteroids and ship
    - Colliding with asteroids will cause ship destruction
    - Colliding with garbage causes garbage to dissapear
- [x] Implement scoring and lives logic
    - Score will probably be in increments of 100
        - May implement alternate trash bags worth more points
    - Limited to three lives per run
        - Game over screen will also be implemented
        - Game over screen will allow player to restart game
- [] Implement SFX and VFX
    - SFX
        - Sound when player collects garbage
        - Sound when player collides with asteroid
        - Possible background music
    - VFX
        - Sparks/ explosion when colliding with asteroid
        - Something for when garbage is collected

### Backlog/ Stretch Goals
1. Player can fire laser to destroy asteroids + SFX/VFX for asteroid destruction
2. Score history/ high score tracking/ scoreboard