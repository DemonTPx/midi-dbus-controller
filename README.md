# MIDI D-Bus controller

Small hobby project which connects my Behringer X-Touch One MIDI controller to D-Bus so I can control my media players

## Prerequisites

The following packages are needed on Ubuntu 18.04 / Linux Mint 19

    libjack-dev libgirepository1.0-dev libcairo2-dev

### Features

- Control media players (Spotify, Rhythmbox, Google Chrome) using the previous, next, stop and play buttons
- Show name of the media player and the album track number in the segment display
- Show artist and track title in the LCD screen
- The LED knob scrolls the text on the LCD screen
- The bank left and right buttons switch between different available media players
- The fader controls the volume of the default pulseaudio sink

### Notes

- The Behringer X-Touch One controller must be in MidiRel mode (standard MIDI, LED knob returns relative values)
