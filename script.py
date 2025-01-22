import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
import datetime
import os

os.chdir("/home/blame/workspace/calendar_generator")

# ------------------------ Configuration ------------------------
URL_HUANGLI = "https://www.huangli.com/huangli/"
URL_WANNIANRILI = "https://wannianrili.bmcx.com/"
FONT_PATH_DEFAULT = "./font/hu.ttf"
FONT_PATH_ART = "./font/maobi.ttf"
ASSETS_WEEKEND = "./assets/weekend.bmp"
OUTPUT_IMAGE = "calendar_400x300.bmp"
OUTPUT_BINARY = "compressed_image.bin"

# 定义颜色映射表（2 位表示一个像素）
COLOR_MAP = {
    (255, 255, 255): 0b00,  # 白色
    (0, 0, 0): 0b01,  # 黑色
    (255, 0, 0): 0b10,  # 红色
}


# ------------------ Data Fetching and Parsing ------------------
def fetch_html_content(url):
    """
    Fetch HTML content from a given URL.
    :param url: URL to fetch content
    :return: BeautifulSoup object if successful, None otherwise
    """
    response = requests.get(url)
    response.encoding = "utf-8"
    if response.status_code == 200:
        return BeautifulSoup(response.text, "html.parser")
    else:
        print(f"请求失败，状态码：{response.status_code}")
        return None


def parse_huangli_data(soup):
    """
    解析黄历网页面内容，获取相关信息（阳历日期、幸运生肖、星座、宜/忌、农历日期等）
    :param soup: BeautifulSoup object from 黄历网
    :return: dict with parsed data
    """
    data = {
        "solar_date": "",
        "lucky_zodiac": "",
        "lucky_constellation": "",
        "yi_list": "",
        "ji_list": "",
        "lunar_month": "",
        "lunar_day": "",
    }

    # 提取公历日期
    data["solar_date"] = soup.find("div", class_="lunar-top").h3.text.strip()

    # 提取今日幸运生肖和星座
    lucky_info = soup.find("div", class_="lunar-top").find_all("span")
    # 生肖
    data["lucky_zodiac"] = lucky_info[0].text.strip()
    data["lucky_zodiac"] = data["lucky_zodiac"].replace("今日幸运生肖：", "")
    # 星座
    data["lucky_constellation"] = lucky_info[1].text.strip()
    data["lucky_constellation"] = data["lucky_constellation"].replace("今日星座：", "")

    # 提取宜事项
    yi_items = (
        soup.find("div", class_="yi").find("div", class_="day-yi").find_all("span")
    )
    data["yi_list"] = " ".join([item.text for item in yi_items])

    # 提取忌事项
    ji_section = soup.find_all("div", class_="yi")[1]
    ji_items = ji_section.find("div", class_="day-yi").find_all("span")
    data["ji_list"] = " ".join([item.text for item in ji_items])

    # 提取农历月份和日期
    data["lunar_month"] = soup.find("h2", class_="lunar-month").text.strip()
    data["lunar_day"] = soup.find("h2", class_="lunar-day").text.strip()

    return data


def parse_wannianrili_data(soup):
    """
    解析万年历页面内容，获取今日文本（例如节日、节气信息等）
    :param soup: BeautifulSoup object from 万年历
    :return: string with today's text if found, otherwise None
    """
    today_text = None
    divs = soup.find_all("div", class_="wnrl_k_you")
    for div in divs:
        style = div.get("style", "")
        if "display: block" in style:
            span = div.find("span", class_="wnrl_k_you_id_wnrl_jieri_neirong")
            if span and span.a:
                today_text = span.a.text
            break
    return today_text


