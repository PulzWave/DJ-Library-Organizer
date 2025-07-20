# DJ-Library-Organizer

**The Problem:** Every DJ knows the struggle - massive music libraries with thousands of tracks where finding the perfect song feels like searching for a needle in a haystack. Large, unorganized libraries lead to:
- ⏱️ Slow syncing across devices and platforms
- 🔍 Frustrating search experiences during live sets
- 📱 Performance issues with DJ software
- 🎵 Great tracks getting buried and forgotten

**The Solution:** Quality over quantity. This intelligent tool transforms your overwhelming music collection into a carefully curated library that actually enhances your DJ workflow.

## ✨ What Makes This Different

Rather than just organizing files, DJ-Library-Organizer provides a **streamlined workflow** that lets you:
- **Rapidly audit** your entire collection with visual waveform analysis
- **Make instant decisions** using intuitive keyboard shortcuts
- **Maintain consistency** by automatically syncing ratings between MP3 metadata and Engine DJ
- **Stay focused** with a distraction-free, purpose-built interface

The process is still thorough, but every aspect has been optimized for speed and efficiency.

# Hotkeys

## ⌨️ Streamlined Controls for Maximum Efficiency

| Key | Action | Result |
|-----|--------|---------|
| **↑** | **Keep Track** | Preserves the MP3 file, updates rating in both Engine DJ library and MP3 metadata |
| **↓** | **Remove Track** | Safely moves MP3 to recycle bin and removes from Engine DJ database |
| **←→** | **Navigate Waveform** | Scroll through the track to preview different sections |
| **Space** | **Play/Pause** | Toggle playback for detailed listening |
| **1 - 5** | **Change rating** | Quickly change the rating before saving |

*Designed for one-handed operation so you can keep your other hand free for coffee ☕*

# Features

## 🎛️ Core Functionality
- **📁 Recursive Directory Processing** - Automatically discovers all MP3 files in your library structure
- **🌊 Advanced Waveform Visualization** - Visual frequency analysis helps you quickly assess track quality
- **⚡ Lightning-Fast Workflow** - Purpose-built keyboard shortcuts keep you in the flow
- **🎨 Intelligent Genre Management** - Configurable genre selection with smart categorization
- **🔄 Dual-Platform Sync** - Seamlessly updates both MP3 metadata and Engine DJ database
- **📅 Smart Filtering** - Year-based filtering to focus on specific eras or releases

## 🚀 Performance & Experience
- **⚙️ Multi-threaded Processing** - Waveform analysis up-front while you listen to your music, so no slowing down
- **🌙 Dark Theme** - Easy on the eyes during long library sessions
- **📊 Progress Tracking with ETA** - Know exactly how much time your library audit will take
- **🔗 API Integration** - Webhook support for advanced deletion workflows (advanced)
- **💾 Reliable State Management** - Picks up where you left off if interrupted because processed MP3's will have a designated ID tag

# Screenshot

![Screenshot](https://github.com/PulzWave/DJ-Library-Organizer/blob/main/src/image/screenshot_001.png?raw=true)

## How to compile to an executable
To create a standalone executable with all dependencies, run:

    pyinstaller --onefile --windowed --icon src/image/pulzwave_icon.png --add-data "src/image/pulzwave_icon.png;src/image" --noconfirm --name DJ-Library-Organizer main.py

This will generate a single-file executable in the `dist/` directory.