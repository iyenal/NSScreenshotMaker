
#Original code Copyright (c) 2018 cheuble (https://github.com/cheuble)
#Modified version iyenal, as IDStudio liability
#All rights reserved to their respective owners.

import os
import io
import hmac
import json
import piexif
import shutil
import appdirs
import rarfile
import zipfile
import tempfile
from sys import exit
from PIL import Image
from AnyQt import QtCore
from hashlib import sha256
from datetime import datetime
#No need UI imports we will command that directly from a dotNet frontend

games_json = {
	"Home Menu (Default)": "57B4628D2267231D57E0FC1078C0596D",
	"Home Menu (Controllers)": "1E95E5926F1CB99A87326D927F27B47E",
	"Home Menu (Profiles)": "CCFA659F4857F96DDA29AFEDB2E166E6",
	"1-2-Switch": "2B1F1288BC05B2D89D8431910DBA2878",
	"Crash Bandicoot N.sane Trilogy": "3D8E1DE4D671F7453AFA0C395B825E90",
	"Kirby Star Allies": "B20FAEC679A3A9320864DC374CFB9713",
	"Mario + Rabbids Kingdom Battle": "9600BAE614E6833B1A261F5FB229CDBA",
	"Mario Kart 8 Deluxe": "16851BE00BC6068871FE49D98876D6C5",
	"Octopath Traveler": "93C1C73A3BAF9123A15B9B24886B634B",
	"Puyo Puyo Tetris": "0585E865DFB68B5298F19360A730EDB3",
	"Snake Pass": "554C97481EFDFC30DCDF01FC5CC877A6",
	"Sonic Mania": "1628E0CE3F839127054B0EE36E28E52A",
	"Splatoon 2": "397A963DA4660090D65D330174AC6B04",
	"Super Mario Odyssey": "8AEDFF741E2D23FBED39474178692DAF",
	"The Legend of Zelda: Breath of the Wild": "F1C11A22FAEE3B82F21B330E1B786A39",
	"Xenoblade Chronicles 2": "659B13F48903294AE2B3FA4F12DA9898",
	"Xenoblade Chronicles 2: Torna - The Golden Country": "4CBEE39065EC88984BABA68A511DDD19"
}

settings_json = {
	"outputfolder": ".",
	"hmackey": "",
	"customgameid": "57B4628D2267231D57E0FC1078C0596D",
	"type": "image",
	"direction": "ltr"
}

#From my testing, piexif's _dump._get_thumbnail() returns an invalid thumbnail for the Switch (it shows a "?"). What we can do though is replace it with this dirty fix.
#There's probably a better way to do it, like using a different library, but eh, it works™ ¯\_(ツ)_/¯
#From StackOverflow (Monkey Patching): https://stackoverflow.com/questions/10429547/how-to-change-a-function-in-existing-3rd-party-library-in-python
piexif._dump._get_thumbnail = lambda jpeg: jpeg #Return it as it is, no need to modify it.

def resizeImage(path, sizeX, sizeY, state, secondFilePath):
	size = (sizeX, sizeY)
	resizedImage  = Image.new("RGB", size, (0, 0, 0))
	image1 = Image.open(path).convert("RGB")
	image1.thumbnail(size)
	width1, height1 = image1.size
	if state != 0 and secondFilePath != "":
		image2 = Image.open(secondFilePath).convert("RGB")
		image2.thumbnail(size)
		width2, height2 = image2.size
		if state == 1:
			resizedImage.paste(image1, (int(sizeX/2-width1), int((sizeY-height1)/2)))
			resizedImage.paste(image2, (int(sizeX/2), int((sizeY-height2)/2)))
		else:
			resizedImage.paste(image2, (int(sizeX/2-width2), int((sizeY-height2)/2)))
			resizedImage.paste(image1, (int(sizeX/2), int((sizeY-height1)/2)))
	else:
		resizedImage.paste(image1, (int((sizeX - width1) / 2), int((sizeY - height1) / 2)))
	return resizedImage

def createJPEGExif(exifDict, makerNote, timestamp, thumbnail):
	newExifDict = exifDict.copy()
	newExifDict.update({
		"Exif": {36864: b"0230", 37121: b"\x01\x02\x03\x00", 40962: 1280, 40963: 720, 40960: b"0100", 40961: 1, 37500: makerNote},
		"0th":  {274: 1, 531: 1, 296: 2, 34665: 164, 282: (72, 1), 283: (72, 1), 306: timestamp, 271: "Nintendo co., ltd"},
		"1st":  {513: 1524, 514: 32253, 259: 6, 296: 2, 282: (72, 1), 283: (72, 1)},
		"thumbnail": thumbnail
		})
	return newExifDict

