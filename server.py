from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from functools import partial
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.uix.recycleview import RecycleView
from kivy.uix.gridlayout import GridLayout
from kivy.config import Config
Config.set('kivy', 'exit_on_escape', '0')
from kivy.uix.popup import Popup
from kivy.core.window import Window
from plyer import filechooser
from pdf2image import convert_from_path
import ntpath
import os
from PIL import Image
import tempfile
from PyPDF2 import PdfFileWriter, PdfFileReader, PdfFileMerger
import fitz
import numpy as np
import cv2
import sys

class ExitApp(App):
    # def build(self):
    #     Window.bind(on_request_close=self.exit_confirmation)

    def exit_confirmation(self):
        # popup can only have one Widget.  This can be fixed by adding a BoxLayout
        self.box_popup = BoxLayout(orientation = 'horizontal')
        self.box_popup.add_widget(Label(text = "Really exit?"))
        self.box_popup.add_widget(Button(
            text = "Yes",
            on_press = ExitApp.exit,
            size_hint = (0.215, 0.075)))
        self.box_popup.add_widget(
            Button(
                text = "No",
                on_press=lambda *args: self.popup_exit.dismiss(),
                # on_press = self.popup_exit.dismiss,
                size_hint=(0.215, 0.075)
            )
        )
        self.popup_exit = Popup(
            title = "Exit",
            content = self.box_popup,
            size_hint = (0.4, 0.4),
            auto_dismiss = True
        )
        self.popup_exit.open()

    def exit(self):
        App.get_running_app().stop()


class UploadFile:
    def __init__(self, filter_="", type_=[]):
        self.filter_ = filter_
        self.type_ = [f"*.{t}" for t in type_]

    def get(self):
        self.path = filechooser.open_file(
                    title="Pick suitable file(s)", 
                    filters=[(self.filter_, *self.type_)],
                    # Doesn't work in macOS, makes merge PDF part useless.
                    multiple=True
                    # TODO: Make this OS specific
                    # multiple=False
                )
        # print(f"self.path : {self.path}")
        return self.path

def arr2pil(arr):
    if arr.dtype == np.dtype("B") and arr.ndim == 2:
        img = Image.frombytes("L", (arr.shape[1], arr.shape[0]), arr.tostring())
    else:
        img = Image.fromarray(arr)
    return img

def pil2array(im,alpha=0):
    if im.mode=="L":
        a = np.frombuffer(im.tobytes(),'B')
        a.shape = im.size[1],im.size[0]
        return a
    if im.mode=="RGB":
        a = np.frombuffer(im.tobytes(),'B')
        a.shape = im.size[1],im.size[0],3
        return a
    if im.mode=="RGBA":
        a = np.frombuffer(im.tobytes(),'B')
        a.shape = im.size[1],im.size[0],4
        if not alpha: a = a[:,:,:3]
        return a
    return pil2array(im.convert("L"))



class PDF2Image:
    def __init__(self, path_):
        # self.file_path = UploadFile()
        self.path_ = path_
        pass

    def convert(self):
        base_path = ntpath.basename(self.path_)
        # print(f"base_path : {base_path}")
        pages = convert_from_path(self.path_, 500)
        for page_no, page in enumerate(pages):
            try:
                save_path = f"{base_path}_page{page_no+1}.jpeg"
                # print(f"sys.argv : {sys.argv}")
                # print(f"sys.path[0] : {sys.path[0]}")
                # print(f"os.path.dirname(os.path.realpath(sys.argv[0])) : {os.path.dirname(os.path.realpath(sys.argv[0]))}")
                # print(f"os.path.realpath(__file__) : {os.path.realpath(__file__)}")
                # temp_ = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'output')
                # temp_ = os.path.join(__file__, 'output')
                temp_ = os.path.join(sys.path[0], 'output')
                save_path = os.path.join(temp_, save_path)
                # print(f"save_path : {save_path}")
                # print(f"type(page) : {type(page)}")
                page.save(save_path, 'JPEG')
            except Exception as e:
                save_path = f"{base_path}_page{page_no+1}.png"
                # temp_ = os.path.join(os.getcwd(), 'output')
                temp_ = os.path.join(sys.path[0], 'output')
                save_path = os.path.join(temp_, save_path)
                # print(f"save_path : {save_path}")
                doc = fitz.open(self.path_)
                page = doc.loadPage(page_no)
                pix = page.getPixmap()
                pix.writePNG(save_path)
        return

class Image2PDF:
    def __init__(self, img_paths):
        self.img_paths = img_paths
        pass

    def convert(self):
        img_list = []
        for path_ in self.img_paths:
            img = Image.open(path_)
            img_list.append(img)
        # print(f"img_list : {img_list}")
        out_path = ntpath.basename(self.img_paths[0]) + '.pdf'
        temp_ = os.path.join(sys.path[0], 'output')
        out_path = os.path.join(temp_, out_path)
        # print(f"out_path : {out_path}")
        img_list[0].save(
            out_path, 
            "PDF", 
            resolution=100.0,
            save_all=True,
            append_images=img_list
        )
        return

