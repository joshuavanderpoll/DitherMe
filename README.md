## Build executable

### OSX
```bash
pyinstaller --clean --windowed --name "DitherMe" --icon="assets/icon.icns" --osx-bundle-identifier=nl.joshuavanderpoll.ditherme DitherMe/__main__.py
```

### Windows
```bash
pyinstaller --clean --windowed --onefile --name "DitherMe" --icon="assets/icon.ico" DitherMe/__main__.py
```