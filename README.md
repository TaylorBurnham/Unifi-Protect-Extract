# Unifi-Protect-Extract
A collection of scripts and utilities that I use to extract videos from my CloudKey Gen 2 running Unifi Protect.

# Introduction

For some reason Ubiquiti has decided that there's no reason to provide long term archival solutions for the Unifi Protect platform. I imagine this is because they use the UBV file format, which are block containers, and to extract the footage would put too much demand on the system. You can upgrade the hard drive to get longer retention, but it doesn't solve the underlying issue that pulling large portions of video can be very time consuming and you have no way of archiving these for legal reasons.

The solution for this came from [petergeneric](https://github.com/petergeneric) in the form of a tool to automate the extraction using `ffmpeg` called [unifi-protect-remux](https://github.com/petergeneric/unifi-protect-remux). The `remux` utility will extract the footage into MP4 files with H.264 and AAC encoding. You can read more about it on the project's page.

The issue I faced was I didn't want to run this on my CloudKey since it's not the beefiest system, and I have other systems I can make use of to do this. This is where this project comes in.

## Objectives

The objective of this project is to automate the extraction and filing of footage. I originally began writing this in bash, but as I put more time into it I realized what a colossal pain it was to deal with making calls to the Protect API using cURL, handling session tokens, CSRF, etc. This led to me rewriting this in Python 3 and it's much more flexible in my opinion.

* A Shell script will be installed on the CloudKey to push .UBV containers onto a remote host.
* A Python script will be installed on my workstation which has some horsepower behind it to wrap around the `remux` utility.

## Requirements

This is my environment that I am running it on.

* CloudKey Gen2+ v2.0.27
* Protect v1.17.3
* Synology NAS Rackstation RS819
* Debian 10 running under Windows Subsystem for Linux
* [Unifi Protect Remux](https://github.com/petergeneric/unifi-protect-remux/)
* Python 3.5+

### A Note about WSL

If you plan to run this in WSL you should know that it will take up a lot of memory and not release it. An open [Issue 4166](https://github.com/microsoft/WSL/issues/4166) on the WSL Github talks about this and there's lots of reasons why this isn't a bad thing but can look like a bad thing, which I won't get into. Nonetheless you can fix this by placing a file called `.wslconfig` in your `%HOMEPATH%` limiting the maximum memory for WSL instances.

```
[wsl2]
memory=12GB
swap=0
```

For more details on `.wslconfig` review [Global Options with wslconfig](https://docs.microsoft.com/en-us/windows/wsl/wsl-config#configure-global-options-with-wslconfig).

# Getting Started
## CloudKey Setup

These steps will get the CloudKey set up for synchronizing the UBV files to another location. There is a lockfile stored at `/tmp/cloudkey_sync.lock` to prevent multiple instances from running at once. If for some reason you notice synchronization isn't happening make sure that file doesn't exist.

1. Install rsync on the CloudKey.

   `apt install rsync`

2. Generate SSH keys on the CloudKey and copy them to the destination server where you will be synchronizing to.

    `ssh-keygen -t rsa -b 4096`

3. Move the `cloudkey_sync` script onto your CloudKey, place it in the `/root/bin` folder, and make it executable.

    ```
    mkdir /root/bin
    mv cloudkey_sync /root/bin/.
    chmod a+x /root/bin/cloudkey_sync
    ```

4. Update the following variables.

    `$RSYNC_USER` with the account you will log on the destination server with.

    `$RSYNC_HOST` with the destination server name.

    `$SYNC_PATH` with the on the destination server you will be synchronizing the files to.

    You can also update the optional variable below, but I recommend keeping it to 1 day.

    `$RSYNC_AGE` will determine how far back to go to synchronize files. This is important for your remux process on the other end so you do not remux and purge files that will just be re-synchronized.

5. Run the script to do the initial synchronization and set the number of days to the maximum age you want to synchronize.

    `/root/bin/cloudkey_sync 7`

    In this case I am only going to grab the last 7 days for my initial pull.

6. Add a crontab entry to synchronize the data at whatever interval you prefer. I only want to do every 4 hours since the UBV files are stored in 1GB blocks and usually roll over every 2-3 hours.

    `0 */4 * * * /root/bin/cloudkey_sync`

    The UBV format means that each time they roll over a new file is allocated in that 1GB block, and rsync will detect changes on that file and synchronize it. That's a waste of time in my opinion and it's better to just run every 4 hours and avoid wasted CPU time.

The files should synchronize and depending on your network speed, the retention policy on the CloudKey, and other things it could take some time.

## Identifying Cameras

All of the output files are named with the MAC address of the camera that was recorded, which isn't very useful for identifying where the originating footage came from. To overcome this we can query the API of the CloudKey Protect instance to return the list of cameras, and this makes it easier to add cameras in the future.

### Credentialing the API User

Your account should be as least privileged as possible since it will be a local authentication account. Mine was granted View Only on UniFi Protect and None on UniFi Network, and I also assigned a very long password.

Once this account is created store the username and password somewhere secure, such as KeePass, 1Password, or anywhere but a plain text file.

## Processing Server Scripts

Now that the files are stored on a network share I will want to run the preparation utility provided by Peter to generate the necessary timecodes to extract footage. The out of the box script he provides works, but I modified it to work on my workstation.

1. Install the necessary utilities to run `qemu-user` and `ffmpeg`.

    `sudo apt install -y qemu-user gcc-aarch64-linux-gnu ffmpeg`

2. Copy the `ubnt_ubvinfo` from your Unifi Protect installation onto your Linux machine. You can locate it under this path.

    `/usr/share/unifi-protect/app/node_modules/.bin/ubnt_ubvinfo`

3. Move it to `/usr/local/bin` and prefix it with `arm-`.

    `sudo mv ubnt_ubvinfo /usr/local/bin/arm-ubnt_ubvinfo`

4. Create a wrapper script to call upon this with the right libraries so it has ARM support and make it executable.

    ```sudo tee /usr/local/bin/ubnt_ubvinfo <<EOF
    #!/bin/sh
    export QEMU_LD_PREFIX=/usr/aarch64-linux-gnu
    exec qemu-aarch64 /usr/local/bin/arm-ubnt_ubvinfo \$*
    EOF
    chmod +x /usr/local/bin/ubnt_ubvinfo```

5. Install `remux` to your path by downloading it from the [release page](https://github.com/petergeneric/unifi-protect-remux/releases), then put it in the `/usr/local/bin` directory.

    ```
    wget https://github.com/petergeneric/unifi-protect-remux/releases/download/3.0.2/remux-x86_64.tar.gz
    tar xfvz remux-x86_64.tar.gz
    sudo mv remux /usr/local/bin/
    ```

Depending on which user is going to run this you need to pause and credential them, give access to the files, etc. Once this is done you will have to create the folder for the processing scripts.

7. As the user that will be running this script create a directory to hold the script and dotenv file.

    `mkdir -pv "${HOME}/bin/unifi-protect-extract"`

8. Place the `ubnt_process` file in that location, and copy the `.env.example` file into the directory with the name `.env`. Make `ubnt_process` executable.

    ```
    cp ubnt_process "${HOME}/bin/unifi-protect-extract/."
    cp .env.example "${HOME}/bin/unifi-protect-extract/.env"
    chmod +x "${HOME}/bin/unifi-protect-extract/ubnt_process"
    ```

9. Update the `.env` file with the proper settings.

    `CLOUDKEY_CONTROLLER` with the hostname of your CloudKey controller.

    `CLOUDKEY_USERNAME` with the username of the service account you created.

    `CLOUDKEY_PASSWORD` with the password of the service account you created.

    `CLOUDKEY_VERIFY_SSL` with Yes or No. If you do not have an SSL certificate installed on your CloudKey you should, but this lets you bypass verification if you live life like nobody is watching.

    `UBV_FILES` with the location of the synchronized UBV files.

    `UBV_TEMP` with a temporary location for files to go as they are processed.

    `UBV_OUTPUT` with the location for the processed output files.

    `UBV_ARCHIVE` with the location to archive .UBV files for eventual deletion.

8. Make the file owned by the user and only accessible by them.

    ```
    sudo chown -Rv $(whoami):$(whoami) "${HOME}/bin/unifi-protect-extract/."
    sudo chmod 700 "${HOME}/bin/unifi-protect-extract/"
    sudo chmod 600 "${HOME}/bin/unifi-protect-extract/.env"
    ```

## Scheduling Processing

### Processing Times

It's up to you how to handle this. Do you want to output them in the same directory, or somewhere else where a media server can index them? I'll be processing them into a separate directory and grouping by camera, then the additional processing.

For my Debian 9 WSL2 instance I've capped it at 12GB memory and it has full use of the AMD Ryzen 7 2700X. End to end processing the 1080p files can vary on duration. My Debian WSL2 instance is accessing these files via NFS mount so there are bottlenecks on the network when handling the files. However, even if the indices aren't created in advance I see 15 - 45 seconds per file.

I do not have any 4K cameras to run against but if it uses the same 1GB structure it should be easy to estimate the time to process, but it may take more time in ffmpeg due to the file size.

My cameras record at 30FPS with 50% quality to minimize it's storage use. This results in 14 files per camera per day for a total of about 14GB. My expectation of processing times per day will be:

`time to process = (cameras * 14 * 30)`

I had 70 files for a single day that took 30 minutes and 15 seconds to process end to end with the indices already created, which isn't that bad.

### Scheduling via Crontab

**TODO - Pending params**

# TODO

 - [x] Update Python script with docstrings
 - [ ] Update Python script with arguments for passing params
 - [x] Update Python script to archive UBV files for purging.
 - [x] Replace `/etc/` conf files with `dotenv`
 - [ ] Update `cloudkey_sync` to have a Python script feed filelists to rsync to be even more granular.
 - [ ] Finish this document
   - [ ] Scheduling via Crontab
   - [ ] Do a dry run end to end of this document.