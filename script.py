import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
import textwrap
import datetime

# 目标网址
url = "https://www.huangli.com/huangli/"
url2 = "https://wannianrili.bmcx.com/"

# 发送 HTTP 请求
response = requests.get(url)
response.encoding = "utf-8"  # 设置编码为 UTF-8

# 检查请求是否成功
if response.status_code == 200:
    # 解析 HTML
    soup = BeautifulSoup(response.text, "html.parser")

    # 查找 <li> 标签
    today_text = None
    # 提取公历日期
    solar_date = soup.find("div", class_="lunar-top").h3.text.strip()

    # 提取今日幸运生肖和星座
    lucky_info = soup.find("div", class_="lunar-top").find_all("span")
    lucky_zodiac = lucky_info[0].text.strip()
    lucky_zodiac = lucky_zodiac.replace("今日幸运生肖：", "")
    lucky_constellation = lucky_info[1].text.strip()
    lucky_constellation = lucky_constellation.replace("今日星座：", "")

    # 提取宜和忌事项
    yi_items = (
        soup.find("div", class_="yi").find("div", class_="day-yi").find_all("span")
    )
    yi_list = " ".join([item.text for item in yi_items])

    ji_section = soup.find_all("div", class_="yi")[1]
    ji_items = ji_section.find("div", class_="day-yi").find_all("span")
    ji_list = " ".join([item.text for item in ji_items])

    # 提取农历月份和日期
    lunar_month = soup.find("h2", class_="lunar-month").text.strip()
    lunar_day = soup.find("h2", class_="lunar-day").text.strip()

    response2 = requests.get(url2)
    response2.encoding = "utf-8"
    soup2 = BeautifulSoup(response2.text, "html.parser")
    divs = soup2.find_all("div", class_="wnrl_k_you")

    for div in divs:
        style = div.get("style", "")
        if "display: block" in style:
            span = div.find("span", class_="wnrl_k_you_id_wnrl_jieri_neirong")
            if span:
                today_text = span.a.text
            break



    # 打印结果
    print(f"公历日期：{solar_date}")
    print(f"今日幸运生肖：{lucky_zodiac}")
    print(f"今日星座：{lucky_constellation}")
    print(f"宜事项：{yi_list}")
    print(f"忌事项：{ji_list}")
    print(f"农历月份：{lunar_month}")
    print(f"农历日期：{lunar_day}")
    print(f"今日：{today_text}")
else:
    print(f"请求失败，状态码：{response.status_code}")
    exit()

# 创建图片对象
width, height = 400, 300  # 调整图片尺寸
image = Image.new("RGB", (width, height), (255, 255, 255))  # 背景为白色
draw = ImageDraw.Draw(image)

def wrap_text_cn(text, font, max_width):
    """
    手动将中文文本按像素宽度换行，确保不超过最大宽度。

    :param text: 待换行的文本
    :param font: PIL ImageFont 对象，用于测量字体宽度
    :param max_width: 最大允许的像素宽度
    :return: 换行后的文本列表
    """
    wrapped_lines = []
    line = ""  # 当前行文本
    for char in text:
        # 测量当前行加上字符的宽度
        line_width = font.getlength(line + char)
        if line_width <= max_width:
            line += char  # 字符可以放入当前行
        else:
            wrapped_lines.append(line.strip())  # 当前行已满，保存
            line = char  # 新行以当前字符开始
    if line:  # 添加最后一行
        wrapped_lines.append(line.strip())
    return wrapped_lines

font_super_height = 40
font_large_height = 20
font_medium_height = 16
font_small_height = 14
font_art_height = 20
# 尝试加载字体
try:
    # 请替换为你的字体路径
    font_path = "./font/hu.ttf"
    font_large = ImageFont.truetype(font_path, font_large_height)  # 调整字体大小
    font_medium = ImageFont.truetype(font_path, font_medium_height)
    font_small = ImageFont.truetype(font_path, font_small_height)
    font_super = ImageFont.truetype(font_path, font_super_height)
except IOError:
    print("字体文件未找到，使用默认字体")
    font_super = ImageFont.load_default()
    font_large = ImageFont.load_default()
    font_medium = ImageFont.load_default()
    font_small = ImageFont.load_default()

try:
    art_font = "./font/maobi.ttf"
    font_art = ImageFont.truetype(art_font, font_art_height)
except IOError:
    font_art = ImageFont.load_default()

# 定义颜色
header_bg_color = (255, 0, 0)  # 顶部背景颜色
text_color = (0, 0, 0)  # 黑色字体
yi_color = (255, 255, 255)  # 宜文字颜色（白色）
ji_color = (255, 255, 255)  # 忌文字颜色（白色）
yi_bg_color = (255, 0, 0)  # 宜背景颜色（红色）
ji_bg_color = (0, 0, 0)  # 忌背景颜色（绿色）

# 绘制顶部背景矩形
draw.rectangle([0, 0, width, 50], fill=header_bg_color)

