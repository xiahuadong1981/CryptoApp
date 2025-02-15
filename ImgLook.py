import io
import os
import logging
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as filedialog
import tkinter.messagebox as tkmessagebox
from libs.CFCrypto import ByteCrypto, StringCrypto
from libs.CFCanvas import CFCanvas
from libs.Util import set_combobox_item
from libs.Util import IMG_EXT_LIST

logging.basicConfig(level=logging.INFO)


# 窗口类
class Window(ttk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, padding=2)
        self.cryptoOptionCombobox = ttk.Combobox(self, state="readonly", values=["解密文件", "不需解密", "解密保名"], width=10)
        self.cryptoOption = tk.StringVar()
        self.cryptoOptionCombobox['textvariable'] = self.cryptoOption
        self.cryptoOptionCombobox.grid(sticky=('w', 'e'), row=0, column=0)
        self.passwordEntry = tk.Entry(self, show="*", width=40)
        self.password = tk.StringVar()
        self.passwordEntry['textvariable'] = self.password
        self.passwordEntry.grid(sticky=('w', 'e'), row=0, column=1)
        self.pageOptionCombobox = ttk.Combobox(self, state="readonly", values=["单页", "双页"], width=10)
        self.pageOption = tk.StringVar()
        self.pageOptionCombobox['textvariable'] = self.pageOption
        self.pageOptionCombobox.grid(sticky=('w', 'e'), row=0, column=2)
        self.orderOptionCombobox = ttk.Combobox(self, state="readonly", values=["左开", "右开"], width=10)
        self.orderOption = tk.StringVar()
        self.orderOptionCombobox['textvariable'] = self.orderOption
        self.orderOptionCombobox.grid(sticky=('w', 'e'), row=0, column=3)
        self.fileFromButton = ttk.Button(self, text="选择文件", width=10)
        self.fileFromButton.grid(sticky=('w', 'e'), row=0, column=4)
        self.fileFromButton['command'] = self.file_from_button_callback
        self.refreshButton = ttk.Button(self, text="重新加载", width=10)
        self.refreshButton.grid(sticky=('w', 'e'), row=0, column=5)
        self.refreshButton['command'] = self.refresh_button_callback
        self.imgCanvas = CFCanvas(500, 500, self)
        self.imgCanvas.grid(sticky=('w', 'e', 'n', 's'), row=1, column=0, columnspan=6)
        self.imgSizeNameLabel = tk.Label(self, text="调整大小", width=10)
        self.imgSizeNameLabel.grid(sticky=('e',), row=2, column=0)
        self.imgSizeScale = ttk.Scale(self, orient="horizontal", from_=1, to=100)
        self.imgSizeScale.grid(sticky=('w', 'e'), row=2, column=1)
        self.imgSizeScale.bind('<ButtonRelease-1>', self.set_img_size)
        self.imgSizeScale.bind('<B1-Motion>', self.set_img_size_info)
        self.imgSizeInfoLabel = tk.Label(self, width=10)
        self.imgSizeInfo = tk.StringVar()
        self.imgSizeInfoLabel['textvariable'] = self.imgSizeInfo
        self.imgSizeInfoLabel.grid(sticky=('w', 'e'), row=2, column=2)
        self.prevImgButton = ttk.Button(self, text="<")
        self.prevImgButton.grid(sticky=('w', 'n', 's'), row=2, column=3)
        self.prevImgButton['command'] = self.prev_img_button_callback
        self.nextImgButton = ttk.Button(self, text=">")
        self.nextImgButton.grid(sticky=('w', 'n', 's'), row=2, column=4)
        self.nextImgButton['command'] = self.next_img_button_callback
        self.rotateImgButton = ttk.Button(self, text="旋转")
        self.rotateImgButton.grid(sticky=('w',), row=2, column=5)
        self.rotateImgButton['command'] = self.rotate_img_button_callback
        self.imgInfoLabel = tk.Label(self, text="图片信息")
        self.imgInfo = tk.StringVar()
        self.imgInfoLabel['textvariable'] = self.imgInfo
        self.imgInfoLabel.grid(sticky=('w',), row=3, column=0, columnspan=2)
        self.jumpPageNumberLabel = tk.Label(self, text="跳转页码:")
        self.jumpPageNumberLabel.grid(sticky=('e',), row=3, column=3)
        self.jumpPageNumberEntry = tk.Entry(self, width=10)
        self.jumpPageNumber = tk.StringVar()
        self.jumpPageNumberEntry['textvariable'] = self.jumpPageNumber
        self.jumpPageNumberEntry.grid(sticky=('w', 'e'), row=3, column=4)
        self.jumpPageNumberButton = ttk.Button(self, text="GO", width=10)
        self.jumpPageNumberButton.grid(sticky=('w', 'e'), row=3, column=5)
        self.jumpPageNumberButton['command'] = self.jump_page_callback

        # 存储图片地址列表，用于前后翻页
        self.img_list = []
        # 保存当前的图片路径
        self.current_img_path = ""
        # 初始化下拉列表，设置默认值
        self.init_default_combobox_item()
        # 设置图片最大的宽度
        self.img_max_width = 1960
        # 设置默认的图片宽度，并设置图片大小滑动条的位置
        self.zoom_width = self.img_max_width * 0.45
        # 图片需要逆时针旋转的角度
        self.rotate_angle = 0
        self.imgSizeScale.set(self.zoom_width * 100 / self.img_max_width)
        self.imgSizeInfo.set(str(self.zoom_width * 100 // self.img_max_width) + "%")
        # 绑定键盘事件
        self.master.bind("<Key>", self.key_event)
        self.jumpPageNumberEntry.bind("<Return>", self.jump_page_callback)
        # 主窗口大小发生变化时，居中图片
        self.master.bind("<Configure>", self.img_center)
        # 绑定鼠标滚轴到图片缩放
        self.master.bind("<MouseWheel>", self.process_wheel)
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        # 保存传入的初始参数，如果传入参数则直接打开图片
        self.kwargs = dict(**kwargs)
        if self.kwargs:
            self.open_img(**self.kwargs)

    # 跳转到指定页码
    def jump_page_callback(self, event=None):
        try:
            page_number = int(self.jumpPageNumber.get())
            if 0 < page_number <= len(self.img_list):
                self.current_img_path = self.img_list[page_number-1]
                self.img_show()
                self.set_img_info()
        except Exception as e:
            logging.error("Jump page number error!")

    # 绑定鼠标滚轴到图片缩放
    def process_wheel(self, event=None):
        img_size_scale = self.imgSizeScale.get()
        if event.delta > 0:
            if img_size_scale * 1.2 <= 100:
                self.imgSizeScale.set(img_size_scale * 1.2)
            else:
                self.imgSizeScale.set(100.0)
        else:
            if img_size_scale * 0.8 >= 5:
                self.imgSizeScale.set(img_size_scale * 0.8)
            else:
                self.imgSizeScale.set(5.0)
        self.set_img_size_info()
        self.set_img_size()

    # 初始化下拉列表，设置默认值
    def init_default_combobox_item(self):
        # 设置默认的选项
        set_combobox_item(self.cryptoOptionCombobox, "不需解密", True)
        # 设置单页显示
        set_combobox_item(self.pageOptionCombobox, "单页", True)
        # 设置双页阅读顺序
        set_combobox_item(self.orderOptionCombobox, "左开", True)

    # 根据图片路径，将当前文件夹内所有图片保存在图片列表，用于前后翻页显示
    def set_img_list(self):
        img_dir_path = self.current_img_path[:self.current_img_path.rindex("/") + 1]
        crypto_option = self.cryptoOption.get()
        if crypto_option == "解密文件":
            self.img_list = []
            # 解密后的图片名称临时列表，用于排序
            decrypt_img_name_list = []
            for img_name in os.listdir(img_dir_path):
                try:
                    decrypt_img_name = StringCrypto(self.password.get()).decrypt(img_name)
                    if os.path.splitext(decrypt_img_name.lower())[1][1:] in IMG_EXT_LIST:
                        decrypt_img_name_list.append(decrypt_img_name)
                except Exception as e:
                    logging.error("Decrypt img name error!")
            # 将解密后的图片名称列表排序，再加密后放入img_list中，用于前后翻页顺序显示
            decrypt_img_name_list.sort()
            for decrypt_img_name in decrypt_img_name_list:
                img_name = StringCrypto(self.password.get()).encrypt(decrypt_img_name)
                self.img_list.append(os.path.join(img_dir_path, img_name))

        elif crypto_option == "解密保名" or crypto_option == "不需解密":
            self.img_list = [os.path.join(img_dir_path, img_name) for img_name in os.listdir(img_dir_path)
                             if os.path.splitext(img_name.lower())[1][1:] in IMG_EXT_LIST]

    # 解密字符串方法
    def decrypt_string(self, str):
        try:
            decrypt_str = StringCrypto(self.password.get()).decrypt(str)
        except Exception as e:
            logging.error("Decrypt img name error!")
            decrypt_str = ""
        return decrypt_str

    # 设置显示图片信息
    def set_img_info(self):
        page_option = self.pageOption.get()
        crypto_option = self.cryptoOption.get()

        if crypto_option == "解密文件":
            img_name = self.decrypt_string(os.path.basename(self.current_img_path))
        else:
            img_name = os.path.basename(self.current_img_path)

        if not self.img_list or self.current_img_path not in self.img_list:
            self.imgInfo.set("")
        elif page_option == "单页":
            img_index = self.img_list.index(self.current_img_path)
            index_str = str(img_index + 1) + "/" + str(len(self.img_list))
            self.imgInfo.set(index_str + " : " + img_name)
        elif page_option == "双页":
            img_index = self.img_list.index(self.current_img_path)
            index_str = str(img_index + 1) + "/" + str(len(self.img_list))
            if img_index < len(self.img_list) - 1:
                img_index_next = img_index + 1
                index_str_next = str(img_index_next + 1) + "/" + str(len(self.img_list))
                if crypto_option == "解密文件":
                    img_name_next = self.decrypt_string(os.path.basename(self.img_list[img_index_next]))
                else:
                    img_name_next = os.path.basename(self.img_list[img_index_next])
                order_option = self.orderOption.get()
                if order_option == "左开":
                    self.imgInfo.set(index_str + ", " + index_str_next + " : " + img_name + " | " + img_name_next)
                else:
                    self.imgInfo.set(index_str_next + ", " + index_str + " : " + img_name_next + " | " + img_name)
            else:
                self.imgInfo.set(index_str + " : " + img_name)

    def key_event(self, event=None):
        # 右方向键下一张图片
        if event.keycode == 39:
            self.next_img_button_callback()
        # 左方向键上一张图片
        elif event.keycode == 37:
            self.prev_img_button_callback()

    # 选择待显示的图片，填充图片路径，设置图片地址列表
    def file_from_button_callback(self, event=None):
        img_path = filedialog.askopenfilename()
        if img_path:
            self.current_img_path = img_path
            self.set_img_list()
            self.img_show()
            self.set_img_info()

    # 传入图片地址，解密选项和密码来打开图片
    def open_img(self, img_path="", password="", crypto_option="不需解密", page_option="单页", order_option="左开"):
        if img_path and os.path.isfile(img_path):
            self.current_img_path = os.path.abspath(img_path).replace("\\", "/")
            self.password.set(str(password))
            if page_option in ["单页", "双页"]:
                self.pageOption.set(page_option)
            if order_option in ["左开", "右开"]:
                self.orderOption.set(order_option)
            if crypto_option in ["解密文件", "不需解密", "解密保名"]:
                self.cryptoOption.set(crypto_option)
            self.set_img_list()
            self.img_show()
            self.set_img_info()

    # 重新加载图片
    def refresh_button_callback(self, event=None):
        self.set_img_list()
        self.img_show()
        self.set_img_info()

    # 设置密码输入栏中的内容显示或者隐藏
    def password_show_button_callback(self, event=None):
        if self.passwordEntry["show"] == "*":
            self.passwordEntry["show"] = ""
        else:
            self.passwordEntry["show"] = "*"

    # 向前翻页显示图片
    def prev_img_button_callback(self, event=None):
        page_option = self.pageOption.get()
        self.rotate_angle = 0
        if not self.img_list:
            return
        elif self.current_img_path not in self.img_list:
            index = len(self.img_list)
        else:
            index = self.img_list.index(self.current_img_path)

        if page_option == "单页":
            if index == 0:
                return
            else:
                self.current_img_path = self.img_list[index - 1]
        elif page_option == "双页":
            if index == 0:
                return
            elif index == 1:
                self.current_img_path = self.img_list[index - 1]
            else:
                self.current_img_path = self.img_list[index - 2]

        self.img_show()
        self.set_img_info()

    # 向后翻页显示图片
    def next_img_button_callback(self, event=None):
        page_option = self.pageOption.get()
        self.rotate_angle = 0
        if not self.img_list:
            return
        elif self.current_img_path not in self.img_list:
            index = -1
        else:
            index = self.img_list.index(self.current_img_path)

        if page_option == "单页":
            if index >= len(self.img_list) - 1:
                return
            else:
                self.current_img_path = self.img_list[index + 1]
        elif page_option == "双页":
            if index >= len(self.img_list) - 2:
                return
            else:
                self.current_img_path = self.img_list[index + 2]

        self.img_show()
        self.set_img_info()

    # 逆时针旋转图片
    def rotate_img_button_callback(self, event=None):
        # 逆时针旋转90度
        self.rotate_angle += 90
        # 超过360度取余
        self.rotate_angle %= 360
        self.img_show()

    def img_center(self, event=None):
        if self.imgCanvas:
            self.imgCanvas.img_center()

    # 拖动图片大小滑动条时，显示图片大小百分比
    def set_img_size_info(self, event=None):
        self.zoom_width = int(self.imgSizeScale.get() * self.img_max_width / 100)
        self.imgSizeInfo.set(str(self.zoom_width * 100 // self.img_max_width) + "%")

    # 设置当前显示的图片的大小，保持横纵比缩放
    def set_img_size(self, event=None):
        self.set_img_size_info()
        self.img_show()

    # 静态图片显示
    def default_img_show(self, img_path):
        self.imgCanvas.default_img_show(img_path, self.rotate_angle, self.zoom_width)

    # 双页静态图片显示
    def default_double_img_show(self, img_path, next_img_path, order_option):
        self.imgCanvas.default_double_img_show(img_path, next_img_path,
                                               order_option, self.rotate_angle, self.zoom_width)

    def default_gif_show(self, img_path):
        self.imgCanvas.default_gif_show(img_path, self.rotate_angle, self.zoom_width)

    # 加密静态图片显示
    def crypto_img_show(self, img_path):
        img_file_like = io.BytesIO(ByteCrypto(self.password.get()).decrypt(img_path))
        self.imgCanvas.default_img_show(img_file_like, self.rotate_angle, self.zoom_width)

    # 双页加密静态图片显示
    def crypto_double_img_show(self, img_path, next_img_path, order_option):
        img_file_like = io.BytesIO(ByteCrypto(self.password.get()).decrypt(img_path))
        next_img_file_like = io.BytesIO(ByteCrypto(self.password.get()).decrypt(next_img_path))
        self.imgCanvas.default_double_img_show(img_file_like, next_img_file_like, order_option,
                                               self.rotate_angle, self.zoom_width)

    # 加密动态图片显示
    def crypto_gif_show(self, img_path):
        img_file_like = io.BytesIO(ByteCrypto(self.password.get()).decrypt(img_path))
        self.imgCanvas.default_gif_show(img_file_like, self.rotate_angle, self.zoom_width)

    def cancel_img(self):
        self.imgCanvas.cancel_img()
        self.imgCanvas = None

    # 根据不同图片类型和解密选项，显示图片
    def img_show(self, event=None):
        page_option = self.pageOption.get()
        self.imgCanvas.cancel_img()
        crypto_option = self.cryptoOption.get()
        # 双页显示的顺序设定
        order_option = self.orderOption.get()
        # 如果路径不存在直接返回
        if not self.current_img_path or not os.path.exists(self.current_img_path):
            return
        img_name = os.path.basename(self.current_img_path)
        if crypto_option == "解密文件":
            try:
                decrypt_img_name = StringCrypto(self.password.get()).decrypt(img_name)
                # 如果图片后缀不支持，则直接返回
                if os.path.splitext(decrypt_img_name.lower())[1][1:] not in IMG_EXT_LIST:
                    tkmessagebox.showerror("错误", "文件格式不支持")
                    return
                if page_option == "单页":
                    if os.path.splitext(decrypt_img_name)[1] == ".gif":
                        self.crypto_gif_show(self.current_img_path)
                    else:
                        self.crypto_img_show(self.current_img_path)
                elif page_option == "双页":
                    index = self.img_list.index(self.current_img_path)
                    # 如果已经到了最后一页，则只显示列表末尾两页
                    if index == len(self.img_list) - 1:
                        next_img_path = self.current_img_path
                        self.current_img_path = self.img_list[index - 1]
                    else:
                        next_img_path = self.img_list[index + 1]
                    self.crypto_double_img_show(self.current_img_path, next_img_path, order_option)
            except ValueError as e:
                logging.error("Decrypt img error!")
                tkmessagebox.showerror("错误", "图片解密失败")

        elif crypto_option == "不需解密":
            try:
                # 如果图片后缀不支持，则直接返回
                if os.path.splitext(img_name.lower())[1][1:] not in IMG_EXT_LIST:
                    tkmessagebox.showerror("错误", "文件格式不支持")
                    return
                if page_option == "单页":
                    if os.path.splitext(self.current_img_path)[1] == ".gif":
                        self.default_gif_show(self.current_img_path)
                    else:
                        self.default_img_show(self.current_img_path)
                elif page_option == "双页":
                    index = self.img_list.index(self.current_img_path)
                    # 如果已经到了最后一页，则只显示列表末尾两页
                    if index == len(self.img_list) - 1:
                        next_img_path = self.current_img_path
                        self.current_img_path = self.img_list[index - 1]
                    else:
                        next_img_path = self.img_list[index + 1]
                    self.default_double_img_show(self.current_img_path, next_img_path, order_option)
            except OSError as e:
                logging.error("Img format error!")
                tkmessagebox.showerror("错误", "图片格式错误")

        elif crypto_option == "解密保名":
            try:
                # 如果图片后缀不支持，则直接返回
                if os.path.splitext(img_name.lower())[1][1:] not in IMG_EXT_LIST:
                    tkmessagebox.showerror("错误", "文件格式不支持")
                    return
                if page_option == "单页":
                    if os.path.splitext(self.current_img_path)[1] == ".gif":
                        self.crypto_gif_show(self.current_img_path)
                    else:
                        self.crypto_img_show(self.current_img_path)
                elif page_option == "双页":
                    index = self.img_list.index(self.current_img_path)
                    # 如果已经到了最后一页，则只显示列表末尾两页
                    if index == len(self.img_list) - 1:
                        next_img_path = self.current_img_path
                        self.current_img_path = self.img_list[index - 1]
                    else:
                        next_img_path = self.img_list[index + 1]
                    self.crypto_double_img_show(self.current_img_path, next_img_path, order_option)
            except ValueError as e:
                logging.error("Decrypt img error!")
                tkmessagebox.showerror("错误", "图片解密失败")


# 通过外部参数直接打开图片窗口
def main_window(img_path="", password="", crypto_option="不需解密", page_option="单页", order_option="左开"):
    app = Window(master=None, img_path=img_path, password=password,
                 crypto_option=crypto_option, page_option=page_option, order_option=order_option)
    app.master.title("图片查看器")
    app.master.minsize(600, 600)
    app.mainloop()


if __name__ == '__main__':
    app = Window()
    # 设置窗口标题:
    app.master.title("图片查看器")
    app.master.minsize(600, 600)
    # 主消息循环:
    app.mainloop()
