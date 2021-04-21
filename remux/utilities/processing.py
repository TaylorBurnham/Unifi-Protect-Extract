import os
import shutil
import logging
import tempfile
import subprocess
from pathlib import Path
from datetime import date, timedelta
from dateutil import parser


class UBVRemux():
    def __init__(self, config, auto_create_tmp=True):
        self.config = config
        self.logger = logging.getLogger(__name__)
        if auto_create_tmp:
            self.temp = tempfile.mkdtemp(
                dir=self.config.temp
            )
            self.logger.debug(
                f"Initialized with {self.temp} as temp path."
            )

    def clean_up(self):
        if len(os.listdir(self.temp)) == 0:
            self.logger.debug(
                f"Cleaning up {self.temp}"
            )
            shutil.rmtree(self.temp)
        else:
            self.logger.warning(
                f"Refusing to clean up {self.temp} due to remaining files."
            )

    def remux_ubv_by_date(self, date, cameras):
        self.logger.debug(f"Remuxing UBV files by date {date}.")
        ubv_files = self.get_ubv_by_date(date)
        self.prepare_ubv_files(ubv_files)
        self.logger.info(f"Beginning remux for {date}")
        for ubv_file in ubv_files:
            mp4_files = self.remux_file(ubv_file)
            for mp4_file in mp4_files:
                mp4dict = self.parse_mp4(mp4_file, cameras)
                result = self.move_mp4(mp4dict)  # noqa: F841
            self.logger.info(
                f"Marking {ubv_file['file']} as muxed."
            )
            self._set_file_muxed(ubv_file)

    def get_ubv_by_date(self, date):
        self.logger.debug(f"Getting UBV files by date {date}.")
        ubv_files = self.get_ubv_files()
        if isinstance(date, str):
            try:
                date = parser.parse(date)
            except parser.ParserError:
                raise ValueError(f"Couldn't parse {date}")
            date = date.date()
        if date in ubv_files:
            self.logger.debug(
                f"Returning {len(ubv_files[date])} files for {date}"
            )
            return ubv_files[date]

    def get_ubv_files(self, filter_age=True):
        self.logger.debug(
            f"Getting UBV files from {self.config.files}"
        )
        filelist = {}
        for root, folder, files in os.walk(self.config.files):
            if len(files) > 0:
                y, m, d = [int(x) for x in root.split(os.path.sep)[-3:]]
                filedate = date(y, m, d)
                # Find if any have been prepared
                ubv = [x for x in files if x.endswith('.ubv')]
                txt = [x for x in files if x.endswith('.txt')]
                muxed = [x for x in files if x.endswith('.muxed')]
                # This returns a list of dicts.
                # - prepared = True if the file has indices created.
                # - muxed = True if the file already has been remuxed
                remux_list = [
                    {
                        "file": os.path.join(root, x),
                        "prepared": (f"{x}.txt" in txt),
                        "muxed": (f"{x}.muxed" in muxed)
                    } for x in ubv
                ]
                # Add them to the list
                filelist[filedate] = remux_list
        # Filter down where filedate > min_age if true
        if filter_age:
            min_age_date = (
                date.today() - timedelta(days=self.config.min_age)
            )
            self.logger.debug(
                "Filtering for files older than "
                f"{self.config.min_age} days."
            )
            filelist = {
                k: v for k, v in filelist.items() if (k < min_age_date)
            }
        self.logger.debug(
            f"Returning {len(filelist)} of files."
        )
        return filelist

    def remux_file(self, ubv_file):
        if ubv_file['muxed']:
            self.logger.debug(
                f"Skipping {ubv_file['file']} - already remuxed"
            )
            mp4_files = None
        else:
            self.logger.debug(
                f"Performing remux against {ubv_file['file']}"
            )
            mp4_files = self._remux(ubv_file, self.config.temp)
        return mp4_files

    @staticmethod
    def _remux(ubv_file, temp_path):
        args = [
            "remux", "-with-audio", "-output-folder",
            temp_path, ubv_file['file']
        ]
        r = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        result = r.stderr.read()
        output_files = [
            x for x in str(result).split('\\n')
            if x.startswith('Writing MP4')
        ]
        if len(output_files) > 0:
            mp4_files = [
                next(
                    (y for y in x.split(' ') if temp_path in y), None
                ) for x in output_files
            ]
        else:
            mp4_files = None
        return mp4_files

    def prepare_ubv_files(self, ubv_files):
        t = len(ubv_files)
        for ubv_file in ubv_files:
            i = ubv_files.index(ubv_file) + 1
            if ubv_file['prepared']:
                self.logger.debug(
                    f"File {i}/{t} {ubv_file['file']} "
                    "is already prepared."
                )
                continue
            self.logger.debug(
                f"Preparing {i}/{t} {ubv_file['file']} in {self.temp}"
            )
            result = self._prepare_file(
                ubv_file, self.temp
            )
            if result:
                self.logger.debug(
                    f"Completed {i}/{t} {ubv_file['file']}"
                )

    def move_mp4(self, mp4dict):
        source_path = mp4dict['file']['path']
        self.logger.debug(
            f"Moving completed MP4 file {source_path}"
        )
        output_path = mp4dict['output']['path']
        output_file = mp4dict['output']['filename']
        if not os.path.exists(output_path):
            self.logger.debug(
                f"Creating output path {output_path}"
            )
            os.makedirs(output_path, exist_ok=True)
        output_filepath = os.path.join(
            output_path, output_file
        )
        self.logger.debug(
            f"Moving MP4 file to {output_filepath}"
        )
        newpath = shutil.move(
            source_path, output_filepath
        )
        return newpath

    def parse_mp4(self, mp4_file, cameras):
        self.logger.debug(
            f"Parsing MP4 File {mp4_file}"
        )
        # Parse the filename
        filepath, filename = os.path.split(mp4_file)
        filename, ext = os.path.splitext(filename)
        # Get the camera ID and date
        file_mac = filename.split('_')[0]
        file_date = filename.split('_')[-1].replace('.', ':')
        file_date = parser.parse(file_date)
        # Identify which camera it's from
        if file_mac in cameras:
            file_camera = cameras[file_mac]
            self.logger.debug(
                f"Identified Camera: {filename} -> {file_camera['name']}"
            )
        else:
            raise ValueError(
                f"Cannot identify {file_mac}. Is this a valid camera?"
                "Options: {cameras}"
            )
        output_path = os.path.join(
            self.config.output,
            file_date.strftime("%Y-%m-%d"),
            file_camera['name']
        )
        self.logger.debug(f"Setting output path: {output_path}")
        of = "_".join([
            file_camera['name'],
            file_date.strftime("%Y-%m-%d_%H-%M-%S")
        ])
        output_file = f"{of}{ext}"
        self.logger.debug(f"Setting output name: {output_file}")
        mp4dict = {
            "file": {
                "path": mp4_file,
                "folder": filepath,
                "filename": filename,
                "ext": ext
            },
            "output": {
                "path": output_path,
                "filename": output_file
            }
        }
        self.logger.debug(f"Returning dict for {mp4_file}")
        return mp4dict

    @staticmethod
    def _set_file_muxed(ubv_file):
        muxed_filepath = f"{ubv_file['file']}.muxed"
        Path(muxed_filepath).touch()

    @staticmethod
    def _prepare_file(ubv_file, temp_path):
        ubv_filepath, ubv_filename = os.path.split(ubv_file['file'])
        stdout_file = f"{ubv_filename}.txt"
        stdout_path = os.path.join(temp_path, stdout_file)
        with open(stdout_path, 'wb') as out:
            args = ['ubnt_ubvinfo', '-P', '-f', ubv_file['file']]
            p = subprocess.Popen(args, stdout=out, cwd=temp_path)
            result = p.wait()
        if result == 0:
            success = shutil.move(
                stdout_path, os.path.join(ubv_filepath, stdout_file)
            )
        else:
            success = False
        return success
