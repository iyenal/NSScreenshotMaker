
using os;
using io;
using hmac;
using json;
using piexif;
using shutil;
using appdirs;
using rarfile;
using zipfile;
using tempfile;
using exit = sys.exit;
using Image = PIL.Image;
using sha256 = hashlib.sha256;
using datetime = datetime.datetime;

//Updated to Systems, let's just do a carry-on for the others

using System;
using System.Collections.Generic;
using System.Collections;
using System.Linq;

public static class nsmp {
    
    public static object games_json = new Dictionary<object, object> {
        {
            "Home Menu (Default)",
            "57B4628D2267231D57E0FC1078C0596D"}};
    
    public static object settings_json = new Dictionary<object, object> {
        {
            "outputfolder",
            "."},
        {
            "hmackey",
            ""},
        {
            "customgameid",
            "57B4628D2267231D57E0FC1078C0596D"},
        {
            "type",
            "image"},
        {
            "direction",
            "ltr"}};
    
    static nsmp() {
        piexif._dump._get_thumbnail = jpeg => jpeg;
    }
    
    public static object resizeImage(
        object path,
        object sizeX,
        object sizeY,
        object state,
        object secondFilePath) {
        var size = Tuple.Create(sizeX, sizeY);
        var resizedImage = Image.@new("RGB", size, Tuple.Create(0, 0, 0));
        var image1 = Image.open(path).convert("RGB");
        image1.thumbnail(size);
        var _tup_1 = image1.size;
        var width1 = _tup_1.Item1;
        var height1 = _tup_1.Item2;
        if (state != 0 && secondFilePath != "") {
            var image2 = Image.open(secondFilePath).convert("RGB");
            image2.thumbnail(size);
            var _tup_2 = image2.size;
            var width2 = _tup_2.Item1;
            var height2 = _tup_2.Item2;
            if (state == 1) {
                resizedImage.paste(image1, Tuple.Create(Convert.ToInt32(sizeX / 2 - width1), Convert.ToInt32((sizeY - height1) / 2)));
                resizedImage.paste(image2, Tuple.Create(Convert.ToInt32(sizeX / 2), Convert.ToInt32((sizeY - height2) / 2)));
            } else {
                resizedImage.paste(image2, Tuple.Create(Convert.ToInt32(sizeX / 2 - width2), Convert.ToInt32((sizeY - height2) / 2)));
                resizedImage.paste(image1, Tuple.Create(Convert.ToInt32(sizeX / 2), Convert.ToInt32((sizeY - height1) / 2)));
            }
        } else {
            resizedImage.paste(image1, Tuple.Create(Convert.ToInt32((sizeX - width1) / 2), Convert.ToInt32((sizeY - height1) / 2)));
        }
        return resizedImage;
    }
    
    public static object createJPEGExif(object exifDict, object makerNote, object timestamp, object thumbnail) {
        var newExifDict = exifDict.copy();
        newExifDict.update(new Dictionary<object, object> {
            {
                "Exif",
                new Dictionary<object, object> {
                    {
                        36864,
                        new byte[] { (byte)'0', (byte)'2', (byte)'3', (byte)'0' }},
                    {
                        37121,
                        new byte[] { 0x01, 0x02, 0x03, 0x00 }},
                    {
                        40962,
                        1280},
                    {
                        40963,
                        720},
                    {
                        40960,
                        new byte[] { (byte)'0', (byte)'1', (byte)'0', (byte)'0' }},
                    {
                        40961,
                        1},
                    {
                        37500,
                        makerNote}}},
            {
                "0th",
                new Dictionary<object, object> {
                    {
                        274,
                        1},
                    {
                        531,
                        1},
                    {
                        296,
                        2},
                    {
                        34665,
                        164},
                    {
                        282,
                        Tuple.Create(72, 1)},
                    {
                        283,
                        Tuple.Create(72, 1)},
                    {
                        306,
                        timestamp},
                    {
                        271,
                        "Nintendo co., ltd"}}},
            {
                "1st",
                new Dictionary<object, object> {
                    {
                        513,
                        1524},
                    {
                        514,
                        32253},
                    {
                        259,
                        6},
                    {
                        296,
                        2},
                    {
                        282,
                        Tuple.Create(72, 1)},
                    {
                        283,
                        Tuple.Create(72, 1)}}},
            {
                "thumbnail",
                thumbnail}});
        return newExifDict;
    }
    
