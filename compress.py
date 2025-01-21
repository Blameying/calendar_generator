from PIL import Image

# 定义颜色映射表
COLOR_MAP = {
    (255, 255, 255): 0b00,  # 白色
    (0, 0, 0): 0b01,        # 黑色
    (255, 0, 0): 0b10       # 红色
}

def bmp_to_c_header_binarize(image_path, header_file_name="compressed_image.h", output_c_name="compressed_image", threshold=128):
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

    # 生成 C 语言头文件内容
    header_content = f"#ifndef {output_c_name.upper()}_H\n"
    header_content += f"#define {output_c_name.upper()}_H\n\n"

    # 声明数组和宽高
    header_content += f"const unsigned char {output_c_name}[] = {{\n"
    for i, byte in enumerate(compressed_data):
        if i % 12 == 0:
            header_content += "    "  # 每行最多 12 个字节
        header_content += f"0x{byte:02X}, "
        if (i + 1) % 12 == 0:
            header_content += "\n"
    if len(compressed_data) % 12 != 0:
        header_content += "\n"
    header_content += "};\n\n"
    header_content += f"const int {output_c_name}_width = {width};\n"
    header_content += f"const int {output_c_name}_height = {height};\n\n"
    header_content += "#endif\n"

    # 写入头文件
    with open(header_file_name, "w") as header_file:
        header_file.write(header_content)

    print(f"Header file '{header_file_name}' has been successfully generated.")


# 示例用法
if __name__ == "__main__":
    # 替换为你的 BMP 图片路径
    image_path = "calendar_400x300.bmp"

    try:
        bmp_to_c_header_binarize(image_path, header_file_name="compressed_image.h", output_c_name="my_image", threshold=128)
    except Exception as e:
        print(f"Error: {e}")
