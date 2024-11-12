# Release Notes
## update v0.2.5
update the image the pattern detection module  
## update v0.2.4
1. Bug fixed by deleting the parameter and then adding a new parameter. The problem was with the created id for the new parameter
2. Fixed bug where drawing names and positions were not saved when switching modes
Issue: When switching between "Add Parameter" and "Add Screen Feature" modes, the names and positions of drawn rectangles were not being saved. This was due to the drawing mode flags (add_par_but_clicked and add_screen_feature_but_clicked) being reset prematurely in the finish_drawing method.
## Update V0.1.4
1. Added “Hide Boxes” button
2. Bug fixed after resetting the template and then adding the screen feature (without closing and reopening the app) then Defined machine status.
3. Some code debugging
## Update V0.0.4
1. Added parameter suggestion button to suggest possible parameters.
2. It is no longer allowed to add parameters with the same name to the same template.
3. Fixed issue with German characters (ä, ö, ü).

## Bugfix Update V0.4.3
### Fixes:
1. Fix application crash when deleting a screen feature
2. Modify to save the image using the original image extension instead of defaulting to .png.
3. Filter out operands that have any empty fields
4. Ensure that the configuration for the current image is complete before selecting a new image.

## Bugfix Update V0.3.3

### Fixes:

1. **Cancellation Issues:**
   - **Problem:** When cancelling the addition of parameters or screen features, the drawn box remained on the canvas, and the corresponding buttons stayed active.
   - **Solution:** The drawn box is now correctly removed when the operation is cancelled, and the buttons reset to their original color. This ensures that the user interface remains consistent without needing to reload the image.
2. **Rectangle Removal on Cancellation:**
   - **Problem:** Previously, when a user cancelled the action of adding a parameter or screen feature, the drawn rectangle remained on the canvas, and the corresponding button stayed highlighted.
   - **Solution:** The drawn rectangle is now properly removed when the user cancels the action. Additionally, the button's background color resets to its default state, ensuring that the UI remains consistent without requiring a manual reload of the image.
3. **Image Path Cleanup:**
   - **Issue:** Debugging enhancement to delete the image path if all features are removed.
   - **Solution:** Implemented logic to automatically delete the image path when no features remain, ensuring a cleaner state within the application.

## App Update V0.2.3

### Changes:

- **Configuration Update:**
  - Updated the `config.ini` file to improve application settings and performance.

## App Update V0.1.3

### Enhancements:

- **Validation Checks for Machine Status Definition:**
  - Implemented checks to ensure that an image is loaded and a screen feature is added before allowing the user to define machine status.
- **Bug Fix - Reset Template:**
  - Resolved an issue where an error occurred upon submitting machine status after resetting the template and selecting a new image.
- **Enhanced Clear Canvas Functionality:**
  - Updated the "Clear Canvas" feature to reset the entire application state, providing a quick way to restart the app without closing it.