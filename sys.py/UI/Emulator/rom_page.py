# -*- coding: utf-8 -*-

import pygame
import os
import sys
import glob
import zipfile

from cStringIO import StringIO
from UI.page import Page
from UI.fonts  import fonts
from UI.util_funcs import FileExists, midRect, CmdClean
from UI.keys_def import CurKeys
from UI.constants import poster_width, poster_height, Width, Height, RUNEVT
from UI.icon_pool import MyIconPool
from rom_so_confirm_page import RomSoConfirmPage
from libs import easing

class Rom():
    _Name = ""
    _Path = ""
    _Selected = False
    _Poster = None
    _Parent = None
    _Border = None
    _X = 0
    _Y = 0

    def __init__(self):
        self._Border = MyIconPool._Icons["roundedrect"]

    # def Draw(self, offset, index):
    #     if self._Border != None and self._Selected == False:
    #        self._Parent._CanvasHWND.blit(self._Border, (160*(offset+index)-(self._Border.get_width()/2), 5))
    #
    #     if self._Poster is not None:
    #        self._Parent._CanvasHWND.blit(self._Poster, (160*(offset+index)-(self._Poster.get_width()/2), (3+self._Border.get_height())/2-self._Poster.get_height()/2+1))

    def Draw(self):
        if self._Border != None and self._Selected == False:
            self._Parent._CanvasHWND.blit(self._Border, (self._X - 18, 5))

        if self._Poster is not None:
            self._Parent._CanvasHWND.blit(self._Poster, (self._X, (3+self._Border.get_height())/2-self._Poster.get_height()/2+1))

