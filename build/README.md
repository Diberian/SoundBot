# 构建资源目录

此目录存放应用打包所需的资源文件。

## 图标文件

已创建：
- ✅ `icon.icns` - macOS 应用图标
- ✅ `icon.png` - 通用图标（也可用于 Windows）

## 如何重新生成图标

### macOS (ICNS)
```bash
mkdir icon.iconset
sips -z 16 16 ../SoundBot.png --out icon.iconset/icon_16x16.png
sips -z 32 32 ../SoundBot.png --out icon.iconset/icon_16x16@2x.png
sips -z 32 32 ../SoundBot.png --out icon.iconset/icon_32x32.png
sips -z 64 64 ../SoundBot.png --out icon.iconset/icon_32x32@2x.png
sips -z 128 128 ../SoundBot.png --out icon.iconset/icon_128x128.png
sips -z 256 256 ../SoundBot.png --out icon.iconset/icon_128x128@2x.png
sips -z 256 256 ../SoundBot.png --out icon.iconset/icon_256x256.png
sips -z 512 512 ../SoundBot.png --out icon.iconset/icon_256x256@2x.png
sips -z 512 512 ../SoundBot.png --out icon.iconset/icon_512x512.png
sips -z 1024 1024 ../SoundBot.png --out icon.iconset/icon_512x512@2x.png
iconutil -c icns icon.iconset -o icon.icns
rm -rf icon.iconset
```

### Windows (ICO)
可以使用在线工具转换 PNG 到 ICO：
- https://convertio.co/png-ico/
- https://cloudconvert.com/png-to-ico

或者使用 Python（需要安装 Pillow）：
```python
from PIL import Image
img = Image.open('SoundBot.png')
img.save('icon.ico', format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
```
