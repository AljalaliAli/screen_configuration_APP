DataGeneration App v0.0.8 Release Notes

Release Date: October 24, 2024

What’s New

Multi-Machine Support

Threaded Execution: Run multiple machines simultaneously from a single software instance.

Enhanced Scalability: Efficiently handle concurrent processing tasks.

OCR Improvements

Blacklist for OCR: Switched from whitelist to blacklist for more effective character filtering.

Enhanced Error Handling: Improved error handling mechanisms and added detailed comments to the image processing logic.

Image Management

Unrecognized Images: Ability to save unrecognized images in a specific, configurable folder.

Configurable Deletion or Archiving: Option to delete images after extraction or move them to a processed_images folder based on config.ini settings.

Database Enhancements

matched_template_id: Added matched_template_id to the database for better tracking and management.

Database Directory Configuration: Specify the database directory via config.ini for greater flexibility.

Bug Fixes

Template Matching: Fixed an issue that caused the application to crash when matched_template_id = -1.

Configurability Enhancements

Waiting Logic: New parameters in config.ini to control waiting behavior between image processing batches:

waiting_for_next_image: Enable or disable waiting for new images.

waiting_duration: Set the duration (in seconds) to wait before checking for new images.

Key Requirements

Directory Structure:

YourAppDirectory
│
├── DataGeneration.exe
├── ini_files/
    ├── config_ID0002_MID0001.ini
    ├── config_ID0002_MID0002.ini
    ├── ... (up to MID0005)

Configuration Files: Place .ini files in the ini_files folder alongside the executable, following the config_ID####_MID####.ini naming format.

Configuration Highlights

Paths Section:

Set directories for configs, images, Tesseract OCR, and the database.

Parameters Section:

Language settings, character blacklist, processing options, and waiting durations.

Installation Steps

Download v0.08: Get DataGeneration_v008.exe .

Setup Directories: Place the executable and create the ini_files folder with your .ini configurations.

Configure Settings: Update the .ini files with your environment paths and preferences.

Tesseract OCR: Ensure Tesseract is installed and correctly referenced in the configuration.

Known Issues

Configuration Errors: Ensure .ini files follow the recommended naming to avoid parsing issues.

Performance: High thread counts may affect system performance. Test to find the optimal number for your setup.