def getImageHmac(key, input):
	return hmac.new(key, input, sha256).digest()

def processFile(fileName, key, titleID, baseOutputFolder, state = 0, secondFilePath = None):
	date = datetime.now()
	outputFolder = baseOutputFolder + date.strftime("/Nintendo/Album/%Y/%m/%d/")
	ind = 0
	while os.path.isfile(outputFolder + date.strftime("%Y%m%d%H%M%S") + "{:02d}".format(ind) + "-" + titleID + ".jpg"):
		ind += 1
		if ind > 99:
			date = datetime.now()
			outputFolder = date.strftime("SD/Nintendo/Album/%Y/%m/%d/")
			ind = 0
	outputPath = outputFolder + date.strftime("%Y%m%d%H%M%S") + "{:02d}".format(ind) + "-" + titleID + ".jpg"
	os.makedirs(outputFolder, exist_ok=True)
	inputImage  = io.BytesIO()
	outputImage = io.BytesIO()
	thumbnail   = io.BytesIO()
	resizeImage(fileName, 1280, 720, state, secondFilePath).save(inputImage, "JPEG", quality = 80) #The screenshots must have a size of 1280x720
	resizeImage(fileName, 320,  180, state, secondFilePath).save(thumbnail,  "JPEG", quality = 40)  #The thumbnails (at least on my screenshots) have a size of 320x180
	makerNoteZero  = b"\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x10\x00" + bytes.fromhex(titleID)
	timestamp = date.strftime("%Y:%m:%d %H:%M:%S")
	exifData = piexif.dump(createJPEGExif(piexif.load(inputImage.getvalue()), makerNoteZero, timestamp, thumbnail.getvalue()))
	piexif.insert(exifData, inputImage.getvalue(), outputImage)
	makerNote  = b"\x00\x00\x00\x00\x00\x00\x10\x00" + getImageHmac(key, outputImage.getvalue())[:16] + b"\x01\x00\x10\x00" + bytes.fromhex(titleID)
	outputBytes = outputImage.getvalue().replace(makerNoteZero, makerNote)
	with open(outputPath, "wb") as file:
		file.write(outputBytes)

#Python UI is shit tbh let's get rid of that, we will refer directly to the main repo for that tldr

class FirstRun(BaseWidget):
	def __init__(self, *args, **kwargs):
		BaseWidget.__init__(self, "First Run Popup")
		self._firstrunlabel = ControlLabel("Hello! It looks like this is your first time\nrunning the app. Please go to the settings\nand fill the encryption key before using\nthe tool. Then, simply drag and drop your\nfiles in the centre of the app and press\n\"Go!\"")
		self.formset = [("_firstrunlabel"), (" "), (" ")]