class RomPage(Page):
    _FootMsg = ["Nav", "Scan", "Del", "Add Fav", "Run"]
    _RomList = []
    _SelectedIndex = 0
    _FontObj = fonts["varela12"]
    _Emulator = None
    _Parent = None
    _SelectedBorder = None
    _RomSoConfirmDownloadPage = None
    _MaxRomListing = 3

    def __init__(self):
        Page.__init__(self)

        self._CanvasHWND = None
        self._RomList = []
        self._Emulator = {}

    def GeneratePathList(self, path):
        if os.path.isdir(path) == False:
            return False

        files_path = glob.glob(path + "/*")

        ret = []

        for i, v in enumerate(files_path):
            dirmap = {}
            if os.path.isdir(v) and self._Emulator["FILETYPE"] == "dir":  ## like DOSBOX
                gameshell_bat = self._Emulator["EXT"][0]

                stats = os.stat(v)
                if stats.st_gid == self._Parent._FavGID:  ##skip fav roms
                    continue

                if FileExists(v + "/" + gameshell_bat):
                    dirmap["gamedir"] = v.decode("utf8")
                    ret.append(dirmap)
            if os.path.isfile(v) and self._Emulator["FILETYPE"] == "file":
                stats = os.stat(v)
                if stats.st_gid == self._Parent._FavGID:  ##skip fav roms
                    continue

                bname = os.path.basename(v)  ### filter extension
                if len(bname) > 1:
                    pieces = bname.split(".")
                    if len(pieces) > 1:
                        if pieces[len(pieces) - 1].lower() in self._Emulator["EXT"]:
                            dirmap["file"] = v
                            ret.append(dirmap)

        return ret

    def SyncList(self, path):

        lists = self.GeneratePathList(path)

        if lists == False:
            print("listfiles return false")
            return

        for i, v in enumerate(sorted(lists)):
            filename = v["file"]
            rom = Rom()
            rom._Parent = self
            rom._Name = os.path.splitext(os.path.basename(filename))[0]
            rom._Path = filename
            rom._Poster = self.ReadPosterFromZip(filename)
            self._RomList.append(rom)

        if len(self._RomList) > 0:
            self._RomList[0]._X = 160  - (self._RomList[0]._Poster.get_width() / 2)
            self._RomList[1]._X = 160 * 2 - (self._RomList[1]._Poster.get_width() / 2)

        self.Draw()

    def ReadPosterFromZip(self, filepath):
        zip = zipfile.ZipFile(filepath, "r")
        files = [name for name in zip.namelist() if name.endswith('.jpg')]

        return self.CreateImage(zip.read(files[0]), files[0])

    def CreateImage(self, imagedata, imagename):
        data_io = StringIO(imagedata)
        image = pygame.image.load(data_io, imagename)

        if image.get_width() > poster_width or image.get_height() > poster_height:
            image = pygame.transform.scale(image, (poster_width, poster_height))

        return image

    def Init(self):
        self._CanvasHWND = self._Screen._CanvasHWND
        self._SelectedBorder = MyIconPool._Icons["roundedrectselector"]

        rom_so_confirm_page = RomSoConfirmPage()
        rom_so_confirm_page._Screen = self._Screen
        rom_so_confirm_page._Name = "Download Confirm"
        rom_so_confirm_page._Parent = self
        rom_so_confirm_page.Init()

        self._RomSoConfirmDownloadPage = rom_so_confirm_page

        self.SyncList(self._Emulator["ROM"])

    def ScrollRight(self):
        if self._SelectedIndex < len(self._RomList) - 1:
            start = self._SelectedIndex - 1
            end = start

            if self._SelectedIndex == 0:
                start = 0

            if self._SelectedIndex + 1 <= len(self._RomList) - 1:
                end = self._SelectedIndex + 1

            if self._SelectedIndex + 2 <= len(self._RomList) - 1:
                end = self._SelectedIndex + 2

            self._RomList[self._SelectedIndex]._Selected = False
            self._SelectedIndex = self._SelectedIndex + 1
            self._RomList[self._SelectedIndex]._Selected = True

            offset = 0
            index = 0

            for rom_index in range(start, end + 1):
                if rom_index == 0:
                    offset = 1

                self._RomList[rom_index]._X = 160 * (offset + index) - (self._RomList[rom_index]._Poster.get_width() / 2)
                self._RomList[rom_index].EasingLeft()
                index += 1

    def ScrollLeft(self):
        if self._SelectedIndex > 0:
            start = self._SelectedIndex - 1
            end = start

            if self._SelectedIndex + 1 <= len(self._RomList) - 1:
                end = self._SelectedIndex + 1

            if self._SelectedIndex + 2 <= len(self._RomList) - 1:
                end = self._SelectedIndex + 2

            self._RomList[self._SelectedIndex]._Selected = False
            self._SelectedIndex = self._SelectedIndex - 1
            self._RomList[self._SelectedIndex]._Selected = True

            offset = 0
            index = 0

            for rom_index in range(start, end + 1):
                if rom_index == 0:
                    offset = 1

                self._RomList[rom_index]._X = 160 * (offset + index) - (self._RomList[rom_index]._Poster.get_width() / 2)
                self._RomList[rom_index].EasingRight()
                index += 1

    def KeyDown(self, event):
        if event.key == CurKeys["Menu"]:
            self.ReturnToUpLevelPage()
            self._Screen.Draw()
            self._Screen.SwapAndShow()

        if event.key == CurKeys["Enter"]:
            self.Launch()

        if event.key == CurKeys["Right"]:
            if len(self._RomList) == 0 or self._SelectedIndex == len(self._RomList) - 1:
                return

            self._RomList[self._SelectedIndex]._Selected = False
            self._SelectedIndex = self._SelectedIndex + 1
            self._RomList[self._SelectedIndex]._Selected = True
            self._Screen.Draw()
            self._Screen.SwapAndShow()

        if event.key == CurKeys["Left"]:
            if self._SelectedIndex == 0:
                return

            self._RomList[self._SelectedIndex]._Selected = False
            self._SelectedIndex = self._SelectedIndex - 1
            self._RomList[self._SelectedIndex]._Selected = True
            self._Screen.Draw()
            self._Screen.SwapAndShow()

    def Launch(self):
        if len(self._RomList) == 0:
            return

        current_rom = self._RomList[self._SelectedIndex]

        self._Screen._MsgBox.SetText("Launching...")
        self._Screen._MsgBox.Draw()
        self._Screen.SwapAndShow()

        if self._Emulator["FILETYPE"] == "dir":
            path = current_rom._Path + "/" + self._Emulator["EXT"][0]
        else:
            path = current_rom._Path

        print("Run  ", path)

        # check ROM_SO exists
        if FileExists(self._Emulator["ROM_SO"]):
            if self._Emulator["FILETYPE"] == "dir":
                escaped_path = CmdClean(path)
            else:
                escaped_path = CmdClean(path)

            custom_config = ""
            if self._Emulator["RETRO_CONFIG"] != "" and len(self._Emulator["RETRO_CONFIG"]) > 5:
                custom_config = " -c " + self._Emulator["RETRO_CONFIG"]

            cmdpath = " ".join(
                (self._Emulator["LAUNCHER"], self._Emulator["ROM_SO"], custom_config, escaped_path))
            pygame.event.post(pygame.event.Event(RUNEVT, message=cmdpath))
            return
        else:
            self._Screen.PushPage(self._RomSoConfirmDownloadPage)
            self._Screen.Draw()
            self._Screen.SwapAndShow()

        self._Screen.Draw()
        self._Screen.SwapAndShow()

    def ClearCanvas(self):
        self._CanvasHWND.fill(self._Screen._SkinManager.GiveColor("White"))

    def Draw(self):
        self.ClearCanvas()

        if len(self._RomList) > 0:
            #pass
            self._CanvasHWND.blit(self._SelectedBorder, (160 - (self._SelectedBorder.get_width() / 2), 5))
        else:
            return

        start = 0
        end = 0
        index = 0
        offset = 1

        if self._SelectedIndex > 0:
            start = self._SelectedIndex - 1
            offset = 0

        end = self._SelectedIndex + 1

        if end >= len(self._RomList) - 1:
            end = len(self._RomList) - 1

        for i in range(start, end + 1):
            rom = self._RomList[i]
            rom._X = 160*(offset + index) - (rom._Poster.get_width() / 2)
            rom.Draw()

            if self._SelectedIndex == i:
                title = self._FontObj.render(rom._Name, True, pygame.Color(83, 83, 83))
                offset_width = title.get_rect().width
                offset_height = title.get_rect().height
                rom._Selected = True

                self._CanvasHWND.blit(title, (Width/2-offset_width/2, Height-offset_height/2-60))

            index += 1