# ----------------------- Image Rendering -----------------------
def wrap_text_cn(text, font, max_width):
    """
    手动将中文文本按像素宽度换行，确保不超过最大宽度。

    :param text: 待换行的文本
    :param font: PIL ImageFont 对象，用于测量字体宽度
    :param max_width: 最大允许的像素宽度
    :return: 换行后的文本列表
    """
    wrapped_lines = []
    line = ""
    for char in text:
        line_width = font.getlength(line + char)
        if line_width <= max_width and char != "\n":
            line += char
        else:
            wrapped_lines.append(line.strip())
            if char != "\n":
                line = char
            else:
                line = ""
    if line:
        wrapped_lines.append(line.strip())
    return wrapped_lines


def load_fonts():
    """
    加载所需字体，若失败则使用默认字体。
    :return: dictionary of ImageFont objects
    """
    fonts = {}
    # 字体大小
    font_super_height = 40
    font_large_height = 20
    font_medium_height = 16
    font_small_height = 14
    font_art_height = 20

    try:
        font_large = ImageFont.truetype(FONT_PATH_DEFAULT, font_large_height)
        font_medium = ImageFont.truetype(FONT_PATH_DEFAULT, font_medium_height)
        font_small = ImageFont.truetype(FONT_PATH_DEFAULT, font_small_height)
        font_super = ImageFont.truetype(FONT_PATH_DEFAULT, font_super_height)
    except IOError:
        print("字体文件未找到，使用默认字体")
        font_super = ImageFont.load_default()
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    try:
        font_art = ImageFont.truetype(FONT_PATH_ART, font_art_height)
    except IOError:
        font_art = ImageFont.load_default()

    fonts["font_super"] = font_super
    fonts["font_large"] = font_large
    fonts["font_medium"] = font_medium
    fonts["font_small"] = font_small
    fonts["font_art"] = font_art
    fonts["font_super_height"] = font_super_height
    fonts["font_large_height"] = font_large_height
    fonts["font_medium_height"] = font_medium_height
    fonts["font_small_height"] = font_small_height
    fonts["font_art_height"] = font_art_height

    return fonts