class SplitPDF:
    def __init__(self, pdf_paths):
        self.pdf_paths = pdf_paths

    def split(self):
        # TODO keep provision for a zip file with all the single page pdf files
        for pdf_path in self.pdf_paths:
            inp_pdf_basepath = ntpath.basename(pdf_path)
            with open(pdf_path, "rb") as pdf_file:
                inputpdf = PdfFileReader(pdf_file)
                for page_num in range(inputpdf.numPages):
                    output = PdfFileWriter()
                    output.addPage(inputpdf.getPage(page_num))
                    out_path = inp_pdf_basepath + f'_page{page_num+1}.pdf'
                    temp_ = os.path.join(sys.path[0], 'output')
                    out_path = os.path.join(temp_, out_path)
                    with open(out_path, 'wb') as output_stream:
                        output.write(output_stream)
        return


class MergePDF:
    def __init__(self, pdf_paths):
        self.pdf_paths = pdf_paths
        pass

    def merge(self):
        merger = PdfFileMerger()
        # print(f"self.pdf_paths : {self.pdf_paths}")
        for pdf in self.pdf_paths:
            merger.append(PdfFileReader(pdf))
        first_base_path = ntpath.basename(self.pdf_paths[0])
        out_path = first_base_path[:10] + f'... and {len(self.pdf_paths) - 1} more merged.pdf'
        temp_ = os.path.join(sys.path[0], 'output')
        out_path = os.path.join(temp_, out_path)
        merger.write(out_path)
        merger.close()
        return

class GridLayoutApp(App):
    # to build the application we have to
    # return a widget on the build() function. 
    def __init__(self, **kwargs):
        super(GridLayoutApp, self).__init__(**kwargs)

    def build(self):
        # print(f"dir(self) : {dir(self)}")
        # self.icon = "icon/pneuka.png"
        self.icon = "icon/pneuka.jpg"
        self.title = "pneuka - an arkistarvh project"
        # self.bind(on_request_close=self.on_request_close)
        # print(f"Window : {Window}")
        Window.bind(on_request_close=self.on_request_close)
        return self.main()
    
    def on_request_close(self, *args):
        self.textpopup(
            title="Exit",
            # text="Are you sure you want to exit?"
        )
        return True
    
    def textpopup(self, title="", text=""):
        box = BoxLayout(orientation='vertical')
        label_ = Label(text=text)
        box.add_widget(label_)
        yes_btn = Button(
            text="Yes",
            on_press=ExitApp.exit,
            # size_hint=(1, 0.25),
            # size=(150,90)
            # width=0.5
        )
        box.add_widget(yes_btn)
        no_btn = Button(
            text="No",
            on_press=lambda *args: self.popup_exit.dismiss(),
            # size_hint=(1, 0.25),
            # size=(150,90)
            # width=0.5
        )
        box.add_widget(no_btn)
        self.popup_exit = Popup(
            title=title,
            content=box,
            size_hint=(None, None),
            size=(300, 180)
        )
        self.popup_exit.open()

    def pdf2img(self, instance):
        self.path = UploadFile('PDF files', ['pdf', 'PDF']).get()
        if self.path:
            for path in self.path:
                p2i = PDF2Image(path)
                p2i.convert()
            return True
        return False

    def img2pdf(self, instance):
        self.path = UploadFile('Image files', ['jpeg', 'png']).get()
        if self.path:
            i2p = Image2PDF(self.path)
            i2p.convert()
            return True
        return False

    def splitpdf(self, instance):
        self.path = UploadFile('PDF files', ['pdf', 'PDF']).get()
        if self.path:
            spltpdf = SplitPDF(self.path)
            spltpdf.split()
            return True
        return False

    def mergepdf(self, instance):
        self.path = UploadFile('PDF files', ['pdf', 'PDF']).get()
        if self.path and len(self.path) > 1:
            mrgpdf = MergePDF(self.path)
            mrgpdf.merge()
            return True
        return False

    def main(self):
        # adding GridLayouts in App
        # Defining number of coloumn
        # You can use row as well depends on need
        layout = GridLayout(cols = 2)
        pdf2img_btn = Button(text ='Pdf to Image')
        pdf2img_btn.bind(on_press=self.pdf2img)
        layout.add_widget(pdf2img_btn)
        img2pdf_btn = Button(text ='Image to pdf')
        img2pdf_btn.bind(on_press=self.img2pdf)
        layout.add_widget(img2pdf_btn)
        split_pdf_btn = Button(text ='Split pdf')
        split_pdf_btn.bind(on_press=self.splitpdf)
        layout.add_widget(split_pdf_btn)
        merge_pdf_btn = Button(text ='Merge pdfs')
        merge_pdf_btn.bind(on_press=self.mergepdf)
        layout.add_widget(merge_pdf_btn)
        # returning the layout
        return layout


if __name__ == '__main__':
    # creating object of the App class
    if not os.path.isdir('output'):
        os.mkdir('output')
    # if not os.path.isdir('log'):
    #     os.mkdir('log')
    # old_stdout = sys.stdout
    # temp_ = os.path.join(sys.path[0], 'log')
    # log_file = open(os.path.join(temp_, "log.log"),"w")
    # sys.stdout = log_file
    # sys.stdout = old_stdout


    root = GridLayoutApp()
    root.run()
    # log_file.close()