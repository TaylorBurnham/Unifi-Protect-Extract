# Work in Progress Warning

**Use this at your own risk. It is _mostly_ working but you should be wary of any script with a single contributor.** Feedback is welcome.

I've nuked this to start from scratch. You can work from older commits at your own risk. For now if you want to follow this project and retain your UBV files for when it's ready I've left the `cloudkey_sync` script in the `shell_scripts` folder. The basic functionality is available in the `remux.py` script and the usage is below. As of now it will not remove any files.

    usage: remux.py [-h] [--environment ENVIRONMENT] [--parse-date PARSE_DATE] [--parse-all     [PARSE_ALL]]
                    [--list-dates [LIST_DATES]]

    Unifi Protect Extract - A Working Title!

    optional arguments:
      -h, --help            show this help message and exit
      --environment ENVIRONMENT, -e ENVIRONMENT
                            The location of the .env file. Defaults to '.env'
      --parse-date PARSE_DATE, -pd PARSE_DATE
                            Parse UBV files from a specific date.
      --parse-all [PARSE_ALL], -pa [PARSE_ALL]
                            Parse all UBV files available.
      --list-dates [LIST_DATES], -ls [LIST_DATES]
                            List all of the dates available for parsing.

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

## Script Setup

At a high level you need to do the following:

* Create a Python 3.9 environment.
* Install requirements via `pip install -r requirements.txt`
* Copy the `.env.example` to `.env` and configure accordingly.

To verify your configuration is _mostly_ working you can run the command below to list available files.

```shell
remux.py --list-dates
```

Example output is below.

    [2021-06-19 13:04:28,695] {processing.py:136} INFO - Found the following files:
    +------------+----------+----------+------------+------------+-------+
    |    Date    | Backyard | Driveway | Rear Entry | Front Yard | Total |
    +------------+----------+----------+------------+------------+-------+
    | 2021-01-27 |    7     |    9     |     8      |     12     |   36  |
    | 2021-01-28 |    15    |    14    |     13     |     22     |   64  |
    | 2021-01-29 |    16    |    14    |     14     |     22     |   66  |
    | 2021-01-30 |    13    |    14    |     13     |     22     |   62  |

From this you can run `remux.py --parse-date <date>`, and it will begin remuxing those files, or you can run `remux.py --parse-all` to parse all files available. By default it will not parse files uploaded within 3 days to avoid conflicts with the sync script, but I plan to fix this in the future.
