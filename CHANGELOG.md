# v1.0.7 (pre-release)
- Ignore chapter markers and single newlines when calculating text length.

# v1.0.6
- Added `Insert chapter marker` button in text editor to insert chapter markers at the current cursor position.
- Added `Preview` button in voice mixer to preview the voice mix with the selected settings.
- Fixed `f-string: unmatched '['` error in Voice preview, mentioned in #14
- Fixed the issue with the content before first chapter not being included in the output.
- Fixed m4b chapter generation opens CMD window in Windows.

# v1.0.5
- Added new output format: `m4b`, enabling chapter metadata in audiobooks. Special thanks to @jborza for implementing this feature in PR #10.
- Better approach for determining the correct configuration folder for Linux and MacOS, using platformdirs. (Fixes Docker issue #12)
- Improvements in documentation and code.

# v1.0.4
- Merge pull request [#7](https://github.com/denizsafak/abogen/pull/7) by @jborza that improves voice preview and documentation.
- Fixed the issue when a voice is selected, the voice mixer tries to pre-select that voice and ignores existing profiles.
- Fixed the error while renaming the default "New profile" in the voice mixer.
- Fixed subtitle_combo enabling/disabling when a voice in the voice mixer is selected.
- Prevented using special characters in the profile name to avoid conflicts.
- Improved invalid profile handling in the voice mixer.

# v1.0.3
- Added voice mixing, allowing multiple voices to be combined into a single “Mixed Voice”, a feature mentioned by @PulsarFTW in #1. Special thanks to @jborza for making this possible through his contributions in #5.
- Added profile system to voice mixer, allowing users to create and manage multiple voice profiles.
- Improvements in the voice mixer, mostly for organizing controls and enhancing user experience.
- Added icons for flags and genders in the GUI, making it easier to identify different options.
- Improved the content and chapter extraction process for EPUB files, ensuring better handling of various structures.
- Switched to platformdirs for determining the correct desktop path, instead of using old methods.
- Fixed preview voices was not using GPU acceleration, which was causing performance issues.
- Improvements in code and documentation.

# v1.0.2
- Enhanced EPUB handling by treating all items in chapter list (including anchors) as chapters, improving navigation and organization for poorly structured books, mentioned by @Darthagnon in #4
- Fixed the issue with some chapters in EPUB files had missing content.
- Fixed the issue with some EPUB files only having one chapter caused the program to ignore the entire book.
- Fixed "utf-8' codec can't decode byte" error, mentioned by @nigelp in #3
- Added "Replace single newlines with spaces" option in the menu. This can be useful for texts that have imaginary line breaks.
- Improvements in code and documentation.

# v1.0.1
- Added abogen-cli command for better troubleshooting and error handling.
- Switched from setuptools to hatchling for packaging.
- Added classifiers to the package metadata.
- Fixed "No module named 'docopt'" and "setuptools.build_meta" import errors while using .bat installer in Windows, mentioned by @nigelp in #2
- Improvements in code and documentation.