import os
import sys
import shutil
import logging
import tempfile
import subprocess
from dotenv import load_dotenv
from datetime import date, datetime
from dateutil import parser

def parse_output_file(filepath):
    """Parses the Output File Name

    Args:
        filepath (str): The full path to the filename to parse.

    Returns:
        dict: A dict containing the path to the file, the base name,
            the file extension, the camera MAC address from the file,
            and the datetime of the file's creation.
    """
    logger.debug("Parsing {}".format(filepath))
    # Get the basename of the file
    filename = os.path.basename(filepath)
    fileext = filepath.split(os.path.extsep)[-1]
    # Remove the extension for further parsing
    filename = filename.replace(".{}".format(fileext),"")
    # Get the MAC address of the camera.
    camera = filename.split('_')[0]
    # Get the date of the file.
    date = parser.parse(filename.split('_')[-1].replace('.',':'))
    file_data = {
        "path": filepath,
        "name": filename,
        "ext": fileext,
        "camera": camera,
        "date": date
    }
    return file_data



def get_ubv_files(ubv_path, min_age=3):
    """Locates UBV files in the given path older than X days.

    Args:
        ubv_path (str): The path to the UBV files.
        min_age (int, optional): The minimum age for files. Defaults to 3.

    Returns:
        dict: Returns a dict with the key as the base path to the files
            and contains a dict with the datetime of the folder and a
            list of the files and if they have indices generates.
    """
    logger.info("Searching for UBV files older than {} days in {}".\
        format(min_age, ubv_path))
    ubv_files = {}
    for root, dirname, filename in os.walk(ubv_path):
        if len(filename) > 0:
            if root not in ubv_files:
                ubv_date = "-".join(
                    [x for x in root.replace(ubv_path, "").split(os.path.sep) if x]
                )
                ubv_date = parser.parse(ubv_date)
                ubv_files[root] = {
                    "files": [],
                    "date": ubv_date
                }
            for f in [x for x in filename if x.endswith('.ubv')]:
                ubv_files[root]['files'].append({
                    "file": os.path.join(root, f),
                    "prepared": (f + ".txt" in filename)
                })
    # Filter files older than min_age days
    ubv_files = {
        x[0]: x[1] for x in ubv_files.items() if (datetime.now() - x[1]['date']).days > min_age
    }
    logger.info("Found {} total days worth of files.".format(len(ubv_files.keys())))
    return ubv_files

def archive_ubv_file(ubv_file, archive_path):
    """Archives the given UBV file to the path. Will create the directory
       if it doesn't exist.

    Args:
        ubv_file (dict): The UBV file dict.
        archive_path (str): The base path for the archive.
    """
    logger.debug("Archiving {} to {}.".format(ubv_file['file'], archive_path))
    ubv_filename = ubv_file['file'].split(os.path.sep)[-1]
    ubv_filepath = ubv_file['file'].replace(ubv_filename, "")
    ubv_basepath = ubv_filepath.replace(config['paths']["ubv_files"] + "/", "")
    ubv_archivepath = os.path.join(archive_path, ubv_basepath)
    ubv_archivefile = os.path.join(ubv_archivepath, ubv_filename)
    ubv_index_archivefile = os.path.join(ubv_archivepath, (ubv_filename + ".txt"))
    os.makedirs(ubv_archivepath, exist_ok=True)
    logger.debug("Moving {} to archive path {}".format(ubv_filename, ubv_archivepath))
    shutil.move(ubv_file['file'], ubv_archivefile)

def prepare_ubv_file(ubv_file, tmp_path):
    """Runs the ubnt_ubvinfo script against the given UBV file.

    Args:
        ubv_file (dict): The UBV file dict.
        tmp_path (str): The temporary path the script is using.
    """
    ubv_filename = ubv_file['file'].split(os.path.sep)[-1]
    logger.debug("Creating Indexes for {}".format(ubv_filename))
    ubv_filepath = ubv_file['file'].replace(ubv_filename, "")

    stdout_file = "{}.txt".format(ubv_filename)
    stdout_path = os.path.join(tmp_path, stdout_file)
    with open(stdout_path, 'wb') as out:
        args = ['ubnt_ubvinfo', '-P', '-f', ubv_file['file']]
        p = subprocess.Popen(args, stdout=out, cwd=tmp_path)
        result = p.wait()
    if result == 0:
        logger.debug("Moving Index file {} to {}".format(stdout_file, ubv_filepath))
        new_path = shutil.move(stdout_path, os.path.join(ubv_filepath, stdout_file))
    else:
        logger.error("Failed to create UBV index file.")

def remux_file(ubv_file, tmp_path):
    """Runs the remux utility against the given UBV file.

    Args:
        ubv_file (dict): The UBV file dict.
        tmp_path (str): The temporary path the script is using.

    Returns:
        str: The name of the generated MP4 file.
    """
    logger.info("Running remux against {}".format(
        ubv_file['file'].split(os.path.sep)[-1]))
    args = ['remux', '-with-audio', '-output-folder', tmp_path, ubv_file['file']]
    r = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    r.wait()
    # When completed get the name of the output file.
    resulterr = r.stderr.read()
    output_files = [x for x in str(resulterr).split('\\n') if x.startswith('Writing MP4')]
    if len(output_files) > 0:
        mp4_files = [next((y for y in x.split(' ') if tmp_path in y), None) for x in output_files]
        logger.info("Completed remux of {}".format(ubv_file['file']))
        for mp4_file in mp4_files:
            logger.debug("Output File(s): {}".format(mp4_file))
        return mp4_files
    else:
        logger.error("Failed to remux file. Full output:\n{}\n".format(str(resulterr)))

def process_ubv_files(ubv_files, tmp_path, output_path, archive_path):
    """The main utility to wrap around the process for handling UBV files.

    Args:
        ubv_files (dict): The list of UBV files to process.
        tmp_path (str): The temporary path the script is using.
        output_path (str): The output path from the configuration file.
        archive_path (str): The archive path from the configuration file.
    """
    # Get the camera information.
    camera_info = get_cameras(
        config['cloudkey']['controller'], config['cloudkey']['username'],
        config['cloudkey']['password'], verify_ssl
    )
    for ubv_folder, ubv_data in ubv_files.items():
        logger.info("Processing {}".format(ubv_data['date'].strftime("%Y-%m-%d")))
        for ubv_file in ubv_data['files']:
            logger.debug("Handling {}".format(ubv_file['file']))
            if not ubv_file['prepared']:
                logger.debug("File hasn't been prepared with indexes.")
                prepare_ubv_file(ubv_file, tmp_path)
            mp4_files = remux_file(ubv_file, tmp_path)
            for mp4_file in mp4_files:
                logger.debug("Relocating {}".format(mp4_file))
                mp4_data = parse_output_file(mp4_file)
                mp4_data['camera'] = camera_info[mp4_data['camera']]
                mp4_output_date = mp4_data['date'].strftime("%Y-%m-%d".format(os.path.sep))
                mp4_output_path = os.path.join(
                    config['paths']['ubv_output'], mp4_output_date, mp4_data['camera']['name']
                )
                os.makedirs(mp4_output_path, exist_ok=True)
                # Now move the file
                mp4_filename = "{}.mp4".format("_".join([mp4_data['camera']['name'], mp4_data['date'].isoformat().replace(':','.')]))
                mp4_output_file = os.path.join(
                    mp4_output_path, mp4_filename
                )
                new_path = shutil.move(mp4_data['path'], mp4_output_file)
                logger.info("Moved output MP4 to {}".format(new_path))
            # Archive
            archive_ubv_file(
                ubv_file, archive_path
            )