    public static object getImageHmac(object key, object input) {
        return hmac.@new(key, input, sha256).digest();
    }
    
    public static object processFile(
        object fileName,
        object key,
        object titleID,
        object baseOutputFolder,
        object state = 0,
        object secondFilePath = null) {
        var date = datetime.now();
        var outputFolder = baseOutputFolder + date.strftime("/Nintendo/Album/%Y/%m/%d/");
        var ind = 0;
        while (os.path.isfile(outputFolder + date.strftime("%Y%m%d%H%M%S") + "{:02d}".format(ind) + "-" + titleID + ".jpg")) {
            ind += 1;
            if (ind > 99) {
                date = datetime.now();
                outputFolder = date.strftime("SD/Nintendo/Album/%Y/%m/%d/");
                ind = 0;
            }
        }
        var outputPath = outputFolder + date.strftime("%Y%m%d%H%M%S") + "{:02d}".format(ind) + "-" + titleID + ".jpg";
        os.makedirs(outputFolder, exist_ok: true);
        var inputImage = io.BytesIO();
        var outputImage = io.BytesIO();
        var thumbnail = io.BytesIO();
        resizeImage(fileName, 1280, 720, state, secondFilePath).save(inputImage, "JPEG", quality: 80);
        resizeImage(fileName, 320, 180, state, secondFilePath).save(thumbnail, "JPEG", quality: 40);
        var makerNoteZero = new byte[] { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x10, 0x00 } + bytes.fromhex(titleID);
        var timestamp = date.strftime("%Y:%m:%d %H:%M:%S");
        var exifData = piexif.dump(createJPEGExif(piexif.load(inputImage.getvalue()), makerNoteZero, timestamp, thumbnail.getvalue()));
        piexif.insert(exifData, inputImage.getvalue(), outputImage);
        var makerNote = new byte[] { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x10, 0x00 } + getImageHmac(key, outputImage.getvalue())[::16] + new byte[] { 0x01, 0x00, 0x10, 0x00 } + bytes.fromhex(titleID);
        var outputBytes = outputImage.getvalue().replace(makerNoteZero, makerNote);
        using (var file = open(outputPath, "wb")) {
            file.write(outputBytes);
        }
    }
    
    public class FirstRun
        : BaseWidget {
        
        public FirstRun(Hashtable kwargs, params object [] args)
            : base("First Run Popup") {
            this._firstrunlabel = ControlLabel("Hello! It looks like this is your first time\nrunning the app. Please go to the settings\nand fill the encryption key before using\nthe tool. Then, simply drag and drop your\nfiles in the centre of the app and press\n\"Go!\"");
            this.formset = new List<object> {
                "_firstrunlabel",
                " ",
                " "
            };
        }
    }
    
