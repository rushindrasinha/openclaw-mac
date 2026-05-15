# FCPXML 1.11 Structure Reference

## Overview
FCPXML (Final Cut Pro XML) is an interchange format for Final Cut Pro projects. Version 1.11 is supported by FCP 10.6.5+.

## File Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.11">

  <!-- RESOURCES: define formats, assets, effects -->
  <resources>

    <!-- Video format (fps, resolution, color space) -->
    <format id="r1" name="FFVideoFormat1080p25"
            frameDuration="1/25s" width="1920" height="1080"
            colorSpace="1-1-1 (Rec. 709)"/>

    <!-- Audio asset -->
    <asset id="r2" name="voiceover"
           src="file:///path/to/audio.mp3"
           start="0s" duration="125/25s"
           hasAudio="1" audioSources="1" audioChannels="2" audioRate="44100"/>

    <!-- Video asset (if using real clips) -->
    <asset id="r3" name="broll_1"
           src="file:///path/to/clip.mp4"
           start="0s" duration="125/25s"
           hasVideo="1" hasAudio="0"
           videoSources="1"/>

  </resources>

  <!-- LIBRARY: contains events and projects -->
  <library>
    <event name="My Project">
      <project name="My Timeline" uid="UNIQUE-UUID-HERE">

        <!-- SEQUENCE: the actual timeline -->
        <sequence duration="125/25s" format="r1"
                  tcStart="0s" tcFormat="NDF"
                  audioLayout="stereo" audioRate="44100">

          <!-- SPINE: primary story line (video clips stacked in time) -->
          <spine>

            <!-- GAP: empty space or placeholder -->
            <gap name="Clip 1" offset="0s" duration="50/25s" start="0s">

              <!-- Colored generator inside gap -->
              <video name="Color Solid" offset="0s" duration="50/25s" ref="r1">
                <param name="Color" value="0.5 0.2 0.8 1"/>  <!-- RGBA 0-1 -->
              </video>

              <!-- Title/text overlay as connected clip -->
              <title name="Line 1 Text" offset="0s" duration="50/25s" ref="r1">
                <text>
                  <text-style ref="ts1">This is the spoken line</text-style>
                </text>
                <text-style-def id="ts1">
                  <text-style font="Helvetica Neue" fontSize="48"
                              fontFace="Bold" fontColor="1 1 1 1"
                              alignment="center"
                              shadowColor="0 0 0 0.8" shadowOffset="5 315"
                              shadowBlurRadius="5"/>
                </text-style-def>
              </title>

            </gap>

            <!-- Asset clip (real video) -->
            <asset-clip name="broll_1" ref="r3" offset="50/25s"
                        duration="75/25s" start="0s" format="r1"/>

          </spine>

          <!-- AUDIO: connected to spine at lane -1 (below video) -->
          <audio lane="-1" offset="0s" ref="r2"
                 duration="125/25s" role="dialogue"/>

        </sequence>
      </project>
    </event>
  </library>

</fcpxml>
```

## Time Notation
FCPXML uses rational time: `<frames>/<fps>s`

Examples at 25fps:
- 0 seconds → `0s`
- 1 second → `25/25s`
- 2.5 seconds → `62/25s` (62 frames at 25fps = 2.48s ≈ 2.5s)
- 10 seconds → `250/25s`

Formula: `frames = round(seconds * fps)` → `"frames/fps s"`

## Key Elements

| Element | Description |
|---|---|
| `<format>` | Defines timeline fps, resolution, color space |
| `<asset>` | References a media file (video, audio, image) |
| `<sequence>` | The actual editing timeline |
| `<spine>` | Primary story line — clips placed left-to-right in time |
| `<gap>` | Empty/placeholder clip on the spine |
| `<asset-clip>` | Real video/audio clip on the spine |
| `<video>` | Video generator (color, gradient, etc.) as connected clip |
| `<title>` | Text/title generator as connected clip |
| `<audio>` | Audio clip, usually at lane="-1" (below video) |
| `<param>` | Parameter for a generator effect |
| `<text-style-def>` | Reusable text style definition |

## Lane System
- Lane `0` (default) = spine
- Lane `-1` = below spine (audio, B-roll connected)
- Lane `+1`, `+2`, etc. = above spine (text overlays, PiP)

## frameDuration Values
- 23.976fps → `1001/24000s`
- 24fps → `1/24s`
- 25fps → `1/25s`
- 29.97fps → `1001/30000s`
- 30fps → `1/30s`
- 60fps → `1/60s`

## Color Format
Colors in `<param name="Color">` use space-separated RGBA values from 0.0 to 1.0:
- White: `1 1 1 1`
- Black: `0 0 0 1`
- Red: `1 0 0 1`
- Purple: `0.5 0.2 0.8 1`
- Blue: `0.2 0.4 0.9 1`

## Importing into Final Cut Pro
1. File → Import → XML...
2. Select the .fcpxml file
3. FCP creates a new event with the project

Or via Terminal:
```bash
osascript -e 'tell application "Final Cut Pro" to open POSIX file "/path/to/timeline.fcpxml"'
```

## Validation
Check your FCPXML against Apple's DTD:
```bash
xmllint --dtdvalid /System/Library/DTDs/fcpxml.dtd timeline.fcpxml
```
Note: DTD location varies by FCP version. The generate_fcpxml.py script targets FCP 10.6+ (FCPXML 1.11).