def create_calendar_image(
    solar_date,
    lucky_zodiac,
    lucky_constellation,
    yi_list,
    ji_list,
    lunar_month,
    lunar_day,
    today_text,
):
    """
    创建并绘制日历图片，返回 PIL.Image 对象。
    """
    # 定义画布大小
    width, height = 400, 300
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    # 加载字体
    fonts = load_fonts()
    font_super = fonts["font_super"]
    font_large = fonts["font_large"]
    font_medium = fonts["font_medium"]
    font_small = fonts["font_small"]
    font_art = fonts["font_art"]
    font_small_height = fonts["font_small_height"]
    font_art_height = fonts["font_art_height"]
    line_spacing = 4

    # 颜色定义
    header_bg_color = (255, 0, 0)  # 顶部背景颜色
    text_color = (0, 0, 0)  # 黑色
    yi_color = (255, 255, 255)  # 宜（白色）
    ji_color = (255, 255, 255)  # 忌（白色）
    yi_bg_color = (255, 0, 0)  # 红色
    ji_bg_color = (0, 0, 0)  # 黑色

    # 绘制顶部背景矩形
    draw.rectangle([0, 0, width, 50], fill=header_bg_color)

    # 去除 "(阳历)" 并绘制
    solar_date = solar_date.replace("(阳历)", "").strip()
    solar_date_width = font_medium.getlength(solar_date)
    draw.text(
        ((width - solar_date_width) // 2, 5),
        solar_date,
        fill=(255, 255, 255),
        font=font_medium,
    )

    # 绘制幸运生肖和星座
    l_zodiac = "今日幸运生肖：" + lucky_zodiac
    draw.text((30, 30), l_zodiac, fill=(255, 255, 255), font=font_small)
    l_constellation = "今日星座：" + lucky_constellation
    lucky_constellation_width = font_small.getlength(l_constellation)
    draw.text(
        (width - lucky_constellation_width - 30, 30),
        l_constellation,
        fill=(255, 255, 255),
        font=font_small,
    )

    # 绘制农历月份和农历日期
    font_super_height = font_super.size  # 取当前 super 字体大小
    lunar_month_width = font_super.getlength(lunar_month)
    lunar_day_width = font_super.getlength(lunar_day)

    draw.text(
        ((width - lunar_month_width) / 2, 75),
        lunar_month,
        fill=text_color,
        font=font_super,
    )
    draw.text(
        ((width - lunar_day_width) / 2, 75 + font_super_height),
        lunar_day,
        fill=text_color,
        font=font_super,
    )

    bottom_of_lunar = 75 + 2 * font_super_height

    # 如果有 today_text 信息（如节日）
    if today_text:
        today_text_width = font_medium.getlength(today_text)
        draw.text(
            ((width - today_text_width) / 2, 75 + 2 * font_super_height + 10),
            today_text,
            fill=header_bg_color,
            font=font_medium,
        )
        bottom_of_lunar += font_medium.size + 10

    # 绘制“宜”圆形及其文本
    circle_yi_x, circle_yi_y = 75, 90
    draw.circle((circle_yi_x, circle_yi_y), font_large.size // 2 + 15, fill=yi_bg_color)
    yi_width = font_large.getlength("宜")
    draw.text(
        (circle_yi_x - yi_width // 2, circle_yi_y - font_large.size // 2),
        "宜",
        fill=yi_color,
        font=font_large,
    )

    # 分行绘制宜事项
    wrapped_yi_list = wrap_text_cn(yi_list, font_small, 100)
    start_y = circle_yi_y + font_large.size // 2 + 15 + 10
    draw.text(
        (circle_yi_x - 50, start_y),
        "\n".join(wrapped_yi_list),
        fill=text_color,
        font=font_small,
    )
    height_yi = (
        start_y
        + font_small_height * len(wrapped_yi_list)
        + line_spacing * (len(wrapped_yi_list) - 1)
    )

    # 绘制“忌”圆形及其文本
    circle_ji_x = 325
    circle_ji_y = circle_yi_y
    draw.circle((circle_ji_x, circle_ji_y), font_large.size // 2 + 15, fill=ji_bg_color)
    ji_width = font_large.getlength("忌")
    draw.text(
        (circle_ji_x - ji_width // 2, circle_ji_y - font_large.size // 2),
        "忌",
        fill=ji_color,
        font=font_large,
    )

    # 分行绘制忌事项
    wrapped_ji_list = wrap_text_cn(ji_list, font_small, 100)
    draw.text(
        (circle_ji_x - 50, start_y),
        "\n".join(wrapped_ji_list),
        fill=text_color,
        font=font_small,
    )
    height_ji = (
        start_y
        + font_small_height * len(wrapped_ji_list)
        + line_spacing * (len(wrapped_ji_list) - 1)
    )
    last_height = max(height_yi, height_ji, bottom_of_lunar)

    # 判断是否是周末
    today = datetime.datetime.now()
    box_y_start = last_height + font_small_height
    if today.weekday() in [5, 6]:
        # 周末
        try:
            img_weekend = Image.open(ASSETS_WEEKEND)
            img_weekend = img_weekend.convert("1")
            image.paste(img_weekend, (50, box_y_start + font_small_height // 2))
            draw.text(
                (
                    50 + img_weekend.width + 40,
                    box_y_start
                    + font_small_height // 2
                    + img_weekend.height // 2
                    - font_art_height,
                ),
                "是谁在加班？\n温暖了寂寞！",
                fill=text_color,
                font=font_art,
            )
        except IOError:
            print("周末提示图片不存在或无法打开。")
    else:
        # 非周末，去 hitokoto 接口
        resp = requests.get("https://v1.hitokoto.cn/?encode=text")
        if resp.status_code == 200:
            hitokoto = resp.text.strip()
            lines = wrap_text_cn(hitokoto, font_art, 320)
            if len(lines) > 1:
                y_position = ((height - 5) + box_y_start) // 2 - (
                    # fontsize the spacing between lines: 4
                    font_art_height * len(lines)
                    + line_spacing * (len(lines) - 1)
                ) // 2
                draw.text(
                    (40, y_position),
                    "\n".join(lines),
                    fill=text_color,
                    font=font_art,
                )
            else:
                text_width = font_art.getlength(lines[0])
                draw.text(
                    (
                        (width - text_width) / 2,
                        ((height - 5) + box_y_start) // 2 - font_art_height // 2,
                    ),
                    lines[0],
                    fill=text_color,
                    font=font_art,
                )
    # draw a double rectangle box
    draw.rounded_rectangle(
        [5, box_y_start, width - 5, height - 5],
        radius=10,
        outline=(255, 0, 0),
        width=3,
    )
    draw.rounded_rectangle(
        [10, box_y_start + 5, width - 10, height - 10],
        radius=10,
        outline=(255, 0, 0),
    )

    draw.rectangle([0, 0, width, height], outline=(255, 0, 0), width=3)

    return image


# -------------------- Image Compression ------------------------
def bmp_to_compressed_binary(image_path, output_path, threshold=128):
    """
    压缩 BMP 图片为二进制文件，并对非标准颜色进行二值化。

    :param image_path: 输入 BMP 图片路径
    :param output_path: 输出的二进制文件路径
    :param threshold: 二值化灰度阈值（默认 128）
    """
    img = Image.open(image_path).convert("RGB")
    width, height = img.size
    pixels = img.load()

    # 将非标准颜色做二值化处理
    for y in range(height):
        for x in range(width):
            color = pixels[x, y]
            if color not in COLOR_MAP:
                gray = int(0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2])
                pixels[x, y] = (255, 255, 255) if gray >= threshold else (0, 0, 0)

    # 开始压缩像素数据
    compressed_data = []
    current_byte = 0
    bit_position = 0

    for y in range(height):
        for x in range(width):
            color_bits = COLOR_MAP[pixels[x, y]]
            # 将颜色编码移到正确的位置，每个像素占 2 位
            current_byte |= color_bits << (6 - bit_position)
            bit_position += 2

            if bit_position == 8:
                compressed_data.append(current_byte)
                current_byte = 0
                bit_position = 0

    # 如果最后一个字节没有填满，补 0
    if bit_position > 0:
        compressed_data.append(current_byte)

    # 保存到二进制文件
    with open(output_path, "wb") as f:
        f.write(bytes(compressed_data))

    print(f"压缩数据已保存到：{output_path}")


# ------------------------ Main Logic ---------------------------
def main():
    # 抓取并解析黄历数据
    soup_huangli = fetch_html_content(URL_HUANGLI)
    if not soup_huangli:
        return
    huangli_data = parse_huangli_data(soup_huangli)

    # 抓取并解析万年历数据
    soup_wannianrili = fetch_html_content(URL_WANNIANRILI)
    if soup_wannianrili:
        today_text = parse_wannianrili_data(soup_wannianrili)
    else:
        today_text = None

    # 打印日志（与原逻辑保持一致）
    print(f"公历日期：{huangli_data['solar_date']}")
    print(f"今日幸运生肖：{huangli_data['lucky_zodiac']}")
    print(f"今日星座：{huangli_data['lucky_constellation']}")
    print(f"宜事项：{huangli_data['yi_list']}")
    print(f"忌事项：{huangli_data['ji_list']}")
    print(f"农历月份：{huangli_data['lunar_month']}")
    print(f"农历日期：{huangli_data['lunar_day']}")
    print(f"今日：{today_text}")

    # 创建图片
    img = create_calendar_image(
        huangli_data["solar_date"],
        huangli_data["lucky_zodiac"],
        huangli_data["lucky_constellation"],
        huangli_data["yi_list"],
        huangli_data["ji_list"],
        huangli_data["lunar_month"],
        huangli_data["lunar_day"],
        today_text,
    )

    # 保存并压缩
    img.save(OUTPUT_IMAGE)
    print(f"图片已生成：{OUTPUT_IMAGE}")
    bmp_to_compressed_binary(OUTPUT_IMAGE, OUTPUT_BINARY)


if __name__ == "__main__":
    main()
