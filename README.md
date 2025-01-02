# What the heck
Screenshot in some area - OCR - translate (2 modules in main for example).

For OCR - using paddleocr.
For translate - LibreTranslate on a local server.

# How to install

Install libretranslate
```
pip install libretranslate==1.6.2
```

Update libretranslate
```
libretranslate --update-models
```
Start local libretranslate
```
libretranslate --load-only {yourlang}, ru, en
```
run main script
```
py main.py
```

# Why
Just for me.