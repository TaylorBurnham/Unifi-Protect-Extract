# Unifi-Protect-Extract
A collection of scripts and utilities that I use to extract videos from my CloudKey Gen 2 running Unifi Protect.

# Introduction

For some reason Ubiquiti has decided that there's no reason to provide long term archival solutions for the Unifi Protect platform. I imagine this is because they use the UBV file format, which are block containers, and to extract the footage would put too much demand on the system. You can upgrade the hard drive to get longer retention, but it doesn't solve the underlying issue that pulling large portions of video can be very time consuming.

The solution for this came from [petergeneric](https://github.com/petergeneric) in the form of a tool to automate the extraction using `ffmpeg` called [unifi-protect-remux](https://github.com/petergeneric/unifi-protect-remux). The `remux` utility will extract the footage into MP4 files with H.264 and AAC encoding. You can read more about it on the project's page.

The issue I faced was I didn't want to run this on my CloudKey since it's not the beefiest system, and I have other systems I can make use of to do this. This is where this project comes in.

## Objectives

The objective of this project is to automate the extraction and filing of footage. I intend on doing this through:

* Running `rsync` on the CloudKey to ship UBV files onto my Synology NAS.
* Running the `prepare.sh` utility to extract the timecodes from the UBV files for `remux`.
* Running the `remux` utility to extract the files.
* Combining the output files and then splitting them into more managable segments.
* Utilizing the Unifi Protect API to name the files based off the source of the footage.
* Then finally storing the footage in a location that can be indexed and searched.

## Requirements

This is my environment that I am running it on.

* CloudKey Gen2+ v2.0.27
* Protect v1.17.3
* Synology NAS Rackstation RS819
* Debian 10 running under Windows Subsystem for Linux

# Getting Started
## CloudKey Setup

These steps will get the CloudKey set up for synchronizing the UBV files to another location. There is a lockfile stored at `/tmp/cloudkey-sync.sh.lock` to prevent multiple instances from running at once. If for some reason you notice synchronization isn't happening make sure that file doesn't exist.

1. Install rsync on the CloudKey.

   `apt install rsync`

2. Generate SSH keys on the CloudKey and copy them to the destination server where you will be synchronizing to.

    `ssh-keygen -t rsa -b 4096`

3. Move the `cloudkey-sync.sh` script onto your CloudKey and make it executable.

    `chmod +x cloudkey-sync.sh`

4. Update the following variables.

    `$RSYNC_USER` with the account you will log on the destination server with.

    `$RSYNC_HOST` with the destination server name.

    `$SYNC_PATH` with the on the destination server you will be synchronizing the files to.

5. Run the script to do the initial synchronization.
6. Add a crontab entry to synchronize the data at whatever interval you prefer. I only want to do every 2 hours since the UBV files are stored in 1GB blocks and usually roll over every 2-3 hours.

    `0 */2 * * * /root/cloudkey-sync.sh`

The files should synchronize and depending on your network speed, the retention policy on the CloudKey, and other things it could take some time.

## Processing Server Scripts

Now that the files are stored on a network share I will want to run the preparation utility provided by Peter to generate the necessary timecodes to extract footage. The out of the box script he provides works, but I modified it to work on my workstation.

1. Install the necessary utilities to run `qemu-user` and `ffmpeg`.

    `sudo apt install -y qemu-user gcc-aarch64-linux-gnu ffmpeg`

2. Copy the `ubnt_ubvinfo` from your Unifi Protect installation onto your Linux machine. You can locate it under this path.

    `/usr/share/unifi-protect/app/node_modules/.bin/ubnt_ubvinfo`

3. Move it to `/usr/bin` and prefix it with `arm-`.

    `sudo mv ubnt_ubvinfo /usr/bin/arm-ubnt_ubvinfo`

4. Create a wrapper script to call upon this with the right libraries so it has ARM support and make it executable.

    ```sudo tee /usr/bin/ubnt_ubvinfo <<EOF
    #!/bin/sh
    export QEMU_LD_PREFIX=/usr/aarch64-linux-gnu
    exec qemu-aarch64 /usr/bin/arm-ubnt_ubvinfo \$*
    EOF
    chmod +x /usr/bin/ubnt_ubvinfo```
5. Install the `ubv-prepare.sh` script to `/usr/bin` and make it executable.

    `chmod +x /usr/bin/ubv-prepare.sh`

6. Installed `remux` to your path by downloading it from the [release page](https://github.com/petergeneric/unifi-protect-remux/releases), then put it in the right directory.

    ```
    wget https://github.com/petergeneric/unifi-protect-remux/releases/download/3.0.2/remux-x86_64.tar.gz
    tar xfvz remux-x86_64.tar.gz
    sudo mv remux /usr/bin/
    ```

## Scheduling Processing

It's up to you how to handle this. Do you want to output them in the same directory, or somewhere else where a media server can index them? I'll be processing them into a separate directory and grouping by camera, then the additional processing.

**This is a work in progress.**