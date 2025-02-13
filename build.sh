APP_NAME="DitherMe"
VOLUME_NAME="DitherMe Installer"
DMG_TMP="dist/${APP_NAME}-temp.dmg"
DMG_FINAL="dist/dmg/${APP_NAME}.dmg"
APP_PATH="dist/macos/${APP_NAME}.app"
DMG_VOLUME="/Volumes/${VOLUME_NAME}"

rm -rf dist
rm -rf build

pyinstaller --clean --windowed --name "DitherMe" --icon="assets/icon.icns" --osx-bundle-identifier=nl.joshuavanderpoll.ditherme DitherMe/__main__.py -y
mkdir -p dist/macos
mv dist/DitherMe.app dist/macos/DitherMe.app

mkdir -p dist/dmg
hdiutil create -size 100m -fs HFS+ -volname "$VOLUME_NAME" -o "$DMG_TMP"

hdiutil attach "$DMG_TMP" -nobrowse -mountpoint "$DMG_VOLUME"
cp -R "$APP_PATH" "$DMG_VOLUME/"
ln -s /Applications "$DMG_VOLUME/Applications"

 osascript <<EOF
tell application "Finder"
    tell disk "$VOLUME_NAME"
        open
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set the bounds of container window to {400, 200, 900, 650}
        set view options of container window to {arrange by position}
        delay 1
        set position of item "$APP_NAME.app" of container window to {150, 150}
        set position of item "Applications" of container window to {450, 150}
        close
    end tell
end tell
EOF

hdiutil detach "$DMG_VOLUME"
hdiutil convert "$DMG_TMP" -format UDZO -o "$DMG_FINAL"
rm -f "$DMG_TMP"