class NSScreenshotMakerGUI(BaseWidget):
	def __init__(self, *args, **kwargs):
		global games_json
		super().__init__("NSScreenshotMaker")
		self._tmpinputfolder = tempfile.mkdtemp()
		self._settingsbutton = ControlButton("⚙️")
		self._settingsbutton.value = self.openSettings
		self._runbutton = ControlButton("Go!")
		self._runbutton.value = self.go
		self._combo = ControlCombo(helptext="The game the Switch will think the screenshot is from")
		self.gameslist = games_json
		for k in self.gameslist:
			self._combo.add_item(k, self.gameslist[k])
		self._combo.add_item("Custom", "Custom")
		self._combolabel = ControlLabel("Game ID", helptext="The game the Switch will think the screenshot is from")
		self._imagelist = ControlFilesTree()
		self._imagelist._form.setDragEnabled(True)
		self._imagelist._form.setAcceptDrops(True)
		self._imagelist._form.setDropIndicatorShown(True)
		self._imagelist._form.dropEvent = self.dropEvent
		model = QFileSystemModel(parent=None)
		model.setReadOnly(False)
		self._imagelist._form.setModel(model)
		model.setRootPath(QtCore.QDir.currentPath())
		self._imagelist._form.setRootIndex(model.setRootPath(self._tmpinputfolder))
		self._imagelist._form.setIconSize(QtCore.QSize(32, 32))
		self.formset=[("_combolabel", "_combo", "_settingsbutton"), "_imagelist" , "_runbutton"]
		self._firstrunpanel = ControlDockWidget()
		self._firstrunpanel.hide()
		self._firstrunwin = FirstRun()
		if not os.path.isfile(appdirs.AppDirs("NSScreenshotMaker", "").user_data_dir+"/settings.json"):
			self._firstrunwin.parent = self
			self._firstrunpanel.value = self._firstrunwin
			self._firstrunpanel.show()
			self._firstrunwin.show()
		self._settingspanel = ControlDockWidget()
		self._settingspanel.hide()
		self._settingswin = SettingsWindow()

	def dropEvent(self, event):
		if event.mimeData().hasUrls:
			event.setDropAction(QtCore.Qt.CopyAction)
			event.accept()
			# to get a list of files:
			drop_list = []
			for url in event.mimeData().urls():
				drop_list.append(str(url.toLocalFile()))
			# handle the list here
			for f in drop_list:
				try:
					if not f.endswith(".cbr") and not f.endswith(".cbz") and not f.endswith(".zip") and not f.endswith(".rar"):
						Image.open(f)
					shutil.copy(f, self._tmpinputfolder)
				except:
					pass
		else:
			event.ignore()
	
	def closeEvent(self, event):
		shutil.rmtree(self._tmpinputfolder)

	def openSettings(self):
		self._firstrunwin.close()
		self._firstrunpanel.hide()
		self._settingswin.close()
		self._settingswin.parent = self
		self._settingspanel.value = self._settingswin
		self._settingspanel.show()
		self._settingswin.show()

	def go(self):
		global settings_json
		if len(os.listdir(self._tmpinputfolder)) == 0:
			return
		prevFileName = ""
		totalElements = 0
		state = 0
		if settings_json["type"] == "manga":
			state = 1
		if settings_json["type"] == "comics":
			state = 2
		for fileName in os.listdir(self._tmpinputfolder):
			print("Processing file " + fileName)
			totalElements += 1
			if fileName.endswith(".zip") or fileName.endswith(".cbz"):
				zf = zipfile.ZipFile(self._tmpinputfolder+"/"+fileName)
				for f in zf.infolist():
					with open(self._tmpinputfolder+"/"+f.filename, "wb") as fp:
						fp.write(zf.read(f))
			elif fileName.endswith(".rar") or fileName.endswith(".cbr"):
				rf = rarfile.RarFile(self._tmpinputfolder+"/"+fileName)
				for f in rf.infolist():
					with open(self._tmpinputfolder+"/"+f.filename, "wb") as fp:
						fp.write(rf.read(f))
			else:
				try:
					if state == 0:
						if list(self._combo._items.values())[self._combo.current_index] != "Custom":
							processFile(self._tmpinputfolder + "/" + fileName, bytes.fromhex(settings_json["hmackey"]), list(self._combo._items.values())[self._combo.current_index], settings_json["outputfolder"])
						else:
							processFile(self._tmpinputfolder + "/" + fileName, bytes.fromhex(settings_json["hmackey"]), settings_json["customgameid"], settings_json["outputfolder"])
					elif prevFileName != "":
						if list(self._combo._items.values())[self._combo.current_index] != "Custom":
							processFile(self._tmpinputfolder + "/" + fileName, bytes.fromhex(settings_json["hmackey"]), list(self._combo._items.values())[self._combo.current_index], settings_json["outputfolder"], state, self._tmpinputfolder+"/"+prevFileName)
						else:
							processFile(self._tmpinputfolder + "/" + fileName, bytes.fromhex(settings_json["hmackey"]), settings_json["customgameid"], settings_json["outputfolder"], state, self._tmpinputfolder+"/"+prevFileName)
						prevFileName = ""
						continue
					prevFileName = fileName
				except:
					pass
		if state != 0 and totalElements % 2 != 0:
			if list(self._combo._items.values())[self._combo.current_index] != "Custom":
				processFile(self._tmpinputfolder + "/" + fileName, bytes.fromhex(settings_json["hmackey"]), list(self._combo._items.values())[self._combo.current_index], settings_json["outputfolder"])
			else:
				processFile(self._tmpinputfolder + "/" + fileName, bytes.fromhex(settings_json["hmackey"]), settings_json["customgameid"], settings_json["outputfolder"])


if __name__ == '__main__':
	NSScreenshotMakerPath = appdirs.AppDirs("NSScreenshotMaker", "").user_data_dir
	if not os.path.isdir(NSScreenshotMakerPath):
		os.mkdir(NSScreenshotMakerPath)
	if os.path.isfile(NSScreenshotMakerPath+"/settings.json"):
		settings_json = json.load(open(NSScreenshotMakerPath+"/settings.json", "r"))
	from pyforms import start_app
	start_app(NSScreenshotMakerGUI)
#くコ:彡