    public class NSScreenshotMakerGUI
        : BaseWidget {
        
        public NSScreenshotMakerGUI(Hashtable kwargs, params object [] args) {
            this._tmpinputfolder = tempfile.mkdtemp();
            this._settingsbutton = ControlButton("⚙️");
            this._settingsbutton.value = this.openSettings;
            this._runbutton = ControlButton("Go!");
            this._runbutton.value = this.go;
            this._combo = ControlCombo(helptext: "The game the Switch will think the screenshot is from");
            this.gameslist = games_json;
            foreach (var k in this.gameslist) {
                this._combo.add_item(k, this.gameslist[k]);
            }
            this._combo.add_item("Custom", "Custom");
            this._combolabel = ControlLabel("Game ID", helptext: "The game the Switch will think the screenshot is from");
            this._imagelist = ControlFilesTree();
            this._imagelist._form.setDragEnabled(true);
            this._imagelist._form.setAcceptDrops(true);
            this._imagelist._form.setDropIndicatorShown(true);
            this._imagelist._form.dropEvent = this.dropEvent;
            var model = QFileSystemModel(parent: null);
            model.setReadOnly(false);
            this._imagelist._form.setModel(model);
            model.setRootPath(QtCore.QDir.currentPath());
            this._imagelist._form.setRootIndex(model.setRootPath(this._tmpinputfolder));
            this._imagelist._form.setIconSize(QtCore.QSize(32, 32));
            this.formset = new List<object> {
                Tuple.Create("_combolabel", "_combo", "_settingsbutton"),
                "_imagelist",
                "_runbutton"
            };
            //First run initialization we'll see that after
            this._firstrunpanel = ControlDockWidget();
            this._firstrunpanel.hide();
            this._firstrunwin = FirstRun();
            if (!os.path.isfile(appdirs.AppDirs("NSScreenshotMaker", "").user_data_dir + "/settings.json")) {
                this._firstrunwin.parent = this;
                this._firstrunpanel.value = this._firstrunwin;
                this._firstrunpanel.show();
                this._firstrunwin.show();
            }
            this._settingspanel = ControlDockWidget();
            this._settingspanel.hide();
            this._settingswin = SettingsWindow();
        }
        
        public virtual object dropEvent(object @event) {
            if (@event.mimeData().hasUrls) {
                @event.setDropAction(QtCore.Qt.CopyAction);
                @event.accept();
                // to get a list of files:
                var drop_list = new List<object>();
                foreach (var url in @event.mimeData().urls()) {
                    drop_list.append(str(url.toLocalFile()));
                }
                // handle the list here
                foreach (var f in drop_list) {
                    try {
                        if (!f.endswith(".cbr") && !f.endswith(".cbz") && !f.endswith(".zip") && !f.endswith(".rar")) {
                            Image.open(f);
                        }
                        shutil.copy(f, this._tmpinputfolder);
                    } catch {
                    }
                }
            } else {
                @event.ignore();
            }
        }
        
        public virtual object closeEvent(object @event) {
            shutil.rmtree(this._tmpinputfolder);
        }
        
        public virtual object go() {
            if (os.listdir(this._tmpinputfolder).Count == 0) {
                return;
            }
            var prevFileName = "";
            var totalElements = 0;
            var state = 0;
            if (settings_json["type"] == "manga") {
                state = 1;
            }
            if (settings_json["type"] == "comics") {
                state = 2;
            }
            foreach (var fileName in os.listdir(this._tmpinputfolder)) {
                Console.WriteLine("Processing file " + fileName);
                totalElements += 1;
                if (fileName.endswith(".zip") || fileName.endswith(".cbz")) {
                    var zf = zipfile.ZipFile(this._tmpinputfolder + "/" + fileName);
                    foreach (var f in zf.infolist()) {
                        using (var fp = open(this._tmpinputfolder + "/" + f.filename, "wb")) {
                            fp.write(zf.read(f));
                        }
                    }
                } else if (fileName.endswith(".rar") || fileName.endswith(".cbr")) {
                    var rf = rarfile.RarFile(this._tmpinputfolder + "/" + fileName);
                    foreach (var f in rf.infolist()) {
                        using (var fp = open(this._tmpinputfolder + "/" + f.filename, "wb")) {
                            fp.write(rf.read(f));
                        }
                    }
                } else {
                    try {
                        if (state == 0) {
                            if (this._combo._items.values().ToList()[this._combo.current_index] != "Custom") {
                                processFile(this._tmpinputfolder + "/" + fileName, bytes.fromhex(settings_json["hmackey"]), this._combo._items.values().ToList()[this._combo.current_index], settings_json["outputfolder"]);
                            } else {
                                processFile(this._tmpinputfolder + "/" + fileName, bytes.fromhex(settings_json["hmackey"]), settings_json["customgameid"], settings_json["outputfolder"]);
                            }
                        } else if (prevFileName != "") {
                            if (this._combo._items.values().ToList()[this._combo.current_index] != "Custom") {
                                processFile(this._tmpinputfolder + "/" + fileName, bytes.fromhex(settings_json["hmackey"]), this._combo._items.values().ToList()[this._combo.current_index], settings_json["outputfolder"], state, this._tmpinputfolder + "/" + prevFileName);
                            } else {
                                processFile(this._tmpinputfolder + "/" + fileName, bytes.fromhex(settings_json["hmackey"]), settings_json["customgameid"], settings_json["outputfolder"], state, this._tmpinputfolder + "/" + prevFileName);
                            }
                            prevFileName = "";
                            continue;
                        }
                        prevFileName = fileName;
                    } catch {
                    }
                }
            }
            if (state != 0 && totalElements % 2 != 0) {
                if (this._combo._items.values().ToList()[this._combo.current_index] != "Custom") {
                    processFile(this._tmpinputfolder + "/" + fileName, bytes.fromhex(settings_json["hmackey"]), this._combo._items.values().ToList()[this._combo.current_index], settings_json["outputfolder"]);
                } else {
                    processFile(this._tmpinputfolder + "/" + fileName, bytes.fromhex(settings_json["hmackey"]), settings_json["customgameid"], settings_json["outputfolder"]);
                }
            }
        }
    }
}