solar_date = solar_date.replace("(阳历)", "").strip()
solar_date_width = font_medium.getlength(solar_date)
# 绘制顶部文字
draw.text(
    ((width - solar_date_width) // 2, 5),
    solar_date,
    fill=(255, 255, 255),
    font=font_medium,
)

lucky_zodiac = "今日幸运生肖：" + lucky_zodiac
draw.text(
    (30, 30),
    lucky_zodiac,
    fill=(255, 255, 255),
    font=font_small,
)
lucky_constellation = "今日星座：" + lucky_constellation
lucky_constellation_width = font_small.getlength(lucky_constellation)
draw.text(
    (width - lucky_constellation_width - 30, 30),
    lucky_constellation,
    fill=(255, 255, 255),
    font=font_small,
)

# 绘制农历日期
lunar_month_width = font_super.getlength(lunar_month)
lunar_day_width = font_super.getlength(lunar_day)
draw.text(((width - lunar_month_width) / 2, 75), lunar_month, fill=text_color, font=font_super)
draw.text(((width - lunar_day_width) / 2, 75 + font_super_height), lunar_day, fill=text_color, font=font_super)
if today_text:
    today_text_width = font_medium.getlength(today_text)
    draw.text(((width - today_text_width) / 2, 75 + 2 * font_super_height + 10), today_text, fill=header_bg_color, font=font_medium)

# 绘制宜框
circle_yi_x = 75
circle_yi_y = 90
draw.circle((circle_yi_x, circle_yi_y), font_large_height // 2 + 15, fill=yi_bg_color)  # 宜圆形背景
yi_width = font_large.getlength("宜")
draw.text((circle_yi_x - yi_width // 2, circle_yi_y - font_large_height // 2), "宜", fill=yi_color, font=font_large)

yi_list = wrap_text_cn(yi_list, font_small, 100)

draw.text(
    (circle_yi_x - 50, circle_yi_y + font_large_height // 2 + 15 + 10),
    "\n".join(yi_list),
    fill=text_color,
    font=font_small,
    align="left",
)

# 绘制忌框
circle_ji_x = 325
circle_ji_y = circle_yi_y
draw.circle((circle_ji_x, circle_ji_y), font_large_height // 2 + 15, fill=ji_bg_color)  # 忌圆形背景
ji_width = font_large.getlength("忌")
draw.text((circle_ji_x - ji_width // 2, circle_ji_y - font_large_height // 2), "忌", fill=ji_color, font=font_large)

ji_list = wrap_text_cn(ji_list, font_small, 100)

draw.text(
    (circle_ji_x - 50, circle_ji_y + font_large_height // 2 + 15 + 10), "\n".join(ji_list), fill=text_color, font=font_small, align="left"
)

# 判断今天是否是周六周日
today = datetime.datetime.now()
if today.weekday() == 5 or today.weekday() == 6:
    # 绘制周末提示
    img = Image.open("./assets/weekend.bmp")
    # 二值化
    img = img.convert("1")
    image.paste(img, (50, 200))
    draw.text((50 + img.width + 40, 220), "是谁在加班？\n温暖了寂寞！", fill=text_color, font=font_art)
else:
    resp = requests.get("https://v1.hitokoto.cn/?c=l&c=j&encode=text")
    if resp.status_code == 200:
        hitokoto = resp.text
        hitokoto = hitokoto.strip()
        hitokoto = wrap_text_cn(hitokoto, font_art, 320)
        if len(hitokoto) > 1:
            draw.text((40, 200), "\n".join(hitokoto), fill=text_color, font=font_art)
        else:
            hitokoto_width = font_art.getlength(hitokoto[0])
            draw.text(((width - hitokoto_width) / 2, 250), hitokoto[0], fill=text_color, font=font_art)


# 保存图片
image.save("calendar_400x300.bmp")
print("图片已生成：calendar_400x300.bmp")

# 定义颜色映射表
COLOR_MAP = {
    (255, 255, 255): 0b00,  # 白色
    (0, 0, 0): 0b01,        # 黑色
    (255, 0, 0): 0b10       # 红色
}

def bmp_to_compressed_binary(image_path, output_path, threshold=128):
    """
    压缩 BMP 图片为 C 语言头文件，并对非标准颜色进行二值化。

    参数：
        image_path: 输入 BMP 图片路径
        header_file_name: 输出 C 头文件路径
        output_c_name: 生成的数组名称
        threshold: 二值化灰度阈值（默认 128）
    """
    # 打开图片
    img = Image.open(image_path)

    # 确保是 RGB 格式
    img = img.convert("RGB")

    # 获取图片的宽和高
    width, height = img.size

    pixels = img.load()

    # 检查并处理非标准颜色
    for y in range(height):
        for x in range(width):
            color = pixels[x, y]
            if color not in COLOR_MAP:
                # 将非标准颜色二值化处理（灰度阈值判断）
                gray = int(0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2])  # 转灰度
                if gray >= threshold:
                    pixels[x, y] = (255, 255, 255)  # 白色
                else:
                    pixels[x, y] = (0, 0, 0)  # 黑色

    # 压缩像素数据
    compressed_data = []
    current_byte = 0
    bit_position = 0

    for y in range(height):
        for x in range(width):
            # 获取当前像素的颜色编码 (2 bits)
            color_bits = COLOR_MAP[pixels[x, y]]

            # 将颜色编码插入到当前字节的正确位置
            current_byte |= (color_bits << (6 - bit_position))  # 每个像素占 2 位

            bit_position += 2
            if bit_position == 8:
                # 当前字节填满 8 位，添加到压缩数据
                compressed_data.append(current_byte)
                current_byte = 0
                bit_position = 0

    # 如果最后一个字节没有填满 8 位，补 0 并添加到压缩数据
    if bit_position > 0:
        compressed_data.append(current_byte)

    # 保存压缩数据到二进制文件
    with open(output_path, "wb") as f:
        f.write(bytes(compressed_data))

    print(f"压缩数据已保存到：{output_path}")

# 压缩图片并保存为二进制文件
bmp_to_compressed_binary("calendar_400x300.bmp", "compressed_image.bin")
